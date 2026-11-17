from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.auth.routes import auth_router
from src.books.routes import book_router
from src.db.main import engine, initdb
from src.db.redis import redis_client
from src.errors import register_exception_handlers
from src.middleware import RequestLoggingMiddleware
from src.reviews.routes import review_router

api_version = "v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await initdb()
        yield
    finally:
        await engine.dispose()
        await redis_client.aclose()


app = FastAPI(title="Bookly", lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)
register_exception_handlers(app)

app.include_router(
    book_router,
    prefix=f"/api/{api_version}/books",
    tags=["books"],
)

app.include_router(
    auth_router,
    prefix=f"/api/{api_version}/auth",
    tags=["auth"],
)

app.include_router(
    review_router,
    prefix=f"/api/{api_version}/reviews",
    tags=["reviews"],
)