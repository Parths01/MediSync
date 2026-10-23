from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import User
from app.schemas import AuthResponse, LoginRequest, UserCreate, UserResponse
from app.security import (
    clear_auth_cookies,
    create_session,
    get_current_user,
    hash_password,
    require_csrf,
    revoke_session,
    set_csrf_cookie,
    verify_password_and_update,
)

router = APIRouter()


@router.get("/csrf")
async def get_csrf_token(response: Response) -> dict[str, str]:
    return {"csrf_token": set_csrf_cookie(response)}


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
async def register(
    payload: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    user = User(
        name=payload.name,
        dob=payload.dob,
        gender=payload.gender,
        contact=payload.contact,
        email=str(payload.email),
        password_hash=hash_password(payload.password),
        blood_group=payload.blood_group,
        role="patient",
    )
    db.add(user)

    try:
        await db.flush()
        csrf_token = await create_session(db, user, response)
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered") from error

    await db.refresh(user)
    return AuthResponse(user=UserResponse.model_validate(user), csrf_token=csrf_token)


@router.post(
    "/login",
    response_model=AuthResponse,
    dependencies=[Depends(require_csrf)],
)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    result = await db.execute(
        select(User).where(func.lower(User.email) == str(payload.email).lower())
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    is_valid, replacement_hash = verify_password_and_update(payload.password, user.password_hash)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if replacement_hash is not None:
        user.password_hash = replacement_hash

    csrf_token = await create_session(db, user, response)
    await db.commit()
    return AuthResponse(user=UserResponse.model_validate(user), csrf_token=csrf_token)


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)])
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Response:
    token = request.cookies.get(get_settings().session_cookie_name)
    await revoke_session(db, token)
    await db.commit()
    clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
