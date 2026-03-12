"""add community_interactions table

Revision ID: e5f6a7b8c9d0
Revises: c9e2f1a3b4d5
Create Date: 2026-03-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "c9e2f1a3b4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add community_interactions table for per-event interaction tracking."""
    op.create_table(
        "community_interactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("arxiv_id", sa.String(), nullable=False),
        sa.Column("interacted_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_interactions_arxiv_id", "community_interactions", ["arxiv_id"], unique=False)
    op.create_index("ix_community_interactions_interacted_at", "community_interactions", ["interacted_at"], unique=False)


def downgrade() -> None:
    """Drop community_interactions table."""
    op.drop_index("ix_community_interactions_interacted_at", table_name="community_interactions")
    op.drop_index("ix_community_interactions_arxiv_id", table_name="community_interactions")
    op.drop_table("community_interactions")
