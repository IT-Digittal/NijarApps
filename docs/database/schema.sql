-- =============================================================================
-- Plataforma DTI Níjar — Esquema PostgreSQL/PostGIS consolidado
-- =============================================================================
-- Expediente: 18962/2025
-- Versión: 0.1 (Hito 1 — entregable preliminar)
--
-- Este script crea el esquema base. La fuente de verdad son los modelos
-- SQLAlchemy en `src/nijar_dti/models/`; este SQL se mantiene sincronizado
-- como entregable documental conforme al Hito 4 (as-built).
--
-- Para aplicar las migraciones reales en un entorno: usar Alembic.
--   alembic upgrade head
-- =============================================================================

-- ----------------- Extensiones obligatorias -----------------
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =============================================================================
-- USUARIOS (RBAC)
-- =============================================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    nombre_completo VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    rol             VARCHAR(50)  NOT NULL,
    scopes_adicionales TEXT[],
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    requiere_2fa    BOOLEAN      NOT NULL DEFAULT FALSE,
    secreto_2fa     VARCHAR(255),
    sso_subject     VARCHAR(255),
    -- Auditoría
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    CONSTRAINT chk_usuarios_rol CHECK (
        rol IN ('administrador_tic','gestor_contenidos','analista_datos',
                'operador_smart_office','auditor')
    )
);
CREATE INDEX IF NOT EXISTS ix_usuarios_email      ON usuarios(email);
CREATE INDEX IF NOT EXISTS ix_usuarios_rol         ON usuarios(rol);
CREATE INDEX IF NOT EXISTS ix_usuarios_email_activo ON usuarios(email, activo);
CREATE INDEX IF NOT EXISTS ix_usuarios_sso         ON usuarios(sso_subject);

-- =============================================================================
-- RECURSOS TURÍSTICOS
-- =============================================================================
CREATE TABLE IF NOT EXISTS recursos_turisticos (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    urn                 VARCHAR(255) NOT NULL UNIQUE,
    nombre              VARCHAR(255) NOT NULL,
    categoria           VARCHAR(50)  NOT NULL,
    descripcion_corta   TEXT,
    nombre_i18n         JSONB,
    descripcion_i18n    JSONB,
    ubicacion           GEOGRAPHY(POINT, 4326),
    direccion           VARCHAR(500),
    municipio           VARCHAR(100) NOT NULL DEFAULT 'Níjar',
    codigo_postal       VARCHAR(10),
    telefono            VARCHAR(50),
    email               VARCHAR(255),
    web                 VARCHAR(500),
    horario             JSONB,
    accesibilidad       JSONB,
    servicios_disponibles TEXT[],
    etiquetas           TEXT[],
    imagenes            TEXT[],
    enlaces_externos    JSONB,
    activo              BOOLEAN      NOT NULL DEFAULT TRUE,
    publicado           BOOLEAN      NOT NULL DEFAULT FALSE,
    metadata_adicional  JSONB,
    -- Auditoría
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID,
    updated_by          UUID,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_recursos_categoria CHECK (
        categoria IN ('playa','monumento','ruta','mirador','centro_visitantes',
                      'parque_natural','museo','yacimiento','punto_interes','oficina_turismo')
    )
);
CREATE INDEX IF NOT EXISTS ix_recursos_urn              ON recursos_turisticos(urn);
CREATE INDEX IF NOT EXISTS ix_recursos_nombre           ON recursos_turisticos(nombre);
CREATE INDEX IF NOT EXISTS ix_recursos_categoria        ON recursos_turisticos(categoria);
CREATE INDEX IF NOT EXISTS ix_recursos_categoria_activo ON recursos_turisticos(categoria, activo);
CREATE INDEX IF NOT EXISTS ix_recursos_ubicacion_gist   ON recursos_turisticos USING GIST(ubicacion);
CREATE INDEX IF NOT EXISTS ix_recursos_etiquetas_gin    ON recursos_turisticos USING GIN(etiquetas);

