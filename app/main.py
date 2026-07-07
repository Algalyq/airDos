import logging

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)

from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.users import router as users_router

app = FastAPI(
    title="airDos API",
    description="API аутентификации и парсинга документов",
    version="1.1.0",
)

app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(documents_router, prefix="/api")


@app.get("/healthcheck", tags=["health"])
async def healthcheck():
    return {"status": "ok"}
