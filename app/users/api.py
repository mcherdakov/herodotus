from webbrowser import get
import asyncpg
from fastapi import APIRouter, Depends

from app.auth.api import get_current_user
from app.users.models import User

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/me/", response_model=User)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
