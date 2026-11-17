from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from src.books import routes as book_routes


def test_list_books_is_scoped_to_authenticated_user(
    client, authenticate_as, monkeypatch
):
    user = authenticate_as()
    get_all_books = AsyncMock(return_value=[])
    monkeypatch.setattr(book_routes.book_service, "get_all_books", get_all_books)

    response = client.get("/api/v1/books/")

    assert response.status_code == 200
    assert response.json() == []
    assert get_all_books.await_args.args[1] == user.uid


def test_get_missing_book_returns_domain_404(client, authenticate_as, monkeypatch):
    authenticate_as()
    monkeypatch.setattr(
        book_routes.book_service,
        "get_book",
        AsyncMock(return_value=None),
    )

    response = client.get(f"/api/v1/books/book/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "book_not_found"


def test_create_book_assigns_authenticated_owner(client, authenticate_as, monkeypatch):
    user = authenticate_as()
    book = SimpleNamespace(
        uid=uuid4(),
        title="Testing FastAPI",
        author="A. Reader",
        publisher="Books",
        published_date="2026",
        page_count=120,
        language="French",
        user_uid=user.uid,
    )
    create_book = AsyncMock(return_value=book)
    monkeypatch.setattr(book_routes.book_service, "create_book", create_book)

    response = client.post(
        "/api/v1/books/",
        json={
            "title": book.title,
            "author": book.author,
            "publisher": book.publisher,
            "published_date": book.published_date,
            "page_count": book.page_count,
            "language": book.language,
        },
    )

    assert response.status_code == 201
    assert response.json()["uid"] == str(book.uid)
    assert create_book.await_args.args[2] == user.uid


def test_delete_book_returns_no_content(client, authenticate_as, monkeypatch):
    authenticate_as()
    delete_book = AsyncMock(return_value=True)
    monkeypatch.setattr(book_routes.book_service, "delete_book", delete_book)

    response = client.delete(f"/api/v1/books/{uuid4()}")

    assert response.status_code == 204
    assert response.content == b""


def test_book_endpoint_requires_authentication(client):
    response = client.get("/api/v1/books/")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"
