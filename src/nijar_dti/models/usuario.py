"""Entidad Usuario — Cuentas con acceso a la plataforma DTI.

Implementa los 5 perfiles RBAC definidos en la Memoria Técnica:
- administrador_tic
- gestor_contenidos
- analista_datos
- operador_smart_office
- auditor

Cumple con el principio de privilegio mínimo (ENS Medio).
"""

from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import AuditMixin


class RolUsuario(StrEnum):
    """Roles RBAC de la plataforma DTI Níjar."""

    ADMINISTRADOR_TIC = "administrador_tic"
    GESTOR_CONTENIDOS = "gestor_contenidos"
    ANALISTA_DATOS = "analista_datos"
    OPERADOR_SMART_OFFICE = "operador_smart_office"
    AUDITOR = "auditor"


class Usuario(Base, AuditMixin):
    """Cuenta de usuario con acceso a la plataforma."""

    __tablename__ = "usuarios"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nombre_completo: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))

    rol: Mapped[RolUsuario] = mapped_column(String(50), index=True)
    scopes_adicionales: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), default=None
    )

    activo: Mapped[bool] = mapped_column(default=True)
    requiere_2fa: Mapped[bool] = mapped_column(default=False)
    secreto_2fa: Mapped[str | None] = mapped_column(String(255), default=None)

    # Si el usuario procede del SSO/AD municipal
    sso_subject: Mapped[str | None] = mapped_column(String(255), default=None, index=True)

    __table_args__ = (
        Index("ix_usuarios_email_activo", "email", "activo"),
    )
