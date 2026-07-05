"""Registro de consumo de IA generativa (tokens y coste por llamada).

Revision ID: 007_consumo_ia
Revises: 006_fuentes_datos
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_consumo_ia"
down_revision: Union[str, None] = "006_fuentes_datos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "consumos_ia",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ocurrido_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("proveedor", sa.String(30), nullable=False),
        sa.Column("modelo", sa.String(80), nullable=False),
        sa.Column("servicio", sa.String(60), nullable=False),
        sa.Column("canal", sa.String(30), nullable=False),
        sa.Column("idioma", sa.String(5)),
        sa.Column("tokens_entrada", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tokens_salida", sa.Integer, nullable=False, server_default="0"),
        sa.Column("coste_estimado_usd", sa.Float, nullable=False, server_default="0"),
        sa.Column("latencia_ms", sa.Integer),
        sa.Column("interaccion_id", postgresql.UUID(as_uuid=True)),
    )
    op.create_index("ix_consumos_ia_ocurrido_en", "consumos_ia", ["ocurrido_en"])
    op.create_index("ix_consumos_ia_servicio", "consumos_ia", ["servicio"])
    op.create_index("ix_consumos_ia_canal", "consumos_ia", ["canal"])


def downgrade() -> None:
    op.drop_index("ix_consumos_ia_canal", table_name="consumos_ia")
    op.drop_index("ix_consumos_ia_servicio", table_name="consumos_ia")
    op.drop_index("ix_consumos_ia_ocurrido_en", table_name="consumos_ia")
    op.drop_table("consumos_ia")
