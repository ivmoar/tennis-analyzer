from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = ""
    MODEL_PATH: str = "app/models/random_forest_model.joblib"
    UPLOAD_DIR: str = "uploads"
    MAX_VIDEO_SIZE_MB: int = 200
    MAX_VIDEO_DURATION_SEC: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
