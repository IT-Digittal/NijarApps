/**
 * Últimas secciones de la consola DTI conectadas a datos reales.
 *
 * Sustituye los renderers demo de: Alertas (derivadas de incidencias,
 * sensores y tótems), Visitantes (serie real de uso de tótems y
 * composición lingüística), Integraciones (catálogo real de fuentes de
 * datos) e Informes (informe mensual de servicio C.1 con descarga).
 */

import { api, tokens } from "./api-client.js?v=17";

let U, UI, DTI;

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function sub(crumb, h1, p, acts) {
  return '<div class="subhead"><div><div class="crumb"><a onclick="UI.go(\'home\')">Plataforma</a> · <a onclick="UI.goD(\'resumen\')">DTI Turismo</a> · <b>' + esc(crumb) + "</b></div>" +
    "<h1>" + esc(h1) + "</h1><p>" + esc(p) + '</p></div><div class="acts">' + (acts || "") + "</div></div>";
}

function kpi(l, v, d, cls, ic, click) {
  const X = window.__UI2;
  return X && X.kpiCard ? X.kpiCard(l, v == null ? "—" : String(v), d, cls, ic, click || "") : "";
}

function cargando(el, t) {
  el.innerHTML = sub(t, t, "Cargando datos de la plataforma…") +
    '<div class="card"><div class="mini" style="color:var(--muted);padding:26px 0;text-align:center">Cargando…</div></div>';
}

const NOMBRE_IDIOMA = { es: "Español", en: "Inglés", de: "Alemán", fr: "Francés" };
const COLOR_IDIOMA = { es: "#1F6FE5", en: "#17BEBB", de: "#F0B429", fr: "#7C6BF0" };

/* ================= ALERTAS (derivadas de datos reales) ================= */

