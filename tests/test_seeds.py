"""Tests de los datos seed: cobertura, formato y consistencia."""

from __future__ import annotations

from nijar_dti.data.seeds.campanas import CAMPANAS_SEED, generar_campanas_seed
from nijar_dti.data.seeds.cliente import CLIENTE_SEED
from nijar_dti.data.seeds.demo_data import (
    generar_contenidos_seed,
    generar_visitas_web_app_seed,
)
from nijar_dti.data.seeds.faqs import FAQS_SEED
from nijar_dti.data.seeds.recursos_turisticos import RECURSOS_SEED
from nijar_dti.data.seeds.sensores import SENSORES_SEED


class TestRecursosSeed:
    def test_minimo_recursos(self):
        # Compromiso mínimo: cubrir las playas y POIs principales
        assert len(RECURSOS_SEED) >= 12

    def test_urns_unicos(self):
        urns = [r["urn"] for r in RECURSOS_SEED]
        assert len(urns) == len(set(urns))

    def test_categorias_validas(self):
        validas = {
            "playa",
            "monumento",
            "ruta",
            "mirador",
            "centro_visitantes",
            "parque_natural",
            "museo",
            "yacimiento",
            "punto_interes",
            "oficina_turismo",
        }
        for r in RECURSOS_SEED:
            assert r["categoria"] in validas, f"Categoría inválida en {r['urn']}"

    def test_coordenadas_dentro_nijar(self):
        # Bounding box aproximado de Níjar y su parque natural
        for r in RECURSOS_SEED:
            assert 36.5 <= r["lat"] <= 37.1, f"Lat fuera de rango: {r['urn']}"
            assert -2.4 <= r["lon"] <= -1.8, f"Lon fuera de rango: {r['urn']}"

    def test_recursos_costeros_no_caen_al_mar(self):
        """Regresión: La Isleta y La Amatista estaban georreferenciados en el agua."""
        esperados = {
            "urn:ngsi-ld:RecursoTuristico:nijar:la-isleta-del-moro": (36.8129, -2.0430),
            "urn:ngsi-ld:RecursoTuristico:nijar:mirador-amatista": (36.8360, -2.0113),
        }
        por_urn = {r["urn"]: r for r in RECURSOS_SEED}
        for urn, (lat, lon) in esperados.items():
            if urn not in por_urn:  # el URN exacto puede variar: localizar por nombre
                continue
            r = por_urn[urn]
            assert abs(r["lat"] - lat) < 0.001 and abs(r["lon"] - lon) < 0.001, urn
        # En cualquier caso, ningún recurso puede quedar al este de la costa
        # en la franja Las Negras–Agua Amarga (lon > -2.0 solo es tierra si lat > 36.90)
        for r in RECURSOS_SEED:
            if r["lon"] > -2.0:
                assert r["lat"] > 36.90, f"{r['urn']} parece estar en el mar"

    def test_urns_estandar_fiware(self):
        for r in RECURSOS_SEED:
            assert r["urn"].startswith("urn:ngsi-ld:RecursoTuristico:nijar:")


class TestSensoresSeed:
    def test_minimo_sensores_smart_office(self):
        # Compromiso A.2: sensores ambientales (CO2, temp, hum, ruido)
        tipos_smart_office = {
            "ambiental_co2",
            "ambiental_temperatura",
            "ambiental_humedad",
            "ambiental_ruido",
        }
        encontrados = {s["tipo"] for s in SENSORES_SEED if "smartoffice" in s["urn"]}
        assert tipos_smart_office.issubset(encontrados)

    def test_sensores_totems(self):
        # Compromiso A.1: 2 tótems con sensores asociados
        urns_totems = [s["urn"] for s in SENSORES_SEED if "totem" in s["urn"]]
        # Cada tótem (rodalquilar y albaricoques) tiene al menos 2 sensores (meteo + aforo)
        rodalquilar = [u for u in urns_totems if "rodalquilar" in u]
        albaricoques = [u for u in urns_totems if "albaricoques" in u]
        assert len(rodalquilar) >= 2
        assert len(albaricoques) >= 2

    def test_urns_unicos(self):
        urns = [s["urn"] for s in SENSORES_SEED]
        assert len(urns) == len(set(urns))


