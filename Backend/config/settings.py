import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GCP_PROJECT_ID: str
    GCP_LOCATION: str = "us-central1"
    DOCUMENT_AI_PROCESSOR_ID: str
    DOCUMENT_AI_LOCATION: str = "us"
    GCS_BUCKET_NAME: str = "investment_memo_ai"
    # Brevo (formerly Sendinblue)
    BREVO_API_KEY: str
    FROM_EMAIL: str = "vanikmanthan@gmail.com"
    BASE_URL: str = "https://your-domain.com"
    FRONTEND_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"

settings = Settings()