async function renderAlertas(el) {
  cargando(el, "Alertas y acciones");
  const [incs, sens, salud, so] = await Promise.all([
    api.get("/incidencias").catch(() => null),
    api.get("/data/iot/sensors?page=1&page_size=100").catch(() => null),
    api.get("/dashboards/totems/health").catch(() => null),
    api.get("/dashboards/smart-office/overview").catch(() => null),
  ]);
  const prioPorSev = { critica: "alta", alta: "alta", media: "media", baja: "baja" };
  const alertas = [];

  (incs && incs.items || []).filter((i) => i.estado !== "resuelta" && i.estado !== "cerrada").forEach((i) => {
    alertas.push({
      prio: prioPorSev[i.severidad] || "media", t: i.titulo,
      w: "Incidencia " + i.severidad + " · componente: " + i.componente,
      imp: i.afecta_disponibilidad ? "Afecta a la disponibilidad del servicio (computa en la Matriz ANS)." : "Sin impacto en disponibilidad.",
      rec: "Gestionar desde SLA y mantenimiento.", go: "slas",
    });
  });
  (sens && sens.items || []).filter((s) => !(s.estado || "").startsWith("operat")).forEach((s) => {
    alertas.push({
      prio: "media", t: "Sensor " + s.nombre + " en estado «" + (s.estado || "desconocido") + "»",
      w: s.descripcion_ubicacion || s.urn, imp: "Pérdida de telemetría de ese punto de medida.",
      rec: "Revisar comunicación y batería del dispositivo.", go: "sensores",
    });
  });
  (salud && salud.totems || []).filter((t) => !(t.estado || "").startsWith("operat") && t.estado !== "online").forEach((t) => {
    alertas.push({
      prio: "alta", t: "Tótem " + t.nombre + " en estado «" + t.estado + "»",
      w: "Disponibilidad " + (t.disponibilidad_pct != null ? t.disponibilidad_pct + "%" : "—") +
        (t.temperatura_interna_max != null ? " · temp. máx " + t.temperatura_interna_max + " °C" : ""),
      imp: "Riesgo de incumplir el SLA de disponibilidad por dispositivo (≥ 99%/mes).",
      rec: "Revisar telemetría y programar intervención si persiste.", go: "totems",
    });
  });

  const orden = { alta: 0, media: 1, baja: 2 };
  alertas.sort((a, b) => orden[a.prio] - orden[b.prio]);
  const prioBadge = U.prioBadge;

  el.innerHTML = sub("Alertas y acciones", "Alertas de la plataforma",
    "Alertas generadas a partir del estado real de la plataforma: incidencias abiertas, sensores sin telemetría y salud de tótems.",
    '<button class="btn btn--pri" onclick="UI.goD(\'slas\')">Ver Matriz ANS</button>') +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Alertas activas", alertas.length, alertas.filter((a) => a.prio === "alta").length + " altas · " + alertas.filter((a) => a.prio === "media").length + " medias", "ic-coral", "bell") +
    kpi("Incidencias abiertas", incs ? (incs.items || []).filter((i) => i.estado !== "resuelta" && i.estado !== "cerrada").length : "—", "Matriz ANS · mantenimiento C.1", "ic-gold", "wrench", "UI.goD('slas')") +
    kpi("Sensores con incidencia", sens ? (sens.items || []).filter((s) => !(s.estado || "").startsWith("operat")).length : "—", "De " + (sens ? (sens.items || []).length : "—") + " en el catálogo", "ic-navy", "bolt", "UI.goD('sensores')") +
    kpi("Alertas ambientales", so ? so.alertas_activas : "—", "Umbrales del Smart Office", "ic-teal", "leaf", "UI.goD('smartoffice')") + "</div>" +
    (alertas.length ? alertas.map((a) =>
      '<div class="alert ' + (a.prio === "alta" ? "alert--err" : a.prio === "media" ? "alert--warn" : "alert--info") + '">' +
      '<div style="flex:1;min-width:0"><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><b>' + esc(a.t) + "</b>" + prioBadge(a.prio) + "</div>" +
      '<div class="mini" style="color:var(--muted);margin-top:4px"><b>Dónde:</b> ' + esc(a.w) + "</div>" +
      '<div class="mini" style="margin-top:4px"><b>Impacto:</b> ' + esc(a.imp) + "</div>" +
      '<div class="mini" style="margin-top:4px;color:var(--blue)"><b>Recomendación:</b> ' + esc(a.rec) + "</div></div>" +
      '<div><button class="btn btn--sm btn--pri" onclick="UI.goD(\'' + a.go + '\')">Ir a la sección</button></div></div>').join("") :
      '<div class="card"><div class="mini" style="color:var(--ok);text-align:center;padding:24px 0">Sin alertas activas: plataforma estable ✓</div></div>');
}

/* ================= VISITANTES (uso real de tótems + idiomas) ================= */

