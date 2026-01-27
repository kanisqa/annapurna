"""
FastAPI main application for Nutrition Tracker REST API.
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add parent directory to path to import nutrition_tracker
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    print("=" * 60)
    print("🚀 Nutrition Tracker API Server Started!")
    print("=" * 60)
    print(f"📝 API Documentation: http://0.0.0.0:8005/docs")
    print(f"📖 ReDoc: http://0.0.0.0:8005/redoc")
    print(f"💚 Health Check: http://0.0.0.0:8005/health")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("👋 Shutting down Nutrition Tracker API...")

# Create FastAPI app
app = FastAPI(
    title="Nutrition Tracker API",
    description="""
    REST API for nutrition tracking, recipe suggestions, and OCR grocery bill scanning.
    
    ## Features
    
    * **Nutrition Tracking**: Get detailed nutrition info for any food using Gemini AI
    * **Nutrition Board**: View user's cumulative nutrition totals
    * **Recipe Suggestions**: Get creative dish ideas from available ingredients
    * **Lock Dish**: Log custom dishes with nutrition data
    * **OCR Scanning**: Extract grocery items from bill images using Azure Vision
    
    ## No Authentication Required
    
    This API is open and does not require authentication.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware (allow all origins for simplicity)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    
    # Run the server on port 8005
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8005,
        log_level="info"
    )
