from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import get_current_user
from app.models.request_models import AuthRequest
from app.models.response_models import AuthResponse, UserInfoResponse
from app.services.auth_service import (
    authenticate_user,
    create_session_token,
    register_user,
    revoke_session_token,
    username_exists,
)

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/register", response_model=AuthResponse)
async def register(payload: AuthRequest) -> AuthResponse:
    try:
        user = register_user(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    token = create_session_token(user["id"])
    return AuthResponse(access_token=token, username=user["username"])


@router.post("/login", response_model=AuthResponse)
async def login(payload: AuthRequest) -> AuthResponse:
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    token = create_session_token(user["id"])
    return AuthResponse(access_token=token, username=user["username"])


@router.get("/me", response_model=UserInfoResponse)
async def me(user: dict = Depends(get_current_user)) -> UserInfoResponse:
    return UserInfoResponse(**user)


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if credentials:
        revoke_session_token(credentials.credentials)
    return {"message": "Logged out."}


@router.get("/availability")
async def availability(username: str = Query(..., min_length=3, max_length=50)) -> dict:
    return {"username": username.strip().lower(), "available": not username_exists(username)}