class TestFAQsSeed:
    def test_categorias_minimas_cubiertas(self):
        categorias_obligatorias = {"playas", "parque", "rutas", "servicios", "emergencias"}
        encontradas = {f["categoria"] for f in FAQS_SEED}
        assert categorias_obligatorias.issubset(encontradas)

    def test_intents_unicos(self):
        intents = [f["intent"] for f in FAQS_SEED]
        assert len(intents) == len(set(intents))

    def test_todas_tienen_respuesta_es(self):
        for f in FAQS_SEED:
            assert f.get("respuesta_es"), f"FAQ {f['intent']} sin respuesta_es"
            assert f.get("pregunta_es"), f"FAQ {f['intent']} sin pregunta_es"

    def test_cobertura_ingles(self):
        """Compromiso: cobertura mínima del 80% en inglés en la base inicial."""
        con_ingles = sum(1 for f in FAQS_SEED if f.get("respuesta_en"))
        ratio = con_ingles / len(FAQS_SEED)
        assert ratio >= 0.8, f"Cobertura EN insuficiente: {ratio:.0%}"

    def test_niveles_confianza_validos(self):
        validos = {"alta", "media", "fuera_de_dominio"}
        for f in FAQS_SEED:
            nivel = f.get("nivel_confianza", "alta")
            assert nivel in validos, f"Nivel de confianza inválido en {f['intent']}: {nivel}"

    def test_emergencias_son_alta_confianza(self):
        """Las FAQs de emergencias deben siempre estar marcadas como alta confianza."""
        for f in FAQS_SEED:
            if f["categoria"] == "emergencias":
                assert f.get("nivel_confianza", "alta") == "alta", (
                    f"FAQ de emergencia {f['intent']} no es de alta confianza"
                )


class TestClienteSeed:
    """Ficha general del cliente / Ayuntamiento (bloque 1 del pliego)."""

    def test_campos_identificacion(self):
        assert CLIENTE_SEED["nombre"]
        assert CLIENTE_SEED["proyecto"]
        assert CLIENTE_SEED["responsable_municipal"].get("email")

    def test_idiomas_pliego(self):
        # El pliego exige ES/EN/FR/DE activos
        assert set(CLIENTE_SEED["idiomas_activos"]) >= {"es", "en", "fr", "de"}

    def test_canales_oficiales(self):
        canales = CLIENTE_SEED["canales_oficiales"]
        for clave in ("web", "app", "facebook", "instagram"):
            assert canales.get(clave), f"Falta canal oficial: {clave}"

    def test_responsables_tecnicos(self):
        areas = {r["area"] for r in CLIENTE_SEED["responsables_tecnicos"]}
        # TI, turismo, comunicación y mantenimiento (bloque 1)
        assert len(areas) >= 4


class TestCampanasSeed:
    """Campañas de promoción turística (bloque 9 del pliego)."""

    def test_minimo_campanas(self):
        assert len(CAMPANAS_SEED) >= 3

    def test_slugs_unicos(self):
        slugs = [c["slug"] for c in CAMPANAS_SEED]
        assert len(slugs) == len(set(slugs))

    def test_estados_validos(self):
        validos = {"planificada", "activa", "finalizada", "cancelada"}
        for c in CAMPANAS_SEED:
            assert c["estado"] in validos, f"Estado inválido en {c['slug']}"

    def test_cubre_pasada_activa_planificada(self):
        estados = {c["estado"] for c in CAMPANAS_SEED}
        # La demo debe tener al menos una finalizada (con resultados) y una activa
        assert "finalizada" in estados
        assert "activa" in estados

    def test_finalizadas_tienen_resultados(self):
        for c in CAMPANAS_SEED:
            if c["estado"] == "finalizada":
                assert c.get("resultados"), f"Campaña finalizada sin resultados: {c['slug']}"

    def test_generar_produce_fechas_coherentes(self):
        for c in generar_campanas_seed():
            assert c["fecha_inicio"] < c["fecha_fin"]


class TestDemoAnaliticaSeed:
    """Analítica web/app + movilidad y contenidos del CMS."""

    def test_visitas_cubre_web_app_wifi_ble(self):
        tipos = {v["tipo"] for v in generar_visitas_web_app_seed(["rid-1", "rid-2"])}
        assert {"web_vista", "app_vista", "wifi_conexion", "proximidad_ble"} <= tipos

    def test_visitas_web_tienen_dispositivo_y_origen(self):
        visitas = generar_visitas_web_app_seed([])
        web = [v for v in visitas if v["tipo"] == "web_vista"]
        assert web
        for v in web:
            attrs = v["atributos"]
            assert "dispositivo" in attrs
            assert "pais" in attrs
            assert "rebote" in attrs

    def test_contenidos_cubren_ciclo_editorial(self):
        estados = {c["estado"] for c in generar_contenidos_seed([])}
        # El flujo editorial completo alimenta el KPI de tiempo de publicación
        assert {"borrador", "pendiente_aprobacion", "aprobado", "publicado", "archivado"} <= estados

    def test_publicados_tienen_fechas_para_kpi(self):
        for c in generar_contenidos_seed([]):
            if c["estado"] == "publicado":
                assert c["fecha_aprobacion"] is not None
                assert c["fecha_publicacion"] is not None
                assert c["fecha_publicacion"] >= c["fecha_aprobacion"]
