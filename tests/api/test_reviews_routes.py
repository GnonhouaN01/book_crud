from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from src.reviews import routes as review_routes


def test_create_review_returns_created_review(client, authenticate_as, monkeypatch):
    user = authenticate_as()
    book_uid = uuid4()
    review = SimpleNamespace(
        uid=uuid4(),
        rating=5,
        review_text="Excellent book",
        user_uid=user.uid,
        book_uid=book_uid,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    add_review = AsyncMock(return_value=review)
    monkeypatch.setattr(review_routes.review_service, "add_review_to_book", add_review)

    response = client.post(
        f"/api/v1/reviews/book/{book_uid}",
        json={"rating": 5, "review_text": "Excellent book"},
    )

    assert response.status_code == 201
    assert response.json()["uid"] == str(review.uid)
    assert add_review.await_args.kwargs["user_email"] == user.email


def test_review_rating_out_of_range_returns_validation_error(
    client, authenticate_as
):
    authenticate_as()

    response = client.post(
        f"/api/v1/reviews/book/{uuid4()}",
        json={"rating": 6, "review_text": "Invalid rating"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_get_missing_review_returns_domain_404(client, authenticate_as, monkeypatch):
    authenticate_as()
    monkeypatch.setattr(
        review_routes.review_service,
        "get_review",
        AsyncMock(return_value=None),
    )

    response = client.get(f"/api/v1/reviews/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "review_not_found"
