/**
 * Listados de interacciones de los visitantes, con filtros, búsqueda,
 * paginación, detalle y exportación a CSV (Excel):
 *
 *  - Chatbot IA (B.2) → «Conversaciones del asistente»: cada pregunta y
 *    respuesta (web, app y tótems). GET /chatbot/interacciones.
 *  - Tótems (A.1) → «Actividad de los visitantes en los tótems»: lo que se ve
 *    en cada tótem (secciones, fichas, noticias, mapa, QR, idioma…).
 *    GET /dashboards/totems/interacciones.
 *
 * Se añaden al final de esas dos secciones del panel sin tocar su contenido.
 */

import { api, tokens } from "./api-client.js?v=18";

const API_BASE = window.NIJAR_API_BASE || window.location.origin + "/api/v1";

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
const fmtFecha = (iso) => {
  const d = new Date(iso);
  return isNaN(d) ? "—" : d.toLocaleDateString("es-ES", { day: "2-digit", month: "2-digit", year: "2-digit" }) + " " +
    d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
};
const corta = (s, n) => { s = String(s ?? ""); return s.length > n ? s.slice(0, n - 1) + "…" : s; };
const fmtN = (n) => (n == null ? "—" : Number(n).toLocaleString("es-ES"));

const IDIOMAS = { es: "Español", en: "Inglés", de: "Alemán", fr: "Francés" };
const CANALES = { web: "Web", app: "App", totem: "Tótem" };
const CONFIANZA = { alta: "Alta", media: "Media", fuera_de_dominio: "Sin respuesta" };
const nombreTotem = (t) => (t ? t.charAt(0).toUpperCase() + t.slice(1) : "—");

const EVENTOS = {
  inicio_sesion: "Inicio de sesión", fin_sesion: "Fin de sesión", seccion: "Abre una sección",
  ficha: "Ve una ficha", noticia: "Lee una noticia", mapa: "Abre el mapa", mapa_punto: "Pulsa un punto del mapa",
  chatbot: "Abre el asistente", pregunta_chatbot: "Pregunta al asistente", qr: "Muestra un QR",
  idioma: "Cambia de idioma", accesibilidad: "Accesibilidad", redes: "Redes sociales",
  ruta_planificada: "Planifica una ruta", recomendaciones: "Pide recomendaciones", interaccion: "Interacción (demo)",
  valoracion_chatbot: "Valora el asistente", explorar: "Abre Explorar",
};
const SECCIONES = {
  playas: "Playas y calas", cabo: "Cabo de Gata", rutas: "Rutas y senderos", naturaleza: "Naturaleza",
  ceramica: "Cerámica y jarapas", gastronomia: "Gastronomía", empresas: "Empresas y servicios",
  eventos: "Agenda", noticias: "Noticias", mapa: "Mapa", chatbot: "Asistente IA", redes: "Redes sociales",
  general: "General", idioma: "Idioma", rutas_planificador: "Planificador", accesibilidad: "Accesibilidad",
};

/* ---------------- piezas comunes ---------------- */

function fld(label, control) {
  return '<div class="fld"><label>' + esc(label) + "</label>" + control + "</div>";
}
function select(id, opciones, todas = "Todos") {
  return '<select class="sel" data-f="' + id + '"><option value="">' + esc(todas) + "</option>" +
    opciones.map(([v, t]) => '<option value="' + esc(v) + '">' + esc(t) + "</option>").join("") + "</select>";
}
function opcionesFaceta(faceta, nombres) {
  return Object.entries(faceta || {}).filter(([v]) => v && v !== "—")
    .map(([v, n]) => [v, (nombres ? nombres(v) : v) + " (" + n + ")"]);
}
function resumenChip(etq, valor) {
  return '<span class="bdg bdg-mut" style="font-size:12px;padding:5px 10px">' + esc(etq) + ": <b>" + esc(valor) + "</b></span>";
}

/** Descarga con el token de sesión (un <a href> no lo enviaría). */
async function descargar(ruta, params, nombre) {
  const r = await fetch(API_BASE + ruta + "?" + params, { headers: { Authorization: "Bearer " + tokens.access } });
  if (!r.ok) throw new Error("Error " + r.status + " al exportar");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(await r.blob());
  a.download = nombre;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
}

