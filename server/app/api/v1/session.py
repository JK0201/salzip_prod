import datetime

from fastapi import APIRouter

from app.core.config import settings
from app.core.deps import ConnDep
from app.core.security import generate_session_token, hash_session_token
from app.repositories.session import SessionRepository
from app.schemas.session import SessionCreateResponse

router = APIRouter(tags=["session"])


@router.post("/session", status_code=201, response_model=SessionCreateResponse)
async def create_session(conn: ConnDep) -> SessionCreateResponse:
    token = generate_session_token()
    token_hash = hash_session_token(token)
    expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        days=settings.SESSION_TTL_DAYS
    )
    await SessionRepository(conn).create(token_hash, expires_at)
    return SessionCreateResponse(token=token, expires_at=expires_at)
