"""add community_papers and paper_notes tables

Revision ID: c9e2f1a3b4d5
Revises: 7faf8835aa4f
Create Date: 2026-03-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9e2f1a3b4d5"
down_revision: Union[str, Sequence[str], None] = "7faf8835aa4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add community_papers and paper_notes tables."""
    op.create_table(
        "community_papers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("arxiv_id", sa.String(), nullable=False),
        sa.Column("interaction_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_interacted_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("arxiv_id"),
    )
    op.create_index("ix_community_papers_arxiv_id", "community_papers", ["arxiv_id"], unique=True)

    op.create_table(
        "paper_notes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("arxiv_id", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paper_notes_arxiv_id", "paper_notes", ["arxiv_id"], unique=False)


def downgrade() -> None:
    """Drop community_papers and paper_notes tables."""
    op.drop_index("ix_paper_notes_arxiv_id", table_name="paper_notes")
    op.drop_table("paper_notes")
    op.drop_index("ix_community_papers_arxiv_id", table_name="community_papers")
    op.drop_table("community_papers")
