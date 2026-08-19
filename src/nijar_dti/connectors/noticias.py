"""Cliente de solo lectura de las noticias del Ayuntamiento de Níjar (Strapi).

La web municipal migró sus noticias de WordPress a **Strapi**, que expone un
**JSON público sin autenticación** pensado para reutilización por terceros
(``https://api.nijaraldia.es/api/articles``). Este conector consume ese API y
normaliza los artículos al esquema de la plataforma, que los surte al tótem, al
panel y al chatbot.

Notas de la API (Strapi 5):

- Filtro por proyecto obligatorio:
  ``filters[projects][documentId][$eq]=<PROJECT_ID>``.
- ``populate`` debe indicarse con índices (``populate[0]=cover&populate[1]=...``);
  Strapi 5 rechaza ``populate=cover,categories``.
- Las URLs de imágenes (``cover.url``) son **relativas**; se convierten a
  absolutas con la base del API.

Es de solo lectura y no requiere credenciales; nunca escribe en el origen.
"""

from __future__ import annotations

from typing import Any

import httpx


class NoticiasError(RuntimeError):
    """Error de comunicación con el API de noticias (Strapi)."""


class ClienteNoticiasStrapi:
    """Cliente REST mínimo del API de noticias en Strapi (solo lectura)."""

    def __init__(
        self,
        base_url: str,
        project_id: str,
        timeout_seconds: int = 12,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._project_id = project_id
        self._timeout = timeout_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self._base and self._project_id)

    async def _get(self, ruta: str, params: list[tuple[str, Any]]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.get(f"{self._base}{ruta}", params=params)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise NoticiasError(f"Error al consultar el API de noticias: {exc}") from exc
        try:
            return resp.json()
        except ValueError as exc:
            raise NoticiasError("El API de noticias no devolvió JSON válido") from exc

    def _params_base(self) -> list[tuple[str, Any]]:
        return [("filters[projects][documentId][$eq]", self._project_id)]

    async def listar(
        self,
        *,
        page: int = 1,
        page_size: int = 12,
        categoria_document_id: str | None = None,
        buscar: str | None = None,
        con_contenido: bool = False,
    ) -> dict[str, Any]:
        """Lista artículos paginados (más recientes primero)."""
        params = self._params_base()
        params += [
            ("pagination[page]", page),
            ("pagination[pageSize]", page_size),
            ("sort[0]", "publishedAt:desc"),
            ("populate[0]", "cover"),
            ("populate[1]", "categories"),
        ]
        if categoria_document_id:
            params.append(("filters[categories][documentId][$eq]", categoria_document_id))
        if buscar:
            params.append(("filters[title][$contains]", buscar))

        data = await self._get("/api/articles", params)
        items = [self._parsear(a, con_contenido) for a in (data.get("data") or [])]
        meta = (data.get("meta") or {}).get("pagination", {})
        return {
            "items": items,
            "page": int(meta.get("page", page)),
            "page_size": int(meta.get("pageSize", page_size)),
            "page_count": int(meta.get("pageCount", 0)),
            "total": int(meta.get("total", len(items))),
        }

    async def por_slug(self, slug: str) -> dict[str, Any] | None:
        """Devuelve un artículo por su slug (con el contenido completo)."""
        params = self._params_base()
        params += [
            ("filters[slug][$eq]", slug),
            ("populate[0]", "cover"),
            ("populate[1]", "categories"),
        ]
        data = await self._get("/api/articles", params)
        arts = data.get("data") or []
        if not arts:
            return None
        return self._parsear(arts[0], con_contenido=True)

    async def categorias(self) -> list[dict[str, str]]:
        """Lista las categorías disponibles (documentId, nombre, slug)."""
        data = await self._get("/api/categories", [])
        out: list[dict[str, str]] = []
        for c in data.get("data") or []:
            out.append({
                "document_id": str(c.get("documentId") or ""),
                "nombre": str(c.get("name") or c.get("title") or ""),
                "slug": str(c.get("slug") or ""),
            })
        return out

    # ---------------- parsing ----------------

    def _url_absoluta(self, url: str | None) -> str | None:
        if not url:
            return None
        if url.startswith("http://") or url.startswith("https://"):
            return url
        return f"{self._base}{url}"

    def _parsear(self, art: dict[str, Any], con_contenido: bool) -> dict[str, Any]:
        cover = art.get("cover") or {}
        formats = cover.get("formats") or {}
        # Preferimos un tamaño medio para tarjetas; caemos al original.
        img_rel = None
        for tam in ("medium", "large", "small", "thumbnail"):
            f = formats.get(tam)
            if isinstance(f, dict) and f.get("url"):
                img_rel = f["url"]
                break
        img_rel = img_rel or cover.get("url")

        categorias = [
            str(c.get("name") or "")
            for c in (art.get("categories") or [])
            if isinstance(c, dict) and c.get("name")
        ]
        return {
            "id": art.get("id"),
            "document_id": str(art.get("documentId") or ""),
            "titulo": str(art.get("title") or ""),
            "descripcion": art.get("description") or None,
            "slug": str(art.get("slug") or ""),
            "contenido": (art.get("content") or None) if con_contenido else None,
            "fecha": art.get("date") or None,
            "publicado_en": art.get("publishedAt") or None,
            "imagen_url": self._url_absoluta(img_rel),
            "categorias": categorias,
        }