-- =============================================================================
-- EVENTOS TURÍSTICOS
-- =============================================================================
CREATE TABLE IF NOT EXISTS eventos_turisticos (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    urn                 VARCHAR(255) NOT NULL UNIQUE,
    nombre              VARCHAR(255) NOT NULL,
    tipo                VARCHAR(50)  NOT NULL,
    descripcion         TEXT,
    nombre_i18n         JSONB,
    descripcion_i18n    JSONB,
    fecha_inicio        TIMESTAMPTZ  NOT NULL,
    fecha_fin           TIMESTAMPTZ  NOT NULL,
    recurso_id          UUID REFERENCES recursos_turisticos(id) ON DELETE SET NULL,
    ubicacion           GEOGRAPHY(POINT, 4326),
    direccion           VARCHAR(500),
    organizador         VARCHAR(255),
    precio              VARCHAR(100),
    capacidad_aforo     INTEGER,
    enlace_inscripcion  VARCHAR(500),
    imagenes            TEXT[],
    etiquetas           TEXT[],
    fuente              VARCHAR(100),
    activo              BOOLEAN      NOT NULL DEFAULT TRUE,
    publicado           BOOLEAN      NOT NULL DEFAULT FALSE,
    metadata_adicional  JSONB,
    -- Auditoría
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID,
    updated_by          UUID,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_eventos_tipo CHECK (
        tipo IN ('cultural','gastronomico','deportivo','musical','festivo',
                 'naturaleza','educativo','otro')
    ),
    CONSTRAINT chk_eventos_fechas CHECK (fecha_fin >= fecha_inicio)
);
CREATE INDEX IF NOT EXISTS ix_eventos_urn          ON eventos_turisticos(urn);
CREATE INDEX IF NOT EXISTS ix_eventos_nombre       ON eventos_turisticos(nombre);
CREATE INDEX IF NOT EXISTS ix_eventos_tipo         ON eventos_turisticos(tipo);
CREATE INDEX IF NOT EXISTS ix_eventos_fechas       ON eventos_turisticos(fecha_inicio, fecha_fin);
CREATE INDEX IF NOT EXISTS ix_eventos_tipo_activo  ON eventos_turisticos(tipo, activo);
CREATE INDEX IF NOT EXISTS ix_eventos_recurso      ON eventos_turisticos(recurso_id);

-- =============================================================================
-- SERVICIOS
-- =============================================================================
CREATE TABLE IF NOT EXISTS servicios (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    urn                 VARCHAR(255) NOT NULL UNIQUE,
    nombre              VARCHAR(255) NOT NULL,
    tipo                VARCHAR(50)  NOT NULL,
    descripcion         TEXT,
    nombre_i18n         JSONB,
    descripcion_i18n    JSONB,
    ubicacion           GEOGRAPHY(POINT, 4326),
    direccion           VARCHAR(500),
    municipio           VARCHAR(100) NOT NULL DEFAULT 'Níjar',
    codigo_postal       VARCHAR(10),
    telefono            VARCHAR(50),
    email               VARCHAR(255),
    web                 VARCHAR(500),
    horario             JSONB,
    rango_precios       VARCHAR(20),
    valoracion_media    NUMERIC(3,2),
    registro_turismo    VARCHAR(100),
    cif                 VARCHAR(20),
    accesibilidad       JSONB,
    idiomas_atencion    TEXT[],
    etiquetas           TEXT[],
    imagenes            TEXT[],
    activo              BOOLEAN      NOT NULL DEFAULT TRUE,
    publicado           BOOLEAN      NOT NULL DEFAULT FALSE,
    metadata_adicional  JSONB,
    -- Auditoría
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID,
    updated_by          UUID,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_servicios_tipo CHECK (
        tipo IN ('alojamiento_hotel','alojamiento_apartamento','alojamiento_rural',
                 'alojamiento_camping','gastronomia_restaurante','gastronomia_bar',
                 'gastronomia_cafeteria','ocio_actividad','ocio_alquiler','transporte',
                 'guia_turistico','comercio','otro')
    )
);
CREATE INDEX IF NOT EXISTS ix_servicios_urn            ON servicios(urn);
CREATE INDEX IF NOT EXISTS ix_servicios_nombre         ON servicios(nombre);
CREATE INDEX IF NOT EXISTS ix_servicios_tipo           ON servicios(tipo);
CREATE INDEX IF NOT EXISTS ix_servicios_tipo_activo    ON servicios(tipo, activo);
CREATE INDEX IF NOT EXISTS ix_servicios_ubicacion_gist ON servicios USING GIST(ubicacion);

