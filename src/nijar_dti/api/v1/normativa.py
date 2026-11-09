"""Normativa municipal: ordenanzas de la sede electrónica, con buscador y PDF.

- Lectura (listado, búsqueda, detalle): cualquier usuario autenticado del panel.
- PDF original: público, porque es documentación ya publicada en la sede
  electrónica y el asistente del tótem enlaza a él en sus respuestas.
- Importación y baja: roles de gestión de contenidos.
"""

from __future__ import annotations

from typing import Annotated, Literal
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user, require_roles
from nijar_dti.core.database import get_db
from nijar_dti.models.normativa import Normativa, NormativaFragmento
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.normativa import (
    FragmentoOut,
    ImportacionNormativaOut,
    NormativaDetalle,
    NormativaOut,
    PasajeOut,
    ResumenNormativa,
)
from nijar_dti.services import normativa_service as svc

router = APIRouter()

_puede_gestionar = require_roles("administrador_tic", "gestor_contenidos")
TipoNormativa = Literal[
    "ordenanza", "reglamento", "edicto", "proyecto", "certificado", "bando", "otro"
]
MAX_PDF_BYTES = 40 * 1024 * 1024


def _out(
    n: Normativa, extracto: str | None = None, relevancia: float | None = None
) -> NormativaOut:
    o = NormativaOut.model_validate(n)
    o.sin_texto = bool((n.metadatos or {}).get("sin_texto"))
    o.extracto, o.relevancia = extracto, relevancia
    return o


@router.get("", response_model=list[NormativaOut], summary="Normativa municipal (con búsqueda)")
async def listar_normativa(
    buscar: str | None = Query(None, max_length=200, description="Palabras a buscar en el texto"),
    tipo: TipoNormativa | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[NormativaOut]:
    resultados = await svc.buscar(db, buscar, tipo)
    return [_out(r.normativa, r.extracto, r.relevancia if buscar else None) for r in resultados]


@router.get("/resumen", response_model=ResumenNormativa, summary="Recuento de la normativa")
async def resumen_normativa(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> ResumenNormativa:
    activas = Normativa.activa.is_(True)
    por_tipo = {
        str(t): int(n)
        for t, n in (
            await db.execute(
                select(Normativa.tipo, func.count()).where(activas).group_by(Normativa.tipo)
            )
        ).all()
    }
    filas = (await db.execute(select(Normativa.metadatos).where(activas))).scalars().all()
    ultima = (await db.execute(select(func.max(Normativa.updated_at)).where(activas))).scalar()
    return ResumenNormativa(
        total=sum(por_tipo.values()),
        por_tipo=por_tipo,
        sin_texto=sum(1 for m in filas if isinstance(m, dict) and m.get("sin_texto")),
        ultima_importacion=ultima,
    )


@router.get(
    "/pasajes",
    response_model=list[PasajeOut],
    summary="Artículos más relevantes para una pregunta (lo que usa el asistente)",
)
async def pasajes(
    pregunta: str = Query(..., min_length=3, max_length=300),
    limite: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[PasajeOut]:
    return [
        PasajeOut(
            normativa_id=p.normativa_id,
            titulo=p.titulo,
            articulo=p.articulo,
            texto=p.texto,
            relevancia=p.relevancia,
            url_pdf=svc.url_pdf(p.normativa_id),
        )
        for p in await svc.buscar_fragmentos(db, pregunta, limite)
    ]


@router.post(
    "/importar",
    response_model=ImportacionNormativaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Importar ordenanzas en PDF (y, opcional, su índice manifest.csv)",
)
async def importar_normativa(
    user: Annotated[CurrentUser, Depends(_puede_gestionar)],
    archivos: list[UploadFile] = File(..., description="Uno o varios PDF"),
    manifest: UploadFile | None = File(None, description="manifest.csv con título, URL y fecha"),
    db: AsyncSession = Depends(get_db),
) -> ImportacionNormativaOut:
    indice = svc.leer_manifest(await manifest.read()) if manifest is not None else {}
    importadas = actualizadas = 0
    errores: list[str] = []
    documentos: list[NormativaOut] = []
    for archivo in archivos:
        nombre = archivo.filename or "documento.pdf"
        contenido = await archivo.read()
        if len(contenido) > MAX_PDF_BYTES:
            errores.append(f"{nombre}: supera 40 MB")
            continue
        datos = svc.datos_de_manifest(indice.get(nombre))
        try:
            async with db.begin_nested():  # un PDF que falla no deja la sesión rota
                norma, nueva = await svc.importar_pdf(
                    db,
                    contenido,
                    nombre,
                    titulo=datos["titulo"],
                    url_origen=datos["url"],
                    fecha_publicacion=datos["fecha"],
                )
        except Exception as exc:  # noqa: BLE001 — un PDF dañado no frena el resto
            errores.append(f"{nombre}: {exc}")
            continue
        importadas += int(nueva)
        actualizadas += int(not nueva)
        documentos.append(_out(norma))
    return ImportacionNormativaOut(
        importadas=importadas, actualizadas=actualizadas, errores=errores, documentos=documentos
    )


@router.get("/{normativa_id}", response_model=NormativaDetalle, summary="Ficha con sus artículos")
async def detalle_normativa(
    normativa_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> NormativaDetalle:
    n = await db.get(Normativa, normativa_id)
    if n is None:
        raise HTTPException(status_code=404, detail="Normativa no encontrada")
    frags = (
        (
            await db.execute(
                select(NormativaFragmento)
                .where(NormativaFragmento.normativa_id == n.id)
                .order_by(NormativaFragmento.orden)
            )
        )
        .scalars()
        .all()
    )
    base = _out(n)
    return NormativaDetalle(
        **base.model_dump(), fragmentos=[FragmentoOut.model_validate(f) for f in frags]
    )


@router.get("/{normativa_id}/pdf", summary="PDF original (público)", response_class=FileResponse)
async def pdf_normativa(normativa_id: UUID, db: AsyncSession = Depends(get_db)) -> FileResponse:
    n = await db.get(Normativa, normativa_id)
    if n is None or not n.activa:
        raise HTTPException(status_code=404, detail="Normativa no encontrada")
    ruta = svc.ruta_fichero(n)
    if not ruta.is_file():
        raise HTTPException(status_code=404, detail="El fichero no está en el almacenamiento")
    return FileResponse(
        ruta,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{quote(n.nombre_archivo)}"},
    )


@router.delete(
    "/{normativa_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Retirar una normativa"
)
async def retirar_normativa(
    normativa_id: UUID,
    user: Annotated[CurrentUser, Depends(_puede_gestionar)],
    db: AsyncSession = Depends(get_db),
) -> None:
    n = await db.get(Normativa, normativa_id)
    if n is None:
        raise HTTPException(status_code=404, detail="Normativa no encontrada")
    n.activa = False  # se retira del buscador y del asistente; el fichero se conserva
