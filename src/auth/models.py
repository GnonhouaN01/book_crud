from datetime import datetime
import uuid
from uuid import uuid4
from typing import TYPE_CHECKING

from sqlmodel import SQLModel, Field, Column, Relationship
import sqlalchemy.dialects.postgresql as pg

if TYPE_CHECKING:
    from src.books.models import Book
    from src.reviews.models import Review


class User(SQLModel,table=True):
    __tablename__ = "user_accounts"

    uid:uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            unique=True,
            nullable=False,
            default=uuid4,
            info={"description":"Unique identifier for the user account"}

        )
    )

    username: str
    first_name: str = Field(nullable=True)
    last_name: str = Field(nullable=True)
    is_verified: bool =False
    email: str
    password_hash: str
    create_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=lambda: datetime.now())
    
    )
    update_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=lambda: datetime.now())
    
    )

    # Controle d'acces
    role: str = Field(
        default="user",
        sa_column=Column(
            pg.VARCHAR(length=20),
            nullable=False,
            server_default="user",
        ),
    )
    is_verified:bool = Field(default=False)
    password_hash: str
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    update_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

    books: list["Book"] = Relationship(back_populates="owner",sa_relationship_kwargs={"lazy":"selectin"})

    books: list[Book] = Relationship(back_populates="owner",sa_relationship_kwargs={"lazy":"selectin"})
    reviews: list["Review"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy":"selectin"})

    def __repr__(self)->str:
        return f"<User {self.username}>"