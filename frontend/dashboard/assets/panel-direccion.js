/**
 * Cuadro de Mando de Dirección (perfil ejecutivo / político).
 *
 * Módulo de nivel superior, al estilo del módulo de Administración: crea su
 * propia vista `view-direccion`, una tarjeta en el lanzador (visible para quien
 * tenga el permiso `ver_resumen_municipal`) y, si el usuario es del rol
 * `direccion_gobierno`, redirige aquí tras el login. Visión resumida y no
 * técnica: estado global, semáforo por vertical, alertas, recomendaciones e
 * impacto (económico, ciudadano, ambiental).
 */

import { api, getCachedUser } from "./api-client.js?v=18";

let UI, U2, UI2;

/* ---------------- utilidades ---------------- */

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function icono(n) { return window.icon ? window.icon(n) : ""; }
function tienePermiso(p) {
  const u = getCachedUser && getCachedUser();
  if (!u) return false;
  if (!Array.isArray(u.permisos)) return true; // compat
  return u.permisos.includes(p);
}
function eur(n) { return (n == null ? "—" : Number(n).toLocaleString("es-ES") + " €"); }

function fmtNum(v) {
  v = Number(v);
  if (Math.abs(v) >= 1e9) return (v / 1e9).toFixed(1).replace(".", ",") + " mM";
  if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(1).replace(".", ",") + " M";
  return v.toLocaleString("es-ES");
}

/* Bloque de comparativa interanual (turismo, datos oficiales). Para el turismo,
   una subida es positiva (verde); una bajada, negativa (rojo). */
function bloqueInteranual(kpis, titulo, claves) {
  const lista = (kpis || []).filter((k) => !claves || claves.includes(k.clave));
  if (!lista.length) return "";
  return '<div class="card" style="margin-bottom:16px"><div class="card__h"><div>' +
    '<div class="card__t">' + esc(titulo) + "</div>" +
    '<div class="card__s">Frente al mismo periodo del año pasado · fuentes oficiales (INE / Junta / AENA)</div></div>' +
    '<span class="ai-chip">✦ interanual</span></div><div class="grid g4">' +
    lista.map((k) => {
      const col = k.tendencia === "sube" ? "var(--ok)" : (k.tendencia === "baja" ? "var(--err)" : "var(--muted)");
      const fl = k.tendencia === "sube" ? "▲" : (k.tendencia === "baja" ? "▼" : "▬");
      const sign = k.variacion_pct > 0 ? "+" : "";
      return '<div class="card" style="box-shadow:none;border:1.5px solid var(--line)">' +
        '<div class="mini" style="color:var(--muted)">' + esc(k.nombre) + "</div>" +
        '<div class="tnum" style="font-size:22px;font-weight:800;margin-top:4px;color:' + col + '">' + fl + " " + sign + k.variacion_pct + "%</div>" +
        '<div class="mini tnum" style="margin-top:4px">' + fmtNum(k.valor) + (k.unidad ? " " + esc(k.unidad) : "") +
        ' <span style="color:var(--muted)">(' + esc(k.periodo) + ")</span></div>" +
        '<div class="mini" style="color:var(--muted)">Año pasado: ' + fmtNum(k.valor_anterior) + " (" + esc(k.periodo_anterior) + ")</div></div>";
    }).join("") + "</div></div>";
}

const ESTADO_BDG = {
  verde: '<span class="bdg bdg-ok">Correcto</span>',
  ambar: '<span class="bdg bdg-warn">Atención</span>',
  rojo: '<span class="bdg bdg-err">Crítico</span>',
};
const ESTADO_GLOBAL_TXT = { correcto: "Correcto", atencion: "Requiere atención", critico: "Crítico" };
const NIVEL_BDG = {
  critico: '<span class="bdg bdg-err">crítico</span>',
  alto: '<span class="bdg bdg-err">alto</span>',
  medio: '<span class="bdg bdg-warn">medio</span>',
  bajo: '<span class="bdg bdg-info">bajo</span>',
};
const PRIO_BDG = {
  critica: '<span class="bdg bdg-err">Crítica</span>',
  alta: '<span class="bdg bdg-warn">Alta</span>',
  media: '<span class="bdg bdg-info">Media</span>',
  informativa: '<span class="bdg bdg-mut">Informativa</span>',
};

function dsub(h1, p) {
  return '<div class="subhead"><div><div class="crumb"><a onclick="UI.go(\'home\')">Plataforma</a> · <b>Dirección</b></div>' +
    "<h1>" + esc(h1) + "</h1><p>" + esc(p) + "</p></div></div>";
}
function estimadoTag() {
  return ' <span class="bdg bdg-mut" title="Valor estimado a partir de factores configurables">estimado</span>';
}

/* ---------------- pantalla: Resumen municipal ---------------- */

