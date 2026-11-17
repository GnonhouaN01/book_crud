from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
import uuid
from datetime import datetime
from uuid import uuid4
from sqlmodel import Relationship

if TYPE_CHECKING:
    from src.auth.models import User
    from src.reviews.models import Review

class Book(SQLModel , table=True):
    __tablename__ = "books"

    uid:uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            unique=True,
            nullable=False,
            default=uuid4,
        )
    )

    title: str
    author: str
    publisher: str
    published_date: str
    page_count: int
    language:str
    user_uid: uuid.UUID | None = Field(
        default=None,
        foreign_key="user_accounts.uid",
        ondelete="SET NULL",
    )
    owner: Optional["User"] = Relationship(back_populates="books")
    reviews: list["Review"] = Relationship(back_populates="book", sa_relationship_kwargs={"lazy":"selectin"})
    created_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=lambda: datetime.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=lambda: datetime.now())
    )

    def __repr__(self) -> str:
        return f"<Book {self.title}>"