async function renderVisitantes(el) {
  cargando(el, "Visitantes y movilidad");
  const [uso, serie, compo, informe] = await Promise.all([
    api.get("/dashboards/totems/usage").catch(() => null),
    api.get("/dashboards/totems/usage/series").catch(() => null),
    api.get("/data/social/kpis/composicion-linguistica").catch(() => null),
    api.get("/dashboards/reports/monthly?year=" + new Date().getFullYear() + "&month=" + (new Date().getMonth() + 1)).catch(() => null),
  ]);
  const fmt = U.fmt, colChart = U.colChart, barRow = U.barRow;
  const puntos = (serie && serie.puntos || []).slice(-14);
  const vals = puntos.map((p) => p.total || 0);
  const labels = puntos.map((p, i) => (i % 2 === 0 && p.fecha ? p.fecha.slice(8, 10) : ""));
  const idiomas = (compo && compo.idiomas || []).slice(0, 6);
  const secciones = (uso && uso.secciones_top || []).slice(0, 6);
  const maxSec = secciones.length ? Math.max.apply(null, secciones.map((s) => s.total || s.conteo || 0)) : 1;

  el.innerHTML = sub("Visitantes y movilidad", "Visitantes del destino",
    "Afluencia medida por la plataforma: uso real de los tótems, visitas web estimadas y composición lingüística de visitantes (aproximación al origen, con k-anonimato).", "") +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Interacciones en tótems", uso ? fmt(uso.interacciones_total) : "—", "Sesiones únicas: " + (uso ? fmt(uso.sesiones_unicas) : "—"), "ic-navy", "totem", "UI.goD('totems')") +
    kpi("Duración media", uso && uso.duracion_media_seg != null ? Math.round(uso.duracion_media_seg) + " s" : "—", "Por sesión en tótem", "ic-teal", "clock") +
    kpi("Visitas web (mes)", informe ? fmt(informe.visitas_web_estimadas) : "—", "Estimación del informe mensual", "ic-gold", "chart") +
    kpi("Idioma principal", idiomas.length ? (NOMBRE_IDIOMA[idiomas[0].idioma] || idiomas[0].idioma) : "—", idiomas.length ? Math.round(idiomas[0].porcentaje) + "% de la muestra (" + (compo.muestra_total || 0) + " señales)" : "composición lingüística", "ic-violet", "globe") + "</div>" +
    '<div class="grid c7-5">' +
    '<div class="card"><div class="card__h"><div><div class="card__t">Interacciones en tótems · últimos 14 días</div><div class="card__s">Serie diaria real de la telemetría</div></div></div>' +
    (vals.length ? colChart(vals, { color: "teal", hpx: 150, h: 175, labels: labels }) :
      '<div class="mini" style="color:var(--muted);padding:30px 0;text-align:center">Sin datos de uso todavía</div>') + "</div>" +
    '<div class="card"><div class="card__h"><div><div class="card__t">Composición lingüística</div><div class="card__s">Tótem + web/app + chatbot + RRSS · k-anonimato</div></div></div><div class="bars">' +
    (idiomas.map((i) => barRow(NOMBRE_IDIOMA[i.idioma] || i.idioma, Math.round(i.porcentaje) + "% ±" + (i.banda_confianza_pp || 0).toFixed(1), i.porcentaje, COLOR_IDIOMA[i.idioma] || "#9AA7BF")).join("") ||
      '<div class="mini" style="color:var(--muted)">Sin muestra suficiente</div>') + "</div>" +
    (secciones.length ? '<div style="margin-top:14px"><div class="card__t" style="font-size:13px;margin-bottom:8px">Secciones más consultadas en tótems</div>' +
      (maxSec > 0
        ? '<div class="bars">' + secciones.map((s) => barRow(s.seccion || s.nombre || "—", s.total || s.conteo || 0, (s.total || s.conteo || 0) / maxSec * 100, "var(--blue)")).join("") + '</div>'
        : '<div class="mini" style="color:var(--muted);padding:14px 0">Aún no hay tráfico registrado en tótems</div>') +
      "</div>" : "") +
    "</div></div>";
}

/* ================= INTEGRACIONES (catálogo real de fuentes) ================= */

