"""Prueba de humo del panel DTI: login + secciones clave con API simulada.

Uso:  python scripts/smoke/smoke_panel.py
Requiere Playwright con Chromium (CHROMIUM_PATH apunta al ejecutable si no
está en la instalación por defecto de Playwright).
"""

import functools
import http.server
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(__file__))
from api_stub import Handler  # noqa: E402

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dashboard")
PORT = 8765
CHROMIUM = os.environ.get("CHROMIUM_PATH", "/opt/pw-browsers/chromium")


def main():
    handler = functools.partial(Handler, directory=os.path.abspath(RAIZ))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    from playwright.sync_api import sync_playwright

    errores = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROMIUM)
        page = b.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda e: errores.append("pageerror: %s" % e))
        page.on("console", lambda m: errores.append("console.error: %s" % m.text) if m.type == "error" else None)

        page.goto(f"http://127.0.0.1:{PORT}/index.html")
        page.wait_for_timeout(1400)
        page.fill("#lg-email", "admin@nijar.es")
        page.fill("#lg-pwd", "x")
        page.click("#lg-btn")
        page.wait_for_timeout(1800)

        sidebar = page.inner_text("#dsidebar")
        assert "Gemelo vivo" in sidebar, "sidebar sin el grupo Gemelo digital"
        assert "Documentos del territorio" in sidebar, "sidebar sin la vista de documentos"
        print("OK login y sidebar completo")

        # Catálogo con datos reales del stub
        page.evaluate("UI.goD('g-catalogo')")
        page.wait_for_timeout(700)
        assert "Playa de Mónsul" in page.inner_text("#dv-g-catalogo")
        print("OK catálogo de recursos")

        # CMS de contenidos: CRUD real
        page.evaluate("UI.goD('contenidos')")
        page.wait_for_timeout(700)
        cms_txt = page.inner_text("#dv-contenidos")
        assert "Aviso de calor" in cms_txt and "Nuevo aviso" in cms_txt, "CRUD del CMS no renderiza"
        assert "totem, web" in cms_txt, "canales del contenido no visibles"
        print("OK CMS de contenidos con CRUD real")

        # Publicidad: CRUD de empresas anunciantes
        page.evaluate("UI.goD('g-publicidad')")
        page.wait_for_timeout(700)
        pub_txt = page.inner_text("#dv-g-publicidad")
        assert "Restaurante La Ola" in pub_txt, "listado de empresas vacío"
        assert "destacada" in pub_txt and "Alta de empresa" in pub_txt, "CRUD de publicidad incompleto"
        assert "412 · 37" in pub_txt, "métricas de impresiones/toques ausentes: %r" % pub_txt[:300]
        print("OK publicidad · empresas con métricas de visibilidad")

        # Gemelo 2D: todas las capas + aforo ThingsBoard
        page.evaluate("UI.goD('gd-mapa')")
        page.wait_for_timeout(1100)
        gk = page.inner_text("#gd-kpis")
        # turismo(1)+sensor(1)+cuadros(2)+contenedores(684)+movilidad(1)+camara(1)+banderas(2)+aire(2)=694
        assert "694" in gk, "KPIs del gemelo sin todas las capas: %r" % gk[:200]
        assert "86" in gk and "cabo de gata" in gk.lower(), "KPI de aforo del parque ausente"
        print("OK gemelo 2D con el parque completo + aforo en vivo")

        page.evaluate("UI.goD('gd-3d')")
        page.wait_for_timeout(700)
        assert "Vista 3D del territorio" in page.inner_text("#dv-gd-3d")
        print("OK vista 3D del territorio")

        # Simulador: SOLO los 5 eventos reales del municipio
        page.evaluate("UI.goD('gd-sim')")
        page.wait_for_timeout(900)
        sim = page.inner_text("#dv-gd-sim")
        assert "Simulador de escenarios" in sim and "Desembarco Pirata" in sim, "simulador no renderiza"
        nombres = page.inner_text("#sim-esc")
        for ev in ("Desembarco Pirata", "Noche de las Velas", "Festival Chío", "ExpoLevante", "Níjar Cup"):
            assert ev in nombres, "falta el evento %r" % ev
        assert page.eval_on_selector("#sim-esc", "e => e.options.length") == 5, "debe haber SOLO 5 escenarios"
        page.select_option("#sim-esc", "3")  # ExpoLevante
        page.wait_for_timeout(300)
        sup = page.inner_text("#sim-supuesto")
        assert "40.000" in sup and "2 años" in sup, "supuestos de ExpoLevante ausentes: %r" % sup[:250]
        page.click("#sim-run")
        page.wait_for_timeout(500)
        kpis_sim = page.inner_text("#sim-kpis")
        assert "Variación" in kpis_sim and "%" in kpis_sim, "simulación sin impacto"
        assert page.query_selector("#sim-chart svg"), "gráfica base vs escenario ausente"
        print("OK simulador con los 5 eventos reales del municipio")

        # Documentos del territorio: listado + formulario
        page.evaluate("UI.goD('gd-docs')")
        page.wait_for_timeout(1000)
        docs_txt = page.inner_text("#dv-gd-docs")
        assert "Documentos del territorio" in docs_txt, "vista de documentos no renderiza"
        assert "ficha-tecnica-monsul.pdf" in docs_txt and "Playa de Mónsul" in docs_txt, "listado sin documentos"
        assert "Adjuntar documento" in docs_txt and page.query_selector("#doc-file"), "formulario de subida ausente"
        assert "471 KB" in docs_txt, "tamaño legible ausente"
        print("OK documentos del territorio (listado + subida)")

        # Vista de Gobierno: portada "tipo web" (héroe + tiles + esta semana)
        page.evaluate("UI.enterDireccion()")
        page.wait_for_timeout(1300)
        dir_txt = page.inner_text("#dir-resumen").lower()
        assert "ayuntamiento de níjar" in dir_txt, "héroe de portada ausente"
        assert "en seguimiento" in dir_txt, "frase de estado en lenguaje llano ausente"
        assert "36°" in dir_txt and "86" in dir_txt, "datos vivos (aire Bettair / aforo) ausentes"
        n_tiles = page.eval_on_selector_all("#dir-resumen .dir-tile", "els => els.length")
        assert n_tiles == 7, "deben salir 7 tiles de servicio, hay %s" % n_tiles
        assert "esta semana en níjar" in dir_txt, "bloque de la semana ausente"
        assert "festival noches del castillo" in dir_txt, "agenda sin eventos"
        assert "aviso de calor" in dir_txt, "aviso vigente del tótem ausente"
        assert "aporta al municipio" in dir_txt, "tarjetas de impacto ausentes"
        print("OK vista de gobierno · portada tipo tótem")

        # Un tile abre el detalle ejecutivo de su vertical
        page.click('#dir-resumen .dir-tile:has-text("Residuos")')
        page.wait_for_timeout(900)
        v_txt = page.inner_text("#dir-residuos").lower()
        assert "llenado medio" in v_txt and "23" in v_txt, "detalle de residuos no renderiza"
        assert page.query_selector("#dir-residuos .dir-vhero"), "cabecera fotográfica de la vertical ausente"
        print("OK vista de gobierno · tile → detalle de la vertical")

        b.close()

    graves = [e for e in errores if "Failed to load resource" not in e and "favicon" not in e]
    if graves:
        print("ERRORES JS:")
        for e in graves:
            print(" -", e)
        sys.exit(1)
    print("SMOKE PANEL OK — sin errores JS")


if __name__ == "__main__":
    main()
