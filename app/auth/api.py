from datetime import datetime, timedelta
from uuid import uuid4

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.db import get_db_connection
from app.settings import settings
from app.users.models import User, UserIn, UserInDB
from app.users.queries import get_user_by_username, insert_user


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token/")

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def create_access_token(data: TokenData, expires_delta: timedelta):
    expire = datetime.utcnow() + expires_delta
    to_encode = {"exp": expire, "sub": data.username}
    return jwt.encode(to_encode, settings.auth_key, algorithm=settings.jwt_alogrithm)


async def authenticate_user(
    conn: asyncpg.Connection, username: str, password: str
) -> UserInDB | None:
    user = await get_user_by_username(conn, username)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> User:
    incorrect_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "reason": "invalid_credentials",
            "message": "Could not validate credentials",
        },
    )
    try:
        payload = jwt.decode(token, settings.auth_key, settings.jwt_alogrithm)
        username: str | None = payload.get("sub")
        if username is None:
            raise incorrect_credentials
        token_data = TokenData(username=username)
    except JWTError:
        raise incorrect_credentials

    user = await get_user_by_username(conn, token_data.username)
    if user is None:
        raise incorrect_credentials

    return User(username=user.username, uuid=user.uuid)


@router.post("/register/", status_code=status.HTTP_201_CREATED)
async def register(
    user: UserIn,
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    try:
        await insert_user(
            conn,
            UserInDB(
                uuid=uuid4(),
                username=user.username,
                password_hash=pwd_context.hash(user.password),
            ),
        )
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "reason": "duplicate_username",
                "message": "User with this username aleready exists",
            },
        )


@router.post("/token/", response_model=Token)
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    user = await authenticate_user(conn, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "reason": "incorrect_credentials",
                "message": "Incorrect username or password",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        TokenData(username=user.username),
        timedelta(minutes=settings.access_token_expires_minutes),
    )
    return Token(access_token=access_token, token_type="bearer")
