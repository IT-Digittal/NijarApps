# =============================================================
# Plataforma DTI Níjar — Imagen API (multistage, producción)
# =============================================================
ARG APP_VERSION=dev

# -------- Stage 1: builder --------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiamos el proyecto e instalamos como wheel a /install
COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir --prefix=/install .

# -------- Stage 2: runtime --------
FROM python:3.11-slim AS runtime

ARG APP_VERSION
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION}

# Usuario no privilegiado
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home --shell /bin/bash app

# Parches de seguridad del sistema base + dependencias mínimas en runtime.
# `apt-get upgrade` aplica las actualizaciones de seguridad de Debian
# (p.ej. util-linux/bsdutils) sin cambiar de imagen base.
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copiar Python instalado por el builder
COPY --from=builder /install /usr/local

# Endurecimiento de las herramientas de empaquetado, que solo se usan en
# build y arrastran CVEs en la imagen final:
#  - setuptools: la copia del builder + base deja metadatos .dist-info
#    duplicados que `pip --upgrade` no limpia (provienen del COPY). Se borra
#    por completo y se reinstala una única versión parcheada. Se conserva
#    setuptools/pkg_resources por si alguna dependencia lo importa en runtime.
#  - pip y wheel: no se usan en runtime. Se eliminan (pip vendoriza msgpack,
#    que también aporta un CVE). Al quitarlos desaparecen esos hallazgos.
RUN rm -rf /usr/local/lib/python3.11/site-packages/setuptools* \
           /usr/local/lib/python3.11/site-packages/pkg_resources* \
           /usr/local/lib/python3.11/site-packages/wheel* \
    && python -m pip install --no-cache-dir --upgrade setuptools \
    && rm -rf /usr/local/lib/python3.11/site-packages/pip \
              /usr/local/lib/python3.11/site-packages/pip-*.dist-info \
              /usr/local/lib/python3.11/site-packages/wheel* \
              /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.11

# Código de la aplicación + frontend + Alembic
COPY --chown=app:app src ./src
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app frontend ./frontend

# Eliminar herramientas de compilación si quedó alguna
RUN find / -name '*.pyc' -delete 2>/dev/null || true

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/health || exit 1

# Etiquetas OCI
LABEL org.opencontainers.image.title="Plataforma DTI Níjar — API" \
      org.opencontainers.image.vendor="IT DIGITTAL" \
      org.opencontainers.image.source="https://github.com/it-digittal/nijar-dti-platform" \
      org.opencontainers.image.licenses="proprietary" \
      org.opencontainers.image.version="${APP_VERSION}"

CMD ["uvicorn", "nijar_dti.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
