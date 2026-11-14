"""Staff session identity endpoint."""
from fastapi import APIRouter, Depends

from app.auth import require_staff_user

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.get("/me")
def current_user(staff: dict = Depends(require_staff_user)):
    return {"data": staff}
