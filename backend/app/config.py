from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "jwworkflow"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/jwworkflow"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./data/uploads"
    KNOWLEDGE_DIR: str = "./data/knowledge"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
