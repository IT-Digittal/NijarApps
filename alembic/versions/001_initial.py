"""Initial schema completo con todas las entidades FIWARE.

Revision ID: 001_initial
Revises:
Create Date: 2026-05-01 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql


revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ---------- usuarios ----------
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("nombre_completo", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("scopes_adicionales", postgresql.ARRAY(sa.String())),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("requiere_2fa", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("secreto_2fa", sa.String(255)),
        sa.Column("sso_subject", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_usuarios_email_activo", "usuarios", ["email", "activo"])
    op.create_index("ix_usuarios_rol", "usuarios", ["rol"])
    op.create_index("ix_usuarios_sso_subject", "usuarios", ["sso_subject"])

    # ---------- recursos_turisticos ----------
    op.create_table(
        "recursos_turisticos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("urn", sa.String(255), nullable=False, unique=True),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("categoria", sa.String(50), nullable=False),
        sa.Column("descripcion_corta", sa.Text()),
        sa.Column("nombre_i18n", postgresql.JSON()),
        sa.Column("descripcion_i18n", postgresql.JSON()),
        sa.Column("ubicacion", Geography(geometry_type="POINT", srid=4326)),
        sa.Column("direccion", sa.String(500)),
        sa.Column("municipio", sa.String(100), nullable=False, server_default="Níjar"),
        sa.Column("codigo_postal", sa.String(10)),
        sa.Column("telefono", sa.String(50)),
        sa.Column("email", sa.String(255)),
        sa.Column("web", sa.String(500)),
        sa.Column("horario", postgresql.JSON()),
        sa.Column("accesibilidad", postgresql.JSON()),
        sa.Column("servicios_disponibles", postgresql.ARRAY(sa.String())),
        sa.Column("etiquetas", postgresql.ARRAY(sa.String())),
        sa.Column("imagenes", postgresql.ARRAY(sa.String())),
        sa.Column("enlaces_externos", postgresql.JSON()),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("publicado", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("metadata_adicional", postgresql.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_recursos_categoria_activo", "recursos_turisticos", ["categoria", "activo"])
    op.create_index("ix_recursos_nombre", "recursos_turisticos", ["nombre"])
    op.execute("CREATE INDEX ix_recursos_ubicacion_gist ON recursos_turisticos USING GIST(ubicacion)")
    op.execute("CREATE INDEX ix_recursos_etiquetas_gin ON recursos_turisticos USING GIN(etiquetas)")

    # ---------- eventos_turisticos ----------
    op.create_table(
        "eventos_turisticos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("urn", sa.String(255), nullable=False, unique=True),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(50), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column("nombre_i18n", postgresql.JSON()),
        sa.Column("descripcion_i18n", postgresql.JSON()),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recurso_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("recursos_turisticos.id", ondelete="SET NULL")),
        sa.Column("ubicacion", Geography(geometry_type="POINT", srid=4326)),
        sa.Column("direccion", sa.String(500)),
        sa.Column("organizador", sa.String(255)),
        sa.Column("precio", sa.String(100)),
        sa.Column("capacidad_aforo", sa.Integer()),
        sa.Column("enlace_inscripcion", sa.String(500)),
        sa.Column("imagenes", postgresql.ARRAY(sa.String())),
        sa.Column("etiquetas", postgresql.ARRAY(sa.String())),
        sa.Column("fuente", sa.String(100)),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("publicado", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("metadata_adicional", postgresql.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_eventos_fechas", "eventos_turisticos", ["fecha_inicio", "fecha_fin"])
    op.create_index("ix_eventos_tipo_activo", "eventos_turisticos", ["tipo", "activo"])
    op.create_index("ix_eventos_recurso_id", "eventos_turisticos", ["recurso_id"])

    # ---------- servicios ----------
    op.create_table(
        "servicios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("urn", sa.String(255), nullable=False, unique=True),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(50), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column("nombre_i18n", postgresql.JSON()),
        sa.Column("descripcion_i18n", postgresql.JSON()),
        sa.Column("ubicacion", Geography(geometry_type="POINT", srid=4326)),
        sa.Column("direccion", sa.String(500)),
        sa.Column("municipio", sa.String(100), nullable=False, server_default="Níjar"),
        sa.Column("codigo_postal", sa.String(10)),
        sa.Column("telefono", sa.String(50)),
        sa.Column("email", sa.String(255)),
        sa.Column("web", sa.String(500)),
        sa.Column("horario", postgresql.JSON()),
        sa.Column("rango_precios", sa.String(20)),
        sa.Column("valoracion_media", sa.Numeric(3, 2)),
        sa.Column("registro_turismo", sa.String(100)),
        sa.Column("cif", sa.String(20)),
        sa.Column("accesibilidad", postgresql.JSON()),
        sa.Column("idiomas_atencion", postgresql.ARRAY(sa.String())),
        sa.Column("etiquetas", postgresql.ARRAY(sa.String())),
        sa.Column("imagenes", postgresql.ARRAY(sa.String())),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("publicado", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("metadata_adicional", postgresql.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_servicios_tipo_activo", "servicios", ["tipo", "activo"])
    op.execute("CREATE INDEX ix_servicios_ubicacion_gist ON servicios USING GIST(ubicacion)")

    # ---------- sensores ----------
    op.create_table(
        "sensores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("urn", sa.String(255), nullable=False, unique=True),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(50), nullable=False),
        sa.Column("fabricante", sa.String(100)),
        sa.Column("modelo", sa.String(100)),
        sa.Column("numero_serie", sa.String(100)),
        sa.Column("firmware_version", sa.String(50)),
        sa.Column("ubicacion", Geography(geometry_type="POINT", srid=4326)),
        sa.Column("descripcion_ubicacion", sa.Text()),
        sa.Column("unidades_medida", sa.String(50)),
        sa.Column("rango_minimo", sa.Float()),
        sa.Column("rango_maximo", sa.Float()),
        sa.Column("umbrales_alerta", postgresql.JSON()),
        sa.Column("frecuencia_muestreo_seg", sa.Integer()),
        sa.Column("estado", sa.String(30), nullable=False, server_default="desconocido"),
        sa.Column("nivel_bateria", sa.Float()),
        sa.Column("topic_mqtt", sa.String(255)),
        sa.Column("fecha_ultima_calibracion", sa.String(20)),
        sa.Column("fecha_proxima_calibracion", sa.String(20)),
        sa.Column("etiquetas", postgresql.ARRAY(sa.String())),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("metadata_adicional", postgresql.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_sensores_tipo_estado", "sensores", ["tipo", "estado"])
    op.execute("CREATE INDEX ix_sensores_ubicacion_gist ON sensores USING GIST(ubicacion)")

    # ---------- observaciones ----------
    op.create_table(
        "observaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sensor_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sensores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("observado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valor", sa.Numeric(12, 4)),
        sa.Column("unidades", sa.String(50)),
        sa.Column("valores", postgresql.JSON()),
        sa.Column("valido", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("motivo_invalidez", sa.String(255)),
        sa.Column("payload_original", postgresql.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_observaciones_sensor_tiempo", "observaciones", ["sensor_id", "observado_en"])
    op.create_index("ix_observaciones_tiempo", "observaciones", ["observado_en"])

    # ---------- visitas ----------
    op.create_table(
        "visitas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("ocurrido_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("visitante_hash", sa.String(64)),
        sa.Column("recurso_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("recursos_turisticos.id", ondelete="SET NULL")),
        sa.Column("idioma", sa.String(5)),
        sa.Column("canal", sa.String(50)),
        sa.Column("atributos", postgresql.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_visitas_tipo_tiempo", "visitas", ["tipo", "ocurrido_en"])
    op.create_index("ix_visitas_canal", "visitas", ["canal"])
    op.create_index("ix_visitas_visitante_hash", "visitas", ["visitante_hash"])

    # ---------- opiniones ----------
    op.create_table(
        "opiniones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("fuente", sa.String(40), nullable=False),
        sa.Column("fuente_id_externo", sa.String(255)),
        sa.Column("autor_handle", sa.String(255)),
        sa.Column("texto_original", sa.Text(), nullable=False),
        sa.Column("idioma", sa.String(5)),
        sa.Column("publicado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sentimiento", sa.String(20), nullable=False, server_default="desconocido"),
        sa.Column("score_sentimiento", sa.Numeric(5, 4)),
        sa.Column("temas", postgresql.ARRAY(sa.String())),
        sa.Column("entidades_mencionadas", postgresql.ARRAY(sa.String())),
        sa.Column("metricas", postgresql.JSON()),
        sa.Column("latitud", sa.Numeric(9, 6)),
        sa.Column("longitud", sa.Numeric(9, 6)),
        sa.Column("capturado_en", sa.DateTime(timezone=True)),
        sa.Column("payload_original", postgresql.JSON()),
        sa.Column("revisado_humano", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("sentimiento_humano", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_opiniones_fuente_publicado", "opiniones", ["fuente", "publicado_en"])
    op.create_index("ix_opiniones_sentimiento_publicado", "opiniones", ["sentimiento", "publicado_en"])
    op.create_index("ix_opiniones_idioma", "opiniones", ["idioma"])

    # ---------- contenidos ----------
    op.create_table(
        "contenidos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("titulo_i18n", postgresql.JSON()),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("cuerpo_i18n", postgresql.JSON()),
        sa.Column("canales", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("plantilla_id", sa.String(100)),
        sa.Column("recurso_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("recursos_turisticos.id", ondelete="SET NULL")),
        sa.Column("estado", sa.String(20), nullable=False, server_default="borrador"),
        sa.Column("publicar_desde", sa.DateTime(timezone=True)),
        sa.Column("publicar_hasta", sa.DateTime(timezone=True)),
        sa.Column("imagenes", postgresql.ARRAY(sa.String())),
        sa.Column("enlaces", postgresql.JSON()),
        sa.Column("etiquetas", postgresql.ARRAY(sa.String())),
        sa.Column("metadata_adicional", postgresql.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_contenidos_estado_publicar", "contenidos", ["estado", "publicar_desde"])

    # ---------- faqs ----------
    op.create_table(
        "faqs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("intent", sa.String(100), nullable=False, unique=True),
        sa.Column("categoria", sa.String(50), nullable=False),
        sa.Column("pregunta_es", sa.Text(), nullable=False),
        sa.Column("pregunta_en", sa.Text()),
        sa.Column("pregunta_de", sa.Text()),
        sa.Column("pregunta_fr", sa.Text()),
        sa.Column("frases_entrenamiento_es", postgresql.ARRAY(sa.String())),
        sa.Column("frases_entrenamiento_en", postgresql.ARRAY(sa.String())),
        sa.Column("frases_entrenamiento_de", postgresql.ARRAY(sa.String())),
        sa.Column("frases_entrenamiento_fr", postgresql.ARRAY(sa.String())),
        sa.Column("respuesta_es", sa.Text(), nullable=False),
        sa.Column("respuesta_en", sa.Text()),
        sa.Column("respuesta_de", sa.Text()),
        sa.Column("respuesta_fr", sa.Text()),
        sa.Column("nivel_confianza", sa.String(20), nullable=False, server_default="alta"),
        sa.Column("fuente_url", sa.String(500)),
        sa.Column("fuente_descripcion", sa.String(255)),
        sa.Column("fecha_validez_hasta", sa.DateTime(timezone=True)),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata_adicional", postgresql.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_faqs_categoria_activo", "faqs", ["categoria", "activo"])

    # ---------- interacciones_chatbot ----------
    op.create_table(
        "interacciones_chatbot",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sesion_id", sa.String(100), nullable=False),
        sa.Column("canal", sa.String(20), nullable=False),
        sa.Column("idioma", sa.String(5), nullable=False),
        sa.Column("pregunta", sa.Text(), nullable=False),
        sa.Column("intent_detectado", sa.String(100)),
        sa.Column("nivel_confianza", sa.String(20), nullable=False, server_default="fuera_de_dominio"),
        sa.Column("score_confianza", sa.Float()),
        sa.Column("respuesta", sa.Text(), nullable=False),
        sa.Column("fuentes", postgresql.JSON()),
        sa.Column("util", sa.Boolean()),
        sa.Column("comentario", sa.Text()),
        sa.Column("latencia_ms", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_interacciones_sesion_creado", "interacciones_chatbot", ["sesion_id", "created_at"])
    op.create_index("ix_interacciones_intent_creado", "interacciones_chatbot", ["intent_detectado", "created_at"])


def downgrade() -> None:
    op.drop_table("interacciones_chatbot")
    op.drop_table("faqs")
    op.drop_table("contenidos")
    op.drop_table("opiniones")
    op.drop_table("visitas")
    op.drop_table("observaciones")
    op.drop_table("sensores")
    op.drop_table("servicios")
    op.drop_table("eventos_turisticos")
    op.drop_table("recursos_turisticos")
    op.drop_table("usuarios")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
    op.execute("DROP EXTENSION IF EXISTS postgis")
