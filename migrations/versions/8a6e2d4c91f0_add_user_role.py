"""Add user role.

Revision ID: 8a6e2d4c91f0
Revises: d50fa9080633
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8a6e2d4c91f0"
down_revision: Union[str, Sequence[str], None] = "d50fa9080633"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("user_accounts")
    }
    if "role" not in columns:
        op.add_column(
            "user_accounts",
            sa.Column(
                "role",
                sa.String(length=20),
                server_default=sa.text("'user'"),
                nullable=False,
            ),
        )


def downgrade() -> None:
    columns = {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("user_accounts")
    }
    if "role" in columns:
        op.drop_column("user_accounts", "role")
