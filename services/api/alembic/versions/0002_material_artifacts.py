"""Add material artifact version registry.

Revision ID: 0002_material_artifacts
Revises: 0001_initial
"""

from typing import Optional, Sequence, Union

from alembic import op

from app.models.entities import MaterialArtifact


revision: str = "0002_material_artifacts"
down_revision: Optional[str] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    MaterialArtifact.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    MaterialArtifact.__table__.drop(bind=op.get_bind(), checkfirst=True)

