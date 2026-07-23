"""Prueba de humo del tótem: home, listados, agenda, chat, meteo y avisos CMS.

Uso:  python scripts/smoke/smoke_totem.py
"""

import functools
import http.server
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(__file__))
from api_stub import Handler  # noqa: E402

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
PORT = 8770
CHROMIUM = os.environ.get("CHROMIUM_PATH", "/opt/pw-browsers/chromium")


def main():
    handler = functools.partial(Handler, directory=os.path.abspath(RAIZ))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    from playwright.sync_api import sync_playwright

    errores = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROMIUM)
        page = b.new_page(viewport={"width": 900, "height": 1600})
        page.on("pageerror", lambda e: errores.append("pageerror: %s" % e))
        page.on("console", lambda m: errores.append("console.error: %s" % m.text) if m.type == "error" else None)

        page.goto(f"http://127.0.0.1:{PORT}/totem/index.html")
        page.wait_for_timeout(2200)

        # Escudo cargado y home rediseñada (6 tiles; la agenda vive en el dock)
        ok_logo = page.evaluate(
            "() => { const i = document.querySelector('.tt-ayuntopill img'); return !!i && i.complete && i.offsetWidth > 0 }"
        )
        assert ok_logo, "escudo del ayuntamiento no cargado"
        assert "BIENVENIDO" in page.inner_text(".tt-hhero").upper()
        assert len(page.query_selector_all(".tt-ptile")) == 6, "esperaba 6 tiles"
        print("OK home rediseñada")

        # Playas → listado y ficha
        page.click('.tt-ptile[data-cat="playas"]')
        page.wait_for_timeout(900)
        assert "Playa de Mónsul" in page.inner_text("#content-grid"), "listado sin datos"
        page.click(".tt-lb")
        page.wait_for_timeout(500)
        assert page.evaluate("() => document.getElementById('poi-dialog').open"), "ficha no abierta"
        assert "Playa de Mónsul" in page.inner_text("#poi-dialog")
        page.click("#poi-close")
        print("OK listado de playas y ficha")

        # Agenda por días (desde el dock)
        page.click(".tt-view.is-on [data-back]")
        page.wait_for_timeout(300)
        page.click('[data-dock-action="agenda"]')
        page.wait_for_timeout(800)
        assert "Festival Noches del Castillo" in page.inner_text("#content-grid"), "agenda sin eventos"
        print("OK agenda de eventos")

        # Asistente IA
        page.click(".tt-view.is-on [data-back]")
        page.wait_for_timeout(300)
        page.click("#btn-open-chat")
        page.wait_for_timeout(400)
        page.fill("#chatbot-input", "¿Qué playas hay?")
        page.click(".tt-chat-send")
        page.wait_for_timeout(1000)
        assert "playas" in page.inner_text("#chat-log").lower(), "chat sin respuesta"
        print("OK asistente IA")

        # Apartado Empresas (publicidad) desde el dock
        page.click(".tt-view.is-on [data-back]")
        page.wait_for_timeout(300)
        page.click('[data-dock-action="empresas"]')
        page.wait_for_timeout(900)
        emp = page.inner_text("#content-grid")
        assert "Restaurante La Ola" in emp and "Kayak Cabo Activo" in emp, "empresas no renderizan"
        assert "empresas colaboradoras" in emp.lower(), "falta el aviso de espacio patrocinado"
        assert "destacada" in emp.lower(), "distintivo de destacada ausente"
        chips_emp = page.inner_text("#list-chips")
        assert "Gastronomía" in chips_emp, "chips de sector ausentes"
        page.click(".tt-emp")  # toque sobre una tarjeta: registra métrica sin romper nada
        page.wait_for_timeout(300)
        print("OK apartado Empresas (publicidad) en el tótem")

        # Chip meteo (Bettair) + ticker de avisos del CMS
        page.click(".tt-view.is-on [data-back]")
        page.wait_for_timeout(400)
        chip = page.inner_text("#header-weather")
        assert "36°" in chip and "buena" in chip.lower(), "chip meteo incorrecto: %r" % chip
        ticker = page.inner_text("#avisos-track")
        assert "Aviso de calor: playas" in ticker, "ticker sin el aviso del CMS"
        assert "Escuela de Verano" not in ticker, "el ticker sigue usando los avisos demo"
        print("OK chip meteo y ticker del CMS")

        # Cambio de idioma (chip y ticker traducidos)
        page.click('.tt-hdock .lang-btn[data-lang="en"]')
        page.wait_for_timeout(600)
        assert "good" in page.inner_text("#header-weather").lower(), "chip no traducido"
        assert "Heat warning" in page.inner_text("#avisos-track"), "aviso del CMS no traducido"
        page.click('.tt-hdock .lang-btn[data-lang="es"]')
        print("OK cambio de idioma")

        b.close()

    graves = [e for e in errores if "Failed to load resource" not in e and "favicon" not in e]
    if graves:
        print("ERRORES JS:")
        for e in graves:
            print(" -", e)
        sys.exit(1)
    print("SMOKE TOTEM OK — sin errores JS")


if __name__ == "__main__":
    main()
