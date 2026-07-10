from fastapi import FastAPI
from app.config import Settings

settings = Settings()
app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)


@app.get("/health")
async def health():
    return {"status": "ok"}
