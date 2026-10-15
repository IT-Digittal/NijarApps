"""Tests de los contenidos abiertos del tótem (OSM + Wikipedia/Commons), sin red."""

from __future__ import annotations

import httpx

from nijar_dti.connectors import contenidos_abiertos as ca
from nijar_dti.data.seeds.contenidos_totem import CONTENIDOS_TOTEM_SEED
from nijar_dti.schemas.tourism import RecursoTuristicoBase, ServicioBase

OVERPASS = {
    "elements": [
        {
            "type": "node",
            "id": 1,
            "lat": 36.76,
            "lon": -2.10,
            "tags": {
                "amenity": "restaurant",
                "name": "Casa Prueba",
                "cuisine": "seafood;tapas",
                "website": "www.ejemplo.es",
                "email": "roto@",
                "addr:postcode": "04118",
                "addr:street": "Calle Correo",
                "addr:housenumber": "3",
                "addr:place": "San José",
            },
        },
        {"type": "way", "id": 2, "center": {"lat": 36.96, "lon": -2.2},
         "tags": {"craft": "pottery", "name": "Alfarería X", "website": "no es url"}},
        {"type": "node", "id": 3, "lat": 36.96, "lon": -2.2,
         "tags": {"shop": "craft", "name": "Jarapas Y"}},
        {"type": "node", "id": 4, "lat": 36.9, "lon": -2.1, "tags": {"amenity": "cafe"}},
    ]
}  # fmt: skip


def test_overpass_normaliza_y_sanea():
    els = ca.parsear_overpass(OVERPASS)
    assert len(els) == 3  # el café sin nombre se descarta
    rest, alfar, jarapas = els
    assert rest.clase == "servicio" and rest.tipo == "gastronomia_restaurante"
    assert rest.etiquetas == ["gastronomia", "pescados y mariscos", "tapas"]
    assert rest.web == "https://www.ejemplo.es" and rest.email is None
    assert rest.direccion == "Calle Correo 3, San José" and rest.codigo_postal == "04118"
    assert rest.slug == "osm-node-1"
    assert alfar.clase == "recurso" and "ceramica" in alfar.etiquetas and alfar.web is None
    assert alfar.lat == 36.96 and alfar.slug == "osm-way-2"
    assert "jarapas" in jarapas.etiquetas


def test_elementos_osm_validan_contra_el_esquema():
    for e in ca.parsear_overpass(OVERPASS):
        datos = {"nombre": e.nombre, "web": e.web, "email": e.email,
                 "codigo_postal": e.codigo_postal, "etiquetas": e.etiquetas}  # fmt: skip
        if e.clase == "servicio":
            ServicioBase(urn="urn:ngsi-ld:Servicio:nijar:" + e.slug, tipo=e.tipo, **datos)
        else:
            RecursoTuristicoBase(
                urn="urn:ngsi-ld:RecursoTuristico:nijar:" + e.slug, categoria="punto_interes",
                **datos,
            )  # fmt: skip


def test_seed_contenidos_totem_valido():
    urns = [r["urn"] for r in CONTENIDOS_TOTEM_SEED]
    assert len(urns) == len(set(urns))
    for r in CONTENIDOS_TOTEM_SEED:
        RecursoTuristicoBase(**{k: v for k, v in r.items() if k not in ("lat", "lon")})
        assert set(r["nombre_i18n"]) == set(r["descripcion_i18n"]) == {"es", "en", "de", "fr"}
        assert 36.6 < r["lat"] < 37.1 and -2.4 < r["lon"] < -1.9  # dentro de Níjar
    cabo = [r for r in CONTENIDOS_TOTEM_SEED if r["categoria"] == "parque_natural"]
    assert len(cabo) >= 8
    assert any("jarapas" in r["etiquetas"] for r in CONTENIDOS_TOTEM_SEED)


def _wikimedia(con_articulo: bool):
    def manejador(req: httpx.Request) -> httpx.Response:
        p = req.url.params
        if req.url.host == "es.wikipedia.org":
            paginas = {"1": {"index": 1, "title": "Castillo de San Felipe (Almería)",
                             "pageimage": "Castillo.jpg",
                             "coordinates": [{"lat": 36.80, "lon": -2.06}]}}  # fmt: skip
            return httpx.Response(200, json={"query": {"pages": paginas if con_articulo else {}}})
        if p.get("list") == "geosearch":
            geo = [{"title": "File:Mini.jpg"}, {"title": "File:Buena.jpg"}]
            return httpx.Response(200, json={"query": {"geosearch": geo}})
        paginas = {}
        for i, t in enumerate(p["titles"].split("|")):
            info = {"mime": "image/jpeg", "width": 300 if "Mini" in t else 4000,
                    "thumburl": f"https://upload.wikimedia.org/{t}",
                    "descriptionurl": f"https://commons.wikimedia.org/wiki/{t}",
                    "extmetadata": {"Artist": {"value": "<a href='u'>Ana</a>"},
                                    "LicenseShortName": {"value": "CC BY 4.0"}}}  # fmt: skip
            paginas[str(i)] = {"title": t, "imageinfo": [info]}
        return httpx.Response(200, json={"query": {"pages": paginas}})

    return httpx.AsyncClient(transport=httpx.MockTransport(manejador))


async def test_imagen_de_wikipedia_con_credito():
    async with _wikimedia(con_articulo=True) as cli:
        img = await ca.buscar_imagen(cli, "Castillo de San Felipe (Los Escullos)", 36.8017, -2.0651)
    assert img is not None and img.origen == "wikipedia"
    assert img.url.endswith("File:Castillo.jpg")
    assert img.credito == "Ana · CC BY 4.0 · Wikimedia Commons"


async def test_sin_articulo_usa_la_foto_cercana_suficientemente_grande():
    async with _wikimedia(con_articulo=False) as cli:
        img = await ca.buscar_imagen(cli, "Duna fósil de Los Escullos", 36.80, -2.064)
    assert img is not None and img.origen == "commons-geo"
    assert img.url.endswith("File:Buena.jpg")  # la primera (300 px) se descarta


async def test_articulo_lejano_se_descarta():
    async with _wikimedia(con_articulo=True) as cli:
        img = await ca.imagen_wikipedia(cli, "Torre de Vela Blanca", 36.0, -3.0)
    assert img is None
