"""Verticales Smart City transversales (alumbrado, agua, residuos, movilidad,
seguridad, energía).

Crea el modelo de datos troncal de las verticales que se despliegan sobre la
misma plataforma DTI, con sus activos e indicadores.

Revision ID: 005_smart_city_verticales
Revises: 004_cliente_campana_contenidos
Create Date: 2026-07-03 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_smart_city_verticales"
down_revision: Union[str, None] = "004_cliente_campana_contenidos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    ]


def upgrade() -> None:
    # ---------------------------------------------------------- alumbrado_zonas
    op.create_table(
        "alumbrado_zonas",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("luminarias", sa.Integer, nullable=False, server_default="0"),
        sa.Column("led", sa.Integer, nullable=False, server_default="0"),
        sa.Column("vsap", sa.Integer, nullable=False, server_default="0"),
        sa.Column("solar", sa.Integer, nullable=False, server_default="0"),
        sa.Column("latitud", sa.Numeric(9, 6)),
        sa.Column("longitud", sa.Numeric(9, 6)),
        *_ts(),
    )

    # -------------------------------------------------------- alumbrado_cuadros
    op.create_table(
        "alumbrado_cuadros",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("codigo", sa.String(20), nullable=False, unique=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("zona_id", sa.String(40), nullable=False),
        sa.Column("ubicacion", sa.String(255)),
        sa.Column("circuitos", sa.Integer, nullable=False, server_default="0"),
        sa.Column("potencia_kw", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("factor_potencia", sa.Numeric(4, 2)),
        sa.Column("comunicaciones", sa.String(30), nullable=False, server_default="online"),
        sa.Column("sla", sa.Integer, nullable=False, server_default="99"),
        sa.Column("estado", sa.String(30), nullable=False, server_default="operativo"),
        sa.Column("alarmas", postgresql.ARRAY(sa.String())),
        sa.Column("latitud", sa.Numeric(9, 6)),
        sa.Column("longitud", sa.Numeric(9, 6)),
        sa.Column("metadatos", sa.JSON()),
        *_ts(),
    )
    op.create_index("ix_alumbrado_cuadros_codigo", "alumbrado_cuadros", ["codigo"])
    op.create_index("ix_alumbrado_cuadros_zona_id", "alumbrado_cuadros", ["zona_id"])
    op.create_index("ix_alumbrado_cuadros_estado", "alumbrado_cuadros", ["estado"])

    # ----------------------------------------------------- alumbrado_luminarias
    op.create_table(
        "alumbrado_luminarias",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("codigo", sa.String(20), nullable=False, unique=True),
        sa.Column("zona_id", sa.String(40), nullable=False),
        sa.Column("cuadro_codigo", sa.String(20)),
        sa.Column("circuito", sa.String(30)),
        sa.Column("direccion", sa.String(255)),
        sa.Column("tecnologia", sa.String(20), nullable=False),
        sa.Column("potencia_w", sa.Integer, nullable=False, server_default="0"),
        sa.Column("marca_modelo", sa.String(120)),
        sa.Column("anio_instalacion", sa.Integer),
        sa.Column("vida_util_h", sa.Integer),
        sa.Column("estado", sa.String(30), nullable=False, server_default="operativo"),
        sa.Column("nivel_regulacion", sa.Integer, nullable=False, server_default="100"),
        sa.Column("horas_funcionamiento", sa.Integer),
        sa.Column("consumo_mes_kwh", sa.Numeric(8, 2)),
        sa.Column("ultima_comunicacion_min", sa.Integer),
        sa.Column("tiene_documentacion", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("latitud", sa.Numeric(9, 6)),
        sa.Column("longitud", sa.Numeric(9, 6)),
        sa.Column("metadatos", sa.JSON()),
        *_ts(),
    )
    op.create_index("ix_alumbrado_luminarias_codigo", "alumbrado_luminarias", ["codigo"])
    op.create_index("ix_alumbrado_luminarias_zona_id", "alumbrado_luminarias", ["zona_id"])
    op.create_index("ix_alumbrado_luminarias_cuadro_codigo", "alumbrado_luminarias", ["cuadro_codigo"])
    op.create_index("ix_luminarias_zona_estado", "alumbrado_luminarias", ["zona_id", "estado"])
    op.create_index("ix_luminarias_tecnologia", "alumbrado_luminarias", ["tecnologia"])

    # ------------------------------------------------------------- agua_sectores
    op.create_table(
        "agua_sectores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("codigo", sa.String(20), nullable=False, unique=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("contadores", sa.Integer, nullable=False, server_default="0"),
        sa.Column("contadores_telelectura", sa.Integer, nullable=False, server_default="0"),
        sa.Column("caudal_entrada_ls", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("caudal_nocturno_ls", sa.Numeric(8, 2)),
        sa.Column("presion_bar", sa.Numeric(4, 2)),
        sa.Column("rendimiento_pct", sa.Numeric(5, 2)),
        sa.Column("fugas_detectadas", sa.Integer, nullable=False, server_default="0"),
        sa.Column("estado", sa.String(30), nullable=False, server_default="operativo"),
        sa.Column("metadatos", sa.JSON()),
        *_ts(),
    )
    op.create_index("ix_agua_sectores_codigo", "agua_sectores", ["codigo"])
    op.create_index("ix_agua_sectores_estado", "agua_sectores", ["estado"])

    # ------------------------------------------------------ residuos_contenedores
    op.create_table(
        "residuos_contenedores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("codigo", sa.String(20), nullable=False, unique=True),
        sa.Column("zona_id", sa.String(40), nullable=False),
        sa.Column("fraccion", sa.String(20), nullable=False),
        sa.Column("tiene_sensor", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("llenado_pct", sa.Integer),
        sa.Column("ruta", sa.String(40)),
        sa.Column("estado", sa.String(30), nullable=False, server_default="operativo"),
        sa.Column("latitud", sa.Numeric(9, 6)),
        sa.Column("longitud", sa.Numeric(9, 6)),
        *_ts(),
    )
    op.create_index("ix_residuos_contenedores_codigo", "residuos_contenedores", ["codigo"])
    op.create_index("ix_residuos_contenedores_zona_id", "residuos_contenedores", ["zona_id"])
    op.create_index("ix_residuos_contenedores_fraccion", "residuos_contenedores", ["fraccion"])
    op.create_index("ix_residuos_contenedores_sensor", "residuos_contenedores", ["tiene_sensor"])
    op.create_index("ix_contenedores_zona_fraccion", "residuos_contenedores", ["zona_id", "fraccion"])

    # --------------------------------------------------------- movilidad_puntos
    op.create_table(
        "movilidad_puntos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("codigo", sa.String(20), nullable=False, unique=True),
        sa.Column("nombre", sa.String(160), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("ubicacion", sa.String(200)),
        sa.Column("valor_actual", sa.Integer),
        sa.Column("capacidad", sa.Integer),
        sa.Column("unidad", sa.String(30)),
        sa.Column("estado", sa.String(30), nullable=False, server_default="operativo"),
        sa.Column("latitud", sa.Numeric(9, 6)),
        sa.Column("longitud", sa.Numeric(9, 6)),
        sa.Column("metadatos", sa.JSON()),
        *_ts(),
    )
    op.create_index("ix_movilidad_puntos_codigo", "movilidad_puntos", ["codigo"])
    op.create_index("ix_movilidad_puntos_tipo", "movilidad_puntos", ["tipo"])

    # --------------------------------------------------------- seguridad_camaras
    op.create_table(
        "seguridad_camaras",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("codigo", sa.String(20), nullable=False, unique=True),
        sa.Column("nombre", sa.String(160), nullable=False),
        sa.Column("zona_id", sa.String(40), nullable=False),
        sa.Column("tipo", sa.String(40)),
        sa.Column("con_analitica", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("retencion_dias", sa.Integer, nullable=False, server_default="30"),
        sa.Column("estado", sa.String(30), nullable=False, server_default="operativo"),
        sa.Column("latitud", sa.Numeric(9, 6)),
        sa.Column("longitud", sa.Numeric(9, 6)),
        *_ts(),
    )
    op.create_index("ix_seguridad_camaras_codigo", "seguridad_camaras", ["codigo"])
    op.create_index("ix_seguridad_camaras_zona_id", "seguridad_camaras", ["zona_id"])
    op.create_index("ix_seguridad_camaras_estado", "seguridad_camaras", ["estado"])

    # ------------------------------------------------------- energia_suministros
    op.create_table(
        "energia_suministros",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cups", sa.String(30), nullable=False, unique=True),
        sa.Column("edificio", sa.String(160), nullable=False),
        sa.Column("tipo", sa.String(60)),
        sa.Column("potencia_contratada_kw", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("consumo_mes_kwh", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("autoconsumo_mes_kwh", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("coste_mes_eur", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("tiene_fotovoltaica", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("estado", sa.String(30), nullable=False, server_default="operativo"),
        sa.Column("metadatos", sa.JSON()),
        *_ts(),
    )
    op.create_index("ix_energia_suministros_cups", "energia_suministros", ["cups"])
    op.create_index("ix_energia_suministros_edificio", "energia_suministros", ["edificio"])


def downgrade() -> None:
    for t in (
        "energia_suministros",
        "seguridad_camaras",
        "movilidad_puntos",
        "residuos_contenedores",
        "agua_sectores",
        "alumbrado_luminarias",
        "alumbrado_cuadros",
        "alumbrado_zonas",
    ):
        op.drop_table(t)