/**
 * Listado genérico: tarjeta con filtros, resumen, tabla y paginador.
 * cfg: { titulo, sub, ruta, rutaExport, nombreExport, filtros(f) → html,
 *        cabecera, fila(item, i), resumen(data) → html, vacio(params) → html,
 *        alPulsar(item), despues(data, el) }
 */
function montarListado(cont, cfg) {
  const estado = { page: 1, page_size: 25, orden: "reciente", f: {}, data: null, cargando: false };
  cont.innerHTML = '<div class="card card--pad0" style="margin-top:16px">' +
    '<div style="padding:16px 16px 4px" class="card__h"><div><div class="card__t">' + esc(cfg.titulo) + '</div><div class="card__s">' + esc(cfg.sub) + "</div></div>" +
    '<div class="chip-row"><button class="btn btn--sm" data-a="csv">⭳ Exportar CSV</button></div></div>' +
    '<div style="padding:8px 16px 4px"><div class="filters" data-zona="filtros"></div>' +
    '<div class="chip-row" style="margin-top:10px;align-items:center;gap:8px">' +
    '<input class="inp" data-f="q" placeholder="Buscar…" style="min-width:240px;flex:1;max-width:420px">' +
    '<label class="mini" style="display:flex;gap:6px;align-items:center"><input type="checkbox" data-f="incluir_demo"> Incluir datos de demostración</label>' +
    '<button class="btn btn--sm btn--pri" data-a="buscar">Aplicar</button><button class="btn btn--sm btn--ghost" data-a="limpiar">Limpiar</button></div>' +
    '<div data-zona="resumen" class="chip-row" style="margin-top:12px;gap:6px"></div></div>' +
    '<div class="tbl-wrap"><table class="tbl"><thead><tr>' + cfg.cabecera.map((c) => "<th>" + esc(c) + "</th>").join("") +
    '</tr></thead><tbody data-zona="filas"></tbody></table></div>' +
    '<div class="pager" data-zona="pager"></div><div data-zona="extra" style="padding:0 16px 16px"></div></div>';
  const $ = (s) => cont.querySelector(s);

  const leerFiltros = () => {
    const f = {};
    cont.querySelectorAll("[data-f]").forEach((c) => {
      const v = c.type === "checkbox" ? (c.checked ? "true" : "") : c.value.trim();
      if (v) f[c.dataset.f] = v;
    });
    return f;
  };
  const params = (extra = {}) => {
    const p = new URLSearchParams();
    Object.entries({ ...estado.f, ...extra }).forEach(([k, v]) => v !== "" && v != null && p.set(k, v));
    return p.toString();
  };

  async function cargar() {
    estado.cargando = true;
    $('[data-zona="filas"]').innerHTML = '<tr><td colspan="' + cfg.cabecera.length + '" class="mini" style="text-align:center;padding:22px;color:var(--muted)">Cargando…</td></tr>';
    let data;
    try {
      data = await api.get(cfg.ruta + "?" + params({ page: estado.page, page_size: estado.page_size, orden: estado.orden }));
    } catch (e) {
      const msg = e && e.status === 403 ? "Tu perfil no tiene acceso a este listado." : "No se ha podido cargar el listado (" + esc(e && e.message || e) + ").";
      $('[data-zona="filas"]').innerHTML = '<tr><td colspan="' + cfg.cabecera.length + '" class="mini" style="text-align:center;padding:22px;color:var(--muted)">' + msg + "</td></tr>";
      return;
    } finally { estado.cargando = false; }
    estado.data = data;
    pintarFiltros(data);
    $('[data-zona="resumen"]').innerHTML = cfg.resumen(data);
    $('[data-zona="filas"]').innerHTML = data.items.length
      ? data.items.map((it, i) => cfg.fila(it, i)).join("")
      : '<tr><td colspan="' + cfg.cabecera.length + '" class="mini" style="text-align:center;padding:22px;color:var(--muted);white-space:normal">' + cfg.vacio(estado.f) + "</td></tr>";
    $('[data-zona="filas"]').querySelectorAll("tr[data-i]").forEach((tr) => {
      tr.onclick = () => cfg.alPulsar(data.items[Number(tr.dataset.i)], recargarCon);
    });
    const paginas = Math.max(1, Math.ceil(data.total / estado.page_size));
    $('[data-zona="pager"]').innerHTML =
      '<button data-a="ant"' + (estado.page <= 1 ? " disabled" : "") + ">‹ Anterior</button>" +
      "<span>Página <b>" + estado.page + "</b> de " + paginas + " · " + fmtN(data.total) + " registros</span>" +
      '<button data-a="sig"' + (estado.page >= paginas ? " disabled" : "") + ">Siguiente ›</button>" +
      '<span style="margin-left:auto">Por página <select class="sel" data-p="page_size" style="height:28px">' +
      [25, 50, 100, 200].map((n) => "<option" + (n === estado.page_size ? " selected" : "") + ">" + n + "</option>").join("") +
      "</select></span>" +
      '<span>Orden <select class="sel" data-p="orden" style="height:28px">' +
      cfg.ordenes.map(([v, t]) => '<option value="' + v + '"' + (v === estado.orden ? " selected" : "") + ">" + t + "</option>").join("") + "</select></span>";
    if (cfg.despues) cfg.despues(data, $('[data-zona="extra"]'), recargarCon);
  }

  function pintarFiltros(data) {
    // Las opciones salen de los datos (facetas); se conserva lo elegido
    const prev = leerFiltros();
    $('[data-zona="filtros"]').innerHTML =
      fld("Desde", '<input class="inp" type="date" data-f="desde">') +
      fld("Hasta", '<input class="inp" type="date" data-f="hasta">') + cfg.filtros(data.facetas || {});
    cont.querySelectorAll('[data-zona="filtros"] [data-f]').forEach((c) => {
      if (prev[c.dataset.f] != null) {
        if (c.tagName === "SELECT" && ![...c.options].some((o) => o.value === prev[c.dataset.f])) {
          c.insertAdjacentHTML("beforeend", '<option value="' + esc(prev[c.dataset.f]) + '">' + esc(prev[c.dataset.f]) + "</option>");
        }
        c.value = prev[c.dataset.f];
      }
      c.onchange = aplicar;
    });
  }

  function aplicar() { estado.f = leerFiltros(); estado.page = 1; cargar(); }
  function recargarCon(filtros) {
    Object.entries(filtros).forEach(([k, v]) => {
      let c = cont.querySelector('[data-f="' + k + '"]');
      if (c && c.tagName === "SELECT" && ![...c.options].some((o) => o.value === v)) {
        c.insertAdjacentHTML("beforeend", '<option value="' + esc(v) + '">' + esc(v) + "</option>");
      }
      if (c) { if (c.type === "checkbox") c.checked = !!v; else c.value = v; }
    });
    aplicar();
  }

  cont.addEventListener("click", async (e) => {
    const b = e.target.closest("[data-a]");
    if (!b || estado.cargando) return;
    const a = b.dataset.a;
    if (a === "buscar") aplicar();
    else if (a === "limpiar") {
      cont.querySelectorAll("[data-f]").forEach((c) => { if (c.type === "checkbox") c.checked = false; else c.value = ""; });
      aplicar();
    } else if (a === "ant") { estado.page--; cargar(); }
    else if (a === "sig") { estado.page++; cargar(); }
    else if (a === "csv") {
      b.disabled = true;
      try {
        await descargar(cfg.rutaExport, params({ orden: estado.orden }), cfg.nombreExport());
        window.UI && UI.toast("CSV exportado con los filtros aplicados");
      } catch (err) { window.UI && UI.toast(String(err.message || err)); }
      b.disabled = false;
    }
  });
  cont.addEventListener("change", (e) => {
    const p = e.target.closest("[data-p]");
    if (!p) return;
    estado[p.dataset.p] = p.dataset.p === "page_size" ? Number(p.value) : p.value;
    estado.page = 1;
    cargar();
  });
  $('[data-f="q"]').addEventListener("keydown", (e) => { if (e.key === "Enter") aplicar(); });
  $('[data-f="incluir_demo"]').addEventListener("change", aplicar);
  cargar();
}

