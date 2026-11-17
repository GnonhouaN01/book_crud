from datetime import datetime
import uuid
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

import sqlalchemy.dialects.postgresql as pg
from sqlmodel import Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.auth.models import User
    from src.books.models import Book


class User(SQLModel, table=True):
    __tablename__ = "user_accounts"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            unique=True,
            nullable=False,
            default=uuid4,
            info={"description": "Unique identifier for the user account"},
        )
    )
    username: str
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    is_verified: bool = Field(default=False)
    email: str
    password_hash: str
    role: str = Field(default="user", nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    books: list["Book"] = Relationship(back_populates="owner", sa_relationship_kwargs={"lazy": "selectin"})
    reviews: list["Review"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Book(SQLModel, table=True):
    __tablename__ = "books"

    uid: uuid.UUID = Field(
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
    language: str
    user_uid: uuid.UUID | None = Field(
        default=None,
        foreign_key="user_accounts.uid",
        ondelete="SET NULL",
    )
    owner: Optional["User"] = Relationship(back_populates="books")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    reviews: list["Review"] = Relationship(back_populates="book", sa_relationship_kwargs={"lazy": "selectin"})

    def __repr__(self) -> str:
        return f"<Book {self.title}>"


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
    user_uid: Optional[uuid.UUID] = Field(default=None, foreign_key="user_accounts.uid", ondelete="SET NULL")
    book_uid: Optional[uuid.UUID] = Field(default=None, foreign_key="books.uid", ondelete="SET NULL")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    user: Optional["User"] = Relationship(back_populates="reviews")
    book: Optional["Book"] = Relationship(back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review for book {self.book_uid} by user {self.user_uid}>"
