from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-opus-4-5"
    MODEL_PATH: str = "app/models/random_forest_model.joblib"
    MEDIAPIPE_MODEL_PATH: str = "pose_landmarker_lite.task"
    UPLOAD_DIR: str = "uploads"
    MAX_VIDEO_SIZE_MB: int = 200
    MAX_VIDEO_DURATION_SEC: int = 60
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    class Config:
        env_file = ".env"


settings = Settings()