/* ================= CHATBOT ================= */

function badgeConfianza(n) {
  const cls = n === "alta" ? "bdg-ok" : n === "media" ? "bdg-info" : "bdg-warn";
  return '<span class="bdg ' + cls + '">' + esc(CONFIANZA[n] || n) + "</span>";
}
function badgeUtil(u) {
  return u === true ? '<span class="bdg bdg-ok">útil</span>' : u === false ? '<span class="bdg bdg-err">no útil</span>' : '<span class="mini" style="color:var(--muted)">—</span>';
}
const canalTxt = (it) => (it.canal === "totem" ? "Tótem " + nombreTotem(it.totem) : CANALES[it.canal] || it.canal);

function detalleChat(it, recargarCon) {
  const html =
    '<div class="dsec"><div class="t">Pregunta</div><p style="margin:0;font-size:14px;line-height:1.55">' + esc(it.pregunta) + "</p></div>" +
    '<div class="dsec"><div class="t">Respuesta del asistente</div><p style="margin:0;font-size:14px;line-height:1.55;white-space:pre-wrap">' + esc(it.respuesta) + "</p></div>" +
    '<div class="dsec"><div class="t">Datos</div>' +
    '<div class="kv"><span class="k">Fecha</span><span class="v tnum">' + fmtFecha(it.fecha) + "</span></div>" +
    '<div class="kv"><span class="k">Canal · idioma</span><span class="v">' + esc(canalTxt(it)) + " · " + esc(IDIOMAS[it.idioma] || it.idioma) + "</span></div>" +
    '<div class="kv"><span class="k">Intención detectada</span><span class="v">' + esc(it.intent_detectado || "—") + "</span></div>" +
    '<div class="kv"><span class="k">Confianza</span><span class="v">' + badgeConfianza(it.nivel_confianza) + (it.score_confianza != null ? ' <span class="mini tnum">' + it.score_confianza.toFixed(2) + "</span>" : "") + "</span></div>" +
    '<div class="kv"><span class="k">Valoración</span><span class="v">' + badgeUtil(it.util) + (it.comentario ? ' <span class="mini">«' + esc(it.comentario) + "»</span>" : "") + "</span></div>" +
    '<div class="kv"><span class="k">Tiempo de respuesta</span><span class="v tnum">' + (it.latencia_ms != null ? fmtN(it.latencia_ms) + " ms" : "—") + "</span></div>" +
    ((it.fuentes || []).length ? '<div class="kv"><span class="k">Fuentes</span><span class="v mini" style="white-space:normal">' + it.fuentes.map((f) => esc(f.descripcion || f.referencia || f.tipo)).join(" · ") + "</span></div>" : "") +
    '<div class="kv"><span class="k">Sesión</span><span class="v mini">' + esc(it.sesion_id) + (it.demo ? ' <span class="bdg bdg-mut">demo</span>' : "") + "</span></div></div>" +
    '<div class="dsec"><div class="t">Conversación completa</div><div id="chat-conv" class="mini" style="color:var(--muted)">Cargando…</div>' +
    '<div class="chip-row" style="margin-top:10px"><button class="btn btn--sm" id="chat-filtrar-sesion">Filtrar el listado por esta sesión</button></div></div>';
  UI.openDrawer("Conversación del asistente", fmtFecha(it.fecha) + " · " + esc(canalTxt(it)), html);
  const btn = document.getElementById("chat-filtrar-sesion");
  if (btn) btn.onclick = () => { UI.closeDrawer && UI.closeDrawer(); recargarCon({ sesion: it.sesion_id, incluir_demo: it.demo ? "true" : "" }); };
  api.get("/chatbot/interacciones/sesion/" + encodeURIComponent(it.sesion_id)).then((conv) => {
    const c = document.getElementById("chat-conv");
    if (!c) return;
    c.style.color = "";
    c.innerHTML = conv.map((m) =>
      '<div style="margin:0 0 10px"><div class="mini tnum" style="color:var(--muted)">' + fmtFecha(m.fecha) + "</div>" +
      '<div style="background:var(--bg);border-radius:10px;padding:8px 10px;margin:3px 0;' + (m.id === it.id ? "outline:2px solid var(--blue)" : "") + '"><b>Visitante:</b> ' + esc(m.pregunta) + "</div>" +
      '<div style="padding:4px 10px;white-space:pre-wrap"><b>Asistente:</b> ' + esc(m.respuesta) + "</div></div>").join("") || "Sin más mensajes.";
  }).catch(() => { const c = document.getElementById("chat-conv"); if (c) c.textContent = "No se ha podido cargar la conversación."; });
}

