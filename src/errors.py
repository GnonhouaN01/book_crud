import logging
from collections.abc import Mapping

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class BooklyException(Exception):
    status_code = 500
    error_code = "internal_error"
    default_message = "An unexpected error occurred."
    headers: Mapping[str, str] | None = None

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class InvalidToken(BooklyException):
    status_code = 401
    error_code = "invalid_token"
    default_message = "The access token is invalid or expired."
    headers = {"WWW-Authenticate": "Bearer"}


class RevokedToken(BooklyException):
    status_code = 401
    error_code = "revoked_token"
    default_message = "The access token has been revoked."
    headers = {"WWW-Authenticate": "Bearer"}


class AccessTokenRequired(BooklyException):
    status_code = 401
    error_code = "access_token_required"
    default_message = "An access token is required."
    headers = {"WWW-Authenticate": "Bearer"}


class RefreshTokenRequired(BooklyException):
    status_code = 401
    error_code = "refresh_token_required"
    default_message = "A refresh token is required."
    headers = {"WWW-Authenticate": "Bearer"}


class UserAlreadyExists(BooklyException):
    status_code = 409
    error_code = "user_already_exists"
    default_message = "A user with this email already exists."


class InvalidCredentials(BooklyException):
    status_code = 401
    error_code = "invalid_credentials"
    default_message = "The email or password is incorrect."


class InsufficientPermission(BooklyException):
    status_code = 403
    error_code = "insufficient_permission"
    default_message = "You do not have permission to perform this action."


class BookNotFound(BooklyException):
    status_code = 404
    error_code = "book_not_found"
    default_message = "Book not found."


class ReviewNotFound(BooklyException):
    status_code = 404
    error_code = "review_not_found"
    default_message = "Review not found."


class TagNotFound(BooklyException):
    status_code = 404
    error_code = "tag_not_found"
    default_message = "Tag not found."


class TagAlreadyExists(BooklyException):
    status_code = 409
    error_code = "tag_already_exists"
    default_message = "Tag already exists."


class UserNotFound(BooklyException):
    status_code = 404
    error_code = "user_not_found"
    default_message = "User not found."


class ServiceUnavailable(BooklyException):
    status_code = 503
    error_code = "service_unavailable"
    default_message = "A required service is temporarily unavailable."


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: object | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    error: dict[str, object] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return JSONResponse(
        status_code=status_code,
        content={"error": error},
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BooklyException)
    async def handle_bookly_exception(
        request: Request, exc: BooklyException
    ) -> JSONResponse:
        return _error_response(
            exc.status_code, exc.error_code, exc.message, headers=exc.headers
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "location": list(error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        return _error_response(
            422,
            "validation_error",
            "The request contains invalid data.",
            details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        details = None if isinstance(exc.detail, str) else exc.detail
        return _error_response(
            exc.status_code,
            "http_error",
            message,
            details,
            exc.headers,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logging.getLogger(__name__).error(
            "Unhandled application error",
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return _error_response(
            500,
            "internal_error",
            "An unexpected error occurred.",
        )
