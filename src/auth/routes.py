from datetime import timedelta

from fastapi import APIRouter, Depends, Response, status
from kombu.exceptions import OperationalError
from redis.exceptions import RedisError
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.dependencies import get_token_payload
from src.config import Config
from src.celery_tasks import send_email
from src.db.main import get_session
from src.db.redis import revoke_token
from src.errors import (
    InvalidCredentials,
    ServiceUnavailable,
    UserAlreadyExists,
)

from .dependencies import RoleChecker
from .schemas import EmailModel, UserBooskModel, UserCreateModel, UserLoginModel, UserModel
from .service import UserService
from .utils import create_access_token, verify_password

auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(["admin", "user"])
email_admin_checker = RoleChecker(["admin"])

@auth_router.post(
    "/signup",
    response_model=UserModel,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_account(
    user_data: UserCreateModel,
    session: AsyncSession = Depends(get_session),
):
    email = user_data.email
    user_exists = await user_service.user_exists(email,session)

    if user_exists:
        raise UserAlreadyExists()

    new_user = await user_service.create_user(user_data,session)

    return new_user


# Login
@auth_router.post("/login")
async def login_users(login_data:UserLoginModel,session:AsyncSession=Depends(get_session)):
    email = login_data.email
    password = login_data.password
    user = await user_service.get_user_by_email(email,session)

    if user is not None:
        password_valid = verify_password(password,user.password_hash)

        if password_valid:
            access_token = create_access_token(
                user_data={"email":user.email,"user_uid":str(user.uid)}
            )

            refresh_token = create_access_token(
                user_data={"email":user.email,"user_uid":str(user.uid)},
                refresh=True,
                expiry=timedelta(days=Config.REFRESH_TOKEN_EXPIRY_DAYS),
            )

            return JSONResponse(
                content = {
                    "message":"Login successful",
                    "access_token":access_token,
                    "refresh_token":refresh_token,
                    "token_type":"bearer",
                    "user":{"email":user.email,"uid":str(user.uid)},
                }
            )

    raise InvalidCredentials()

@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(token_details: dict = Depends(get_token_payload)) -> Response:
    try:
        await revoke_token(token_details["jti"], token_details["exp"])
    except RedisError as error:
        raise ServiceUnavailable(
            "Token revocation service is unavailable."
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_router.get("/me", response_model=UserBooskModel)
async def get_me(user=Depends(role_checker)):
    return user


# Email
@auth_router.post(
    "/send_mail",
    dependencies=[Depends(email_admin_checker)],
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_mail(emails: EmailModel):
    html = "<h1>Welcome to the app</h1>"
    subject = "Welcome to our app"

    try:
        task = send_email.delay(
            recipients=[str(address) for address in emails.addresses],
            subject=subject,
            body=html,
        )
    except OperationalError as error:
        raise ServiceUnavailable("Email queue is unavailable.") from error

    return {
        "message": "Email queued successfully",
        "task_id": task.id,
    }