function montarChatbot(cont) {
  montarListado(cont, {
    titulo: "Conversaciones del asistente",
    sub: "Cada pregunta de los usuarios (web, app y tótems) con la respuesta del asistente · pulsa una fila para ver la conversación completa",
    ruta: "/chatbot/interacciones",
    rutaExport: "/chatbot/interacciones/export",
    nombreExport: () => "conversaciones_asistente_" + new Date().toISOString().slice(0, 10) + ".csv",
    cabecera: ["Fecha", "Canal", "Idioma", "Pregunta", "Respuesta", "Intención", "Confianza", "Valoración"],
    ordenes: [["reciente", "Más recientes"], ["antiguo", "Más antiguas"], ["confianza", "Menor confianza"], ["latencia", "Más lentas"]],
    filtros: (fa) =>
      fld("Canal", select("canal", opcionesFaceta(fa.canal, (v) => CANALES[v] || v))) +
      fld("Tótem", select("totem", opcionesFaceta(fa.totem, nombreTotem))) +
      fld("Idioma", select("idioma", opcionesFaceta(fa.idioma, (v) => IDIOMAS[v] || v))) +
      fld("Intención", select("intent", opcionesFaceta(fa.intent), "Todas")) +
      fld("Confianza", select("nivel", Object.entries(CONFIANZA), "Todas")) +
      fld("Valoración", select("util", [["si", "Útil"], ["no", "No útil"], ["sin", "Sin valorar"]], "Todas")),
    resumen: (d) => {
      const r = d.resumen;
      const val = r.utiles + r.no_utiles;
      return resumenChip("Preguntas", fmtN(r.interacciones)) + resumenChip("Sesiones", fmtN(r.sesiones)) +
        resumenChip("Sin respuesta", fmtN(r.sin_respuesta) + (r.interacciones ? " (" + Math.round(r.sin_respuesta / r.interacciones * 100) + "%)" : "")) +
        resumenChip("Valoradas útiles", val ? Math.round(r.utiles / val * 100) + "% de " + fmtN(val) : "—") +
        resumenChip("Respuesta media", r.latencia_media_ms != null ? fmtN(Math.round(r.latencia_media_ms)) + " ms" : "—");
    },
    fila: (it, i) =>
      '<tr class="rowclick" data-i="' + i + '"><td class="mini tnum" style="white-space:nowrap">' + fmtFecha(it.fecha) + "</td>" +
      '<td class="mini">' + esc(canalTxt(it)) + (it.demo ? ' <span class="bdg bdg-mut">demo</span>' : "") + "</td>" +
      '<td class="mini">' + esc((it.idioma || "").toUpperCase()) + "</td>" +
      '<td style="white-space:normal;min-width:200px;font-weight:600">' + esc(corta(it.pregunta, 140)) + "</td>" +
      '<td class="mini" style="white-space:normal;min-width:220px;color:var(--muted)">' + esc(corta(it.respuesta, 160)) + "</td>" +
      '<td class="mini">' + esc(it.intent_detectado || "—") + "</td><td>" + badgeConfianza(it.nivel_confianza) + "</td><td>" + badgeUtil(it.util) + "</td></tr>",
    vacio: (f) => f.incluir_demo ? "No hay conversaciones con estos filtros."
      : "No hay conversaciones reales con estos filtros. Marca «Incluir datos de demostración» para ver también las de ejemplo.",
    alPulsar: detalleChat,
  });
}

