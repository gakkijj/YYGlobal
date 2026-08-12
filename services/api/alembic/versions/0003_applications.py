"""Add per-program application status.

Revision ID: 0003_applications
Revises: 0002_material_artifacts
"""

from typing import Optional, Sequence, Union

from alembic import op

from app.models.entities import Application


revision: str = "0003_applications"
down_revision: Optional[str] = "0002_material_artifacts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Application.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    Application.__table__.drop(bind=op.get_bind(), checkfirst=True)

