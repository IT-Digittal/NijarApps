"""Normativa municipal (ordenanzas de la sede electrónica) con búsqueda en español.

Revision ID: 020_normativa_municipal
Revises: 019_registros_verticales
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "020_normativa_municipal"
down_revision: Union[str, None] = "019_registros_verticales"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "normativas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("titulo", sa.String(500), nullable=False),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("nombre_archivo", sa.String(255), nullable=False),
        sa.Column("fichero", sa.String(255), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("tamano_bytes", sa.Integer(), nullable=False),
        sa.Column("paginas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("texto", sa.Text(), nullable=False, server_default=""),
        sa.Column("url_origen", sa.String(500), nullable=True),
        sa.Column("fecha_publicacion", sa.Date(), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadatos", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_normativas_sha256", "normativas", ["sha256"], unique=True)
    op.create_index("ix_normativas_tipo", "normativas", ["tipo"])
    op.create_index("ix_normativas_activa", "normativas", ["activa"])
    op.execute(
        "CREATE INDEX ix_normativas_busqueda ON normativas USING gin "
        "(to_tsvector('spanish', titulo || ' ' || texto))"
    )
    op.create_table(
        "normativa_fragmentos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "normativa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("normativas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("articulo", sa.String(160), nullable=True),
    )
    op.create_index("ix_normativa_fragmentos_normativa_id", "normativa_fragmentos", ["normativa_id"])
    op.execute(
        "CREATE INDEX ix_normativa_fragmentos_busqueda ON normativa_fragmentos USING gin "
        "(to_tsvector('spanish', coalesce(articulo, '') || ' ' || texto))"
    )


def downgrade() -> None:
    op.drop_table("normativa_fragmentos")
    op.drop_table("normativas")