async function renderResumen(el) {
  el.innerHTML = dsub("Cuadro de Mando de Dirección · Smart City Níjar",
    "Visión ejecutiva de los servicios inteligentes municipales: estado global, impacto, alertas relevantes y recomendaciones para la toma de decisiones.") +
    '<div class="card"><div class="mini" style="color:var(--muted);padding:26px 0;text-align:center">Cargando…</div></div>';

  let r, recs;
  try {
    [r, recs] = await Promise.all([
      api.getResumenDireccion(),
      api.getRecomendacionesDireccion().catch(() => []),
    ]);
  } catch (e) {
    el.innerHTML = dsub("Cuadro de Mando de Dirección", "Visión ejecutiva municipal.") +
      '<div class="card"><div class="mini" style="color:var(--muted);text-align:center;padding:26px 0">' +
      (e && e.status === 403 ? "Tu rol no tiene acceso al cuadro de mando de dirección." : "Error: " + esc(e && e.message || e)) + "</div></div>";
    return;
  }
  const im = r.impacto;
  const gauge = U2 && U2.gauge ? U2.gauge(r.estado_global, 168) : "";
  const kpi = (l, v, d, cls, ic) => (UI2 && UI2.kpiCard ? UI2.kpiCard(l, esc(String(v)), d, cls, ic, "") : "");

  // Estado global + resumen
  let h = dsub("Cuadro de Mando de Dirección · Smart City Níjar",
    "Visión ejecutiva de los servicios inteligentes municipales: estado global, impacto, alertas relevantes y recomendaciones para la toma de decisiones.");

  h += '<div class="grid c7-5" style="margin-bottom:16px">' +
    '<div class="card"><div class="card__h"><div><div class="card__t">Estado global de la Smart City</div>' +
    '<div class="card__s">Índice compuesto de disponibilidad, alertas e incidencias</div></div>' +
    '<span class="ai-chip">✦ ' + ESTADO_GLOBAL_TXT[r.estado_texto] + "</span></div>" +
    '<div class="gauge">' + gauge +
    '<div style="flex:1;min-width:220px"><div class="bars">' +
    (U2 ? U2.barRow("Servicios en correcto estado", r.servicios_ok + " / " + r.servicios_total, r.servicios_ok / r.servicios_total * 100, "var(--ok)") : "") +
    (U2 ? U2.barRow("Disponibilidad media", r.disponibilidad_media_pct.toFixed(1) + "%", r.disponibilidad_media_pct, "var(--teal2)") : "") +
    (U2 ? U2.barRow("Satisfacción ciudadana (proxy)", (r.satisfaccion_pct != null ? r.satisfaccion_pct + "%" : "—"), r.satisfaccion_pct || 0, "var(--blue)") : "") +
    "</div></div></div>" +
    '<div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap">' +
    r.areas_alerta.map((a) => '<span class="bdg bdg-warn">' + esc(a) + "</span>").join("") +
    (r.areas_alerta.length ? "" : '<span class="bdg bdg-ok">Sin áreas en alerta</span>') + "</div></div>" +
    // columna derecha: impacto rápido
    '<div class="card"><div class="card__h"><div><div class="card__t">Impacto del mes</div>' +
    '<div class="card__s">Estimaciones a partir de los datos de la plataforma</div></div></div>' +
    '<div style="display:flex;align-items:baseline;gap:10px"><span class="tnum" style="font-size:30px;font-weight:800">' + eur(im.economico.ahorro_estimado_eur_mes) + "</span>" +
    '<span style="color:var(--muted);font-weight:700">ahorro' + estimadoTag() + "</span></div>" +
    '<div class="mini" style="color:var(--muted);margin-top:6px">CO₂ evitado ' + im.ambiental.co2_evitado_t_anio + " t/año" + estimadoTag() + "</div>" +
    '<div class="mini" style="color:var(--muted);margin-top:4px">Coste energético del mes ' + eur(im.economico.coste_energetico_mes_eur) + "</div>" +
    '<div class="mini" style="color:var(--muted);margin-top:4px">Autoconsumo FV ' + im.ambiental.autoconsumo_pct.toFixed(0) + "%</div></div></div>";

  // KPI row
  h += '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Estado general", r.estado_global + "/100", ESTADO_GLOBAL_TXT[r.estado_texto], r.estado_texto === "correcto" ? "ic-ok" : (r.estado_texto === "atencion" ? "ic-gold" : "ic-coral"), "chart") +
    kpi("Servicios en correcto", r.servicios_ok + " de " + r.servicios_total, "Verticales sin alerta", "ic-teal", "chart") +
    kpi("Incidencias críticas", r.incidencias_criticas, "Requieren decisión", r.incidencias_criticas ? "ic-coral" : "ic-ok", "bell") +
    kpi("Satisfacción ciudadana", (r.satisfaccion_pct != null ? r.satisfaccion_pct + "%" : "—"), "Proxy (NPS " + (im.ciudadano.nps ?? "—") + ")", "ic-blue", "chart") + "</div>";

  // Titular interanual de turismo (los 3 más relevantes para decisión política)
  h += bloqueInteranual(r.interanual_turismo, "Turismo · evolución interanual", ["viajeros", "gasto", "pasajeros_aena"]);

  // Semáforo por vertical
  h += '<div class="card card--pad0" style="margin-bottom:16px"><div style="padding:16px 16px 4px" class="card__h"><div>' +
    '<div class="card__t">Semáforo por servicio</div><div class="card__s">Estado, indicador clave y recomendación de cada vertical</div></div></div>' +
    '<div class="grid g3" style="padding:0 16px 16px">' +
    r.semaforo.map((s) =>
      '<div class="card" style="box-shadow:none;border:1.5px solid var(--line)"><div style="display:flex;align-items:center;gap:8px">' +
      '<div class="stat__chip ic-navy" style="width:30px;height:30px">' + icono(s.icono) + "</div>" +
      '<div style="font-weight:700;flex:1">' + esc(s.nombre) + "</div>" + (ESTADO_BDG[s.estado] || "") + "</div>" +
      '<div class="mini" style="color:var(--muted);margin-top:8px">' + esc(s.indicador_clave) + "</div>" +
      '<div class="mini" style="margin-top:8px"><b>Riesgo:</b> ' + esc(s.riesgo) + "</div>" +
      '<div class="mini" style="margin-top:4px;color:var(--ink)">' + esc(s.recomendacion) + "</div></div>").join("") +
    "</div></div>";

  // Alertas relevantes
  h += '<div class="card" style="margin-bottom:16px"><div class="card__h"><div><div class="card__t">Alertas relevantes para Dirección</div>' +
    '<div class="card__s">Solo lo importante para la decisión, no incidencias técnicas</div></div></div>' +
    (r.alertas.length ? r.alertas.map((a) =>
      '<div style="border-left:3px solid var(--warn);padding:8px 12px;margin:8px 0;background:var(--bg);border-radius:0 8px 8px 0">' +
      "<div>" + (NIVEL_BDG[a.nivel] || "") + ' <b>' + esc(a.area) + "</b></div>" +
      '<div class="mini" style="margin-top:4px">' + esc(a.motivo) + "</div>" +
      '<div class="mini" style="color:var(--muted);margin-top:2px">Impacto: ' + esc(a.impacto) + "</div>" +
      '<div class="mini" style="margin-top:2px">→ ' + esc(a.recomendacion) + "</div></div>").join("") :
      '<div class="mini" style="color:var(--muted);padding:14px 0;text-align:center">Sin alertas relevantes.</div>') + "</div>";

  // Recomendaciones IA
  h += '<div class="card" style="margin-bottom:16px"><div class="card__h"><div><div class="card__t">Recomendaciones de la IA</div>' +
    '<div class="card__s">Propuestas priorizadas para la toma de decisiones</div></div><span class="ai-chip">✦ IA</span></div>' +
    '<div class="grid g2">' +
    recs.map((x) =>
      '<div class="card" style="box-shadow:none;border:1.5px solid var(--line)"><div style="display:flex;gap:8px;align-items:center">' +
      (PRIO_BDG[x.prioridad] || "") + '<span class="bdg bdg-info">' + esc(x.area) + "</span></div>" +
      '<div style="font-weight:700;margin-top:8px">' + esc(x.titulo) + "</div>" +
      '<div class="mini" style="color:var(--muted);margin-top:6px">' + esc(x.justificacion) + "</div>" +
      '<div class="mini" style="margin-top:6px"><b>Impacto:</b> ' + esc(x.impacto) + "</div>" +
      '<div class="mini" style="margin-top:4px"><b>Acción:</b> ' + esc(x.accion) + "</div></div>").join("") + "</div></div>";

  // Impacto detallado
  h += '<div class="grid g3">' +
    '<div class="card"><div class="card__t">Impacto económico' + estimadoTag() + "</div>" +
    '<div class="mini" style="margin-top:8px">Ahorro estimado/mes: <b>' + eur(im.economico.ahorro_estimado_eur_mes) + "</b></div>" +
    '<div class="mini" style="margin-top:4px">Coste energético/mes: ' + eur(im.economico.coste_energetico_mes_eur) + "</div></div>" +
    '<div class="card"><div class="card__t">Impacto ciudadano</div>' +
    '<div class="mini" style="margin-top:8px">Satisfacción (proxy): <b>' + (im.ciudadano.satisfaccion_pct ?? "—") + "%</b></div>" +
    '<div class="mini" style="margin-top:4px">Sentimiento en redes: ' + (im.ciudadano.sentimiento_medio != null ? im.ciudadano.sentimiento_medio.toFixed(2) : "—") + "</div>" +
    '<div class="mini" style="margin-top:4px">Menciones del mes: ' + im.ciudadano.menciones_mes + "</div></div>" +
    '<div class="card"><div class="card__t">Sostenibilidad' + estimadoTag() + "</div>" +
    '<div class="mini" style="margin-top:8px">CO₂ evitado: <b>' + im.ambiental.co2_evitado_t_anio + " t/año</b></div>" +
    '<div class="mini" style="margin-top:4px">Autoconsumo FV: ' + im.ambiental.autoconsumo_pct.toFixed(0) + "%</div>" +
    '<div class="mini" style="margin-top:4px">Consumo energético/mes: ' + Number(im.ambiental.consumo_energetico_kwh_mes).toLocaleString("es-ES") + " kWh</div></div></div>";

  el.innerHTML = h;
  if (U2 && U2.animateBars) U2.animateBars(el);
}

