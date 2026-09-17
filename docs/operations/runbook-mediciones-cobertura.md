# Runbook · Servidor de pruebas para las mediciones de cobertura (G-NetTrack)

| | |
|---|---|
| **Objeto** | Servidor HTTP propio y estable para las pruebas de descarga/subida de la campaña de campo (puntos P01–P25) |
| **Por qué no Drive** | Google Drive no entrega el fichero como descarga HTTP directa (redirecciones, páginas intermedias, cookies, límites) y no ofrece un endpoint que acepte subidas automáticas: distorsiona la velocidad que registra G-NetTrack |
| **Dónde** | La propia API de la plataforma en producción (OVH, detrás de Caddy/TLS), mismo dominio que el panel y el tótem |

## 1. Las dos URLs para G-NetTrack

Sustituye `<DOMINIO>` por el dominio de producción (el del panel):

| Prueba | URL | Método |
|---|---|---|
| **Descarga** (100 MB) | `https://<DOMINIO>/api/v1/cobertura/descarga` | GET |
| **Subida** | `https://<DOMINIO>/api/v1/cobertura/subida` | POST (también PUT) |
| Latencia (opcional) | `https://<DOMINIO>/api/v1/cobertura/ping` | GET |

- La descarga son **100 MiB de bytes aleatorios** (incompresibles, `Cache-Control: no-store`,
  `Content-Length` fijo). Se puede cambiar el tamaño con `?mb=50` (máx. 500).
- La subida **acepta cualquier cuerpo** (binario o multipart) hasta 1 GiB, lo consume en
  streaming sin guardarlo y responde JSON con `bytes`, `megabytes`, `duracion_ms` y `mbps`.
- No hay autenticación (la app no puede hacer login). Si se quiere evitar uso ajeno,
  definir `COBERTURA_TOKEN=<clave>` en el `.env` de producción y añadir `?k=<clave>` a
  las dos URLs en G-NetTrack.

En G-NetTrack (Pro/Lite): *Settings → Data test* → **Download URL** y **Upload URL**;
en la subida, tamaño de fichero de prueba a gusto (p. ej. 20–50 MB). Todas las
mediciones P01–P25 van así contra el mismo servidor y el mismo fichero.

## 2. Comprobación antes de salir a campo (desde cualquier PC)

```bash
# Descarga: debe tardar según el ancho de banda y devolver 104857600 bytes
curl -o /dev/null -w "HTTP %{http_code} · %{size_download} bytes · %{speed_download} B/s\n" \
  https://<DOMINIO>/api/v1/cobertura/descarga

# Subida: 20 MB de prueba
head -c 20971520 /dev/urandom > /tmp/p.bin
curl -X POST --data-binary @/tmp/p.bin https://<DOMINIO>/api/v1/cobertura/subida
# → {"ok":true,"bytes":20971520,"megabytes":20.0,"duracion_ms":…,"mbps":…}
```

## 3. Documentar la campaña

Cada prueba recibida queda anotada (fecha/hora UTC, tipo, bytes, duración, Mbps medidos por
el servidor, IP y *user-agent*) en el log de la API y en
`GET /api/v1/cobertura/registro` (requiere sesión del panel; últimas 500). Es el
contraste del lado servidor para los valores que registra G-NetTrack en cada punto.

## 4. Notas técnicas

- Caddy no comprime `application/octet-stream` ni limita el tamaño del cuerpo, y
  la API sirve y consume en streaming: no hay ficheros en disco ni memoria acumulada.
- El fichero se genera al vuelo, así que no ocupa espacio en la imagen ni en el VPS.
- Cada descarga de 100 MB consume ~100 MB de tráfico de salida del VPS (irrelevante
  para 25 puntos × unas pocas repeticiones).
