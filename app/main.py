import logging

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)

from app.api.auth import router as auth_router
from app.api.users import router as users_router

app = FastAPI(
    title="airDos API",
    description="API аутентификации с верификацией через Email PIN-код",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(users_router)


@app.get("/healthcheck", tags=["health"])
async def healthcheck():
    return {"status": "ok"}
