"""
FastAPI route handlers for nutrition tracking API.
"""
import os
import base64
import io
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from api.models import (
    GetNutritionRequest,
    NutritionBoardRequest,
    SuggestDishesRequest,
    LockDishRequest,
    ScanGroceryBillRequest,
    NutritionResponse,
    NutritionBoardResponse,
    SuggestDishesResponse,
    LockDishResponse,
    GroceryBillResponse,
    HealthResponse,
)
from nutrition_tracker.tracker import get_nutrition_from_gemini, suggest_dishes_from_gemini
from nutrition_tracker.db import AsyncSessionLocal
from nutrition_tracker.models import User, NutritionLog, NutritionTotals

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint to verify API is running."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat(),
        service="Nutrition Tracker API"
    )


@router.post("/nutrition", response_model=NutritionResponse, tags=["Nutrition"])
async def get_nutrition(request: GetNutritionRequest):
    """
    Get detailed nutrition information for any food or meal using Gemini AI.
    
    Provide the user ID, food name, and amount (with units).
    Returns calories, protein, carbs, and fat estimates.
    """
    if not request.user_id:
        raise HTTPException(status_code=400, detail="User ID is required.")
    
    try:
        nutrition = get_nutrition_from_gemini(request.food, request.amount)
        required_keys = ["calories", "protein", "carbs", "fat"]
        
        if not nutrition or any(nutrition.get(k) is None for k in required_keys):
            raise HTTPException(
                status_code=500,
                detail=f"Could not get nutrition info for {request.amount} {request.food}. Please try a different food or amount."
            )
        
        return NutritionResponse(**nutrition)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nutrition/board", response_model=NutritionBoardResponse, tags=["Nutrition"])
async def get_nutrition_board(request: NutritionBoardRequest):
    """
    Get user's current nutrition scoreboard (totals).
    
    Returns the running total of calories, protein, carbs, and fat consumed by the user.
    """
    if not request.user_id:
        raise HTTPException(status_code=400, detail="User ID is required.")
    
    try:
        async with AsyncSessionLocal() as session:
            user = (await session.execute(
                select(User).where(User.user_id == request.user_id)
            )).scalar_one_or_none()
            
            if not user:
                return NutritionBoardResponse(
                    user_id=request.user_id,
                    calories=0.0,
                    protein=0.0,
                    carbs=0.0,
                    fat=0.0
                )
            
            totals = (await session.execute(
                select(NutritionTotals).where(NutritionTotals.user_id == user.id)
            )).scalar_one_or_none()
            
            if not totals:
                return NutritionBoardResponse(
                    user_id=request.user_id,
                    calories=0.0,
                    protein=0.0,
                    carbs=0.0,
                    fat=0.0
                )
            
            return NutritionBoardResponse(
                user_id=request.user_id,
                calories=totals.calories,
                protein=totals.protein,
                carbs=totals.carbs,
                fat=totals.fat
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recipes/suggest", response_model=SuggestDishesResponse, tags=["Recipes"])
async def suggest_dishes(request: SuggestDishesRequest):
    """
    Suggest 3 creative, healthy dish names using ONLY the provided ingredients.
    
    Provide a list of ingredients and get dish suggestions powered by Gemini AI.
    """
    if not request.ingredients or not isinstance(request.ingredients, list):
        raise HTTPException(
            status_code=400,
            detail="Ingredients must be a non-empty list of strings."
        )
    
    try:
        dishes = suggest_dishes_from_gemini(request.ingredients)
        
        if not dishes:
            raise HTTPException(
                status_code=500,
                detail="Could not get dish suggestions from Gemini."
            )
        
        return SuggestDishesResponse(dishes=dishes)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nutrition/lock", response_model=LockDishResponse, tags=["Nutrition"])
async def lock_dish(request: LockDishRequest):
    """
    Log a custom dish and its nutrition facts to the nutrition tracker.
    
    Provide user ID, dish name, and nutrition dictionary (calories, protein, carbs, fat).
    The dish will be added to the user's daily nutrition log and totals will be updated.
    """
    required_keys = {"calories", "protein", "carbs", "fat"}
    
    if not request.user_id:
        raise HTTPException(status_code=400, detail="User ID is required.")
    
    if not request.dish:
        raise HTTPException(status_code=400, detail="Dish name is required.")
    
    if not request.nutrition or not required_keys.issubset(request.nutrition) or any(
        request.nutrition[k] is None for k in required_keys
    ):
        raise HTTPException(
            status_code=400,
            detail="Nutrition must include valid calories, protein, carbs, and fat (not None)."
        )
    
    try:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': request.user_id,
            'food': request.dish,
            'amount': 1,
            'nutrition': {k: float(request.nutrition[k]) for k in required_keys}
        }
        
        async with AsyncSessionLocal() as session:
            # Get or create user
            user = (await session.execute(
                select(User).where(User.user_id == request.user_id)
            )).scalar_one_or_none()
            
            if not user:
                user = User(user_id=request.user_id)
                session.add(user)
                await session.flush()
            
            # Add nutrition log for dish
            log = NutritionLog(
                user_id=user.id,
                food=request.dish,
                amount=1,
                calories=request.nutrition['calories'],
                protein=request.nutrition['protein'],
                carbs=request.nutrition['carbs'],
                fat=request.nutrition['fat']
            )
            session.add(log)
            
            # Update totals
            totals = (await session.execute(
                select(NutritionTotals).where(NutritionTotals.user_id == user.id)
            )).scalar_one_or_none()
            
            if not totals:
                totals = NutritionTotals(
                    user_id=user.id,
                    calories=0.0,
                    protein=0.0,
                    carbs=0.0,
                    fat=0.0,
                )
                session.add(totals)
            
            totals.calories = (totals.calories or 0.0) + request.nutrition['calories']
            totals.protein = (totals.protein or 0.0) + request.nutrition['protein']
            totals.carbs = (totals.carbs or 0.0) + request.nutrition['carbs']
            totals.fat = (totals.fat or 0.0) + request.nutrition['fat']
            
            await session.commit()
        
        return LockDishResponse(**log_entry)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr/grocery-bill", response_model=GroceryBillResponse, tags=["OCR"])