/* ---------------- bootstrap del módulo ---------------- */

/* ---------------- caché compartida de resumen + recomendaciones ---------------- */

let _resumen = null;
let _recs = null;
async function datosResumen(force) {
  if (force || !_resumen) _resumen = await api.getResumenDireccion();
  return _resumen;
}
async function datosRecs(force) {
  if (force || !_recs) _recs = await api.getRecomendacionesDireccion().catch(() => []);
  return _recs;
}
function invalidarRecs() { _recs = null; }

const ESTADO_REC = {
  pendiente: "Pendiente", en_revision: "En revisión", aceptada: "Aceptada",
  descartada: "Descartada", ejecutada: "Ejecutada",
};

/* ---------------- vistas ejecutivas por vertical ---------------- */

const VERTICALES = [
  { id: "turismo", nombre: "Turismo inteligente", icono: "totem", clave: "dti", area: "turismo",
    preguntas: ["¿Está aumentando el interés turístico?", "¿Qué se está diciendo del destino en redes?", "¿Dónde conviene reforzar la promoción?"] },
  { id: "alumbrado", nombre: "Alumbrado público", icono: "bulb", clave: "alumbrado", ep: "/verticales/alumbrado/overview", area: "alumbrado",
    preguntas: ["¿Qué zonas tienen más problemas de alumbrado?", "¿Qué actuaciones deben priorizarse?", "¿Dónde se puede ahorrar más energía?"] },
  { id: "agua", nombre: "Ciclo del agua", icono: "drop", clave: "agua", ep: "/verticales/agua/overview", area: "agua",
    preguntas: ["¿Dónde se consume más agua?", "¿Existen fugas o pérdidas relevantes?", "¿Qué zonas necesitan intervención?"] },
  { id: "residuos", nombre: "Residuos", icono: "trash", clave: "residuos", ep: "/verticales/residuos/overview", area: "residuos",
    preguntas: ["¿Dónde se llenan antes los contenedores?", "¿Hay riesgo de desbordamiento?", "¿Se puede reducir el coste de recogida?"] },
  { id: "movilidad", nombre: "Movilidad", icono: "car", clave: "movilidad", ep: "/verticales/movilidad/overview", area: "movilidad",
    preguntas: ["¿Dónde se concentran los visitantes?", "¿Hay saturación en aparcamientos?", "¿Debe activarse algún aviso ciudadano?"] },
  { id: "seguridad", nombre: "Seguridad", icono: "cam", clave: "seguridad", ep: "/verticales/seguridad/overview", area: "seguridad",
    preguntas: ["¿Qué dispositivos están fuera de servicio?", "¿Existe riesgo en espacios públicos?", "¿Qué actuaciones preventivas se recomiendan?"] },
  { id: "energia", nombre: "Energía municipal", icono: "bolt", clave: "energia", ep: "/verticales/energia/overview", area: "energia",
    preguntas: ["¿Qué edificios consumen más?", "¿Qué ahorro genera el autoconsumo?", "¿Dónde conviene invertir?"] },
];

