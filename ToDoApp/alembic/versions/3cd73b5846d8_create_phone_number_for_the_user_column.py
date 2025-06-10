"""Create phone number for the user column

Revision ID: 3cd73b5846d8
Revises: 
Create Date: 2025-06-10 10:31:36.630603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3cd73b5846d8'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'phone_number',
            sa.String(),
            nullable=True,
            comment='The phone number of the user'
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
