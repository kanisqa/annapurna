"""
Pydantic models for FastAPI request and response validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime


# === Request Models ===

class GetNutritionRequest(BaseModel):
    """Request model for getting nutrition information."""
    user_id: str = Field(..., description="Unique user identifier")
    food: str = Field(..., description="Food name (e.g., 'apple', 'chicken breast')")
    amount: float = Field(..., description="Amount (e.g., 2 for 2 apples or 100 for 100g)")


class NutritionBoardRequest(BaseModel):
    """Request model for getting user's nutrition totals."""
    user_id: str = Field(..., description="Unique user identifier")


class SuggestDishesRequest(BaseModel):
    """Request model for suggesting dishes from ingredients."""
    ingredients: list[str] = Field(
        ..., 
        description="List of available ingredients (e.g., ['egg', 'spinach', 'cheese'])",
        min_length=1
    )


class LockDishRequest(BaseModel):
    """Request model for logging a custom dish."""
    user_id: str = Field(..., description="Unique user identifier")
    dish: str = Field(..., description="Name of the dish to log")
    nutrition: dict[str, float] = Field(
        ..., 
        description="Nutrition facts (must include: calories, protein, carbs, fat)"
    )


class ScanGroceryBillRequest(BaseModel):
    """Request model for scanning grocery bill via OCR."""
    user_id: str = Field(..., description="Unique user identifier")
    image_base64: str = Field(..., description="Base64-encoded image data of the grocery bill")


# === Response Models ===

class NutritionResponse(BaseModel):
    """Response model for nutrition information."""
    calories: float = Field(..., description="Calories in kcal")
    protein: float = Field(..., description="Protein in grams")
    carbs: float = Field(..., description="Carbohydrates in grams")
    fat: float = Field(..., description="Fat in grams")


class NutritionBoardResponse(BaseModel):
    """Response model for user's nutrition totals."""
    user_id: str = Field(..., description="User identifier")
    calories: float = Field(..., description="Total calories consumed")
    protein: float = Field(..., description="Total protein consumed (grams)")
    carbs: float = Field(..., description="Total carbs consumed (grams)")
    fat: float = Field(..., description="Total fat consumed (grams)")


class SuggestDishesResponse(BaseModel):
    """Response model for dish suggestions."""
    dishes: list[str] = Field(..., description="List of 3 suggested dish names")


class LockDishResponse(BaseModel):
    """Response model for logged dish entry."""
    timestamp: str = Field(..., description="ISO 8601 timestamp of when dish was logged")
    user_id: str = Field(..., description="User identifier")
    food: str = Field(..., description="Dish name")
    amount: int = Field(..., description="Amount (always 1 for dishes)")
    nutrition: dict[str, float] = Field(..., description="Nutrition breakdown")


class GroceryBillResponse(BaseModel):
    """Response model for OCR extracted grocery items."""
    items: list[str] = Field(..., description="List of detected grocery item names")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current server time (ISO 8601)")
    service: str = Field(..., description="Service name")


class ErrorResponse(BaseModel):
    """Response model for error cases."""
    detail: str = Field(..., description="Error message")
