"""Add book ownership.

Revision ID: 3c4d5e6f7a8b
Revises: 8a6e2d4c91f0
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3c4d5e6f7a8b"
down_revision: Union[str, Sequence[str], None] = "8a6e2d4c91f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"]: column for column in inspector.get_columns("books")}

    if "user_uid" not in columns:
        op.add_column(
            "books",
            sa.Column("user_uid", sa.Uuid(), nullable=True),
        )
    elif not columns["user_uid"]["nullable"]:
        op.alter_column("books", "user_uid", nullable=True)

    foreign_keys = sa.inspect(bind).get_foreign_keys("books")
    correct_foreign_key_exists = False
    for foreign_key in foreign_keys:
        if "user_uid" not in foreign_key["constrained_columns"]:
            continue
        is_correct = (
            foreign_key["referred_table"] == "user_accounts"
            and foreign_key["referred_columns"] == ["uid"]
            and foreign_key.get("options", {}).get("ondelete", "").upper()
            == "SET NULL"
        )
        if is_correct:
            correct_foreign_key_exists = True
        elif foreign_key["name"] is not None:
            op.drop_constraint(foreign_key["name"], "books", type_="foreignkey")

    if not correct_foreign_key_exists:
        op.create_foreign_key(
            "fk_books_user_uid_user_accounts",
            "books",
            "user_accounts",
            ["user_uid"],
            ["uid"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    foreign_keys = sa.inspect(bind).get_foreign_keys("books")
    for foreign_key in foreign_keys:
        if "user_uid" in foreign_key["constrained_columns"] and foreign_key["name"]:
            op.drop_constraint(foreign_key["name"], "books", type_="foreignkey")

    columns = {column["name"] for column in sa.inspect(bind).get_columns("books")}
    if "user_uid" in columns:
        op.drop_column("books", "user_uid")