function _kpisVertical(id, ov, extra) {
  const k = (l, v, d, cls, ic) => (UI2 && UI2.kpiCard ? UI2.kpiCard(l, esc(String(v)), d, cls, ic, "") : "");
  const n = (x, dec) => (x == null ? "—" : Number(x).toLocaleString("es-ES", { maximumFractionDigits: dec ?? 0 }));
  if (id === "turismo") {
    const bd = ov, uso = extra || {};
    return k("Menciones del mes", n(bd.menciones_ultimo_mes), "En redes y reseñas", "ic-navy", "globe") +
      k("Sentimiento medio", bd.sentimiento_medio != null ? bd.sentimiento_medio.toFixed(2) : "—", "Percepción del destino", "ic-teal", "chart") +
      k("Interacciones en tótems", n(uso.interacciones_total), "Sesiones únicas: " + n(uso.sesiones_unicas), "ic-violet", "totem") +
      k("Fuentes activas", n(bd.fuentes_activas), "Canales monitorizados", "ic-blue", "chart");
  }
  if (id === "alumbrado") return k("Disponibilidad", n(ov.disponibilidad_pct, 1) + "%", "Servicio operativo", "ic-ok", "bulb") +
    k("Incidencias abiertas", n(ov.incidencias_abiertas), "Requieren seguimiento", ov.incidencias_abiertas ? "ic-coral" : "ic-ok", "wrench") +
    k("Consumo mensual", n(ov.consumo_mes_kwh) + " kWh", "Red de alumbrado", "ic-teal", "bolt") +
    k("Ahorro energético", n(ov.ahorro_energetico_pct, 1) + "%", "Frente a VSAP", "ic-gold", "leaf");
  if (id === "agua") return k("Fugas detectadas", n(ov.fugas_detectadas), "Sectores afectados", ov.fugas_detectadas ? "ic-gold" : "ic-ok", "drop") +
    k("Rendimiento medio", n(ov.rendimiento_medio_pct, 0) + "%", "Eficiencia de la red", "ic-teal", "chart") +
    k("Sectores en alerta", n(ov.sectores_en_alerta), "Consumo anómalo", "ic-coral", "bell") +
    k("Telelectura", n(ov.pct_telelectura, 0) + "%", "Contadores telemedidos", "ic-blue", "chart");
  if (id === "residuos") return k("Llenado medio", n(ov.llenado_medio_pct, 0) + "%", "Contenedores con sensor", "ic-teal", "trash") +
    k("Llenado alto (≥80%)", n(ov.llenado_alto), "Riesgo de desbordamiento", ov.llenado_alto >= 20 ? "ic-gold" : "ic-ok", "bell") +
    k("Con sensor", n(ov.con_sensor), "De " + n(ov.total) + " contenedores", "ic-navy", "chart") +
    k("Rutas", n(ov.rutas), "Optimizadas por llenado", "ic-blue", "map");
  if (id === "movilidad") return k("Tráfico actual", n(ov.trafico_actual_veh_h) + " veh/h", "Accesos monitorizados", "ic-navy", "car") +
    k("Ocupación parking", n(ov.ocupacion_parking_pct, 0) + "%", n(ov.plazas_ocupadas) + " / " + n(ov.plazas_totales) + " plazas", ov.ocupacion_parking_pct >= 90 ? "ic-gold" : "ic-ok", "car") +
    k("Puntos de recarga EV", n(ov.puntos_recarga_ev), "Tomas libres: " + n(ov.tomas_ev_libres), "ic-teal", "bolt") +
    k("Aforos", n(ov.aforos), "Puntos de conteo", "ic-blue", "chart");
  if (id === "seguridad") return k("Cámaras online", n(ov.pct_online, 0) + "%", n(ov.online) + " de " + n(ov.camaras), "ic-ok", "cam") +
    k("Sin comunicación", n(ov.sin_comunicacion), "Dispositivos a revisar", ov.sin_comunicacion ? "ic-coral" : "ic-ok", "bell") +
    k("Con analítica", n(ov.con_analitica), "Detección automática", "ic-violet", "chart") +
    k("Retención", n(ov.retencion_dias) + " días", "Grabaciones", "ic-blue", "clock");
  if (id === "energia") return k("Consumo mensual", n(ov.consumo_mes_kwh) + " kWh", n(ov.edificios) + " edificios", "ic-navy", "bolt") +
    k("Autoconsumo FV", n(ov.autoconsumo_pct, 0) + "%", n(ov.cups_con_fotovoltaica) + " CUPS con FV", "ic-ok", "leaf") +
    k("Coste mensual", n(ov.coste_mes_eur) + " €", "Factura estimada", "ic-gold", "euro") +
    k("Coste medio", n(ov.coste_medio_kwh, 3) + " €/kWh", "Precio unitario", "ic-teal", "chart");
  return "";
}

