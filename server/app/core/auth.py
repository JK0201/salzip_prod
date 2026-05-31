import typing
import uuid
from datetime import UTC, datetime
from typing import Annotated

import fastapi
from fastapi import Depends

from app.core.deps import ConnDep
from app.core.exceptions import UnauthorizedError
from app.core.security import hash_session_token
from app.repositories.session import SessionRepository


class SessionContext(typing.NamedTuple):
    session_id: uuid.UUID
    token: str


async def require_session(request: fastapi.Request, conn: ConnDep) -> SessionContext:
    header = request.headers.get("Authorization")
    if header is None:
        raise UnauthorizedError("missing authorization header")

    parts = header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("invalid authorization header")

    token_hash = hash_session_token(parts[1])
    session_id = await SessionRepository(conn).get_active(token_hash, datetime.now(UTC))
    if session_id is None:
        raise UnauthorizedError("invalid or expired session")

    return SessionContext(session_id=session_id, token=parts[1])


SessionDep = Annotated[SessionContext, Depends(require_session)]


class CurrentUser(typing.NamedTuple):
    session_id: uuid.UUID
    user_id: uuid.UUID


async def require_user(session: SessionDep, conn: ConnDep) -> CurrentUser:
    user_id = await SessionRepository(conn).get_user_id(session.session_id)
    if user_id is None:
        raise UnauthorizedError("login required")
    return CurrentUser(session_id=session.session_id, user_id=user_id)


UserDep = Annotated[CurrentUser, Depends(require_user)]
