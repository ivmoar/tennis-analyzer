from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api import analysis, health
from app.core.config import settings

app = FastAPI(
    title="TennisAnalyzer API",
    description="API para análisis técnico del golpe de derecha en tenis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir vídeos procesados estáticamente
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
