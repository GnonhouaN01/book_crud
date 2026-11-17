from uuid import UUID

from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.service import UserService
from src.books.models import Book
from src.errors import (
    BookNotFound,
    InsufficientPermission,
    ReviewNotFound,
    UserNotFound,
)
from src.reviews.models import Review

from .schemas import ReviewCreateModel

user_service = UserService()


class ReviewService:
    async def add_review_to_book(
        self,
        user_email: str,
        book_uid: UUID,
        review_data: ReviewCreateModel,
        session: AsyncSession,
    ):
        user = await user_service.get_user_by_email(email=user_email, session=session)
        if user is None:
            raise UserNotFound()

        book = await session.get(Book, book_uid)
        if book is None:
            raise BookNotFound()

        new_review = Review(
            rating=review_data.rating,
            review_text=review_data.review_text,
            user_uid=user.uid,
            book_uid=book.uid,
        )
        new_review.user = user
        new_review.book = book
        session.add(new_review)
        await session.commit()
        await session.refresh(new_review)
        return new_review

    async def get_review(self, review_uid: UUID, session: AsyncSession):
        statement = select(Review).where(Review.uid == review_uid)
        result = await session.exec(statement)
        return result.first()

    async def get_all_reviews(self, session: AsyncSession):
        statement = select(Review).order_by(desc(Review.created_at))
        result = await session.exec(statement)
        return result.all()

    async def delete_review_to_from_book(
        self, review_uid: UUID, user_email: str, session: AsyncSession
    ):
        user = await user_service.get_user_by_email(user_email, session)
        review = await self.get_review(review_uid, session)

        if user is None:
            raise UserNotFound()
        if review is None:
            raise ReviewNotFound()
        if review.user_uid != user.uid:
            raise InsufficientPermission("You cannot delete another user's review.")

        await session.delete(review)
        await session.commit()