-- =============================================================================
-- SENSORES
-- =============================================================================
CREATE TABLE IF NOT EXISTS sensores (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    urn                         VARCHAR(255) NOT NULL UNIQUE,
    nombre                      VARCHAR(255) NOT NULL,
    tipo                        VARCHAR(50)  NOT NULL,
    fabricante                  VARCHAR(100),
    modelo                      VARCHAR(100),
    numero_serie                VARCHAR(100),
    firmware_version            VARCHAR(50),
    ubicacion                   GEOGRAPHY(POINT, 4326),
    descripcion_ubicacion       TEXT,
    unidades_medida             VARCHAR(50),
    rango_minimo                DOUBLE PRECISION,
    rango_maximo                DOUBLE PRECISION,
    umbrales_alerta             JSONB,
    frecuencia_muestreo_seg     INTEGER,
    estado                      VARCHAR(30)  NOT NULL DEFAULT 'desconocido',
    nivel_bateria               DOUBLE PRECISION,
    topic_mqtt                  VARCHAR(255),
    fecha_ultima_calibracion    DATE,
    fecha_proxima_calibracion   DATE,
    etiquetas                   TEXT[],
    activo                      BOOLEAN      NOT NULL DEFAULT TRUE,
    metadata_adicional          JSONB,
    -- Auditoría
    created_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by                  UUID,
    updated_by                  UUID,
    deleted_at                  TIMESTAMPTZ,
    CONSTRAINT chk_sensores_tipo CHECK (
        tipo IN ('ambiental_co2','ambiental_temperatura','ambiental_humedad',
                 'ambiental_ruido','meteo','aforo','beacon_ble','wifi_publico',
                 'videocamara','alumbrado','totem','otro')
    ),
    CONSTRAINT chk_sensores_estado CHECK (
        estado IN ('operativo','offline','mantenimiento','averia','bateria_baja','desconocido')
    )
);
CREATE INDEX IF NOT EXISTS ix_sensores_urn            ON sensores(urn);
CREATE INDEX IF NOT EXISTS ix_sensores_tipo           ON sensores(tipo);
CREATE INDEX IF NOT EXISTS ix_sensores_estado         ON sensores(estado);
CREATE INDEX IF NOT EXISTS ix_sensores_tipo_estado    ON sensores(tipo, estado);
CREATE INDEX IF NOT EXISTS ix_sensores_ubicacion_gist ON sensores USING GIST(ubicacion);

