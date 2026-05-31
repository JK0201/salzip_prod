import datetime

from pydantic import BaseModel


class SessionCreateResponse(BaseModel):
    token: str
    expires_at: datetime.datetime
