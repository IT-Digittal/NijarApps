"""Entidad Cliente — Ficha general del cliente / Ayuntamiento.

Centraliza los datos de identificación del proyecto exigidos por el pliego
(bloque 1): cliente y área responsable, responsables municipales y técnicos,
canales oficiales, idiomas activos y periodo de explotación / mantenimiento.

Sirve de cabecera para filtrar informes y para justificar la trazabilidad de
los KPIs (¿quién?, ¿en qué periodo?, ¿por qué canal?).
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import AuditMixin


class Cliente(Base, AuditMixin):
    """Ficha general del cliente / Ayuntamiento (bloque 1 del pliego)."""

    __tablename__ = "clientes"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    # ---- obligatorios ----
    nombre: Mapped[str] = mapped_column(String(255), index=True)

    # ---- opcionales con default ----
    area_responsable: Mapped[str | None] = mapped_column(String(255), default=None)
    proyecto: Mapped[str | None] = mapped_column(String(255), default=None)
    descripcion: Mapped[str | None] = mapped_column(Text, default=None)

    cif: Mapped[str | None] = mapped_column(String(20), default=None)
    direccion: Mapped[str | None] = mapped_column(String(500), default=None)
    municipio: Mapped[str] = mapped_column(String(100), default="Níjar")
    provincia: Mapped[str] = mapped_column(String(100), default="Almería")

    # Responsable municipal (contacto principal): {nombre, cargo, email, telefono}
    responsable_municipal: Mapped[dict | None] = mapped_column(JSON, default=None)

    # Responsables técnicos por área (TI, turismo, comunicación, mantenimiento):
    # [{"area": "...", "nombre": "...", "email": "...", "telefono": "..."}]
    responsables_tecnicos: Mapped[list[dict] | None] = mapped_column(JSON, default=None)

    # Canales oficiales: {web, app, facebook, instagram, otros: [...]}
    canales_oficiales: Mapped[dict | None] = mapped_column(JSON, default=None)

    # Idiomas activos de la plataforma (ES/EN/FR/DE)
    idiomas_activos: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)

    # Periodo de explotación y mantenimiento
    fecha_inicio_explotacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    fecha_fin_mantenimiento: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    # Hitos del proyecto: [{"nombre": "...", "fecha": "...", "estado": "..."}]
    hitos: Mapped[list[dict] | None] = mapped_column(JSON, default=None)

    activo: Mapped[bool] = mapped_column(default=True)

    metadata_adicional: Mapped[dict | None] = mapped_column(JSON, default=None)
