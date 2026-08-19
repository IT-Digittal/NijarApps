"""Configuración global de la aplicación cargada desde variables de entorno."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la plataforma DTI Níjar.

    Todas las variables se cargan desde el entorno (o el fichero .env).
    Ver `.env.example` para la lista completa.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Aplicación ---
    app_name: str = "Plataforma DTI Níjar"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_version: str = "0.1.0"
    log_level: str = "INFO"

    # --- Seguridad ---
    secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # --- CORS ---
    cors_allowed_origins: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        """Lista de orígenes CORS permitidos."""
        if not self.cors_allowed_origins:
            return []
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    # --- Base de datos ---
    database_url: PostgresDsn
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False
    # Ejecuta seed_loader (idempotente) en el arranque. True en dev/staging,
    # False en producción para no tocar datos reales sin querer.
    run_seeds_on_startup: bool = True

    # --- Redis ---
    redis_url: str = "redis://redis:6379/0"
    redis_ttl_default: int = 300

    # --- MQTT ---
    mqtt_broker_host: str = "mqtt"
    mqtt_broker_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_client_id: str = "nijar-dti-platform"
    mqtt_topic_sensors: str = "nijar/sensors/+/observation"
    mqtt_topic_pattern: str = "nijar/sensors/+/+"
    mqtt_keepalive: int = 60
    mqtt_qos: int = 1
    mqtt_use_tls: bool = False
    mqtt_tls_ca_cert: str = ""
    mqtt_tls_client_cert: str = ""
    mqtt_tls_client_key: str = ""
    mqtt_reconnect_delay_min_seconds: int = 1
    mqtt_reconnect_delay_max_seconds: int = 60

    # --- Social Listening (X / Twitter) ---
    twitter_bearer_token: str = ""
    twitter_search_query: str = (
        "Cabo de Gata OR Níjar OR \"Playa de Mónsul\" OR \"Parque Natural Cabo de Gata\" "
        "OR Rodalquilar OR \"San José Almería\""
    )
    twitter_max_results_per_poll: int = 50

    # --- Social Listening (Facebook / Instagram Graph API) ---
    facebook_access_token: str = ""
    # App de Meta: solo se usan para RENOVAR el token de larga duración (60 días)
    # con scripts/renovar_token_facebook.py. No hacen falta si el token es de
    # System User (no caduca).
    facebook_app_id: str = ""
    facebook_app_secret: str = ""
    facebook_page_id: str = ""
    # Alias público de la página oficial; sirve de fallback cuando no se conoce
    # el ID numérico (la Graph API acepta el usuario en la ruta con token válido).
    facebook_page_handle: str = ""
    instagram_business_account_id: str = ""
    instagram_handle: str = ""
    instagram_hashtags: str = (
        "cabodegata,nijar,playamonsul,parquenaturalcabodegata,rodalquilar,sanjosenijar"
    )

    # --- Social Listening (común) ---
    social_polling_interval_minutes: int = 15
    social_listening_enabled: bool = False
    social_dry_run: bool = True  # cuando True, usa datos sintéticos en vez de llamar a las APIs

    # --- Chatbot ---
    chatbot_engine: Literal["lexical", "rasa", "openai"] = "lexical"
    rasa_url: str = "http://rasa:5005"
    rasa_timeout_seconds: int = 8
    rasa_fallback_to_lexical: bool = True

    # --- Chatbot generativo (CHATBOT_ENGINE=openai) ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: int = 15
    openai_max_tokens: int = 400

    # --- Contexto histórico (backfill fuentes públicas INE/Junta/AENA) ---
    contexto_backfill_dry_run: bool = True  # True = series sintéticas sin llamar a APIs
    contexto_backfill_anios: int = 3

    # --- Gemelo digital: plataforma ThingsBoard municipal (vertical externa) ---
    # Banderas de playa y aforo del P.N. Cabo de Gata. Sin configurar,
    # los endpoints /gemelo responden 503 y el panel marca la fuente pendiente.
    thingsboard_base_url: str = ""  # p. ej. https://plataforma.nijardti.com
    thingsboard_usuario: str = ""
    thingsboard_password: str = ""
    thingsboard_timeout_seconds: int = 12

    # --- Gemelo digital: red Bettair de calidad del aire y meteo (OAuth2) ---
    # client_id/client_secret = «app password» generado en cloud.bettair.city.
    bettair_base_url: str = "https://api.v3.bettair.city"
    bettair_client_id: str = ""
    bettair_client_secret: str = ""
    bettair_timeout_seconds: int = 12

    # --- Google Analytics 4 ---
    ga4_property_id: str = ""
    # Ruta a un fichero JSON de service-account o JSON inline
    ga4_service_account_json: str = ""

    # --- Noticias del Ayuntamiento (Strapi, acceso público de solo lectura) ---
    # La web del Ayuntamiento publica sus noticias en Strapi (JSON abierto, sin
    # autenticación). La plataforma las consume para el tótem, el dashboard y el
    # chatbot. Valores por defecto = los facilitados por el Ayuntamiento.
    noticias_strapi_base_url: str = "https://api.nijaraldia.es"
    noticias_strapi_project_id: str = "bs261ckcuumnj68xcjncw7rf"
    # documentId de la categoría "Turismo" (para el atajo de noticias turísticas).
    noticias_categoria_turismo_id: str = "lj6bv606bqnpvf1u1bovf2m8"
    noticias_timeout_seconds: int = 12

    # --- Almacenamiento ---
    storage_backend: Literal["local", "s3", "gcs"] = "local"
    storage_local_path: str = "/data/storage"

    # --- Observabilidad ---
    sentry_dsn: str = ""
    prometheus_enabled: bool = True

    # --- Indicadores de dirección (estimaciones económicas/ambientales) ---
    # Factores para calcular ahorro € y CO₂ evitado (no hay dato directo: se
    # muestran como "estimado"). Ajustables por entorno.
    precio_kwh_eur: float = 0.165
    factor_co2_kwh_kg: float = 0.19
    baseline_consumo_vsap_factor: float = 1.45  # VSAP consumiría ~45% más que LED
    # Motor de las recomendaciones de dirección: reglas (por defecto) u OpenAI
    # (requiere OPENAI_API_KEY; sin clave o ante error cae a reglas).
    direccion_recomendaciones_engine: Literal["reglas", "openai"] = "reglas"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Obtiene la instancia única de configuración (cacheada)."""
    return Settings()  # type: ignore[call-arg]