function renderVertical(id) {
  return async function (el) {
    const cfg = VERTICALES.find((v) => v.id === id);
    el.innerHTML = dsub(cfg.nombre + " · Resumen de Dirección", "Cargando…") +
      '<div class="card"><div class="mini" style="color:var(--muted);padding:26px 0;text-align:center">Cargando…</div></div>';
    let ov, extra, resumen, recs;
    try {
      if (id === "turismo") {
        [ov, extra] = await Promise.all([api.get("/dashboards/big-data/overview"), api.get("/dashboards/totems/usage").catch(() => ({}))]);
      } else {
        ov = await api.get(cfg.ep);
      }
      [resumen, recs] = await Promise.all([datosResumen(), datosRecs()]);
    } catch (e) {
      el.innerHTML = dsub(cfg.nombre, "Resumen de dirección") +
        '<div class="card"><div class="mini" style="color:var(--muted);text-align:center;padding:26px 0">' +
        (e && e.status === 403 ? "Tu rol no tiene acceso a esta vertical." : "Error: " + esc(e && e.message || e)) + "</div></div>";
      return;
    }
    const sem = (resumen.semaforo || []).find((s) => s.clave === cfg.clave);
    const recsArea = (recs || []).filter((r) => (r.area || "").toLowerCase().includes(cfg.area));

    let h = dsub(cfg.nombre + " · Resumen de Dirección",
      "Visión resumida para la toma de decisiones. Estado del servicio, indicadores clave y recomendaciones.");
    if (sem) {
      h += '<div class="card" style="margin-bottom:16px"><div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">' +
        '<div class="stat__chip ic-navy" style="width:34px;height:34px">' + icono(cfg.icono) + "</div>" +
        '<div style="font-weight:800;font-size:16px;flex:1">' + esc(cfg.nombre) + "</div>" + (ESTADO_BDG[sem.estado] || "") + "</div>" +
        '<div class="mini" style="color:var(--muted);margin-top:8px">' + esc(sem.indicador_clave) + "</div>" +
        '<div class="mini" style="margin-top:6px"><b>Recomendación:</b> ' + esc(sem.recomendacion) + "</div></div>";
    }
    h += '<div class="grid g4" style="margin-bottom:16px">' + _kpisVertical(id, ov, extra) + "</div>";
    // Comparativa interanual real donde procede (turismo completo; movilidad: proxy AENA).
    if (id === "turismo") {
      h += bloqueInteranual(resumen.interanual_turismo, "Evolución interanual del turismo", null);
    } else if (id === "movilidad") {
      h += bloqueInteranual(resumen.interanual_turismo, "Presión turística sobre la movilidad (proxy: aeropuerto)", ["pasajeros_aena"]);
    }
    h += '<div class="grid g2">' +
      '<div class="card"><div class="card__t">Preguntas que responde</div><ul style="margin:10px 0 0;padding-left:18px;font-size:13.5px;line-height:1.9">' +
      cfg.preguntas.map((p) => "<li>" + esc(p) + "</li>").join("") + "</ul></div>" +
      '<div class="card"><div class="card__h"><div><div class="card__t">Recomendaciones</div></div><span class="ai-chip">✦ IA</span></div>' +
      (recsArea.length ? recsArea.map((r) =>
        '<div style="border-left:3px solid var(--blue);padding:6px 12px;margin:8px 0;background:var(--bg);border-radius:0 8px 8px 0">' +
        '<div>' + (PRIO_BDG[r.prioridad] || "") + " <b>" + esc(r.titulo) + "</b></div>" +
        '<div class="mini" style="margin-top:4px">' + esc(r.accion) + "</div></div>").join("") :
        '<div class="mini" style="color:var(--muted);padding:10px 0">Sin recomendaciones específicas para esta área.</div>') + "</div></div>";
    el.innerHTML = h;
    if (U2 && U2.animateBars) U2.animateBars(el);
  };
}

