"""Normativa municipal: importar los PDF de la sede electrónica, buscarlos y citarlos.

Flujo:

1. ``importar_pdf`` recibe un PDF (subido desde el panel o desde una carpeta con
   ``python -m nijar_dti.workers.importar_normativa``), extrae su texto con
   ``pypdf``, lo guarda en ``STORAGE_LOCAL_PATH/normativa/`` y lo parte en
   artículos (``fragmentar``). Un PDF ya importado (mismo SHA-256) se actualiza,
   no se duplica.
2. ``buscar`` (panel) y ``buscar_fragmentos`` (asistente) usan la búsqueda de
   texto completo de PostgreSQL en español: cualquier palabra de la consulta
   cuenta (OR) y se ordena por relevancia, para que una pregunta natural
   («¿se puede vender en la playa?») encuentre la ordenanza de venta ambulante.
3. El asistente (``chatbot_openai_adapter`` y el motor léxico) recibe los
   pasajes encontrados y responde citando la ordenanza y el artículo, con el
   enlace público al PDF (``/api/v1/normativa/{id}/pdf``).

Un PDF escaneado sin capa de texto se guarda igualmente (se puede descargar),
pero no se puede buscar: queda marcado con ``metadatos.sin_texto``.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import get_settings
from nijar_dti.core.logging import get_logger
from nijar_dti.models.normativa import Normativa, NormativaFragmento

logger = get_logger(__name__)

TAMANO_FRAGMENTO = 1500  # caracteres por pasaje cuando no hay artículos
MAX_FRAGMENTO = 2500
_RE_ARTICULO = re.compile(
    r"(?im)^[ \t]*(art[íi]culo|art\.)[ \t]+(\d+[ºª°]?(?:[ \t]*(?:bis|ter))?)[ \t]*[.:\-–—]?[ \t]*"
)
# Palabras que no ayudan a encontrar la ordenanza (además de las vacías del español de PostgreSQL)
_VACIAS = """que como donde cuando cual cuales quien puedo puede pueden hay tengo tiene para por con
sin sobre una uno unos unas los las del al en el la de y o se es me mi nijar ayuntamiento
municipio municipal ordenanza normativa norma dice regula esto eso esta este estos estas
aqui alli algo todo hacer saber quiero necesito informacion hola gracias favor"""
_PALABRAS_VACIAS = frozenset(_VACIAS.split())


# ------------------------------------------------------------ utilidades -----
def _sin_acentos(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def limpiar_texto(texto: str) -> str:
    """Une las palabras partidas por guion al final de línea y normaliza espacios."""
    texto = texto.replace("\r", "\n").replace("­", "")
    texto = re.sub(r"(\w)-\n(\w)", r"\1\2", texto)
    texto = re.sub(r"[ \t ]+", " ", texto)
    texto = re.sub(r"\n[ \t]+", "\n", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def extraer_texto(contenido: bytes) -> tuple[str, int]:
    """Texto del PDF y número de páginas (texto vacío si es un escaneo sin OCR)."""
    from pypdf import PdfReader

    lector = PdfReader(io.BytesIO(contenido))
    paginas = []
    for pagina in lector.pages:
        try:
            paginas.append(pagina.extract_text() or "")
        except Exception:  # noqa: BLE001 — una página ilegible no invalida el documento
            paginas.append("")
    return limpiar_texto("\n".join(paginas)), len(lector.pages)


def tipo_de(nombre: str) -> str:
    n = _sin_acentos(nombre).lower()
    for clave, tipo in (
        ("certificado", "certificado"),
        ("edicto", "edicto"),
        ("proyecto", "proyecto"),
        ("reglamento", "reglamento"),
        ("ordenanza", "ordenanza"),
        ("bando", "bando"),
    ):
        if clave in n:
            return tipo
    return "otro"


def titulo_de_archivo(nombre_archivo: str) -> str:
    """«ORDENANZA_REGULADORA_DE_LA_CIRCULACION.pdf» → «Ordenanza reguladora de la circulacion»."""
    base = Path(nombre_archivo).stem
    base = re.sub(r"[_]+", " ", base)
    base = re.sub(r"\s+", " ", base).strip(" -.")
    return (base[:1].upper() + base[1:].lower()) if base else nombre_archivo


def _fecha(valor: str | None) -> date | None:
    if not valor:
        return None
    valor = valor.strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%y"):
        try:
            return datetime.strptime(valor[:10], formato).date()
        except ValueError:
            continue
    return None


def leer_manifest(contenido: bytes) -> dict[str, dict[str, str]]:
    """Índice ``manifest.csv`` → {nombre de archivo: fila}, con cabeceras normalizadas.

    Acepta «,» o «;» como separador y cualquier nombre de columna razonable
    (archivo/fichero/filename, titulo/title/nombre, url/enlace, fecha…).
    """
    texto = contenido.decode("utf-8-sig", errors="replace")
    try:
        dialecto = csv.Sniffer().sniff(texto[:4096], delimiters=",;\t")
        separador = dialecto.delimiter
    except csv.Error:
        separador = ";" if texto.count(";") > texto.count(",") else ","
    lector = csv.DictReader(io.StringIO(texto), delimiter=separador)
    salida: dict[str, dict[str, str]] = {}
    for fila in lector:
        norm = {
            _sin_acentos(str(k or "")).strip().lower(): (v or "").strip() for k, v in fila.items()
        }
        archivo = next(
            (
                norm[k]
                for k in (
                    "archivo",
                    "fichero",
                    "filename",
                    "file",
                    "nombre_archivo",
                    "pdf",
                    "local",
                )
                if norm.get(k)
            ),
            "",
        )
        if not archivo:
            # una columna cuyo valor acaba en .pdf
            archivo = next((v for v in norm.values() if v.lower().endswith(".pdf")), "")
        if archivo:
            salida[Path(archivo).name] = norm
    return salida


def datos_de_manifest(fila: dict[str, str] | None) -> dict[str, Any]:
    fila = fila or {}
    titulo = next(
        (fila[k] for k in ("titulo", "title", "nombre", "name", "descripcion") if fila.get(k)),
        None,
    )
    url = next((fila[k] for k in ("url", "enlace", "link", "href", "origen") if fila.get(k)), None)
    fecha = next(
        (
            _fecha(fila[k])
            for k in ("fecha", "fecha_publicacion", "date", "publicacion")
            if fila.get(k)
        ),
        None,
    )
    return {"titulo": titulo, "url": url, "fecha": fecha}


# ------------------------------------------------------------ fragmentos -----
@dataclass(frozen=True)
class Fragmento:
    orden: int
    articulo: str | None
    texto: str


def _trocear(texto: str, tam: int = TAMANO_FRAGMENTO) -> list[str]:
    """Trozos de ~``tam`` caracteres cortando en fin de párrafo o de frase."""
    trozos: list[str] = []
    resto = texto.strip()
    while len(resto) > tam:
        corte = resto.rfind("\n", 0, tam)
        if corte < tam * 0.5:
            corte = resto.rfind(". ", 0, tam)
        if corte < tam * 0.5:
            corte = tam
        trozos.append(resto[: corte + 1].strip())
        resto = resto[corte + 1 :].strip()
    if resto:
        trozos.append(resto)
    return trozos


def fragmentar(texto: str) -> list[Fragmento]:
    """Parte el texto por artículos («Artículo 12. …»); si no los hay, en trozos."""
    if not texto.strip():
        return []
    marcas = list(_RE_ARTICULO.finditer(texto))
    piezas: list[tuple[str | None, str]] = []
    if len(marcas) >= 2:
        preambulo = texto[: marcas[0].start()].strip()
        if preambulo:
            piezas.extend((None, t) for t in _trocear(preambulo))
        for i, m in enumerate(marcas):
            fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
            cuerpo = texto[m.start() : fin].strip()
            nombre = f"Artículo {m.group(2).strip()}"
            linea = cuerpo.split("\n", 1)[0]
            titulo_art = linea[m.end() - m.start() :].strip(" .:-–—")
            if titulo_art and len(titulo_art) < 120:
                nombre = f"{nombre}. {titulo_art}"
            trozos = _trocear(cuerpo, MAX_FRAGMENTO) if len(cuerpo) > MAX_FRAGMENTO else [cuerpo]
            piezas.extend((nombre[:160], t) for t in trozos)
    else:
        piezas = [(None, t) for t in _trocear(texto)]
    return [Fragmento(i, a, t) for i, (a, t) in enumerate(piezas) if t.strip()]


# ------------------------------------------------------------ importación -----
def _ruta_almacen(sha: str) -> Path:
    return Path(get_settings().storage_local_path) / "normativa" / sha[:2] / f"{sha}.pdf"


async def importar_pdf(
    db: AsyncSession,
    contenido: bytes,
    nombre_archivo: str,
    *,
    titulo: str | None = None,
    url_origen: str | None = None,
    fecha_publicacion: date | None = None,
    guardar_fichero: bool = True,
) -> tuple[Normativa, bool]:
    """Importa (o actualiza) un PDF. Devuelve (normativa, es_nueva)."""
    if not contenido.startswith(b"%PDF"):
        raise ValueError(f"{nombre_archivo}: no es un PDF")
    sha = hashlib.sha256(contenido).hexdigest()
    texto, paginas = extraer_texto(contenido)
    ruta = _ruta_almacen(sha)
    if guardar_fichero:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(contenido)
    existente = (
        await db.execute(select(Normativa).where(Normativa.sha256 == sha))
    ).scalar_one_or_none()
    titulo_final = (titulo or "").strip() or titulo_de_archivo(nombre_archivo)
    metadatos: dict[str, Any] = {"sin_texto": not texto}
    if existente is None:
        norma = Normativa(
            titulo=titulo_final[:500],
            tipo=tipo_de(f"{titulo_final} {nombre_archivo}"),
            nombre_archivo=nombre_archivo[:255],
            fichero=str(ruta.relative_to(Path(get_settings().storage_local_path))),
            sha256=sha,
            tamano_bytes=len(contenido),
            paginas=paginas,
            texto=texto,
            url_origen=(url_origen or None) and url_origen[:500],
            fecha_publicacion=fecha_publicacion,
            metadatos=metadatos,
        )
        db.add(norma)
        await db.flush()
        nueva = True
    else:
        norma = existente
        norma.titulo = titulo_final[:500] if titulo else norma.titulo
        norma.url_origen = url_origen or norma.url_origen
        norma.fecha_publicacion = fecha_publicacion or norma.fecha_publicacion
        norma.texto, norma.paginas = texto, paginas
        norma.metadatos = {**(norma.metadatos or {}), **metadatos}
        norma.activa = True
        await db.execute(
            delete(NormativaFragmento).where(NormativaFragmento.normativa_id == norma.id)
        )
        nueva = False
    for f in fragmentar(texto):
        db.add(
            NormativaFragmento(
                normativa_id=norma.id, orden=f.orden, texto=f.texto, articulo=f.articulo
            )
        )
    await db.flush()
    return norma, nueva


def ruta_fichero(norma: Normativa) -> Path:
    return Path(get_settings().storage_local_path) / norma.fichero


# ------------------------------------------------------------ búsqueda -------
def terminos(consulta: str) -> list[str]:
    """Palabras significativas de una consulta en lenguaje natural."""
    palabras = re.findall(r"[0-9a-záéíóúüñ]+", consulta.lower())
    return [p for p in palabras if len(p) > 2 and _sin_acentos(p) not in _PALABRAS_VACIAS][:12]


def consulta_ts(consulta: str) -> str | None:
    """Expresión ``to_tsquery`` en OR con prefijos («ambulante | vend:*»)."""
    t = terminos(consulta)
    return " | ".join(f"{p}:*" for p in t) if t else None


_ES: Any = literal_column("'spanish'")  # regconfig literal: el mismo que usan los índices GIN


def _vector_normativa() -> Any:
    return func.to_tsvector(
        _ES, Normativa.titulo.op("||")(literal_column("' '")).op("||")(Normativa.texto)
    )


def _vector_fragmento() -> Any:
    return func.to_tsvector(
        _ES,
        func.coalesce(NormativaFragmento.articulo, literal_column("''"))
        .op("||")(literal_column("' '"))
        .op("||")(NormativaFragmento.texto),
    )


@dataclass
class ResultadoBusqueda:
    normativa: Normativa
    relevancia: float
    extracto: str | None


async def buscar(
    db: AsyncSession,
    consulta: str | None = None,
    tipo: str | None = None,
    limite: int = 100,
) -> list[ResultadoBusqueda]:
    q = select(Normativa).where(Normativa.activa.is_(True))
    if tipo:
        q = q.where(Normativa.tipo == tipo)
    ts = consulta_ts(consulta or "")
    if not ts:
        filas = (await db.execute(q.order_by(Normativa.titulo).limit(limite))).scalars().all()
        return [ResultadoBusqueda(n, 0.0, None) for n in filas]
    vector = _vector_normativa()
    query = func.to_tsquery(_ES, ts)
    rango = func.ts_rank_cd(vector, query)
    extracto = func.ts_headline(
        _ES,
        Normativa.texto,
        query,
        "MaxFragments=2, MaxWords=30, MinWords=12, StartSel=«, StopSel=»",
    )
    filas2 = (
        await db.execute(
            select(Normativa, rango.label("r"), extracto.label("e"))
            .where(Normativa.activa.is_(True), vector.op("@@")(query))
            .where(*([Normativa.tipo == tipo] if tipo else []))
            .order_by(rango.desc())
            .limit(limite)
        )
    ).all()
    return [ResultadoBusqueda(n, float(r or 0), e) for n, r, e in filas2]


@dataclass
class Pasaje:
    normativa_id: UUID
    titulo: str
    articulo: str | None
    texto: str
    relevancia: float


async def buscar_fragmentos(db: AsyncSession, consulta: str, limite: int = 4) -> list[Pasaje]:
    """Pasajes más relevantes para una pregunta (para el asistente)."""
    ts = consulta_ts(consulta)
    if not ts:
        return []
    vector = _vector_fragmento()
    query = func.to_tsquery(_ES, ts)
    rango = func.ts_rank_cd(vector, query, 32)  # 32: normaliza por longitud
    filas = (
        await db.execute(
            select(
                NormativaFragmento.normativa_id,
                Normativa.titulo,
                NormativaFragmento.articulo,
                NormativaFragmento.texto,
                rango.label("r"),
            )
            .join(Normativa, Normativa.id == NormativaFragmento.normativa_id)
            .where(Normativa.activa.is_(True), vector.op("@@")(query))
            .order_by(rango.desc())
            .limit(limite)
        )
    ).all()
    return [Pasaje(i, t, a, x, float(r or 0)) for i, t, a, x, r in filas]


def url_pdf(normativa_id: UUID | str) -> str:
    """Enlace público al PDF (absoluto si está configurado DOMINIO)."""
    dominio = (get_settings().dominio or "").strip().strip("/")
    base = f"https://{dominio}" if dominio and dominio.upper() != "CAMBIAR" else ""
    return f"{base}/api/v1/normativa/{normativa_id}/pdf"


def contexto_asistente(pasajes: list[Pasaje], max_chars: int = 900) -> str:
    """Texto de los pasajes para el contexto del modelo, con su cita."""
    lineas = []
    for p in pasajes:
        cita = p.titulo + (f", {p.articulo}" if p.articulo else "")
        texto = (
            p.texto if len(p.texto) <= max_chars else p.texto[:max_chars].rsplit(" ", 1)[0] + "…"
        )
        lineas.append(f"- [{cita}] (texto completo: {url_pdf(p.normativa_id)})\n  {texto}")
    return "\n".join(lineas)


def fuentes(pasajes: list[Pasaje]) -> list[Any]:
    """Fuentes de la respuesta del asistente (una por ordenanza citada)."""
    from nijar_dti.schemas.chatbot import FuenteRespuesta

    vistas: dict[UUID, Any] = {}
    for p in pasajes:
        if p.normativa_id not in vistas:
            vistas[p.normativa_id] = FuenteRespuesta(
                tipo="normativa",
                referencia=url_pdf(p.normativa_id),
                descripcion=p.titulo + (f" · {p.articulo}" if p.articulo else ""),
            )
    return list(vistas.values())[:3]


RELEVANCIA_MINIMA = 0.05  # por debajo, el pasaje comparte palabras sueltas, no el tema

_INTRO = {
    "es": "Según la normativa municipal, «{t}»{a}:",
    "en": "According to the municipal regulations, «{t}»{a}:",
    "de": "Laut der Gemeindeverordnung «{t}»{a}:",
    "fr": "Selon la réglementation municipale, «{t}»{a} :",
}
_CIERRE = {
    "es": "Texto oficial completo: {u}",
    "en": "Full official text (in Spanish): {u}",
    "de": "Vollständiger amtlicher Text (auf Spanisch): {u}",
    "fr": "Texte officiel complet (en espagnol) : {u}",
}


def respuesta_basica(pasajes: list[Pasaje], idioma: str) -> tuple[str, list[Any]] | None:
    """Respuesta del motor sin IA: el artículo más relevante resumido y el enlace al PDF."""
    if not pasajes or pasajes[0].relevancia < RELEVANCIA_MINIMA:
        return None
    p = pasajes[0]
    cuerpo = re.sub(r"\s+", " ", p.texto).strip()
    # quita la cabecera «Artículo 12. Prohibiciones en playas» (ya va en la cita)
    cuerpo = re.sub(r"(?i)^(art[íi]culo|art\.)\s+\S+\s*[.:\-–—]?\s*", "", cuerpo)
    if p.articulo and ". " in p.articulo:
        titulo_art = p.articulo.split(". ", 1)[1]
        if cuerpo.lower().startswith(titulo_art.lower()):
            cuerpo = cuerpo[len(titulo_art) :].lstrip(" .:-–—")
    if len(cuerpo) > 420:
        corte = cuerpo.rfind(". ", 0, 420)
        cuerpo = cuerpo[: corte + 1] if corte > 150 else cuerpo[:420].rsplit(" ", 1)[0] + "…"
    articulo = ""
    if p.articulo:
        numero, _, titulo_art = p.articulo.partition(". ")
        articulo = f", {numero.lower()}" + (f" ({titulo_art})" if titulo_art else "")
    intro = _INTRO.get(idioma, _INTRO["es"]).format(t=p.titulo, a=articulo)
    cierre = _CIERRE.get(idioma, _CIERRE["es"]).format(u=url_pdf(p.normativa_id))
    return f"{intro} {cuerpo}\n\n{cierre}", fuentes(pasajes[:1])
