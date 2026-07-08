#!/usr/bin/env bash
# Arranque local de la plataforma DTI Níjar.
#
# Uso:
#   ./scripts/dev_up.sh                 # solo servicios base (api + db + redis + mqtt)
#   ./scripts/dev_up.sh --workers       # incluye mqtt-subscriber y social-worker
#   ./scripts/dev_up.sh --workers --rasa  # incluye Rasa (chatbot avanzado)
set -euo pipefail

cd "$(dirname "$0")/.."

PROFILES=()
WITH_WORKERS=false
WITH_RASA=false

for arg in "$@"; do
    case "$arg" in
        --workers) WITH_WORKERS=true; PROFILES+=(--profile workers) ;;
        --rasa)    WITH_RASA=true;    PROFILES+=(--profile rasa) ;;
    esac
done

echo "[1/5] Levantando servicios base (PostgreSQL/PostGIS, Redis, MQTT)..."
docker compose up -d db redis mqtt

echo "[2/5] Esperando a que PostgreSQL responda..."
for i in {1..30}; do
    if docker compose exec -T db pg_isready -U nijar -d nijar_dti >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "[3/5] Aplicando migraciones Alembic..."
docker compose run --rm api alembic upgrade head

echo "[4/5] Cargando datos seed iniciales..."
docker compose run --rm api python -m nijar_dti.data.seed_loader

if $WITH_RASA; then
    echo "[5a/5] Generando configuración Rasa desde FAQs..."
    docker compose run --rm api python -m nijar_dti.workers.rasa_generator

    echo "[5b/5] Entrenando modelo Rasa (puede tardar varios minutos)..."
    docker compose --profile rasa-train run --rm rasa-trainer
fi

if $WITH_WORKERS; then
    echo "[6/6] Levantando workers en segundo plano..."
    docker compose --profile workers up -d mqtt-subscriber social-worker
fi

if $WITH_RASA; then
    echo "[7/7] Levantando servidor Rasa..."
    docker compose --profile rasa up -d rasa
fi

cat <<EOF

✓ Plataforma lista.

  - API REST:     http://localhost:8000
  - Swagger UI:   http://localhost:8000/docs
  - ReDoc:        http://localhost:8000/redoc
EOF
if $WITH_RASA; then
cat <<EOF
  - Rasa server:  http://localhost:5005
EOF
fi
cat <<EOF

Levantar la API en primer plano con:
  docker compose up api

Para detener todo:
  docker compose down

Para ver logs de los workers:
  docker compose logs -f mqtt-subscriber social-worker
EOF
