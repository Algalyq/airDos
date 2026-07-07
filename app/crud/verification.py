import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.verification import VerificationCode


async def get_verification_code_by_user_id(
    db: AsyncSession, user_id
) -> VerificationCode | None:
    result = await db.execute(
        select(VerificationCode).where(VerificationCode.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_verification_code(
    db: AsyncSession, user: User
) -> VerificationCode:
    await delete_old_codes(db, user.id)

    code = generate_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    verification_code = VerificationCode(
        user_id=user.id,
        code=code,
        expires_at=expires_at,
        attempts=0,
    )
    db.add(verification_code)
    await db.flush()
    await db.refresh(verification_code)
    return verification_code


async def increment_attempts(
    db: AsyncSession, verification_code: VerificationCode
) -> VerificationCode:
    verification_code.attempts += 1
    db.add(verification_code)
    await db.flush()
    await db.refresh(verification_code)
    return verification_code


async def delete_old_codes(db: AsyncSession, user_id) -> None:
    await db.execute(delete(VerificationCode).where(VerificationCode.user_id == user_id))
    await db.flush()


def generate_code() -> str:
    return "".join(random.choices("0123456789", k=4))


def is_code_expired(verification_code: VerificationCode) -> bool:
    return datetime.now(timezone.utc) > verification_code.expires_at
