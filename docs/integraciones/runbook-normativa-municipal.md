# Runbook · Normativa municipal (ordenanzas de la sede electrónica)

Las ordenanzas y documentos del [portal de transparencia](https://nijar.sedelectronica.es/transparency/c9a3aaec-46f8-4a66-8a27-187955d569e6/)
se importan en la plataforma para:

- **consultarlas** en el panel: DTI Turismo → «Normativa municipal» (buscador de texto
  completo con resaltado, ficha por artículos y PDF original);
- **que el asistente responda con ellas**: el chatbot y el tótem buscan los artículos
  relacionados con la pregunta y contestan citando la ordenanza y el artículo, con el
  enlace al PDF.

## Cómo se importan

Dos vías, equivalentes (un PDF ya importado, mismo contenido, se actualiza; no se duplica):

1. **Desde el panel** (administrador TIC o gestor de contenidos): Normativa municipal →
   «Importar ordenanzas» → seleccionar todos los PDF de la carpeta y el `manifest.csv`.
2. **Desde el servidor**:

   ```bash
   scp -r ordenanzas ubuntu@IP_DEL_VPS:~/ordenanzas          # desde tu ordenador
   cd ~/NijarApps/infra/ovh
   docker compose -f docker-compose.prod.yml cp ~/ordenanzas api:/tmp/ordenanzas
   docker compose -f docker-compose.prod.yml exec api python -m nijar_dti.workers.importar_normativa /tmp/ordenanzas --dry-run
   docker compose -f docker-compose.prod.yml exec api python -m nijar_dti.workers.importar_normativa /tmp/ordenanzas
   docker compose -f docker-compose.prod.yml exec api rm -rf /tmp/ordenanzas
   ```

El `manifest.csv` es opcional: si trae columnas de archivo, título, URL y fecha (con
cualquier nombre razonable y separador «,» o «;»), se usan; si no, el título sale del
nombre del fichero.

## Qué hace la importación

- Extrae el texto del PDF (`pypdf`) y lo parte por artículos («Artículo 12. …»); si un
  documento no tiene artículos, en pasajes de ~1.500 caracteres.
- Guarda el PDF en `STORAGE_LOCAL_PATH/normativa/` y lo sirve en público en
  `/api/v1/normativa/{id}/pdf` (es documentación ya publicada en la sede).
- Clasifica por tipo según el nombre: ordenanza, reglamento, edicto, proyecto,
  certificado, bando u otro.
- Un PDF **escaneado sin texto** se guarda y se puede descargar, pero no se puede buscar
  ni lo usa el asistente (aparece como «sin texto»). Habría que pasarle OCR.

## Cómo responde el asistente

- **Con OpenAI** (`CHATBOT_ENGINE=openai`): recibe los 4 artículos más relevantes y la
  instrucción de resumir lo que dicen, citar ordenanza y artículo y remitir al texto oficial.
- **Sin OpenAI** (motor léxico/Rasa): si ninguna FAQ encaja y hay un artículo relevante,
  responde con ese artículo resumido y el enlace al PDF.
- Las respuestas llevan la fuente `normativa` con el título, el artículo y el enlace.
- Para que el enlace sea absoluto, `DOMINIO` debe estar en el `.env` (ya lo está en producción).

## API

`GET /api/v1/normativa?buscar=&tipo=` · `/resumen` · `/pasajes?pregunta=` (lo que usaría el
asistente) · `/{id}` (con artículos) · `/{id}/pdf` (público) · `POST /importar` · `DELETE /{id}`
(la retira del buscador y del asistente; el fichero se conserva).

## Pendiente

Revisión periódica de la sede electrónica para detectar ordenanzas nuevas o modificadas:
la sede corta las conexiones automatizadas desde el entorno de desarrollo; hay que probar
desde el servidor de producción antes de automatizarla.
