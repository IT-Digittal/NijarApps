# API REST/JSON — Plataforma DTI Níjar

Especificación de la API en formato **OpenAPI 3.1**: [`openapi.yaml`](openapi.yaml).

## Visualización interactiva

Cuando el servidor está activo, la documentación es accesible en:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

## Convenciones generales

| Elemento | Norma |
|----------|-------|
| Formato | JSON (UTF-8) |
| Fechas | ISO 8601 con zona horaria (`2026-05-15T10:23:45+02:00`) |
| Identificadores | UUID v4 + URN FIWARE NGSI-LD |
| Coordenadas | GeoJSON `Point` en WGS84 (EPSG:4326), orden `[longitud, latitud]` |
| Idiomas | ISO 639-1 (`es`, `en`, `de`, `fr`) |
| Paginación | `?page=1&page_size=20` (máximo configurable por endpoint) |
| Autenticación | `Authorization: Bearer <JWT>` |
| Versionado | Prefijo `/api/v1`; cambios incompatibles → `/api/v2` |

## Rate limiting

Compromiso operativo del Hito 4:

- **Endpoints autenticados:** 600 req/min por usuario.
- **Endpoints públicos** (web/app/tótems): 1.200 req/min por IP.
- **Endpoints de ingesta IoT (HTTP):** 6.000 req/min por sensor.

## Códigos de error

| Código | Significado |
|--------|-------------|
| 200 | OK |
| 201 | Recurso creado |
| 202 | Aceptado para procesamiento async |
| 204 | OK sin cuerpo |
| 400 | Petición mal formada |
| 401 | Sin credenciales o token expirado |
| 403 | Sin permisos suficientes (RBAC) |
| 404 | Recurso no encontrado |
| 409 | Conflicto (ej. URN duplicado) |
| 422 | Validación de schema fallida |
| 429 | Rate limit excedido |
| 500 | Error interno (registrado y reportado a SIEM) |
| 503 | Servicio no disponible (mantenimiento programado) |

Todos los errores devuelven un cuerpo conforme al esquema:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "El campo 'urn' no cumple el patrón requerido",
  "details": { "field": "urn", "value": "..." }
}
```

## Validación del fichero OpenAPI

```bash
# Con redoc-cli
npx @redocly/cli lint docs/api/openapi.yaml

# Con swagger-cli
npx swagger-cli validate docs/api/openapi.yaml
```
