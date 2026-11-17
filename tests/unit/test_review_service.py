from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.errors import InsufficientPermission
from src.reviews.service import ReviewService, user_service


@pytest.mark.asyncio
async def test_user_can_delete_own_review(monkeypatch):
    user = SimpleNamespace(uid=uuid4())
    review = SimpleNamespace(uid=uuid4(), user_uid=user.uid)
    session = SimpleNamespace(delete=AsyncMock(), commit=AsyncMock())
    service = ReviewService()
    monkeypatch.setattr(
        user_service,
        "get_user_by_email",
        AsyncMock(return_value=user),
    )
    monkeypatch.setattr(
        service,
        "get_review",
        AsyncMock(return_value=review),
    )

    await service.delete_review_to_from_book(
        review.uid,
        "reader@example.com",
        session,
    )

    session.delete.assert_awaited_once_with(review)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_user_cannot_delete_another_users_review(monkeypatch):
    user = SimpleNamespace(uid=uuid4())
    review = SimpleNamespace(uid=uuid4(), user_uid=uuid4())
    session = SimpleNamespace(delete=AsyncMock(), commit=AsyncMock())
    service = ReviewService()
    monkeypatch.setattr(
        user_service,
        "get_user_by_email",
        AsyncMock(return_value=user),
    )
    monkeypatch.setattr(
        service,
        "get_review",
        AsyncMock(return_value=review),
    )

    with pytest.raises(InsufficientPermission):
        await service.delete_review_to_from_book(
            review.uid,
            "reader@example.com",
            session,
        )

    session.delete.assert_not_awaited()
    session.commit.assert_not_awaited()
