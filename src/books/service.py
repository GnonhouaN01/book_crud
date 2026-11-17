from uuid import UUID

from sqlalchemy import desc
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.books.models import Book
from src.books.schemas import BookCreateModel, BookUpdateModel


class BookService:
    async def get_all_books(
        self,
        session: AsyncSession,
        user_uid: UUID,
    ) -> list[Book]:
        statement = (
            select(Book)
            .where(Book.user_uid == user_uid)
            .order_by(desc(Book.created_at))
        )
        result = await session.exec(statement)
        return result.all()

    async def create_book(
        self,
        book_data: BookCreateModel,
        session: AsyncSession,
        user_uid: UUID,
    ) -> Book:
        new_book = Book(**book_data.model_dump(), user_uid=user_uid)
        session.add(new_book)
        await session.commit()
        await session.refresh(new_book)
        return new_book

    async def get_book(
        self,
        book_uid: UUID,
        session: AsyncSession,
        user_uid: UUID,
    ) -> Book | None:
        statement = select(Book).where(
            Book.uid == book_uid,
            Book.user_uid == user_uid,
        )
        result = await session.exec(statement)
        return result.first()

    async def update_book(
        self,
        book_uid: UUID,
        update_data: BookUpdateModel,
        session: AsyncSession,
        user_uid: UUID,
    ) -> Book | None:
        book_to_update = await self.get_book(book_uid, session, user_uid)
        if book_to_update is None:
            return None

        for key, value in update_data.model_dump().items():
            setattr(book_to_update, key, value)
        await session.commit()
        await session.refresh(book_to_update)
        return book_to_update

    async def delete_book(
        self,
        book_uid: UUID,
        session: AsyncSession,
        user_uid: UUID,
    ) -> bool:
        book_to_delete = await self.get_book(book_uid, session, user_uid)
        if book_to_delete is None:
            return False

        await session.delete(book_to_delete)
        await session.commit()
        return True
