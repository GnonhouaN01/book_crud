from uuid import UUID

from pydantic import BaseModel, ConfigDict



class BookCreateModel(BaseModel):

    title: str
    author: str
    publisher: str
    published_date: str
    page_count: int
    language: str


class Book(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: UUID
    title: str 
    author: str
    publisher: str
    published_date: str
    page_count: int
    language: str
    user_uid: UUID | None = None


class BookUpdateModel(BaseModel):
    title: str 
    author: str
    publisher: str
    page_count: int
    language: str
