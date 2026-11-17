from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.books.service import BookService
from src.books.schemas import Book, BookUpdateModel, BookCreateModel
from src.db.main import get_session
from src.errors import BookNotFound


book_router = APIRouter()
book_service = BookService()


@book_router.get("/", response_model=list[Book])
async def get_all_books(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await book_service.get_all_books(session, current_user.uid)

# Route de création de livre
@book_router.post("/", status_code=status.HTTP_201_CREATED, response_model=Book)
async def create_a_book(
    book_data: BookCreateModel,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await book_service.create_book(book_data, session, current_user.uid)

# Route pour réccuperer un livre spécifique
@book_router.get("/book/{book_uid}", response_model=Book)
async def get_book(
    book_uid: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    book = await book_service.get_book(book_uid, session, current_user.uid)

    if book:
        return book
    raise BookNotFound()

# Route pour la mise à jour de la ressources
@book_router.patch("/{book_uid}", response_model=Book)
async def update_book(
    book_uid: UUID,
    book_update_data: BookUpdateModel,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    updated_book = await book_service.update_book(
        book_uid, book_update_data, session, current_user.uid
    )
    if updated_book is None:
        raise BookNotFound()
    return updated_book


# Route de supprssion
@book_router.delete("/{book_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_uid: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    deleted = await book_service.delete_book(book_uid, session, current_user.uid)

    if not deleted:
        raise BookNotFound()
    return None
