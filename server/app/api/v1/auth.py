import structlog
from fastapi import APIRouter

from app.core.auth import SessionDep
from app.core.deps import ConnDep
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserResponse
from app.services import auth as auth_service
from app.utils.normalize import normalize_email

log = structlog.get_logger(__name__)
router = APIRouter(tags=["auth"])


@router.post("/signup", status_code=201, response_model=AuthResponse)
async def signup(body: SignupRequest, session: SessionDep, conn: ConnDep) -> AuthResponse:
    user_id, expires_at = await auth_service.register_user(
        conn, session.session_id, body.email, body.password, body.name
    )
    return AuthResponse(
        user=UserResponse(id=user_id, email=normalize_email(body.email), name=body.name),
        expires_at=expires_at,
        token=session.token,
    )


@router.post("/login", status_code=200, response_model=AuthResponse)
async def login(body: LoginRequest, session: SessionDep, conn: ConnDep) -> AuthResponse:
    user, expires_at = await auth_service.login_user(
        conn, session.session_id, body.email, body.password
    )
    return AuthResponse(
        user=UserResponse(id=user.id, email=user.email, name=user.name),
        expires_at=expires_at,
        token=session.token,
    )


@router.post("/logout", status_code=204)
async def logout(session: SessionDep, conn: ConnDep) -> None:
    await auth_service.logout_user(conn, session.session_id)