/* ---------------- pantalla: Recomendaciones IA (con estados) ---------------- */

async function renderRecomendaciones(el) {
  el.innerHTML = dsub("Recomendaciones de la IA", "Cargando…") +
    '<div class="card"><div class="mini" style="color:var(--muted);padding:26px 0;text-align:center">Cargando…</div></div>';
  let recs;
  try { recs = await datosRecs(true); }
  catch (e) {
    el.innerHTML = dsub("Recomendaciones de la IA", "Propuestas para la toma de decisiones") +
      '<div class="card"><div class="mini" style="color:var(--muted);text-align:center;padding:26px 0">' +
      (e && e.status === 403 ? "Tu rol no tiene acceso a las recomendaciones." : "Error: " + esc(e && e.message || e)) + "</div></div>";
    return;
  }
  const opciones = (sel) => Object.keys(ESTADO_REC).map((k) =>
    '<option value="' + k + '"' + (k === sel ? " selected" : "") + ">" + ESTADO_REC[k] + "</option>").join("");

  el.innerHTML = dsub("Recomendaciones de la IA",
    "Propuestas priorizadas. Marca el estado de cada una (aceptada, descartada, ejecutada…) y deja un comentario de dirección.") +
    '<div class="grid g2">' + recs.map((r) =>
      '<div class="card" data-clave="' + esc(r.clave) + '"><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
      (PRIO_BDG[r.prioridad] || "") + '<span class="bdg bdg-info">' + esc(r.area) + '</span><span class="bdg bdg-mut" data-badge>' + ESTADO_REC[r.estado] + "</span></div>" +
      '<div style="font-weight:700;margin-top:8px">' + esc(r.titulo) + "</div>" +
      '<div class="mini" style="color:var(--muted);margin-top:6px">' + esc(r.justificacion) + "</div>" +
      '<div class="mini" style="margin-top:4px"><b>Acción:</b> ' + esc(r.accion) + "</div>" +
      '<div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;align-items:center">' +
      '<select data-estado ' + INPUT_MINI + ">" + opciones(r.estado) + "</select>" +
      '<input data-coment placeholder="Comentario de dirección…" value="' + esc(r.comentario || "") + '" ' + INPUT_MINI + ' style="flex:1;min-width:160px">' +
      '<button class="btn btn--sm btn--pri" data-guardar>Guardar</button></div></div>').join("") + "</div>";

  el.querySelectorAll("[data-clave]").forEach((card) => {
    const clave = card.getAttribute("data-clave");
    card.querySelector("[data-guardar]").onclick = async () => {
      const estado = card.querySelector("[data-estado]").value;
      const comentario = card.querySelector("[data-coment]").value.trim();
      try {
        await api.actualizarRecomendacion(clave, { estado, comentario: comentario || null });
        card.querySelector("[data-badge]").textContent = ESTADO_REC[estado];
        invalidarRecs();
        UI.toast("Recomendación actualizada");
      } catch (e) { UI.toast("Error: " + (e && e.message || e)); }
    };
  });
}

