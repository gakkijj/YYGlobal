"""make material drafts immutable version chains

Revision ID: 0007_material_draft_versions
Revises: 0006_material_drafts
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_material_draft_versions"
down_revision: Union[str, None] = "0006_material_drafts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("material_drafts", sa.Column("parent_id", sa.String(36), nullable=True))
    op.add_column("material_drafts", sa.Column("root_id", sa.String(36), nullable=True))
    op.add_column(
        "material_drafts",
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "material_drafts",
        sa.Column("revision_type", sa.String(30), nullable=False, server_default="generated"),
    )
    op.add_column(
        "material_drafts",
        sa.Column("change_summary", sa.Text(), nullable=False, server_default="首次生成"),
    )
    op.create_foreign_key(
        "fk_material_drafts_parent", "material_drafts", "material_drafts", ["parent_id"], ["id"]
    )
    op.create_index("ix_material_drafts_parent_id", "material_drafts", ["parent_id"])
    op.create_index("ix_material_drafts_root_id", "material_drafts", ["root_id"])


def downgrade() -> None:
    op.drop_index("ix_material_drafts_root_id", table_name="material_drafts")
    op.drop_index("ix_material_drafts_parent_id", table_name="material_drafts")
    op.drop_constraint("fk_material_drafts_parent", "material_drafts", type_="foreignkey")
    for name in ["change_summary", "revision_type", "version_number", "root_id", "parent_id"]:
        op.drop_column("material_drafts", name)
