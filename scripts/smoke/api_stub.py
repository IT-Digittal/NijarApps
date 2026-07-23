"""Stub de la API para las pruebas de humo del panel y del tótem.

Sirve el frontend estático y responde a las rutas de la API con datos fijos
que replican los esquemas reales de la plataforma. Las rutas no listadas
devuelven 404 y el frontend aplica su degradación normal (demo u ocultar).
"""

import http.server
import json
import re

FAKE = {
    r"/api/v1/auth/login$": {"access_token": "tok", "refresh_token": "ref", "token_type": "bearer", "expires_in": 3600},
    r"/api/v1/auth/me$": {"id": "1", "email": "admin@nijar.es", "nombre_completo": "Admin", "rol": "administrador_tic", "scopes": [], "activo": True},

    # Documentos adjuntos a puntos (DocumentosPage)
    r"/api/v1/documentos": {"items": [
        {"id": "11111111-1111-1111-1111-111111111111", "entidad_tipo": "recurso",
         "entidad_id": "urn:ngsi-ld:RecursoTuristico:nijar:playa-monsul", "entidad_nombre": "Playa de Mónsul",
         "latitud": 36.7305, "longitud": -2.1442, "nombre_archivo": "ficha-tecnica-monsul.pdf",
         "descripcion": "Ficha técnica de la playa", "tipo_mime": "application/pdf",
         "tamano_bytes": 482133, "subido_por": "admin@nijar.es", "created_at": "2026-07-15T09:00:00"}], "total": 1},

    # Publicidad: empresas anunciantes (publico del totem + EmpresasPage del panel)
    r"/api/v1/publicidad/publico/totem": [
        {"id": "e1", "nombre": "Restaurante La Ola", "sector": "gastronomia",
         "descripcion": "Pescado fresco frente al puerto.",
         "descripcion_i18n": {"es": "Pescado fresco frente al puerto.", "en": "Fresh fish by the harbour.",
                              "de": "Frischer Fisch am Hafen.", "fr": "Poisson frais face au port."},
         "nucleo": "San José", "direccion": "Paseo Marítimo, 12", "telefono": "+34 950 000 001",
         "web": "https://ejemplo-laola.es", "imagenes": None, "destacado": True},
        {"id": "e2", "nombre": "Kayak Cabo Activo", "sector": "ocio_activo",
         "descripcion": "Rutas guiadas en kayak.", "descripcion_i18n": None,
         "nucleo": "Las Negras", "direccion": None, "telefono": "+34 950 000 003",
         "web": None, "imagenes": None, "destacado": False}],
    r"/api/v1/publicidad$": {"items": [
        {"id": "e1", "nombre": "Restaurante La Ola", "sector": "gastronomia",
         "descripcion": "Pescado fresco frente al puerto.", "descripcion_i18n": None,
         "nucleo": "San José", "direccion": "Paseo Marítimo, 12", "telefono": "+34 950 000 001",
         "web": "https://ejemplo-laola.es", "email": None, "imagenes": None,
         "latitud": 36.7609, "longitud": -2.1062, "destacado": True, "prioridad": 10,
         "publicado": True, "campana_desde": None, "campana_hasta": None,
         "created_at": "2026-07-20T09:00:00", "updated_at": "2026-07-20T09:00:00"}], "total": 1},

    # CMS: publico del totem + ContenidoOut real
    r"/api/v1/cms/publico/totem": [
        {"id": "c1", "titulo": "Aviso de calor: playas con alta ocupación",
         "titulo_i18n": {"es": "Aviso de calor: playas con alta ocupación", "en": "Heat warning: beaches at high occupancy",
                         "de": "Hitzewarnung", "fr": "Alerte chaleur"},
         "cuerpo": "Se recomienda hidratarse.", "cuerpo_i18n": None, "publicar_hasta": None}],
    r"/api/v1/cms/content": {"items": [
        {"id": "c1", "titulo": "Aviso de calor: playas con alta ocupación", "titulo_i18n": None,
         "cuerpo": "Se recomienda hidratarse.", "cuerpo_i18n": None, "canales": ["totem", "web"],
         "plantilla_id": None, "recurso_id": None, "publicar_desde": None, "publicar_hasta": None,
         "imagenes": None, "enlaces": None, "etiquetas": None, "estado": "publicado",
         "created_at": "2026-07-04T10:00:00", "updated_at": "2026-07-04T10:00:00"}], "total": 1},

    # Bettair (resumen publico + estaciones, esquemas de schemas/gemelo.py)
    r"/api/v1/gemelo/aire/resumen": {"fuente": "bettair", "obtenido_en": "2026-07-10T10:35:00Z",
        "medido_en": "2026-07-10T10:30:00Z", "estaciones_activas": 5, "temperatura_media_c": 36.4,
        "temperatura_max_c": 40.6, "humedad_media_pct": 37.7, "eaqi_peor": 1, "eaqi_peor_texto": "buena"},
    r"/api/v1/gemelo/aire/estaciones": {"fuente": "bettair", "obtenido_en": "2026-07-10T10:00:00Z", "total": 2,
        "estaciones": [
            {"id": "BET00260097", "latitud": 36.84688, "longitud": -2.040669, "estado": "active",
             "bateria_pct": 100, "ultima_conexion": "2026-07-10T09:40:20Z", "medido_en": "2026-07-10T09:35:00Z",
             "eaqi": 1, "eaqi_texto": "buena", "temperatura_c": 37.0, "humedad_pct": 26.2, "presion_hpa": 1002.9,
             "no2_ugm3": 16.3, "o3_ugm3": 66.7, "pm25_ugm3": 8, "pm10_ugm3": 33},
            {"id": "BET00260101", "latitud": 36.9424, "longitud": -1.93285, "estado": "active",
             "bateria_pct": 100, "ultima_conexion": "2026-07-10T09:40:20Z", "medido_en": "2026-07-10T09:35:00Z",
             "eaqi": 5, "eaqi_texto": "muy desfavorable", "temperatura_c": 32.8, "humedad_pct": 30.0,
             "presion_hpa": 1003.0, "no2_ugm3": 0.1, "o3_ugm3": 60.0, "pm25_ugm3": 11, "pm10_ugm3": 30}]},

    # ThingsBoard (banderas + aforo del parque)
    r"/api/v1/gemelo/playas/banderas": {"fuente": "thingsboard", "obtenido_en": "2026-07-09T18:00:00Z", "total": 2,
        "banderas": [{"nombre": "Playa de Mónsul", "estado": "verde", "latitud": 36.7305, "longitud": -2.1442},
                     {"nombre": "Playa Agua Amarga", "estado": "roja", "latitud": 36.9389, "longitud": -1.9347}]},
    r"/api/v1/gemelo/parque/aforo": {"fuente": "thingsboard", "obtenido_en": "2026-07-09T18:00:00Z",
        "medido_en": "2026-07-09T17:56:28Z", "aforo_actual": 86, "entradas_hoy": 1380, "salidas_hoy": 1294,
        "total_vehiculos": 2674, "total_motorizados": 2485, "total_no_motorizados": 80, "total_personas": 45},

    # Prediccion (esquemas PrediccionAfluencia / ValidacionModelo)
    r"/api/v1/prediccion/afluencia": {"metrica": "totem", "horizonte_dias": 14, "dias_historico": 90,
        "generado_en": "2026-07-05T00:00:00", "mape_validacion": 12.4, "cumple_umbral_mape": True,
        "puntos": [{"fecha": "2026-07-%02d" % (i + 6), "valor_estimado": 100 + i * 5,
                    "banda_inferior": 80 + i * 5, "banda_superior": 120 + i * 5} for i in range(14)]},
    r"/api/v1/prediccion/validacion": {"metrica": "totem", "mape": 12.4, "umbral": 20.0, "cumple_umbral": True,
        "n_test": 14, "n_evaluable": 12, "dias_holdout": 14},

    # Turismo (recursos, eventos y servicios con coordenadas)
    r"/api/v1/tourism/resources": {"items": [
        {"id": "r1", "urn": "urn:ngsi-ld:RecursoTuristico:nijar:playa-monsul", "nombre": "Playa de Mónsul",
         "categoria": "playa", "municipio": "Níjar", "publicado": True, "activo": True,
         "descripcion_corta": "Playa icónica", "nombre_i18n": {"es": "Playa de Mónsul", "en": "Monsul Beach"},
         "descripcion_i18n": None, "imagenes": None,
         "ubicacion": {"type": "Point", "coordinates": [-2.1442, 36.7305]},
         "created_at": "t", "updated_at": "t"}], "total": 14},
    r"/api/v1/tourism/events": {"items": [
        {"id": "e1", "urn": "urn:e1", "nombre": "Festival Noches del Castillo", "tipo": "cultural",
         "descripcion": "Conciertos", "nombre_i18n": None, "imagenes": None,
         "fecha_inicio": "2026-07-20T21:00:00", "fecha_fin": "2026-07-20T23:59:00",
         "direccion": "San José", "organizador": "Ayuntamiento", "publicado": True,
         "created_at": "t", "updated_at": "t"}], "total": 1},
    r"/api/v1/tourism/services": {"items": [
        {"id": "sv1", "urn": "urn:sv1", "nombre": "Restaurante La Ola", "tipo": "gastronomia_restaurante",
         "municipio": "Níjar", "direccion": "Paseo Marítimo 12", "telefono": "+34 950 000 000",
         "descripcion": "Cocina marinera", "horario": None,
         "ubicacion": {"type": "Point", "coordinates": [-2.11, 36.76]}}], "total": 1},

    # IoT + verticales para el gemelo
    r"/api/v1/data/iot/sensors": {"items": [
        {"urn": "urn:s1", "nombre": "CO2 sala", "tipo": "co2", "estado": "operativo",
         "ubicacion": {"type": "Point", "coordinates": [-2.207, 36.965]}, "id": "s1",
         "created_at": "t", "updated_at": "t"}], "total": 9},
    r"/api/v1/verticales/alumbrado/cuadros": [
        {"codigo": "CM-001", "nombre": "Cuadro Plaza Mayor", "estado": "operativo", "circuitos": 4,
         "latitud": 36.9656, "longitud": -2.2070},
        {"codigo": "CM-004", "nombre": "Cuadro San José", "estado": "sin_comunicacion", "circuitos": 3,
         "latitud": 36.7597, "longitud": -2.1064}],
    r"/api/v1/verticales/movilidad/puntos": [
        {"codigo": "MOV-05", "nombre": "Parking Playa de Mónsul", "tipo": "parking", "estado": "operativo",
         "latitud": 36.7307, "longitud": -2.1447}],
    r"/api/v1/verticales/seguridad/camaras": [
        {"codigo": "CCTV-01", "nombre": "Playa de Mónsul", "tipo": "fija", "estado": "operativo",
         "latitud": 36.7305, "longitud": -2.1442}],

    # Chatbot del totem
    r"/api/v1/chatbot/query": {"session_id": "s", "idioma": "es",
        "respuesta": "Las mejores playas son Mónsul y Genoveses.", "intent": "playas_destacadas",
        "confianza": 0.98, "nivel_confianza": "alta", "fuentes": [{"tipo": "faq", "id": "f1"}]},

    r"/api/v1/version": {"name": "Plataforma DTI Níjar", "version": "1.1.0", "environment": "production",
        "chatbot_engine": "rasa", "expediente": "18962/2025", "adjudicatario": "IT DIGITTAL", "marco": "PSTD"},
}

# Los contenedores se sirven paginados como la API real (684 en 4 páginas de 200)
def _contenedores(path):
    m = re.search(r"page=(\d+)", path)
    page = int(m.group(1)) if m else 1
    return {
        "total": 684,
        "items": [{"codigo": "RSU-%04d" % (i + 1), "fraccion": "organica", "estado": "operativo",
                   "llenado_pct": 40, "latitud": 36.75 + (i % 40) * 0.005,
                   "longitud": -2.20 + (i // 40) * 0.01}
                  for i in range((page - 1) * 200, min(page * 200, 684))],
    }

FAKE[r"/api/v1/verticales/residuos/contenedores"] = _contenedores


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _api(self):
        for pat, payload in FAKE.items():
            if re.search(pat, self.path):
                if callable(payload):
                    payload = payload(self.path)
                body = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return True
        if self.path.startswith("/api/"):
            self.send_response(404)
            self.end_headers()
            return True
        return False

    def do_GET(self):
        if not self._api():
            super().do_GET()

    def do_POST(self):
        self._api()