const INPUT_MINI = 'style="border:1.5px solid var(--line);border-radius:8px;padding:6px 9px;font-size:12.5px;font-family:inherit"';

/* ---------------- Informe de Dirección (imprimible → PDF) ---------------- */

async function abrirInforme() {
  let r, recs;
  try { [r, recs] = await Promise.all([datosResumen(true), datosRecs(true)]); }
  catch (e) { UI.toast("No se pudo generar el informe: " + (e && e.message || e)); return; }
  const im = r.impacto;
  const fila = (a, b) => '<tr><td style="padding:4px 8px;border-bottom:1px solid #e5e5e5">' + a + '</td><td style="padding:4px 8px;border-bottom:1px solid #e5e5e5;text-align:right">' + b + "</td></tr>";
  const semTxt = { verde: "Correcto", ambar: "Atención", rojo: "Crítico" };

  const cuerpo =
    '<div style="display:flex;justify-content:space-between;align-items:baseline;border-bottom:2px solid #003B7A;padding-bottom:8px">' +
    '<h1 style="margin:0;font-size:20px;color:#003B7A">Informe de Dirección · Smart City Níjar</h1>' +
    '<div style="font-size:12px;color:#555">Estado global: <b>' + r.estado_global + "/100</b></div></div>" +
    '<p style="font-size:12.5px;color:#333">Visión ejecutiva de los servicios inteligentes municipales para la toma de decisiones.</p>' +
    '<h2 style="font-size:14px;color:#003B7A;margin:14px 0 6px">Semáforo por servicio</h2>' +
    '<table style="width:100%;border-collapse:collapse;font-size:12.5px">' +
    r.semaforo.map((s) => fila(esc(s.nombre) + " — " + esc(s.indicador_clave), "<b>" + semTxt[s.estado] + "</b>")).join("") + "</table>" +
    '<h2 style="font-size:14px;color:#003B7A;margin:14px 0 6px">Impacto (estimado)</h2>' +
    '<table style="width:100%;border-collapse:collapse;font-size:12.5px">' +
    fila("Ahorro estimado / mes", eur(im.economico.ahorro_estimado_eur_mes)) +
    fila("CO₂ evitado", im.ambiental.co2_evitado_t_anio + " t/año") +
    fila("Satisfacción ciudadana (proxy)", (im.ciudadano.satisfaccion_pct ?? "—") + "%") +
    fila("Incidencias críticas", r.incidencias_criticas) + "</table>" +
    '<h2 style="font-size:14px;color:#003B7A;margin:14px 0 6px">Recomendaciones y próximas actuaciones</h2>' +
    '<ol style="font-size:12.5px;line-height:1.7;padding-left:18px">' +
    recs.map((x) => "<li><b>[" + x.prioridad + "]</b> " + esc(x.titulo) + " — " + esc(x.accion) + " <i>(" + ESTADO_REC[x.estado] + ")</i></li>").join("") + "</ol>" +
    '<div style="margin-top:16px;font-size:11px;color:#888">Generado por la Plataforma DTI de Níjar · Exp. 18962/2025</div>';

  let dlg = document.getElementById("informe-direccion");
  if (dlg) dlg.remove();
  dlg = document.createElement("div");
  dlg.id = "informe-direccion";
  dlg.innerHTML =
    '<style>@media print{body>*:not(#informe-direccion){display:none!important}#informe-direccion{position:static!important;box-shadow:none!important}#informe-direccion .no-print{display:none!important}}</style>' +
    '<div class="no-print" style="display:flex;gap:8px;justify-content:flex-end;margin-bottom:12px">' +
    '<button class="btn" id="informe-cerrar">Cerrar</button>' +
    '<button class="btn btn--pri" id="informe-imprimir">Imprimir / Guardar PDF</button></div>' +
    '<div id="informe-hoja" style="background:#fff;color:#111;padding:28px;border-radius:8px;max-width:800px;margin:0 auto;box-shadow:var(--sh-lg)">' + cuerpo + "</div>";
  dlg.style.cssText = "position:fixed;inset:0;z-index:9999;overflow:auto;padding:24px;background:rgba(15,25,45,.55);font-family:var(--ff)";
  document.body.appendChild(dlg);
  dlg.querySelector("#informe-cerrar").onclick = () => dlg.remove();
  dlg.querySelector("#informe-imprimir").onclick = () => window.print();
}

const SECCIONES = [
  { id: "resumen", n: "Resumen municipal", i: "chart", r: renderResumen },
  ...VERTICALES.map((v) => ({ id: v.id, n: v.nombre, i: v.icono, r: renderVertical(v.id) })),
  { id: "recomendaciones", n: "Recomendaciones IA", i: "chat", r: renderRecomendaciones },
];
const R = {};
let rendered = {};
let cur = null;
let instalado = false;
let redirigido = false;