-- =============================================================================
-- OBSERVACIONES (alta cardinalidad — particionable)
-- =============================================================================
CREATE TABLE IF NOT EXISTS observaciones (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sensor_id           UUID NOT NULL REFERENCES sensores(id) ON DELETE CASCADE,
    observado_en        TIMESTAMPTZ NOT NULL,
    valor               NUMERIC(12,4),
    unidades            VARCHAR(50),
    valores             JSONB,
    valido              BOOLEAN     NOT NULL DEFAULT TRUE,
    motivo_invalidez    VARCHAR(255),
    payload_original    JSONB,
    -- Auditoría reducida (por volumen)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_observaciones_sensor_tiempo ON observaciones(sensor_id, observado_en);
CREATE INDEX IF NOT EXISTS ix_observaciones_tiempo        ON observaciones(observado_en);

-- NOTA: en producción se evaluará particionar por mes:
--   CREATE TABLE observaciones (...) PARTITION BY RANGE (observado_en);
-- O bien activar TimescaleDB:
--   SELECT create_hypertable('observaciones', 'observado_en');

-- =============================================================================
-- VISITAS (interacciones anonimizadas)
-- =============================================================================
CREATE TABLE IF NOT EXISTS visitas (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tipo            VARCHAR(40)  NOT NULL,
    ocurrido_en     TIMESTAMPTZ  NOT NULL,
    visitante_hash  CHAR(64),
    recurso_id      UUID REFERENCES recursos_turisticos(id) ON DELETE SET NULL,
    idioma          VARCHAR(5),
    canal           VARCHAR(50),
    atributos       JSONB,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_visitas_tipo CHECK (
        tipo IN ('proximidad_ble','interaccion_totem','consulta_chatbot',
                 'app_vista','web_vista','wifi_conexion')
    )
);
CREATE INDEX IF NOT EXISTS ix_visitas_tipo          ON visitas(tipo);
CREATE INDEX IF NOT EXISTS ix_visitas_tiempo        ON visitas(ocurrido_en);
CREATE INDEX IF NOT EXISTS ix_visitas_tipo_tiempo   ON visitas(tipo, ocurrido_en);
CREATE INDEX IF NOT EXISTS ix_visitas_hash          ON visitas(visitante_hash);
CREATE INDEX IF NOT EXISTS ix_visitas_recurso       ON visitas(recurso_id);
CREATE INDEX IF NOT EXISTS ix_visitas_canal         ON visitas(canal);

-- =============================================================================
-- OPINIONES (Social Listening)
-- =============================================================================
CREATE TABLE IF NOT EXISTS opiniones (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fuente                  VARCHAR(40)  NOT NULL,
    fuente_id_externo       VARCHAR(255),
    autor_handle            VARCHAR(255),
    texto_original          TEXT         NOT NULL,
    idioma                  VARCHAR(5),
    publicado_en            TIMESTAMPTZ  NOT NULL,
    sentimiento             VARCHAR(20)  NOT NULL DEFAULT 'desconocido',
    score_sentimiento       NUMERIC(5,4),
    temas                   TEXT[],
    entidades_mencionadas   TEXT[],
    metricas                JSONB,
    latitud                 NUMERIC(9,6),
    longitud                NUMERIC(9,6),
    capturado_en            TIMESTAMPTZ,
    payload_original        JSONB,
    revisado_humano         BOOLEAN      NOT NULL DEFAULT FALSE,
    sentimiento_humano      VARCHAR(20),
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_opiniones_fuente CHECK (
        fuente IN ('twitter_x','facebook','instagram','tripadvisor',
                   'google_reviews','encuesta_municipal','otro')
    ),
    CONSTRAINT chk_opiniones_sentimiento CHECK (
        sentimiento IN ('positivo','neutro','negativo','desconocido')
    )
);
CREATE INDEX IF NOT EXISTS ix_opiniones_fuente              ON opiniones(fuente);
CREATE INDEX IF NOT EXISTS ix_opiniones_fuente_publicado    ON opiniones(fuente, publicado_en);
CREATE INDEX IF NOT EXISTS ix_opiniones_sentimiento         ON opiniones(sentimiento);
CREATE INDEX IF NOT EXISTS ix_opiniones_sent_publicado      ON opiniones(sentimiento, publicado_en);
CREATE INDEX IF NOT EXISTS ix_opiniones_idioma              ON opiniones(idioma);
CREATE INDEX IF NOT EXISTS ix_opiniones_temas_gin           ON opiniones USING GIN(temas);
CREATE INDEX IF NOT EXISTS ix_opiniones_externo             ON opiniones(fuente_id_externo);

-- =============================================================================
-- CLIENTE / AYUNTAMIENTO (ficha general — bloque 1 del pliego)
-- =============================================================================
CREATE TABLE IF NOT EXISTS clientes (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre                    VARCHAR(255) NOT NULL,
    area_responsable          VARCHAR(255),
    proyecto                  VARCHAR(255),
    descripcion               TEXT,
    cif                       VARCHAR(20),
    direccion                 VARCHAR(500),
    municipio                 VARCHAR(100) NOT NULL DEFAULT 'Níjar',
    provincia                 VARCHAR(100) NOT NULL DEFAULT 'Almería',
    responsable_municipal     JSONB,     -- {nombre, cargo, email, telefono}
    responsables_tecnicos     JSONB,     -- [{area, nombre, email, telefono}]
    canales_oficiales         JSONB,     -- {web, app, facebook, instagram, otros[]}
    idiomas_activos           TEXT[],    -- ['es','en','fr','de']
    fecha_inicio_explotacion  TIMESTAMPTZ,
    fecha_fin_mantenimiento   TIMESTAMPTZ,
    hitos                     JSONB,     -- [{nombre, fecha, estado}]
    activo                    BOOLEAN NOT NULL DEFAULT TRUE,
    metadata_adicional        JSONB,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by                UUID,
    updated_by                UUID,
    deleted_at                TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_clientes_nombre ON clientes(nombre);

-- =============================================================================
-- CAMPAÑAS DE PROMOCIÓN TURÍSTICA (bloque 9 del pliego)
-- =============================================================================
CREATE TABLE IF NOT EXISTS campanas (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre              VARCHAR(255) NOT NULL,
    fecha_inicio        TIMESTAMPTZ NOT NULL,
    fecha_fin           TIMESTAMPTZ NOT NULL,
    slug                VARCHAR(120) UNIQUE,
    descripcion         TEXT,
    objetivo            VARCHAR(30) NOT NULL DEFAULT 'difusion',
    publico_objetivo    VARCHAR(255),
    canales             TEXT[],
    presupuesto         NUMERIC(12,2),
    landing_url         VARCHAR(500),
    recurso_id          UUID REFERENCES recursos_turisticos(id) ON DELETE SET NULL,
    estado              VARCHAR(20) NOT NULL DEFAULT 'planificada',
    kpis_objetivo       JSONB,     -- objetivos numéricos de la campaña
    resultados          JSONB,     -- resultados agregados calculados
    etiquetas           TEXT[],
    metadata_adicional  JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by          UUID,
    updated_by          UUID,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_campanas_estado CHECK (
        estado IN ('planificada','activa','finalizada','cancelada')
    )
);
CREATE INDEX IF NOT EXISTS ix_campanas_fechas        ON campanas(fecha_inicio, fecha_fin);
CREATE INDEX IF NOT EXISTS ix_campanas_estado_inicio ON campanas(estado, fecha_inicio);
CREATE INDEX IF NOT EXISTS ix_campanas_recurso_id    ON campanas(recurso_id);

-- Nota: la tabla `contenidos` (CMS) incorpora además las columnas
--   fecha_aprobacion TIMESTAMPTZ  y  fecha_publicacion TIMESTAMPTZ
-- para medir el KPI de tiempo de publicación (≤ 24 h desde la aprobación),
-- junto con el estado ampliado del flujo editorial
-- (borrador → pendiente_aprobacion → aprobado → programado → publicado → archivado).

-- =============================================================================
-- VISTAS Y ROLES (referencia — implementación opcional)
-- =============================================================================
-- Vista materializada para KPI de sentimiento diario (refresco vía cron):
--   CREATE MATERIALIZED VIEW kpi_sentimiento_diario AS
--   SELECT date_trunc('day', publicado_en) AS dia,
--          fuente,
--          COUNT(*) FILTER (WHERE sentimiento = 'positivo') AS positivos,
--          COUNT(*) FILTER (WHERE sentimiento = 'neutro') AS neutros,
--          COUNT(*) FILTER (WHERE sentimiento = 'negativo') AS negativos,
--          AVG(score_sentimiento) AS score_medio
--     FROM opiniones
--     GROUP BY 1, 2;

-- =============================================================================
-- FIN DEL ESQUEMA
-- =============================================================================
