"""Caché de traducciones automáticas (avisos, noticias y agenda del tótem).

Revision ID: 017_traducciones
Revises: 016_energia_datadis
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "017_traducciones"
down_revision: Union[str, None] = "016_energia_datadis"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "traducciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("clave", sa.String(64), nullable=False),
        sa.Column("idioma", sa.String(5), nullable=False),
        sa.Column("texto_origen", sa.Text(), nullable=False),
        sa.Column("texto_traducido", sa.Text(), nullable=False),
        sa.Column("modelo", sa.String(80), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_traducciones_clave", "traducciones", ["clave"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_traducciones_clave", table_name="traducciones")
    op.drop_table("traducciones")