function construirVista() {
  if (document.getElementById("view-direccion")) return;
  const home = document.getElementById("view-home");
  if (!home) return;
  const div = document.createElement("div");
  div.className = "view";
  div.id = "view-direccion";
  div.innerHTML = '<div class="app"><aside class="sidebar" id="dir-sidebar"></aside>' +
    '<main class="main" id="dir-main">' +
    SECCIONES.map((s) => '<section class="dirview" id="dir-' + s.id + '"></section>').join("") +
    "</main></div>";
  home.insertAdjacentElement("afterend", div);
  SECCIONES.forEach((s) => { R[s.id] = s.r; });
}

function renderSidebar() {
  const sb = document.getElementById("dir-sidebar");
  if (!sb) return;
  let h = '<div class="sb-head"><div class="sb-title">' + icono("chart") + " Dirección</div>" +
    '<div class="sb-sub">Cuadro de mando ejecutivo</div></div><div class="sb-g">Gobierno</div>';
  SECCIONES.forEach((s) => {
    h += '<button class="sb-it" data-dirsec="' + s.id + '" onclick="UI.goDir(\'' + s.id + '\')">' + icono(s.i) + s.n + "</button>";
  });
  if (tienePermiso("generar_informes")) {
    h += '<div class="sb-g">Informes</div>' +
      '<button class="sb-it" onclick="UI.informeDireccion()">' + icono("doc") + "Generar informe</button>";
  }
  sb.innerHTML = h;
}

function tarjetaHTML() {
  return '<div class="vcard vcard--on" data-dircard onclick="UI.enterDireccion()">' +
    '<div class="vi ic-navy">' + icono("chart") + "</div>" +
    "<h3>Vista de Gobierno</h3><p>Cuadro de mando de dirección: estado global del municipio, semáforo por servicio, alertas relevantes y recomendaciones de la IA para la toma de decisiones.</p>" +
    '<div class="vfoot"><span class="bdg bdg-info">Perfil directivo</span>' +
    '<button class="btn btn--sm btn--pri">Abrir cuadro de mando</button></div></div>';
}

function inyectarTarjeta() {
  const cont = document.getElementById("home-verticals");
  if (!cont) return;
  const ya = cont.querySelector("[data-dircard]");
  if (!tienePermiso("ver_resumen_municipal")) { if (ya) ya.remove(); return; }
  if (!ya) cont.insertAdjacentHTML("afterbegin", tarjetaHTML());
}

function instalar() {
  if (instalado) return;
  UI = window.UI; U2 = window.__U; UI2 = window.__UI2;
  if (!UI || !UI._VIEWS || !UI2) return;
  construirVista();
  renderSidebar();
  if (UI._VIEWS.indexOf("view-direccion") === -1) UI._VIEWS.push("view-direccion");

  UI.goDir = function (id) {
    UI._showV("view-direccion");
    const ctx = document.getElementById("tb-ctx");
    if (ctx) ctx.style.display = "flex";
    const pill = document.getElementById("tb-pill");
    if (pill) pill.innerHTML = icono("chart") + ' Dirección <span class="bdg bdg-info" style="margin-left:4px">vista de gobierno</span>';
    const p2 = document.getElementById("tb-pill2");
    if (p2) p2.textContent = "Cuadro de mando ejecutivo";
    cur = id;
    document.querySelectorAll(".dirview").forEach((v) => { v.style.display = "none"; });
    const el = document.getElementById("dir-" + id);
    if (!el) return;
    if (!rendered[id]) { R[id](el); rendered[id] = true; }
    el.style.display = "block";
    document.querySelectorAll("[data-dirsec]").forEach((b) => b.classList.toggle("on", b.dataset.dirsec === id));
    window.scrollTo(0, 0);
  };
  UI.enterDireccion = function () { UI.goDir(SECCIONES[0].id); };
  UI.rerenderDir = function (id) { rendered[id] = false; if (cur === id) UI.goDir(id); };
  UI.informeDireccion = abrirInforme;

  // Mantener la tarjeta al re-renderizar el home.
  const X = window.__UI2;
  if (X && X.renderHome && !X._dirWrap) {
    const orig = X.renderHome;
    X.renderHome = function () { orig.apply(this, arguments); inyectarTarjeta(); };
    X._dirWrap = true;
  }

  inyectarTarjeta();
  const poll = setInterval(() => {
    const u = getCachedUser && getCachedUser();
    if (!u) return;
    inyectarTarjeta();
    // Redirección: el perfil directivo aterriza en su cuadro de mando.
    if (!redirigido && u.rol === "direccion_gobierno") { redirigido = true; UI.enterDireccion(); }
    clearInterval(poll);
  }, 1000);

  instalado = true;
}

(function init() {
  if (!window.UI || !window.__UI2 || !window.__UI2.renderHome) { setTimeout(init, 300); return; }
  instalar();
  if (!instalado) setTimeout(init, 300);
})();
