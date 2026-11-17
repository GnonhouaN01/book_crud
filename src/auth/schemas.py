from datetime import datetime
from uuid import UUID
from typing import List
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.books.schemas import Book


class UserCreateModel(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str


class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: UUID
    username: str
    first_name: str
    last_name: str
    is_verified: bool
    role: str
    email: str
    create_at: datetime
    update_at: datetime
    

class UserLoginModel(BaseModel):
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)


class EmailModel(BaseModel):
    addresses: list[EmailStr] = Field(min_length=1)


class UserBooskModel(UserModel):
    books:List[Book]