async def scan_grocery_bill(request: ScanGroceryBillRequest):
    """
    Scan a grocery bill image and extract a list of purchased items using Azure AI Vision OCR.
    
    Provide a base64-encoded image of the grocery bill to extract item names.
    """
    from azure.cognitiveservices.vision.computervision import ComputerVisionClient
    from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
    from msrest.authentication import CognitiveServicesCredentials
    
    VISION_KEY = os.environ.get("VISION_KEY")
    VISION_ENDPOINT = os.environ.get("VISION_ENDPOINT")
    
    if not VISION_KEY or not VISION_ENDPOINT:
        raise HTTPException(
            status_code=500,
            detail="Azure Vision credentials not set in environment."
        )
    
    try:
        image_bytes = base64.b64decode(request.image_base64)
        computervision_client = ComputerVisionClient(
            VISION_ENDPOINT, CognitiveServicesCredentials(VISION_KEY)
        )
        
        image_stream = io.BytesIO(image_bytes)
        read_response = computervision_client.read_in_stream(image_stream, raw=True)
        operation_location = read_response.headers["Operation-Location"]
        operation_id = operation_location.split("/")[-1]
        
        while True:
            result = computervision_client.get_read_result(operation_id)
            if result.status not in ["notStarted", "running"]:
                break
            time.sleep(1)
        
        if result.status == OperationStatusCodes.succeeded:
            lines = []
            for page in result.analyze_result.read_results:
                for line in page.lines:
                    lines.append(line.text)
            
            # Simple heuristic: filter out lines that look like totals, prices, etc.
            items = [
                l for l in lines 
                if l and not any(x in l.lower() for x in ["total", "amount", "price", "rs", "$", "qty", "tax"])
            ]
            
            return GroceryBillResponse(items=items)
        else:
            raise HTTPException(
                status_code=500,
                detail="OCR failed to extract text from image."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
