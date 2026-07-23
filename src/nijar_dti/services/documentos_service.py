"""Lógica de negocio de los documentos adjuntos a puntos del territorio.

El binario se guarda en el almacenamiento local de la plataforma
(``STORAGE_LOCAL_PATH``, volumen persistente en producción) con un nombre
interno UUID — nunca el nombre original — y los metadatos en BBDD.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import get_settings
from nijar_dti.models.documento_punto import DocumentoPunto
from nijar_dti.schemas.documentos import TAMANO_MAX_BYTES, TIPOS_ENTIDAD_VALIDOS


class DocumentoError(Exception):
    """Error de validación o de almacenamiento de un documento."""


class DocumentoNoEncontradoError(DocumentoError):
    pass


def _directorio_documentos() -> Path:
    base = Path(get_settings().storage_local_path) / "documentos"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _nombre_seguro(nombre: str) -> str:
    """Nombre visible saneado (sin rutas ni caracteres de control)."""
    limpio = re.sub(r"[\\/\x00-\x1f]", "_", (nombre or "").strip()) or "documento"
    return limpio[:255]


async def crear_documento(
    db: AsyncSession,
    *,
    entidad_tipo: str,
    entidad_id: str,
    entidad_nombre: str,
    latitud: float | None,
    longitud: float | None,
    nombre_archivo: str,
    tipo_mime: str | None,
    contenido: bytes,
    descripcion: str | None,
    subido_por: str | None,
) -> DocumentoPunto:
    if entidad_tipo not in TIPOS_ENTIDAD_VALIDOS:
        raise DocumentoError(
            f"Tipo de entidad '{entidad_tipo}' no válido. Válidos: {sorted(TIPOS_ENTIDAD_VALIDOS)}"
        )
    if not contenido:
        raise DocumentoError("El fichero está vacío")
    if len(contenido) > TAMANO_MAX_BYTES:
        raise DocumentoError(
            f"El fichero supera el máximo de {TAMANO_MAX_BYTES // (1024 * 1024)} MB"
        )

    nombre = _nombre_seguro(nombre_archivo)
    sufijo = Path(nombre).suffix[:16]
    interno = f"{uuid.uuid4().hex}{sufijo}"
    destino = _directorio_documentos() / interno
    destino.write_bytes(contenido)

    doc = DocumentoPunto(
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id[:255],
        entidad_nombre=(entidad_nombre or entidad_id)[:255],
        latitud=latitud,
        longitud=longitud,
        nombre_archivo=nombre,
        descripcion=(descripcion or None),
        tipo_mime=(tipo_mime or "application/octet-stream")[:120],
        tamano_bytes=len(contenido),
        ruta_almacen=str(destino),
        subido_por=subido_por,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


async def listar_documentos(
    db: AsyncSession,
    entidad_tipo: str | None = None,
    entidad_id: str | None = None,
    buscar: str | None = None,
    limite: int = 500,
) -> tuple[list[DocumentoPunto], int]:
    base = select(DocumentoPunto)
    if entidad_tipo:
        base = base.where(DocumentoPunto.entidad_tipo == entidad_tipo)
    if entidad_id:
        base = base.where(DocumentoPunto.entidad_id == entidad_id)
    if buscar:
        patron = f"%{buscar.lower()}%"
        base = base.where(
            func.lower(DocumentoPunto.nombre_archivo).like(patron)
            | func.lower(DocumentoPunto.entidad_nombre).like(patron)
        )
    total = int(
        (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one() or 0
    )
    filas = (
        (await db.execute(base.order_by(DocumentoPunto.created_at.desc()).limit(limite)))
        .scalars()
        .all()
    )
    return list(filas), total


async def obtener_documento(db: AsyncSession, doc_id: UUID) -> DocumentoPunto:
    doc = await db.get(DocumentoPunto, doc_id)
    if doc is None:
        raise DocumentoNoEncontradoError(f"Documento {doc_id} no encontrado")
    return doc


async def eliminar_documento(db: AsyncSession, doc_id: UUID) -> None:
    doc = await obtener_documento(db, doc_id)
    ruta = Path(doc.ruta_almacen)
    await db.delete(doc)
    await db.flush()
    try:
        if ruta.is_file():
            ruta.unlink()
    except OSError:
        pass  # los metadatos ya no existen; un huérfano en disco no bloquea