/* ================= TÓTEM ================= */

const eventoTxt = (e) => EVENTOS[e] || (e ? e.replace(/_/g, " ") : "—");
const seccionTxt = (s) => SECCIONES[s] || (s || "—");

function detalleTotem(it, recargarCon) {
  const html =
    '<div class="dsec"><div class="t">Acción</div>' +
    '<div class="kv"><span class="k">Fecha</span><span class="v tnum">' + fmtFecha(it.fecha) + "</span></div>" +
    '<div class="kv"><span class="k">Tótem · idioma</span><span class="v">' + esc(nombreTotem(it.totem)) + " · " + esc(IDIOMAS[it.idioma] || it.idioma || "—") + "</span></div>" +
    '<div class="kv"><span class="k">Acción</span><span class="v">' + esc(eventoTxt(it.evento)) + "</span></div>" +
    '<div class="kv"><span class="k">Sección</span><span class="v">' + esc(seccionTxt(it.seccion)) + "</span></div>" +
    (it.contenido ? '<div class="kv"><span class="k">Contenido</span><span class="v" style="white-space:normal">' + esc(it.contenido) + "</span></div>" : "") +
    (it.detalle ? '<div class="kv"><span class="k">Detalle</span><span class="v mini" style="white-space:normal;word-break:break-all">' + esc(it.detalle) + "</span></div>" : "") +
    (it.duracion_seg != null ? '<div class="kv"><span class="k">Duración de la sesión</span><span class="v tnum">' + fmtN(Math.round(it.duracion_seg)) + " s</span></div>" : "") +
    "</div>" +
    (it.sesion ? '<div class="dsec"><div class="t">Recorrido del visitante (sesión)</div><div id="tot-recorrido" class="mini" style="color:var(--muted)">Cargando…</div>' +
      '<div class="chip-row" style="margin-top:10px"><button class="btn btn--sm" id="tot-filtrar-sesion">Filtrar el listado por esta sesión</button></div></div>'
      : '<div class="dsec mini" style="color:var(--muted)">Registro de demostración: sin recorrido de sesión.</div>');
  UI.openDrawer("Actividad en el tótem", fmtFecha(it.fecha) + " · " + esc(nombreTotem(it.totem)), html);
  if (!it.sesion) return;
  const btn = document.getElementById("tot-filtrar-sesion");
  if (btn) btn.onclick = () => { UI.closeDrawer && UI.closeDrawer(); recargarCon({ sesion: it.sesion }); };
  api.get("/dashboards/totems/interacciones/sesion/" + encodeURIComponent(it.sesion)).then((pasos) => {
    const c = document.getElementById("tot-recorrido");
    if (!c) return;
    c.style.color = "";
    c.innerHTML = '<ol style="margin:0;padding-left:18px;line-height:1.7">' + pasos.map((p) =>
      "<li" + (p.id === it.id ? ' style="font-weight:800"' : "") + '><span class="tnum" style="color:var(--muted)">' +
      new Date(p.fecha).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit" }) + "</span> · " +
      esc(eventoTxt(p.evento)) + (p.seccion ? " · " + esc(seccionTxt(p.seccion)) : "") + (p.contenido ? " · <i>" + esc(corta(p.contenido, 80)) + "</i>" : "") +
      (p.evento === "idioma" || p.evento === "accesibilidad" || p.evento === "pregunta_chatbot" ? " · " + esc(corta(p.detalle, 80)) : "") +
      (p.duracion_seg != null ? " · " + Math.round(p.duracion_seg) + " s" : "") + "</li>").join("") + "</ol>";
  }).catch(() => { const c = document.getElementById("tot-recorrido"); if (c) c.textContent = "No se ha podido cargar el recorrido."; });
}

