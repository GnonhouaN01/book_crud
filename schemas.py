from sqlmodel import SQLModel,Field,Column
from sqlalchemy.dialects.postgresql as pg
import uuid

# creons notre model
class Book(SQLModel,table=True):
    __tablename__ = "books"
    uid:uuid.UUID = Field(
        sa_column = Column(
            pg.UUID,
            primary_key=True,
            unique=True,
            nullable=False
        )
    )

    title:str
    author: str
    publisher: str
    published_date: str
    page_count:int
    language:str
    create_at:datetime = Field(sa_column=Column(pg.TIMESTAMP,default=datatime.now))
    updated_at:datetime = Field(sa_column=Column(pg.TIMESTAMP,default=datatime.now))

    def __repr__(self):
        return f"<Book {self.title}>"
