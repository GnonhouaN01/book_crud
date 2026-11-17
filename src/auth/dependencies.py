from collections.abc import Collection
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.exceptions import RedisError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.models import User
from src.auth.utils import decode_token
from src.db.main import get_session
from src.db.redis import is_token_revoked
from src.errors import (
    AccessTokenRequired,
    InsufficientPermission,
    InvalidToken,
    RevokedToken,
    ServiceUnavailable,
)


bearer_scheme = HTTPBearer(auto_error=False)


async def get_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise InvalidToken("Invalid or missing bearer token.")

    try:
        token_data = decode_token(credentials.credentials)
        if token_data.get("refresh") is not False:
            raise AccessTokenRequired()
        token_id = token_data["jti"]
        if not isinstance(token_id, str):
            raise InvalidToken()
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise InvalidToken() from None

    try:
        if await is_token_revoked(token_id):
            raise RevokedToken()
    except RedisError as error:
        raise ServiceUnavailable("Token revocation service is unavailable.") from error

    return token_data


async def get_current_user(
    token_data: dict = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> User:
    try:
        user_uid = UUID(token_data["user"]["user_uid"])
    except (KeyError, TypeError, ValueError):
        raise InvalidToken() from None

    result = await session.exec(select(User).where(User.uid == user_uid))
    user = result.first()
    if user is None:
        raise InvalidToken()

    return user


class RoleChecker:
    def __init__(self, allowed_roles: Collection[str]) -> None:
        self.allowed_roles = frozenset(allowed_roles)
        if not self.allowed_roles or not self.allowed_roles <= {"admin", "user"}:
            raise ValueError("allowed_roles must contain 'admin' and/or 'user'")

    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in self.allowed_roles:
            raise InsufficientPermission()
        return current_user
