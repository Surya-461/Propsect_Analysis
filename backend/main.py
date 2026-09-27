from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import datetime
import logging

from routes import router as api_router
from database_init import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to handle database initialization on application startup."""
    init_db()
    yield

app = FastAPI(
    title="Prospect AI",
    description="Enterprise B2B Underwriting & Prospect Intelligence Platform powered by Gemini AI with UUID Security",
    lifespan=lifespan
)

# CORS middleware configuration
raw_cors = os.getenv("CORS_ALLOWED_ORIGINS", "")
if raw_cors.strip():
    allowed_origins = [o.strip() for o in raw_cors.split(",") if o.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from ai.gemini import GEMINI_MODEL

uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Single canonical API router
app.include_router(api_router)

@app.get("/")
def home():
    return {
        "status": "Prospect AI API is running.",
        "ai_engine": f"Gemini AI ({GEMINI_MODEL})",
        "auth": "JWT Bearer Token Authentication Active (UUID Identity)",
        "docs": "/docs",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }