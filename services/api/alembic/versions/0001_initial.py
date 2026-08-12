"""Create the complete P0 schema.

Revision ID: 0001_initial
Revises:
"""

from typing import Optional, Sequence, Union

from alembic import op

from app.core.database import Base
from app.models import entities  # noqa: F401


revision: str = "0001_initial"
down_revision: Optional[str] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())

