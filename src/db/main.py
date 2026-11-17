from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from src.config import Config
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from src.books.models import Book


engine = create_async_engine(
    url=Config.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)



async def initdb():
    """create a connection to our db"""

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session