async function renderIntegraciones(el) {
  cargando(el, "Integraciones");
  const [resumen, fuentes] = await Promise.all([
    api.get("/integraciones/resumen").catch(() => null),
    api.get("/integraciones/fuentes").catch(() => []),
  ]);
  const estadoBadge = (e) =>
    e === "operativa" ? '<span class="bdg bdg-ok">operativa</span>' :
    e === "pendiente_desarrollo" ? '<span class="bdg bdg-info">pendiente desarrollo</span>' :
    e === "pendiente_acceso" ? '<span class="bdg bdg-warn">pendiente acceso</span>' :
    '<span class="bdg bdg-mut">' + esc(e) + "</span>";

  const porCategoria = {};
  (fuentes || []).forEach((f) => { (porCategoria[f.categoria] = porCategoria[f.categoria] || []).push(f); });

  el.innerHTML = sub("Integraciones", "Integraciones y fuentes de datos",
    "Catálogo real de fuentes conectadas a la plataforma: sistemas municipales, redes sociales, sensórica y servicios externos, con su estado de integración.",
    '<button class="btn" id="btn-csv-fuentes">Exportar CSV</button>') +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Fuentes de datos", resumen ? resumen.total : (fuentes || []).length, (resumen ? resumen.propias : "—") + " propias · " + (resumen ? resumen.externas : "—") + " externas", "ic-navy", "box") +
    kpi("Operativas", resumen ? resumen.operativas : "—", "Ingiriendo datos ahora", "ic-ok", "bolt") +
    kpi("Pendientes", resumen ? resumen.pendiente_desarrollo + resumen.pendiente_acceso : "—", "De desarrollo o de acceso/credenciales", "ic-gold", "clock") +
    kpi("Requieren credenciales", resumen ? resumen.requieren_credenciales : "—", "Tokens/API keys del Ayuntamiento", "ic-coral", "gear") + "</div>" +
    Object.entries(porCategoria).map(([cat, lista]) =>
      '<div class="card card--pad0" style="margin-bottom:14px"><div style="padding:14px 16px 4px" class="card__h"><div><div class="card__t">' + esc(cat) + '</div><div class="card__s">' + lista.length + " fuentes</div></div></div>" +
      '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Fuente</th><th>Origen</th><th>Conexión</th><th>Periodicidad</th><th>Estado</th></tr></thead><tbody>' +
      lista.map((f) =>
        '<tr><td style="white-space:normal;min-width:220px;font-weight:600">' + esc(f.nombre) +
        (f.notas ? '<br><span class="mini" style="color:var(--muted);font-weight:400">' + esc(f.notas) + "</span>" : "") + "</td>" +
        '<td class="mini">' + esc(f.origen) + '</td><td class="mini">' + esc(f.tipo_conexion || "—") + "</td>" +
        '<td class="mini">' + esc(f.periodicidad || "—") + "</td><td>" + estadoBadge(f.estado) + "</td></tr>").join("") +
      "</tbody></table></div></div>").join("");

  const btn = el.querySelector("#btn-csv-fuentes");
  if (btn) btn.onclick = async () => {
    try {
      const resp = await fetch("/api/v1/integraciones/fuentes.csv", { headers: { Authorization: "Bearer " + tokens.access } });
      const blob = await resp.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "fuentes_datos_nijar.csv";
      a.click();
      URL.revokeObjectURL(a.href);
    } catch { UI.toast("No se pudo exportar el CSV"); }
  };
}

/* ================= INFORMES (informe mensual real C.1) ================= */

function lineaInforme(k, v) {
  return '<div class="kv"><span class="k">' + esc(k) + '</span><span class="v tnum">' + esc(v ?? "—") + "</span></div>";
}

