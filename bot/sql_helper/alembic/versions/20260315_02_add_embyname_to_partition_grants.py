"""add embyname to partition_grants

Revision ID: 20260315_02
Revises: 20260315_01
Create Date: 2026-03-15 13:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260315_02"
down_revision = "20260315_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("partition_grants")}
    if "embyname" not in column_names:
        op.add_column("partition_grants", sa.Column("embyname", sa.String(length=255), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("partition_grants")}
    if "embyname" in column_names:
        op.drop_column("partition_grants", "embyname")