function montarTotem(cont) {
  montarListado(cont, {
    titulo: "Actividad de los visitantes en los tótems",
    sub: "Lo que ve cada visitante: secciones, fichas, noticias, mapa, QR, idioma y preguntas al asistente · pulsa una fila para ver su recorrido",
    ruta: "/dashboards/totems/interacciones",
    rutaExport: "/dashboards/totems/interacciones/export",
    nombreExport: () => "actividad_totems_" + new Date().toISOString().slice(0, 10) + ".csv",
    cabecera: ["Fecha", "Tótem", "Acción", "Sección", "Contenido", "Detalle", "Idioma"],
    ordenes: [["reciente", "Más recientes"], ["antiguo", "Más antiguas"]],
    filtros: (fa) =>
      fld("Tótem", select("totem", opcionesFaceta(fa.totem, nombreTotem))) +
      fld("Acción", select("evento", opcionesFaceta(fa.evento, eventoTxt), "Todas")) +
      fld("Sección", select("seccion", opcionesFaceta(fa.seccion, seccionTxt), "Todas")) +
      fld("Idioma", select("idioma", opcionesFaceta(fa.idioma, (v) => IDIOMAS[v] || v))),
    resumen: (d) => {
      const r = d.resumen;
      return resumenChip("Acciones", fmtN(r.interacciones)) + resumenChip("Visitantes (sesiones)", fmtN(r.sesiones)) +
        resumenChip("Duración media de sesión", r.duracion_media_seg != null ? fmtN(Math.round(r.duracion_media_seg)) + " s" : "—");
    },
    fila: (it, i) =>
      '<tr class="rowclick" data-i="' + i + '"><td class="mini tnum" style="white-space:nowrap">' + fmtFecha(it.fecha) + "</td>" +
      '<td class="mini">' + esc(nombreTotem(it.totem)) + (it.demo ? ' <span class="bdg bdg-mut">demo</span>' : "") + "</td>" +
      '<td style="font-weight:600">' + esc(eventoTxt(it.evento)) + "</td>" +
      '<td class="mini">' + esc(seccionTxt(it.seccion)) + "</td>" +
      '<td style="white-space:normal;min-width:180px">' + esc(corta(it.contenido || "", 90)) + "</td>" +
      '<td class="mini" style="white-space:normal;max-width:260px;color:var(--muted);word-break:break-word">' +
      esc(corta(it.evento === "fin_sesion" && it.duracion_seg != null ? Math.round(it.duracion_seg) + " s · " + (it.detalle || "") : it.detalle || "", 90)) + "</td>" +
      '<td class="mini">' + esc((it.idioma || "").toUpperCase()) + "</td></tr>",
    vacio: (f) => f.incluir_demo ? "No hay actividad con estos filtros."
      : "Aún no hay actividad real con estos filtros. Los tótems la envían desde la versión 31 del tótem; marca «Incluir datos de demostración» para ver los ejemplos.",
    alPulsar: detalleTotem,
    despues: (d, extra, recargarCon) => {
      const top = d.resumen.contenidos_top || [];
      extra.innerHTML = top.length
        ? '<div class="card__t" style="font-size:13px;margin:6px 0 8px">Contenidos más vistos (con los filtros aplicados)</div><div class="bars">' +
          top.map((c) => {
            const max = top[0].vistas || 1;
            return '<div class="bar-row" style="display:grid;grid-template-columns:minmax(160px,320px) 1fr 40px;gap:10px;align-items:center;margin:4px 0;cursor:pointer" data-q="' + esc(c.contenido) + '">' +
              '<span class="mini" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="' + esc(c.contenido) + '">' + esc(c.contenido) + ' <span style="color:var(--muted)">· ' + esc(seccionTxt(c.seccion)) + "</span></span>" +
              '<span style="height:8px;border-radius:5px;background:var(--line)"><span style="display:block;height:8px;border-radius:5px;background:var(--blue);width:' + Math.round(c.vistas / max * 100) + '%"></span></span>' +
              '<span class="mini tnum" style="text-align:right">' + c.vistas + "</span></div>";
          }).join("") + "</div>"
        : "";
      extra.querySelectorAll("[data-q]").forEach((r) => (r.onclick = () => recargarCon({ q: r.dataset.q })));
    },
  });
}

/* ---------------- registro ---------------- */

(function init() {
  const DTI = window.__DTI, UI = window.UI;
  if (!DTI || !DTI.DR || !DTI.DR.chatbot || !DTI.DR.totems || !UI) return setTimeout(init, 300);
  const envolver = (id, montar) => {
    const original = DTI.DR[id];
    if (original.__conListado) return;
    const nuevo = function (el) {
      original.apply(this, arguments);
      const cont = document.createElement("div");
      el.appendChild(cont);
      montar(cont);
    };
    nuevo.__conListado = true;
    DTI.DR[id] = nuevo;
    UI.rerenderD && UI.rerenderD(id);
  };
  envolver("chatbot", montarChatbot);
  envolver("totems", montarTotem);
})();
