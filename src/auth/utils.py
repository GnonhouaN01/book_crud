from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from passlib.context import CryptContext
from src.config import Config

passwd_context = CryptContext(
    schemes = ['bcrypt']
)

def create_access_token(
    user_data: dict,
    expiry: timedelta | None = None,
    refresh: bool = False,
) -> str:
    payload = {
        'user':user_data,
        'exp':datetime.now(timezone.utc) + (expiry if expiry is not None else timedelta(minutes=60)),
        'jti':str(uuid4()),
        'refresh':refresh
    }

    token = jwt.encode(
        payload=payload,
        key=Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM,
    )
    return token

def decode_token(token: str) -> dict:
    return jwt.decode(
        jwt=token,
        key=Config.JWT_SECRET,
        algorithms=[Config.JWT_ALGORITHM],
        options={"require": ["exp", "jti", "refresh", "user"]},
    )
    

def generate_password_hash(password:str)->str:
    hash = passwd_context.hash(password)
    return hash

def verify_password(password:str,hash:str) ->bool:
    return passwd_context.verify(password,hash)