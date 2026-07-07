from fastapi import APIRouter, Depends

from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.user import UserProfileResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        is_verified=current_user.is_verified,
    )
