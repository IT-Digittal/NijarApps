# Dependencias de terceros

Inventario de componentes de software de terceros utilizados en la plataforma DTI Níjar, conforme a la cláusula del PCAP que obliga a documentar licencias de COTS y librerías y a priorizar software libre.

## Backend Python

| Paquete | Versión mínima | Licencia | Función |
|---------|----------------|----------|---------|
| FastAPI | ≥ 0.110 | MIT | Framework web async |
| Uvicorn | ≥ 0.27 | BSD-3 | Servidor ASGI |
| Pydantic | ≥ 2.6 | MIT | Validación y serialización |
| SQLAlchemy | ≥ 2.0.25 | MIT | ORM |
| asyncpg | ≥ 0.29 | Apache 2.0 | Driver async PostgreSQL |
| Alembic | ≥ 1.13 | MIT | Migraciones BBDD |
| GeoAlchemy2 | ≥ 0.14 | MIT | Soporte PostGIS para SQLAlchemy |
| passlib | ≥ 1.7.4 | BSD | Hashing de contraseñas |
| python-jose | ≥ 3.3 | MIT | Generación/validación JWT |
| Redis (cliente) | ≥ 5.0 | MIT | Cliente Redis |
| paho-mqtt | ≥ 2.0 | EPL-2.0 / EDL | Cliente MQTT |
| structlog | ≥ 24.1 | Apache 2.0 / MIT | Logging estructurado |
| httpx | ≥ 0.27 | BSD-3 | Cliente HTTP |
| orjson | ≥ 3.9 | Apache 2.0 / MIT | Serialización JSON eficiente |

## Infraestructura

| Componente | Versión | Licencia | Función |
|------------|---------|----------|---------|
| PostgreSQL | 16 | PostgreSQL License | Base de datos relacional |
| PostGIS | 3.4 | GPL-2.0 | Extensión geoespacial |
| Redis | 7 | RSAL / SSPL (uso interno permitido) | Cache + pub/sub |
| Eclipse Mosquitto | 2 | EPL-2.0 / EDL | Broker MQTT |
| Docker | latest | Apache 2.0 | Contenedores |
| Nginx (proxy reverso) | latest | BSD-2 | Proxy reverso (opcional, según despliegue) |

## Servicios SaaS evaluados (a confirmar en producción)

| Servicio | Función | Justificación de uso |
|----------|---------|----------------------|
| Cloudflare WAF | Web Application Firewall (OWASP Top 10) | Cumplimiento ENS Medio |
| Sentry | Tracking de errores | Reducción MTTR |
| UptimeRobot / Nagios | Monitorización externa SLA | Si se oferta mejora SLA 99,5 % |

## Componentes de IA / NLP (a confirmar en Hito 2)

| Componente | Licencia esperada | Función |
|------------|-------------------|---------|
| Rasa Open Source | Apache 2.0 | Motor del chatbot |
| spaCy | MIT | Pipeline NLP (tokenización, NER) |
| Transformers (Hugging Face) | Apache 2.0 | Modelos pre-entrenados de sentimiento multilingüe |

## Política de actualizaciones

- **Parches críticos** de seguridad: aplicación inmediata en ventana de mantenimiento.
- **Actualizaciones menores**: revisión mensual y aplicación tras tests de regresión.
- **Actualizaciones mayores**: revisión trimestral con análisis de impacto.

## Verificación de licencias

Antes de cada release se ejecuta `pip-licenses` para validar que ninguna dependencia incorpora una licencia incompatible con el uso comercial y la cesión de derechos al Ayuntamiento (no se admiten licencias copyleft fuertes tipo GPL/AGPL en el código de la API).
