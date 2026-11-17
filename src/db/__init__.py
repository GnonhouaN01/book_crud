from sqlmodel import create_engine,text
from sqlalchemy.ext.asyncio import create_async_engine
from src.config import Config

engine = create_async_engine(
    url = Config.DATABASE_URL,
    # enregistre les donnée dans la BD a chaque execution
    echo = True 
)

async def initdb():
    async with engine.begin() as conn:
        statement = text("Select 'Hello World'")
        result = await conn.execute(statement)
        print(result)