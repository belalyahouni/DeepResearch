"""drop conversations table

Revision ID: 833cf4d8ea5b
Revises: a364be21935c
Create Date: 2026-03-11 00:25:32.764993

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '833cf4d8ea5b'
down_revision: Union[str, Sequence[str], None] = 'a364be21935c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(op.f('ix_conversations_id'), table_name='conversations')
    op.drop_table('conversations')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table('conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paper_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_conversations_id'), 'conversations', ['id'], unique=False)
