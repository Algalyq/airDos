from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.password import verify_password
from app.core.security import create_access_token
from app.crud.user import create_user, get_user_by_email, verify_user
from app.crud.verification import (
    create_verification_code,
    delete_old_codes,
    get_verification_code_by_user_id,
    increment_attempts,
    is_code_expired,
)
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    ResendCodeRequest,
    ResendCodeResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
)
from app.schemas.token import Token
from app.utils.email import send_verification_code

router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    existing_user = await get_user_by_email(db, email=payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже занят",
        )

    user = await create_user(db, user_in=payload)
    verification_code = await create_verification_code(db, user=user)
    await db.commit()

    send_verification_code(
        background_tasks,
        email=user.email,
        code=verification_code.code,
    )

    return RegisterResponse(
        status="pending_verification",
        message="Код подтверждения отправлен на email",
    )


@router.post(
    "/verify-code",
    response_model=VerifyCodeResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_code(payload: VerifyCodeRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, email=payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    verification_code = await get_verification_code_by_user_id(db, user_id=user.id)
    if not verification_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Код подтверждения не найден",
        )

    if verification_code.attempts >= 3:
        await delete_old_codes(db, user_id=user.id)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Слишком много неудачных попыток. Запросите код заново",
        )

    if is_code_expired(verification_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Код просрочен",
        )

    if verification_code.code != payload.code:
        await increment_attempts(db, verification_code)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код",
        )

    await verify_user(db, user=user)
    await delete_old_codes(db, user_id=user.id)
    await db.commit()

    return VerifyCodeResponse(
        status="success",
        message="Email успешно подтвержден",
    )


@router.post(
    "/resend-code",
    response_model=ResendCodeResponse,
    status_code=status.HTTP_200_OK,
)
async def resend_code(
    payload: ResendCodeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(db, email=payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже подтвержден",
        )

    await delete_old_codes(db, user_id=user.id)
    verification_code = await create_verification_code(db, user=user)
    await db.commit()

    send_verification_code(
        background_tasks,
        email=user.email,
        code=verification_code.code,
    )

    return ResendCodeResponse(
        status="success",
        message="Код подтверждения повторно отправлен на email",
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный email или пароль",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email не подтвержден. Пожалуйста, пройдите верификацию",
        )

    access_token = create_access_token(
        subject=user.email,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")
