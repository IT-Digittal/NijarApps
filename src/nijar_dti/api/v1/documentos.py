"""Endpoints de documentos adjuntos a puntos del territorio (gemelo digital).

Subida multipart (cualquier tipo de fichero: fichas técnicas, fotos, planos…),
listado filtrable, descarga autenticada y borrado. Escritura restringida a los
roles de gestión; lectura para cualquier usuario autenticado del panel.
"""

from __future__ import annotations

from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user, require_roles
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.documentos import DocumentoPuntoOut, DocumentosPage
from nijar_dti.services import documentos_service as svc

router = APIRouter()

_puede_gestionar = require_roles("administrador_tic", "gestor_contenidos", "operador_smart_office")


@router.post(
    "",
    response_model=DocumentoPuntoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Adjuntar un documento a un punto del mapa",
)
async def subir_documento(
    user: Annotated[CurrentUser, Depends(_puede_gestionar)],
    archivo: UploadFile = File(...),
    entidad_tipo: str = Form(...),
    entidad_id: str = Form(...),
    entidad_nombre: str = Form(""),
    latitud: float | None = Form(None),
    longitud: float | None = Form(None),
    descripcion: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> DocumentoPuntoOut:
    contenido = await archivo.read()
    try:
        doc = await svc.crear_documento(
            db,
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            entidad_nombre=entidad_nombre,
            latitud=latitud,
            longitud=longitud,
            nombre_archivo=archivo.filename or "documento",
            tipo_mime=archivo.content_type,
            contenido=contenido,
            descripcion=descripcion,
            subido_por=user.email,
        )
    except svc.DocumentoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    await db.commit()
    return DocumentoPuntoOut.model_validate(doc)


@router.get(
    "",
    response_model=DocumentosPage,
    summary="Listado de documentos del territorio",
)
async def listar(
    entidad_tipo: str | None = Query(None),
    entidad_id: str | None = Query(None),
    buscar: str | None = Query(None, max_length=120),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> DocumentosPage:
    filas, total = await svc.listar_documentos(db, entidad_tipo, entidad_id, buscar)
    return DocumentosPage(items=[DocumentoPuntoOut.model_validate(d) for d in filas], total=total)


@router.get("/{doc_id}/archivo", summary="Descargar el fichero de un documento")
async def descargar(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> FileResponse:
    try:
        doc = await svc.obtener_documento(db, doc_id)
    except svc.DocumentoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    disposicion = f"attachment; filename*=UTF-8''{quote(doc.nombre_archivo)}"
    return FileResponse(
        doc.ruta_almacen,
        media_type=doc.tipo_mime,
        headers={"Content-Disposition": disposicion},
    )


@router.delete(
    "/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un documento",
)
async def eliminar(
    doc_id: UUID,
    user: Annotated[CurrentUser, Depends(_puede_gestionar)],
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await svc.eliminar_documento(db, doc_id)
    except svc.DocumentoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    await db.commit()