async function renderInformes(el) {
  cargando(el, "Informes");
  const hoy = new Date();
  let rep = null, error = null;
  try {
    rep = await api.get("/dashboards/reports/monthly?year=" + hoy.getFullYear() + "&month=" + (hoy.getMonth() + 1));
  } catch (e) { error = e; }

  if (!rep) {
    el.innerHTML = sub("Informes", "Informe mensual de servicio (C.1)", "Informe de mantenimiento y niveles de servicio del mes en curso.") +
      '<div class="card"><div class="mini" style="color:var(--muted);text-align:center;padding:26px 0">' +
      (error && error.code === "FORBIDDEN" ? "Tu rol no tiene acceso al informe mensual (requiere administrador TIC, analista de datos o auditor)."
        : "No se pudo generar el informe: " + esc(error && error.message || "sin datos")) + "</div></div>";
    return;
  }

  const disp = rep.disponibilidad_por_componente || {};
  const barRow = U.barRow, fmt = U.fmt;
  const mesTxt = hoy.toLocaleDateString("es-ES", { month: "long", year: "numeric" });

  el.innerHTML = sub("Informes", "Informe mensual de servicio (C.1) · " + mesTxt,
    "Generado en tiempo real con los datos de la plataforma: disponibilidad por componente, uso, incidencias, seguridad y social listening.",
    '<button class="btn btn--pri" id="btn-dl-informe">Descargar .md</button>') +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Interacciones tótems", fmt(rep.interacciones_totems), "En el periodo", "ic-navy", "totem") +
    kpi("Sesiones chatbot", fmt(rep.sesiones_chatbot), "Asistente virtual", "ic-blue", "chat") +
    kpi("Visitas web estimadas", fmt(rep.visitas_web_estimadas), "Eficacia digital", "ic-gold", "chart") +
    kpi("Menciones del periodo", fmt(rep.menciones_periodo), "Sentimiento medio " + (rep.sentimiento_medio != null ? rep.sentimiento_medio.toFixed(2) : "—"), "ic-teal", "globe") + "</div>" +
    '<div class="grid c7-5">' +
    '<div class="card"><div class="card__h"><div><div class="card__t">Disponibilidad por componente</div><div class="card__s">SLA ≥ 99% mensual</div></div></div><div class="bars">' +
    (Object.entries(disp).map(([c, v]) => barRow(c, (v != null ? v.toFixed(2) : "—") + "%", v || 0, v >= 99 ? "var(--ok)" : "var(--err)")).join("") ||
      '<div class="mini" style="color:var(--muted)">Sin mediciones este mes</div>') + "</div>" +
    '<div class="card"><div class="card__h"><div><div class="card__t">Incidencias y seguridad</div><div class="card__s">Matriz ANS del periodo</div></div></div>' +
    lineaInforme("Incidencias críticas", rep.incidencias_criticas) +
    lineaInforme("Incidencias altas", rep.incidencias_altas) +
    lineaInforme("Incidencias resueltas", rep.incidencias_resueltas) +
    lineaInforme("Eventos de seguridad", rep.eventos_seguridad) +
    lineaInforme("Incidentes confirmados", rep.incidentes_confirmados) +
    lineaInforme("Acciones preventivas ejecutadas", rep.acciones_preventivas_ejecutadas) + "</div></div>";

  const btn = el.querySelector("#btn-dl-informe");
  if (btn) btn.onclick = () => {
    const md = ["# Informe mensual de servicio (C.1) — Plataforma DTI Níjar",
      "", "Periodo: " + mesTxt, "", "## Disponibilidad por componente", ""]
      .concat(Object.entries(disp).map(([c, v]) => "- " + c + ": " + (v != null ? v.toFixed(2) : "—") + "%"))
      .concat(["", "## Uso del servicio", "",
        "- Interacciones en tótems: " + rep.interacciones_totems,
        "- Sesiones de chatbot: " + rep.sesiones_chatbot,
        "- Visitas web estimadas: " + rep.visitas_web_estimadas,
        "", "## Incidencias y seguridad", "",
        "- Críticas: " + rep.incidencias_criticas + " · Altas: " + rep.incidencias_altas + " · Resueltas: " + rep.incidencias_resueltas,
        "- Eventos de seguridad: " + rep.eventos_seguridad + " · Incidentes confirmados: " + rep.incidentes_confirmados,
        "- Acciones preventivas: " + rep.acciones_preventivas_ejecutadas,
        "", "## Social listening", "",
        "- Menciones del periodo: " + rep.menciones_periodo,
        "- Sentimiento medio: " + (rep.sentimiento_medio != null ? rep.sentimiento_medio.toFixed(2) : "—"),
      ]).join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([md], { type: "text/markdown" }));
    a.download = "informe_mensual_" + hoy.getFullYear() + "_" + String(hoy.getMonth() + 1).padStart(2, "0") + ".md";
    a.click();
    URL.revokeObjectURL(a.href);
  };
}

/* ---------------- registro ---------------- */

(function init() {
  DTI = window.__DTI;
  UI = window.UI;
  U = window.__U;
  if (!DTI || !DTI.DR || !UI || !U) return setTimeout(init, 300);
  DTI.DR.alertas = renderAlertas;
  DTI.DR.visitantes = renderVisitantes;
  DTI.DR.integraciones = renderIntegraciones;
  DTI.DR.informes = renderInformes;
  ["alertas", "visitantes", "integraciones", "informes"].forEach((id) => UI.rerenderD && UI.rerenderD(id));
})();
