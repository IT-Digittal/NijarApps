/* Energía municipal con datos reales de Datadis.
   Sustituye las pantallas de demostración del vertical «Energía municipal»
   (Resumen, Suministros, Autoconsumo, Costes y contratos, Informes) por los
   suministros reales del Ayuntamiento: /verticales/energia/municipal/*.
   «Consumo del municipio» lo pinta verticales-live.js. */

import { api, fetchAuth } from "./api-client.js?v=19";

const BASE = "/verticales/energia/municipal";
const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MESES_LARGO = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
  "septiembre", "octubre", "noviembre", "diciembre"];

let resumen = null; // última respuesta de /resumen
let filtros = { tipo: "", buscar: "", orden: "consumo" };

/* ---------------- utilidades ---------------- */

function esc(t) {
  return String(t == null ? "" : t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
const U = () => window.__U;
const X = () => window.__V4.ui;
/* Formato español con punto de miles también en números de 4 cifras (7.172), que
   toLocaleString("es-ES") deja sin agrupar. */
function num(n, d) {
  if (n == null || isNaN(n)) return "—";
  const [ent, dec] = Math.abs(Number(n)).toFixed(d || 0).split(".");
  return (Number(n) < 0 ? "−" : "") + ent.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + (dec ? "," + dec : "");
}
function mwh(kwh, d) { return num(kwh / 1000, d == null ? 1 : d) + " <small>MWh</small>"; }
function eur(n) { return num(n) + " €"; }
function pct(v, conSigno = true) {
  if (v == null) return "—";
  return (conSigno && v > 0 ? "+" : "") + num(v, 1) + " %";
}
function pl(n, uno, varios) { return num(n) + " " + (n === 1 ? uno : varios); }
function mesCorto(p) { return MESES[+p.slice(5, 7) - 1] + " " + p.slice(2, 4); }
function mesLargo(p) { return p ? MESES_LARGO[+p.slice(5, 7) - 1] + " de " + p.slice(0, 4) : ""; }
function fecha(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es-ES", { day: "numeric", month: "short", year: "numeric" });
}
function colorVar(v, bajarBueno = true) {
  if (v == null || Math.abs(v) < 0.5) return "";
  const bueno = bajarBueno ? v < 0 : v > 0;
  return bueno ? "color:var(--ok);font-weight:700" : "color:var(--err);font-weight:700";
}
function badgeEstado(e) {
  if (e === "ok") return '<span class="bdg bdg-ok">con lecturas</span>';
  if (e === "sin_datos_recientes") return '<span class="bdg bdg-warn">sin lecturas recientes</span>';
  return '<span class="bdg bdg-mut">sin datos</span>';
}
function badgeTipo(t) {
  return t === "alumbrado" ? '<span class="bdg bdg-warn">alumbrado</span>' : '<span class="bdg bdg-info">edificio</span>';
}
function prio(p) {
  return U().prioBadge ? U().prioBadge(p === "informativa" ? "baja" : p) : '<span class="bdg">' + esc(p) + "</span>";
}
function card(t, s, cuerpo, extra) {
  return '<div class="card"' + (extra || "") + '><div class="card__h"><div><div class="card__t">' + t + "</div>" +
    (s ? '<div class="card__s">' + s + "</div>" : "") + "</div></div>" + cuerpo + "</div>";
}
function vacio(el, titulo) {
  const V4 = window.__V4;
  el.innerHTML = X().vsub(V4.ENE, titulo, titulo, "Datos reales de los suministros del Ayuntamiento (Datadis).", "") +
    card("Aún no hay lecturas de los suministros municipales",
      "Se mostrarán aquí en cuanto se carguen los consumos de Datadis con el usuario autorizado por el Ayuntamiento.",
      '<div class="mini" style="color:var(--muted)">En el servidor: <code>python -m nijar_dti.workers.datadis_carga --solo privado --mes-desde 2025/01</code>. ' +
      'Mientras tanto, el consumo agregado del término municipal está en <a class="lnk" onclick="UI.goE(\'municipio\')">Consumo del municipio</a>.</div>');
}
function cargando(el, titulo) {
  el.innerHTML = X().vsub(window.__V4.ENE, titulo, titulo, "Cargando los suministros de Datadis…", "") +
    '<div class="card"><div class="mini" style="color:var(--muted)">Cargando…</div></div>';
}
function errorCarga(el, titulo, e) {
  el.innerHTML = X().vsub(window.__V4.ENE, titulo, titulo, "", "") +
    card("No se pudieron cargar los datos", "", '<div class="mini" style="color:var(--err)">' + esc(e && e.message ? e.message : e) + "</div>");
}

async function descargar(ruta, nombre) {
  const r = await fetchAuth(ruta);
  if (!r.ok) throw new Error("error " + r.status);
  const blob = await r.blob();
  const m = (r.headers.get("content-disposition") || "").match(/filename="([^"]+)"/);
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = m ? m[1] : nombre;
  a.click();
  URL.revokeObjectURL(a.href);
}
window.__energiaDescargar = async (ruta, nombre) => {
  try { await descargar(ruta, nombre); } catch (e) { window.UI && UI.toast && UI.toast("No se pudo descargar: " + (e.message || e)); }
};

/* Barras apiladas por mes (alumbrado + edificios); el mes en curso, más claro */
function barrasMensuales(serie, hpx) {
  const w = 640, h = 200, pad = 8, base = 22;
  const n = serie.length || 1;
  const max = Math.max(...serie.map((m) => m.kwh), 1) * 1.1;
  const gap = Math.max(3, 50 / n), bw = (w - 2 * pad - (n - 1) * gap) / n;
  let s = '<svg viewBox="0 0 ' + w + " " + h + '" style="width:100%;height:' + (hpx || h) + 'px" preserveAspectRatio="none" role="img" aria-label="Consumo mensual">';
  serie.forEach((m, i) => {
    const x = pad + i * (bw + gap);
    const hE = (m.edificios_kwh / max) * (h - base - 8), hA = (m.alumbrado_kwh / max) * (h - base - 8);
    const op = m.completo ? 1 : 0.4;
    s += '<rect x="' + x.toFixed(1) + '" y="' + (h - base - hE).toFixed(1) + '" width="' + bw.toFixed(1) + '" height="' + hE.toFixed(1) + '" fill="#1F6FE5" opacity="' + op + '"><title>' + mesCorto(m.periodo) + " · edificios " + num(m.edificios_kwh) + " kWh</title></rect>";
    s += '<rect x="' + x.toFixed(1) + '" y="' + (h - base - hE - hA).toFixed(1) + '" width="' + bw.toFixed(1) + '" height="' + hA.toFixed(1) + '" fill="#F0B429" opacity="' + op + '"><title>' + mesCorto(m.periodo) + " · alumbrado " + num(m.alumbrado_kwh) + " kWh</title></rect>";
    if (n <= 14 || i % 2 === 0) s += '<text x="' + (x + bw / 2) + '" y="' + (h - 6) + '" font-size="10" fill="#9AA7BF" text-anchor="middle" font-family="Inter,sans-serif">' + mesCorto(m.periodo) + "</text>";
  });
  return s + "</svg>";
}
const LEYENDA_MESES = '<div class="mini" style="display:flex;gap:14px;flex-wrap:wrap;color:var(--muted);margin-top:6px">' +
  '<span><span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:#1F6FE5;margin-right:5px"></span>Edificios y resto</span>' +
  '<span><span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:#F0B429;margin-right:5px"></span>Alumbrado público</span>' +
  '<span>Más claro: mes en curso (incompleto)</span></div>';

async function cargarResumen(forzar) {
  if (!resumen || forzar) resumen = await api.get(BASE + "/resumen");
  return resumen;
}

/* ---------------- RESUMEN EJECUTIVO ---------------- */

function irSuministros(tipo) {
  filtros = { tipo: tipo || "", buscar: "", orden: tipo === "revisar" ? "ahorro" : "consumo" };
  window.__V4.ENE.rerender("edificios");
  UI.goE("edificios");
}
window.__energiaIr = irSuministros;

async function pintarResumen(el) {
  const T = "Resumen ejecutivo";
  cargando(el, T);
  let r;
  try { r = await cargarResumen(); } catch (e) { errorCarga(el, T, e); return; }
  if (!r.hay_datos) { vacio(el, T); return; }
  const V4 = window.__V4, K = X().kpiCard;
  const pctAlum = r.consumo_mes_kwh ? Math.round((r.consumo_mes_alumbrado_kwh / r.consumo_mes_kwh) * 100) : 0;
  let h = X().vsub(V4.ENE, T, "Energía municipal",
    esc(r.suministros_total) + " suministros del Ayuntamiento con lectura horaria de Datadis · último mes cerrado: <b>" + mesLargo(r.periodo) +
    "</b> · última lectura: " + fecha(r.ultima_lectura) + ".",
    '<button class="btn btn--pri" onclick="__energiaIr(\'\')">' + X().icon("panel") + " Ver suministros</button>");
  h += '<div class="grid g4" style="margin-bottom:16px">' +
    K("Consumo de " + MESES_LARGO[+r.periodo.slice(5, 7) - 1], mwh(r.consumo_mes_kwh), r.variacion_mes_pct == null ? "Todos los suministros" : pct(r.variacion_mes_pct) + " frente al mes anterior", "ic-blue", "bolt") +
    K("Coste estimado del mes", eur(r.coste_mes_eur), "a " + num(r.precio_kwh_eur, 3) + " €/kWh · " + eur(r.coste_12m_eur) + " en 12 meses", "ic-navy", "euro", "UI.goE('costes')") +
    K("Alumbrado público", mwh(r.consumo_mes_alumbrado_kwh), pctAlum + " % del consumo · " + r.suministros_alumbrado + " suministros", "ic-gold", "bulb") +
    K("Edificios y resto", mwh(r.consumo_mes_edificios_kwh), r.suministros_edificios + " suministros", "ic-teal", "panel") +
    K("Frente al mismo mes del año pasado", r.variacion_interanual_pct == null ? "—" : pct(r.variacion_interanual_pct), r.variacion_interanual_pct == null ? "Aún sin 12 meses de lecturas de ese mes" : "consumo total", "ic-violet", "chart") +
    K("CO₂ del mes", num(r.co2_mes_t, 1) + " <small>t</small>", "Factor medio de la red eléctrica", "ic-ok", "leaf") +
    K("Contratos a revisar", num(r.contratos_a_revisar), r.contratos_a_revisar ? "Ahorro estimado " + eur(r.ahorro_potencia_eur_anio) + "/año" : "Potencias acordes al consumo", "ic-coral", "doc", "__energiaIr('revisar')") +
    K("Sin lecturas recientes", num(r.sin_datos_recientes), r.sin_datos_recientes ? "Revisar contador o baja" : "Todos los suministros al día", "ic-gold", "warn", "__energiaIr('sin_datos')") +
    "</div>";
  h += '<div class="grid c7-5">';
  h += card("Consumo mensual de los suministros municipales", "Últimos " + r.serie_mensual.length + " meses · MWh",
    barrasMensuales(r.serie_mensual, 190) + LEYENDA_MESES);
  const tot = (r.consumo_mes_alumbrado_kwh + r.consumo_mes_edificios_kwh) || 1;
  h += card("¿En qué se va la energía?", mesLargo(r.periodo),
    '<div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap">' +
    X().donut([{ v: r.consumo_mes_alumbrado_kwh, c: "#F0B429" }, { v: r.consumo_mes_edificios_kwh, c: "#1F6FE5" }], 140, 16, num(r.consumo_mes_kwh / 1000, 0), "MWh") +
    '<div style="flex:1;min-width:160px">' +
    '<div class="kv"><span class="k">Alumbrado público</span><span class="v">' + Math.round((r.consumo_mes_alumbrado_kwh / tot) * 100) + " %</span></div>" +
    '<div class="kv"><span class="k">Edificios y resto</span><span class="v">' + Math.round((r.consumo_mes_edificios_kwh / tot) * 100) + " %</span></div>" +
    '<div class="kv"><span class="k">Potencia contratada total</span><span class="v">' + num(r.potencia_contratada_total_kw) + " kW</span></div>" +
    Object.entries(r.por_tarifa).map(([t, n]) => '<div class="kv"><span class="k">Tarifa ' + esc(t) + '</span><span class="v">' + n + " CUPS</span></div>").join("") +
    "</div></div>");
  h += "</div>";
  h += '<div class="grid c7-5" style="margin-top:16px">';
  const maxTop = Math.max(...r.top_consumo.map((f) => f.consumo_mes_kwh), 1);
  h += card("Los que más consumen", mesLargo(r.periodo) + " · pulsa para ver la ficha",
    '<div class="bars">' + r.top_consumo.map((f) =>
      U().barRow(esc(f.direccion), num(f.consumo_mes_kwh) + " kWh", (f.consumo_mes_kwh / maxTop) * 100,
        f.tipo === "alumbrado" ? "var(--gold)" : "var(--blue)", "__energiaFicha('" + esc(f.cups) + "')")).join("") + "</div>");
  h += card("Recomendaciones", "Calculadas con los consumos reales",
    (r.recomendaciones.length ? r.recomendaciones.map((x) =>
      '<div class="kv" style="align-items:flex-start;gap:10px"><span class="k" style="max-width:74%"><b>' + esc(x.titulo) + "</b><br>" +
      '<span class="mini" style="color:var(--muted)">' + esc(x.detalle) + "</span></span>" +
      '<span class="v" style="display:flex;flex-direction:column;gap:6px;align-items:flex-end">' + prio(x.prioridad) +
      '<button class="btn btn--sm" onclick="__energiaIr(\'' + (x.ahorro_eur_anio ? "revisar" : x.prioridad === "informativa" ? "sin_datos" : "") + '\')">Ver</button></span></div>').join("")
      : '<div class="mini" style="color:var(--muted)">Sin avisos: consumos y potencias dentro de lo esperado.</div>'));
  h += "</div>";
  h += '<div class="mini" style="margin-top:12px;color:var(--muted)">' + r.notas.map(esc).join(" · ") + "</div>";
  el.innerHTML = h;
  U().animateBars(el);
}

/* ---------------- SUMINISTROS (CUPS) ---------------- */

async function pintarSuministros(el) {
  const T = "Suministros";
  cargando(el, T);
  let r;
  try { r = await cargarResumen(); } catch (e) { errorCarga(el, T, e); return; }
  if (!r.hay_datos) { vacio(el, T); return; }
  const V4 = window.__V4;
  const opc = (v, t, sel) => '<option value="' + v + '"' + (sel === v ? " selected" : "") + ">" + t + "</option>";
  let h = X().vsub(V4.ENE, "Suministros", "Suministros eléctricos (CUPS)",
    "Los " + r.suministros_total + " suministros del Ayuntamiento en Datadis: consumo de " + mesLargo(r.periodo) +
    ", variación, pico horario frente a la potencia contratada y estado de las lecturas. Pulsa una fila para ver su ficha.",
    '<button class="btn btn--pri" onclick="__energiaDescargar(\'' + BASE + "/suministros.csv" + (filtros.tipo ? "?tipo=" + filtros.tipo : "") + '\',\'suministros.csv\')">' + X().icon("doc") + " Exportar CSV</button>");
  h += '<div class="card card--pad0"><div style="padding:16px 16px 4px" class="card__h"><div><div class="card__t">Listado de suministros</div><div class="card__s" id="en-cuenta"></div></div>' +
    '<div class="filters">' +
    '<div class="fld"><label>Buscar</label><input class="inp" id="en-q" placeholder="CUPS o dirección…" value="' + esc(filtros.buscar) + '"></div>' +
    '<div class="fld"><label>Mostrar</label><select class="sel" id="en-tipo">' +
    opc("", "Todos", filtros.tipo) + opc("alumbrado", "Alumbrado público", filtros.tipo) + opc("edificios", "Edificios y resto", filtros.tipo) +
    opc("revisar", "Potencia a revisar", filtros.tipo) + opc("autoconsumo", "Con autoconsumo", filtros.tipo) + opc("sin_datos", "Sin lecturas recientes", filtros.tipo) + "</select></div>" +
    '<div class="fld"><label>Ordenar por</label><select class="sel" id="en-orden">' +
    opc("consumo", "Consumo del mes", filtros.orden) + opc("variacion", "Mayor subida", filtros.orden) + opc("ahorro", "Ahorro de potencia", filtros.orden) +
    opc("utilizacion", "Menor utilización", filtros.orden) + opc("direccion", "Dirección", filtros.orden) + opc("cups", "CUPS", filtros.orden) + "</select></div>" +
    "</div></div>" +
    '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>CUPS</th><th>Dirección</th><th>Tipo</th><th>Tarifa</th><th>Potencia</th>' +
    "<th>kWh " + mesCorto(r.periodo) + "</th><th>Var. mes</th><th>kWh 12 meses</th><th>Pico / uso</th><th>Lecturas</th></tr></thead>" +
    '<tbody id="en-filas"><tr><td colspan="10" class="mini">Cargando…</td></tr></tbody></table></div></div>';
  el.innerHTML = h;
  const aplicar = async () => {
    filtros.buscar = el.querySelector("#en-q").value;
    filtros.tipo = el.querySelector("#en-tipo").value;
    filtros.orden = el.querySelector("#en-orden").value;
    const q = new URLSearchParams({ orden: filtros.orden });
    if (filtros.tipo) q.set("tipo", filtros.tipo);
    if (filtros.buscar.trim()) q.set("buscar", filtros.buscar.trim());
    let filas;
    try { filas = await api.get(BASE + "/suministros?" + q.toString()); } catch (e) {
      el.querySelector("#en-filas").innerHTML = '<tr><td colspan="10" class="mini" style="color:var(--err)">' + esc(e.message || e) + "</td></tr>";
      return;
    }
    el.querySelector("#en-cuenta").textContent = filas.length + " de " + r.suministros_total + " suministros";
    el.querySelector("#en-filas").innerHTML = filas.length ? filas.map((f) =>
      '<tr class="rowclick" onclick="__energiaFicha(\'' + esc(f.cups) + '\')"><td class="lnk">' + esc(f.cups) + "</td>" +
      '<td style="white-space:normal;min-width:200px">' + esc(f.direccion) + "</td><td>" + badgeTipo(f.tipo) + "</td>" +
      '<td class="mini">' + esc(f.tarifa || "—") + '</td><td class="tnum">' + (f.potencia_contratada_kw ? num(f.potencia_contratada_kw, 1) + " kW" : "—") + "</td>" +
      '<td class="tnum"><b>' + num(f.consumo_mes_kwh) + "</b></td>" +
      '<td class="tnum" style="' + colorVar(f.variacion_mes_pct) + '">' + pct(f.variacion_mes_pct) + "</td>" +
      '<td class="tnum mini">' + num(f.consumo_12m_kwh) + "</td>" +
      '<td class="tnum mini">' + (f.pico_horario_kw == null ? "—" : num(f.pico_horario_kw, 1) + " kW" + (f.utilizacion_pct == null ? "" : " · " + num(f.utilizacion_pct, 0) + " %")) +
      (f.ahorro_potencia_eur_anio ? ' <span class="bdg bdg-warn">revisar</span>' : "") + "</td>" +
      "<td>" + badgeEstado(f.estado) + "</td></tr>").join("")
      : '<tr><td colspan="10" class="mini">Ningún suministro coincide con el filtro.</td></tr>';
  };
  let t = null;
  el.querySelector("#en-q").oninput = () => { clearTimeout(t); t = setTimeout(aplicar, 300); };
  el.querySelector("#en-tipo").onchange = aplicar;
  el.querySelector("#en-orden").onchange = aplicar;
  aplicar();
}

/* ---------------- FICHA DE UN SUMINISTRO ---------------- */

window.__energiaFicha = async function (cups) {
  UI.openDrawer(esc(cups), "Cargando la ficha…", '<div class="mini" style="color:var(--muted)">Cargando…</div>');
  let d, curva;
  try {
    [d, curva] = await Promise.all([
      api.get(BASE + "/suministros/" + encodeURIComponent(cups)),
      api.get("/verticales/energia/suministros/" + encodeURIComponent(cups) + "/curva?dias=7").catch(() => []),
    ]);
  } catch (e) {
    UI.openDrawer(esc(cups), "", '<div class="mini" style="color:var(--err)">No se pudo cargar: ' + esc(e.message || e) + "</div>");
    return;
  }
  const f = d.suministro, c = d.contrato || {};
  const kv = (k, v) => '<div class="kv"><span class="k">' + k + '</span><span class="v tnum">' + v + "</span></div>";
  const pots = (c.potencias_kw || []).map((p, i) => p == null ? null : "P" + (i + 1) + " " + num(p, 2)).filter(Boolean).join(" · ");
  let h = '<div class="dsec"><div class="t">' + (f.tipo === "alumbrado" ? "Alumbrado público" : "Edificio / dependencia") + "</div>" +
    kv("Consumo del último mes", num(f.consumo_mes_kwh) + " kWh") +
    kv("Mes anterior", num(f.consumo_mes_anterior_kwh) + ' kWh <span style="' + colorVar(f.variacion_mes_pct) + '">(' + pct(f.variacion_mes_pct) + ")</span>") +
    (f.consumo_mismo_mes_anio_anterior_kwh != null ? kv("Mismo mes del año pasado", num(f.consumo_mismo_mes_anio_anterior_kwh) + ' kWh <span style="' + colorVar(f.variacion_interanual_pct) + '">(' + pct(f.variacion_interanual_pct) + ")</span>") : "") +
    kv("Últimos 12 meses", num(f.consumo_12m_kwh) + " kWh") +
    kv("Coste estimado del mes", eur(f.coste_mes_eur)) +
    kv("Última lectura", fecha(f.ultima_lectura) + " " + badgeEstado(f.estado)) + "</div>";
  h += '<div class="dsec"><div class="t">Contrato (Datadis)</div>' +
    kv("Tarifa de acceso", esc(c.tarifa_acceso || "—")) + kv("Tensión", esc(/^\d+$/.test(c.tension || "") ? c.tension + " V" : c.tension || "—")) +
    kv("Potencias contratadas (kW)", pots || (f.potencia_contratada_kw ? num(f.potencia_contratada_kw, 2) : "—")) +
    kv("Distribuidora", esc(c.distribuidora || d.distribuidora || "—")) +
    (c.comercializadora ? kv("Comercializadora", esc(c.comercializadora)) : "") +
    (c.fecha_inicio ? kv("Contrato desde", esc(c.fecha_inicio)) : "") + "</div>";
  const uso = f.utilizacion_pct;
  h += '<div class="dsec"><div class="t">Potencia: contratada frente a la usada</div>' +
    kv("Pico horario (12 meses)", f.pico_horario_kw == null ? "—" : num(f.pico_horario_kw, 2) + " kW · " + fecha(f.pico_momento)) +
    kv("Utilización de la potencia", uso == null ? "—" : num(uso, 0) + " %") +
    (f.potencia_recomendada_kw ? '<div class="kv"><span class="k" style="color:var(--warn);font-weight:700">Se podría bajar a ' + num(f.potencia_recomendada_kw, 1) +
      " kW: ahorro estimado " + eur(f.ahorro_potencia_eur_anio) + '/año</span><span class="v"></span></div>' +
      '<div class="mini" style="color:var(--muted)">Pico horario + 30 % de margen. Confirmar con el maxímetro de la factura antes de pedir el cambio.</div>'
      : '<div class="mini" style="color:var(--muted)">' + (f.meses_con_datos < 6 ? "Hacen falta 6 meses completos de lecturas para recomendar un ajuste." : "La potencia contratada es acorde al consumo.") + "</div>") + "</div>";
  if (d.serie_mensual.length) {
    h += '<div class="dsec"><div class="t">Consumo mensual (kWh)</div>' + barrasMensuales(d.serie_mensual, 130) + "</div>";
  }
  if (d.perfil_horario_kwh.some((v) => v > 0)) {
    const etq = Array.from({ length: 24 }, (_, i) => (i % 4 === 0 ? i + "h" : ""));
    h += '<div class="dsec"><div class="t">Consumo medio por hora · últimos 30 días (kWh)</div>' +
      X().areaChart(d.perfil_laborable_kwh, { color: f.tipo === "alumbrado" ? "gold" : "blue", hpx: 110, h: 140, labels: etq, compare: d.perfil_festivo_kwh }) +
      '<div class="mini" style="color:var(--muted)">Línea continua: días laborables · discontinua: fines de semana y festivos.</div></div>';
  }
  if (curva && curva.length > 2) {
    h += '<div class="dsec"><div class="t">Últimos 7 días, hora a hora (kWh)</div>' +
      X().areaChart(curva.map((x) => x.consumo_kwh), { color: "teal", hpx: 110, h: 140 }) + "</div>";
  }
  UI.openDrawer(esc(f.direccion), esc(f.cups) + " · " + (f.tarifa ? esc(f.tarifa) + " · " : "") + num(f.consumo_mes_kwh) + " kWh el último mes", h);
};

/* ---------------- AUTOCONSUMO ---------------- */

async function pintarAutoconsumo(el) {
  const T = "Autoconsumo";
  cargando(el, T);
  let r, filas;
  try {
    r = await cargarResumen();
    if (!r.hay_datos) { vacio(el, T); return; }
    filas = await api.get(BASE + "/suministros?tipo=autoconsumo&orden=consumo");
  } catch (e) { errorCarga(el, T, e); return; }
  const V4 = window.__V4, K = X().kpiCard;
  let h = X().vsub(V4.ENE, T, "Autoconsumo fotovoltaico",
    "Energía autoconsumida y excedentes vertidos a la red según las lecturas de Datadis de los suministros municipales (últimos 12 meses).", "");
  h += '<div class="grid g4" style="margin-bottom:16px">' +
    K("Suministros con autoconsumo", num(r.cups_con_autoconsumo), "de " + r.suministros_total + " suministros", "ic-gold", "sun") +
    K("Energía autoconsumida", mwh(r.autoconsumo_12m_kwh), "últimos 12 meses", "ic-ok", "bolt") +
    K("Excedentes a la red", mwh(r.excedente_12m_kwh), "candidatos a compensación", "ic-teal", "chart") +
    K("Ahorro del autoconsumo", eur(Math.round(r.autoconsumo_12m_kwh * r.precio_kwh_eur)), "estimado a " + num(r.precio_kwh_eur, 3) + " €/kWh", "ic-blue", "euro") + "</div>";
  if (!filas.length) {
    h += card("Ningún suministro registra autoconsumo en Datadis",
      "Si el Ayuntamiento tiene placas solares, su producción no figura todavía en las lecturas de las distribuidoras.",
      '<div class="mini" style="color:var(--muted)">Pasa cuando la instalación no está legalizada como autoconsumo con excedentes o compensación, ' +
      "o cuando la distribuidora aún no publica sus medidas. Para seguirlas habría que integrar el inversor o el monitor de cada instalación.</div>");
  } else {
    h += '<div class="card card--pad0"><div style="padding:16px 16px 4px" class="card__h"><div><div class="card__t">Suministros con autoconsumo</div><div class="card__s">Pulsa para ver la ficha</div></div></div>' +
      '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>CUPS</th><th>Dirección</th><th>Consumo 12 meses</th><th>Autoconsumido</th><th>Excedentes</th><th>Cobertura</th></tr></thead><tbody>' +
      filas.map((f) => {
        const cob = f.consumo_12m_kwh + f.autoconsumo_12m_kwh ? (f.autoconsumo_12m_kwh / (f.consumo_12m_kwh + f.autoconsumo_12m_kwh)) * 100 : 0;
        return '<tr class="rowclick" onclick="__energiaFicha(\'' + esc(f.cups) + '\')"><td class="lnk">' + esc(f.cups) + '</td><td style="white-space:normal;min-width:200px">' + esc(f.direccion) +
          '</td><td class="tnum">' + num(f.consumo_12m_kwh) + ' kWh</td><td class="tnum">' + num(f.autoconsumo_12m_kwh) + ' kWh</td><td class="tnum">' + num(f.excedente_12m_kwh) +
          ' kWh</td><td class="tnum">' + num(cob, 0) + " %</td></tr>";
      }).join("") + "</tbody></table></div></div>";
  }
  el.innerHTML = h;
}

/* ---------------- COSTES Y CONTRATOS ---------------- */

async function pintarCostes(el) {
  const T = "Costes y contratos";
  cargando(el, T);
  let r, revisar;
  try {
    r = await cargarResumen();
    if (!r.hay_datos) { vacio(el, T); return; }
    revisar = await api.get(BASE + "/suministros?tipo=revisar&orden=ahorro");
  } catch (e) { errorCarga(el, T, e); return; }
  const V4 = window.__V4, K = X().kpiCard;
  let h = X().vsub(V4.ENE, "Costes", "Costes y contratos",
    "Coste estimado con el consumo real y revisión de la potencia contratada de cada suministro frente a su pico de consumo.",
    '<button class="btn btn--pri" onclick="__energiaDescargar(\'' + BASE + '/suministros.csv?tipo=revisar\',\'potencia_a_revisar.csv\')">' + X().icon("doc") + " Exportar lista</button>");
  h += '<div class="grid g4" style="margin-bottom:16px">' +
    K("Coste estimado del mes", eur(r.coste_mes_eur), mesLargo(r.periodo) + " · " + num(r.precio_kwh_eur, 3) + " €/kWh", "ic-navy", "euro") +
    K("Coste estimado 12 meses", eur(r.coste_12m_eur), mwh(r.consumo_12m_kwh, 0) + " consumidos", "ic-blue", "chart") +
    K("Potencia contratada", num(r.potencia_contratada_total_kw) + " <small>kW</small>", "suma de " + r.suministros_total + " suministros", "ic-violet", "bolt") +
    K("Potencia a revisar", num(r.contratos_a_revisar) + " <small>" + (r.contratos_a_revisar === 1 ? "contrato" : "contratos") + "</small>", r.contratos_a_revisar ? "Ahorro estimado " + eur(r.ahorro_potencia_eur_anio) + "/año" : "Sin sobredimensionados", "ic-coral", "doc") + "</div>";
  h += '<div class="card card--pad0"><div style="padding:16px 16px 4px" class="card__h"><div><div class="card__t">Contratos con potencia sobredimensionada</div>' +
    '<div class="card__s">Su mayor consumo horario del último año no llega a la mitad de la potencia contratada</div></div></div>';
  if (revisar.length) {
    h += '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>CUPS</th><th>Dirección</th><th>Tarifa</th><th>Contratada</th><th>Pico horario</th><th>Uso</th><th>Propuesta</th><th>Ahorro/año</th></tr></thead><tbody>' +
      revisar.map((f) => '<tr class="rowclick" onclick="__energiaFicha(\'' + esc(f.cups) + '\')"><td class="lnk">' + esc(f.cups) + '</td><td style="white-space:normal;min-width:200px">' + esc(f.direccion) +
        '</td><td class="mini">' + esc(f.tarifa || "—") + '</td><td class="tnum">' + num(f.potencia_contratada_kw, 1) + ' kW</td><td class="tnum">' + num(f.pico_horario_kw, 1) +
        ' kW</td><td class="tnum">' + num(f.utilizacion_pct, 0) + ' %</td><td class="tnum"><b>' + num(f.potencia_recomendada_kw, 1) + ' kW</b></td><td class="tnum" style="color:var(--ok);font-weight:800">' +
        eur(f.ahorro_potencia_eur_anio) + "</td></tr>").join("") + "</tbody></table></div>";
  } else {
    h += '<div style="padding:0 16px 16px" class="mini">Ningún suministro tiene la potencia claramente sobredimensionada (o aún no hay 6 meses de lecturas).</div>';
  }
  h += "</div>";
  h += '<div class="mini" style="margin-top:12px;color:var(--muted)">Cómo se calcula: propuesta = pico horario de los últimos 12 meses + 30 % de margen (el maxímetro de 15 minutos puede superar al pico horario), redondeada a 0,5 kW; ' +
    "ahorro = potencia que se reduce × término de potencia medio. En tarifas de 6 periodos se compara con la mayor potencia contratada. " +
    "Antes de solicitar el cambio a la comercializadora, contrastar con el maxímetro de las últimas facturas. El coste es una estimación: Datadis no facilita importes de factura.</div>";
  el.innerHTML = h;
}

/* ---------------- INFORMES ---------------- */

function textoInforme(r) {
  const partes = [];
  partes.push("En " + mesLargo(r.periodo) + " los " + r.suministros_con_datos + " suministros eléctricos municipales con lectura en Datadis consumieron " +
    num(r.consumo_mes_kwh / 1000, 1) + " MWh, con un coste estimado de " + eur(r.coste_mes_eur) +
    (r.variacion_mes_pct != null ? " (" + pct(r.variacion_mes_pct) + " frente al mes anterior" + (r.variacion_interanual_pct != null ? " y " + pct(r.variacion_interanual_pct) + " frente al mismo mes del año pasado" : "") + ")" : "") + ".");
  const tot = r.consumo_mes_kwh || 1;
  partes.push("El alumbrado público supone el " + Math.round((r.consumo_mes_alumbrado_kwh / tot) * 100) + " % del consumo y los edificios y demás dependencias el " +
    Math.round((r.consumo_mes_edificios_kwh / tot) * 100) + " %. En los últimos 12 meses el consumo ha sido de " + num(r.consumo_12m_kwh / 1000, 0) + " MWh (" + eur(r.coste_12m_eur) + " estimados).");
  if (r.contratos_a_revisar) partes.push((r.contratos_a_revisar === 1 ? "Hay 1 contrato con la potencia sobredimensionada: ajustarlo" : "Hay " + r.contratos_a_revisar + " contratos con la potencia sobredimensionada: ajustarlos") + " ahorraría unos " + eur(r.ahorro_potencia_eur_anio) + " al año.");
  if (r.cups_con_autoconsumo) partes.push(pl(r.cups_con_autoconsumo, "suministro registra", "suministros registran") + " autoconsumo (" + num(r.autoconsumo_12m_kwh / 1000, 1) + " MWh en 12 meses).");
  if (r.sin_datos_recientes) partes.push(pl(r.sin_datos_recientes, "suministro no tiene", "suministros no tienen") + " lecturas recientes en Datadis y conviene revisarlo" + (r.sin_datos_recientes === 1 ? "." : "s."));
  partes.push("Emisiones asociadas: " + num(r.co2_mes_t, 1) + " t de CO₂ en el mes.");
  return partes.join(" ");
}

async function pintarInformes(el) {
  const T = "Informes";
  cargando(el, T);
  let r;
  try { r = await cargarResumen(); } catch (e) { errorCarga(el, T, e); return; }
  if (!r.hay_datos) { vacio(el, T); return; }
  const V4 = window.__V4;
  const texto = textoInforme(r);
  let h = X().vsub(V4.ENE, T, "Informes de energía",
    "Resumen del último mes cerrado generado con los consumos reales y descargas para el Servicio de Gestión de Infraestructuras.", "");
  h += card("Resumen de " + mesLargo(r.periodo), "Texto listo para copiar en un informe o correo",
    '<p id="en-informe" style="margin:0 0 12px;font-size:13.5px;line-height:1.65">' + esc(texto) + "</p>" +
    '<button class="btn" id="en-copiar">Copiar texto</button>');
  const anexos = "/verticales/energia/anexos.xlsx";
  h += '<div style="margin-top:16px">' + card("Descargas", "Ficheros con los datos reales de Datadis",
    '<div class="kv"><span class="k"><b>Anexos I y II (Excel)</b><br><span class="mini" style="color:var(--muted)">Formato de los pliegos: CUPS con peaje, tensión y potencias; consumo por tarifa y periodo (últimos 12 meses)</span></span>' +
    '<span class="v"><button class="btn btn--sm btn--pri" onclick="__energiaDescargar(\'' + anexos + '\',\'anexos.xlsx\')">Descargar</button></span></div>' +
    '<div class="kv"><span class="k"><b>Suministros y consumos (CSV)</b><br><span class="mini" style="color:var(--muted)">Todos los CUPS con consumo del mes, variación, 12 meses, pico y potencia</span></span>' +
    '<span class="v"><button class="btn btn--sm" onclick="__energiaDescargar(\'' + BASE + '/suministros.csv\',\'suministros.csv\')">Descargar</button></span></div>' +
    '<div class="kv"><span class="k"><b>Potencia a revisar (CSV)</b><br><span class="mini" style="color:var(--muted)">Contratos sobredimensionados con la potencia propuesta y el ahorro</span></span>' +
    '<span class="v"><button class="btn btn--sm" onclick="__energiaDescargar(\'' + BASE + '/suministros.csv?tipo=revisar\',\'potencia_a_revisar.csv\')">Descargar</button></span></div>' +
    '<div class="mini" style="margin-top:8px;color:var(--muted)">Para elegir fechas o filtrar alumbrado / edificios en los Anexos, usa la tarjeta de descarga de <a class="lnk" onclick="UI.goE(\'municipio\')">Consumo del municipio</a>.</div>') + "</div>";
  el.innerHTML = h;
  el.querySelector("#en-copiar").onclick = async () => {
    try { await navigator.clipboard.writeText(texto); UI.toast && UI.toast("Texto copiado"); } catch { UI.toast && UI.toast("No se pudo copiar: selecciona el texto a mano"); }
  };
}

/* Modo presentación (sala de control): KPIs reales si ya están cargados */
window.__energiaPresentacion = function () {
  const r = resumen;
  if (!r || !r.hay_datos) return null;
  const top = (r.recomendaciones || [])[0];
  return {
    ic: "bolt",
    t: "Energía municipal",
    k: [
      ["Consumo de " + MESES_LARGO[+r.periodo.slice(5, 7) - 1], num(r.consumo_mes_kwh / 1000, 1) + " <small>MWh</small>", r.variacion_mes_pct == null ? r.suministros_con_datos + " suministros" : pct(r.variacion_mes_pct) + " frente al mes anterior"],
      ["Coste estimado", num(r.coste_mes_eur) + " <small>€</small>", num(r.precio_kwh_eur, 3) + " €/kWh medio"],
      ["Alumbrado público", num(r.consumo_mes_alumbrado_kwh / 1000, 1) + " <small>MWh</small>", Math.round((r.consumo_mes_alumbrado_kwh / (r.consumo_mes_kwh || 1)) * 100) + " % del consumo"],
      ["Potencia a revisar", num(r.contratos_a_revisar), r.contratos_a_revisar ? num(r.ahorro_potencia_eur_anio) + " €/año de ahorro" : "Contratos ajustados"],
    ],
    rec: top ? top.titulo + ". " + top.detalle : "Consumos y potencias dentro de lo esperado.",
  };
};

/* ---------------- instalación ---------------- */

function instalar() {
  const V4 = window.__V4;
  if (!V4 || !V4.ENE || !V4.ui || !window.__U) { setTimeout(instalar, 200); return; }
  const ENE = V4.ENE;
  const R = ENE.R;
  R.resumen = pintarResumen;
  R.edificios = pintarSuministros;
  R.fotovoltaica = pintarAutoconsumo;
  R.costes = pintarCostes;
  R.informes = pintarInformes;
  const nombres = { edificios: ["Suministros (CUPS)", "panel"], fotovoltaica: ["Autoconsumo", "sun"] };
  ENE.sections.forEach((s) => {
    if (nombres[s.id]) { s.n = nombres[s.id][0]; }
    if (s.id === "edificios") s.cnt = () => (resumen && resumen.hay_datos ? resumen.suministros_total : "");
    if (s.id === "costes") s.cnt = () => (resumen && resumen.contratos_a_revisar ? resumen.contratos_a_revisar : "");
  });
  ENE.pill = "Datos reales de Datadis";
  ENE.renderSidebar();
  ["resumen", "edificios", "fotovoltaica", "costes", "informes"].forEach((id) => ENE.rerender(id));
  /* contador de la barra lateral en cuanto haya sesión */
  const precargar = () => {
    if (!sessionStorage.getItem("nijar.dti.access")) { setTimeout(precargar, 1500); return; }
    cargarResumen().then((r) => {
      if (r && r.hay_datos) ENE.pill = r.suministros_total + " CUPS · Datadis";
      ENE.renderSidebar();
    }).catch(() => setTimeout(precargar, 60000));
  };
  setTimeout(precargar, 1500);
}

instalar();
