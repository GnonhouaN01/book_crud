import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import sqlalchemy.dialects.postgresql as pg
from sqlmodel import Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.auth.models import User
    from src.books.models import Book


class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            unique=True,
            nullable=False,
            default=uuid.uuid4,
        )
    )
    rating: int = Field(ge=1, le=5)
    review_text: str = Field(nullable=False)
    user_uid: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="user_accounts.uid",
        ondelete="SET NULL",
    )
    book_uid: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="books.uid",
        ondelete="SET NULL",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(pg.TIMESTAMP, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(pg.TIMESTAMP, nullable=False),
    )
    user: Optional["User"] = Relationship(back_populates="reviews")
    book: Optional["Book"] = Relationship(back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review for book {self.book_uid} by user {self.user_uid}>"
