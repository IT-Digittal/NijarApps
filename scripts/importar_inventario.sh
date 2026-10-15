#!/usr/bin/env bash
# Importa el Inventario Municipal de Bienes (DWG) en el Gemelo vivo 2D.
#
#   scripts/importar_inventario.sh <zip, carpeta o .dwg> [--srid 25830] [--dry-run]
#
# 1. Descomprime los DWG (si es un zip).
# 2. Los convierte a GeoJSON con tools/dwg2geojson (LibreDWG) en un contenedor
#    node:20 desechable (no hace falta instalar nada en el servidor).
# 3. Importa los GeoJSON en la API (nijar-dti-api): una capa por categoría,
#    grupo «Inventario de bienes». Reimportar un núcleo lo sustituye.
#
# Requisitos: Docker y el contenedor nijar-dti-api en marcha. Solo se usan los
# .dwg; los .pdf del zip se ignoran.
set -euo pipefail

if [[ $# -lt 1 ]]; then
  sed -n '2,13p' "$0"; exit 2
fi
if [[ ! -e "$1" ]]; then
  echo "✘ No existe «$1» en este servidor."
  echo "  Súbelo antes desde tu PC, p. ej.:  scp inventario.zip ubuntu@<servidor>:~/"
  exit 1
fi
ENTRADA="$(realpath "$1")"; shift
REPO="$(cd "$(dirname "$0")/.." && pwd)"
CONTENEDOR="${CONTENEDOR_API:-nijar-dti-api}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/dwg" "$TMP/geojson"

if [[ -d "$ENTRADA" ]]; then
  find "$ENTRADA" -iname '*.dwg' -exec cp {} "$TMP/dwg/" \;
elif [[ "${ENTRADA,,}" == *.zip ]]; then
  python3 - "$ENTRADA" "$TMP/dwg" <<'PY'
import sys, zipfile, pathlib
destino = pathlib.Path(sys.argv[2])
with zipfile.ZipFile(sys.argv[1]) as z:
    for n in z.namelist():
        if n.lower().endswith(".dwg") and not n.startswith("__MACOSX"):
            (destino / pathlib.Path(n).name).write_bytes(z.read(n))
PY
else
  cp "$ENTRADA" "$TMP/dwg/"
fi
echo "DWG a convertir: $(ls "$TMP/dwg" | wc -l)"

docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$REPO/tools/dwg2geojson:/src:ro" -v "$TMP:/datos" \
  node:20-slim sh -c "cp -r /src /tmp/app && cd /tmp/app && npm ci --silent --no-audit --no-fund && node convertir.mjs /datos/dwg /datos/geojson" \
  | grep -v "Open dwg file with error code" || true

if ! ls "$TMP"/geojson/*.geojson >/dev/null 2>&1; then
  echo "✘ No se ha generado ningún GeoJSON"; exit 1
fi
docker exec "$CONTENEDOR" rm -rf /tmp/inventario_geojson
docker cp "$TMP/geojson" "$CONTENEDOR:/tmp/inventario_geojson"
docker exec "$CONTENEDOR" python -m nijar_dti.data.importar_inventario /tmp/inventario_geojson "$@"
