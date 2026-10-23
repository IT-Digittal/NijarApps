"""Origen de cada punto del histórico mensual (ejemplo de instalación o dato real).

Las filas existentes vienen del seed de instalación y quedan como ``ejemplo``;
el proceso de captura mensual escribe ``datadis`` (real) o ``estimado``.

Revision ID: 018_origen_metricas
Revises: 017_traducciones
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "018_origen_metricas"
down_revision: Union[str, None] = "017_traducciones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "metricas_historicas",
        sa.Column("origen", sa.String(20), nullable=False, server_default="ejemplo"),
    )


def downgrade() -> None:
    op.drop_column("metricas_historicas", "origen")
