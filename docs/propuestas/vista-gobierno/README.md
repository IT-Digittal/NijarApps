# Vista de Gobierno 2.0 · maquetas

> **Implementado.** El panel real está en `frontend/dashboard/assets/panel-direccion.js`
> y sus datos salen de `GET /api/v1/direccion/panel/{modulo}`
> (`src/nijar_dti/services/direccion_panel_service.py`). Estas maquetas quedan como
> referencia de diseño; las cifras del panel real son las de la base de datos.

Maquetas HTML de la propuesta de mejora de la Vista de Gobierno, con el aspecto
que tendrá cada módulo en el panel antes de implementarlo.

Abrir `index.html` en el navegador (no necesita servidor). La barra lateral
enlaza las 9 pantallas:

| Pantalla | Fichero |
|---|---|
| Resumen municipal | `index.html` |
| Turismo inteligente | `turismo.html` |
| Alumbrado público | `alumbrado.html` |
| Ciclo del agua | `agua.html` |
| Residuos | `residuos.html` |
| Movilidad | `movilidad.html` |
| Seguridad | `seguridad.html` |
| Energía municipal | `energia.html` |
| Recomendaciones IA | `recomendaciones.html` |

- Estilos y componentes compartidos en `assets/vg.css` y `assets/vg.js`
  (tokens del panel actual; gráficos con Chart.js 4.4.1 desde cdnjs).
- Cada página declara sus datos en un único `VG.render({...})`.
- Los valores de la portada actual (23 oct 2026) son reales; el resto son
  ilustrativos. Cada indicador lleva su etiqueta: Real hoy, Al integrar,
  Estimado o Modelo predictivo.
