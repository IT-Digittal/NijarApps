# Correo al Ayuntamiento — Estado de las integraciones

**Para:** [contacto municipal / área de Informática del Ayuntamiento de Níjar]
**De:** IT DIGITTAL — Dirección de Proyecto (Álvaro)
**Asunto:** Integraciones de la Plataforma DTI — qué hemos conectado y qué nos falta

---

Hola [nombre]:

Muchas gracias por la información tan detallada sobre los servicios que gestionáis; nos ha permitido avanzar bastante. Os resumo el estado de cada integración por nuestra parte y lo que necesitaríamos para cerrar las que quedan.

## Ya integrado ✅

- **Noticias del Ayuntamiento (Strapi).** Hemos conectado la plataforma al JSON público de `api.nijaraldia.es` y ya consumimos las noticias municipales (listado, detalle e imágenes). Las mostramos en el **panel**, en el **tótem** (sección de Noticias para el visitante) y las usamos también para **fundamentar las respuestas del chatbot**. Las **noticias de Turismo** las tomamos directamente de Strapi filtrando por esa categoría, como nos recomendasteis. No necesitamos nada más para esto; funciona con el acceso público.

- **Meteorología pública (Open-Meteo).** Integrada como fuente meteorológica abierta (condiciones actuales + previsión). Cada tótem muestra el tiempo de su propia ubicación. Es la misma fuente pública que ya combinabais en vuestra app.

- **Estado de las banderas de playa.** Ya lo estábamos leyendo en tiempo real desde vuestra plataforma IoT (ThingsBoard): se ven las banderas en el mapa del panel y las hemos añadido también a las fichas de playa del tótem (verde/amarilla/roja). Por ahora **se queda tal cual está**, funcionando.

## Pendiente por vuestra parte (para activar el resto)

- **Redes sociales (Facebook + Instagram).** Ya nos disteis acceso a los perfiles; para leer los datos por la API de Meta solo nos falta el **token de la app de Meta** y los IDs (página + cuenta de Instagram Business). Tenemos el procedimiento preparado; en cuanto nos lo facilitéis por el canal seguro, lo activamos.

- **Google Analytics 4.** Necesitamos una **cuenta de servicio de Google Cloud** (fichero JSON) con permiso de *Visualizador* sobre la propiedad GA4 del destino, y el **Property ID** (el número de la propiedad, no el `G-XXXX`). Con eso, la analítica web pasa a datos reales.

## Para más adelante

- **Nuevo sistema de banderas.** Nos comentáis que la próxima temporada lo reestructuraréis para guardar histórico e independizarlo de WordPress. Perfecto: cuando lo tengáis, **apuntamos nuestro conector a esa nueva fuente** y ganamos el histórico, sin cambios por vuestra parte más allá de indicarnos cómo acceder.

- **Meteo de las estaciones (Bettair).** Si en algún momento queréis que incorporemos también los datos de vuestras estaciones (además de Open-Meteo), habría que **coordinar el acceso con Bettair**, que es quien gestiona esa infraestructura. Nuestro conector ya está preparado para ello.

- **Webhook de noticias (opcional).** Nos ofrecíais crear un webhook de aviso ante nuevas noticias. De momento **no es necesario**: consultamos Strapi de forma periódica y es suficiente. Si en el futuro quisiéramos refresco inmediato, os lo comentaríamos.

## Nota de seguridad

Cualquier token o credencial (Meta, Google) **no lo enviéis por correo en texto plano**, por favor: os pasamos un **canal seguro** para compartirlo.

Quedamos a vuestra disposición para cualquier detalle técnico (endpoints, ejemplos de respuesta, etc.). Muchas gracias de nuevo por la colaboración.

Un saludo,

**Álvaro** · IT DIGITTAL — Dirección de Proyecto
Exp. 18962/2025 · [email] · [teléfono]
