/* Registros de las verticales: listado de eventos con filtros, exportación y modo «en directo».
   Añade la sección «Registros» a Residuos, Movilidad, Seguridad y Energía (makeVertical) y
   pinta la que index.html ya reserva en Alumbrado y Agua. API: /verticales/{vertical}/registros. */

import { api, fetchAuth } from "./api-client.js?v=19";

const VERTICALES_LIGERAS = { RES: "residuos", MOV: "movilidad", SEG: "seguridad", ENE: "energia" };
const NOMBRE = {
  alumbrado: "Alumbrado público", agua: "Ciclo del agua", residuos: "Residuos",
  movilidad: "Movilidad", seguridad: "Seguridad", energia: "Energía municipal",
};
const TIPOS = { alarma: "Alarma", estado: "Cambio de estado", lectura: "Lectura", carga: "Carga de datos", incidencia: "Incidencia", sistema: "Sistema" };
const SEV = { critico: ["err", "Crítico"], aviso: ["warn", "Aviso"], info: ["info", "Info"] };
const DIRECTO_MS = 20000;
const POR_PAGINA = 50;

const estado = {}; // por vertical: filtros, página, temporizador

function esc(t) {
  return String(t == null ? "" : t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function num(n) { return Number(n || 0).toString().replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
function fechaHora(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("es-ES", { day: "2-digit", month: "2-digit", year: "2-digit" }) + " " +
    d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
function hace(iso) {
  if (!iso) return "—";
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "hace " + Math.round(s) + " s";
  if (s < 3600) return "hace " + Math.round(s / 60) + " min";
  if (s < 86400) return "hace " + Math.round(s / 3600) + " h";
  return "hace " + Math.round(s / 86400) + " d";
}
function kpi(l, v, d, cls) {
  return '<div class="stat"><div class="stat__l">' + l + '</div><div class="stat__v tnum"' + (cls ? ' style="color:var(--' + cls + ')"' : "") + ">" + v + '</div><div class="stat__d">' + d + "</div></div>";
}
function cabecera(vertical) {
  return '<div class="subhead"><div><div class="crumb"><a onclick="UI.go(\'home\')">Plataforma</a> · ' + esc(NOMBRE[vertical]) + " · <b>Registros</b></div>" +
    "<h1>Registros de " + esc(NOMBRE[vertical].toLowerCase()) + "</h1>" +
    "<p>Todo lo que pasa en la vertical, momento a momento: alarmas, cambios de estado de los activos, lecturas de sensores y cargas de datos. Filtra, exporta o activa el modo en directo.</p></div>" +
    '<div class="acts"><button class="btn" data-rg="directo">● En directo</button><button class="btn btn--pri" data-rg="csv">Exportar CSV</button></div></div>';
}
function consulta(e, conPagina) {
  const q = new URLSearchParams();
  const f = e.filtros;
  ["tipo", "severidad", "activo", "buscar"].forEach((k) => { if (f[k]) q.set(k, f[k]); });
  if (f.desde) q.set("desde", new Date(f.desde + "T00:00:00").toISOString());
  if (f.hasta) q.set("hasta", new Date(f.hasta + "T23:59:59").toISOString());
  if (!f.demo) q.set("incluir_demo", "false");
  if (conPagina) { q.set("page", e.pagina); q.set("page_size", POR_PAGINA); }
  return q.toString();
}

async function render(el, vertical) {
  const e = estado[vertical] || (estado[vertical] = {
    filtros: { tipo: "", severidad: "", activo: "", buscar: "", desde: "", hasta: "", demo: true },
    pagina: 1, directo: false, temporizador: null, vistos: new Set(),
  });
  const f = e.filtros;
  const opt = (v, t, sel) => '<option value="' + v + '"' + (sel === v ? " selected" : "") + ">" + t + "</option>";
  el.innerHTML = cabecera(vertical) +
    '<div id="rg-aviso"></div>' +
    '<div class="grid g4" style="margin-bottom:16px" id="rg-kpis"><div class="stat"><div class="stat__l">Cargando…</div></div></div>' +
    '<div class="card card--pad0"><div style="padding:16px 16px 4px" class="card__h"><div><div class="card__t">Listado de registros</div><div class="card__s" id="rg-cuenta"></div></div>' +
    '<div class="filters">' +
    '<div class="fld"><label>Buscar en el mensaje</label><input class="inp" data-f="buscar" placeholder="Texto…" value="' + esc(f.buscar) + '"></div>' +
    '<div class="fld"><label>Activo</label><input class="inp" data-f="activo" placeholder="Código o nombre…" value="' + esc(f.activo) + '" style="width:150px"></div>' +
    '<div class="fld"><label>Tipo</label><select class="sel" data-f="tipo">' + opt("", "Todos", f.tipo) +
    Object.entries(TIPOS).map(([k, t]) => opt(k, t, f.tipo)).join("") + "</select></div>" +
    '<div class="fld"><label>Severidad</label><select class="sel" data-f="severidad">' + opt("", "Todas", f.severidad) +
    opt("critico", "Crítico", f.severidad) + opt("aviso", "Aviso", f.severidad) + opt("info", "Info", f.severidad) + "</select></div>" +
    '<div class="fld"><label>Desde</label><input class="inp" type="date" data-f="desde" value="' + esc(f.desde) + '"></div>' +
    '<div class="fld"><label>Hasta</label><input class="inp" type="date" data-f="hasta" value="' + esc(f.hasta) + '"></div>' +
    '<label class="mini" style="display:flex;gap:6px;align-items:center;margin-top:16px"><input type="checkbox" data-f="demo"' + (f.demo ? " checked" : "") + "> Incluir demostración</label>" +
    '<button class="btn btn--sm" data-rg="limpiar" style="margin-top:16px">Limpiar</button>' +
    "</div></div>" +
    '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Fecha y hora</th><th>Severidad</th><th>Tipo</th><th>Activo</th><th>Mensaje</th><th>Origen</th></tr></thead>' +
    '<tbody id="rg-filas"><tr><td colspan="6" class="mini">Cargando…</td></tr></tbody></table></div>' +
    '<div class="pager"><button data-rg="ant">← Anteriores</button><span id="rg-pag"></span><button data-rg="sig">Siguientes →</button></div></div>';

  let total = 0;
  const pintarKpis = async () => {
    try {
      const r = await api.get("/verticales/" + vertical + "/registros/resumen");
      el.querySelector("#rg-kpis").innerHTML =
        kpi("Últimas 24 horas", num(r.ultimas_24h), "registros", "") +
        kpi("Críticos (24 h)", num(r.criticos_24h), "averías, pérdidas de comunicación, SOS…", r.criticos_24h ? "err" : "") +
        kpi("Avisos (24 h)", num(r.avisos_24h), "umbrales superados, lecturas fuera de rango", r.avisos_24h ? "warn" : "") +
        kpi("Último registro", hace(r.ultimo), num(r.ultimos_7d) + " en los últimos 7 días", "");
      el.querySelector("#rg-aviso").innerHTML = r.solo_demo
        ? '<div class="note" style="margin-bottom:14px">Registros de demostración: ' + esc(NOMBRE[vertical]) +
          " aún no está integrado con el sistema municipal. Cuando lo esté, aquí aparecerán sus eventos reales (los de demostración se pueden ocultar con el filtro).</div>"
        : r.total === 0
          ? '<div class="note" style="margin-bottom:14px">Aún no hay registros. Se generan solos cuando cambia el estado de un activo, llega una lectura de un sensor o se cargan datos.</div>'
          : "";
    } catch (err) {
      el.querySelector("#rg-kpis").innerHTML = '<div class="stat"><div class="stat__l" style="color:var(--err)">' + esc(err.message || err) + "</div></div>";
    }
  };
  const pintarFilas = async () => {
    const tbody = el.querySelector("#rg-filas");
    let r;
    try { r = await api.get("/verticales/" + vertical + "/registros?" + consulta(e, true) + "&_=" + Date.now()); } catch (err) {
      tbody.innerHTML = '<tr><td colspan="6" class="mini" style="color:var(--err)">' + esc(err.message || err) + "</td></tr>";
      return;
    }
    total = r.total;
    const nuevos = e.vistos.size ? r.items.filter((x) => !e.vistos.has(x.id)).length : 0;
    tbody.innerHTML = r.items.length ? r.items.map((x) => {
      const [cls, txt] = SEV[x.severidad] || ["mut", x.severidad];
      const nuevo = e.vistos.size && !e.vistos.has(x.id);
      return '<tr class="rowclick" data-id="' + esc(x.id) + '"' + (nuevo ? ' style="background:#fff8e1"' : "") + ">" +
        '<td class="tnum mini" title="' + esc(hace(x.momento)) + '">' + fechaHora(x.momento) + "</td>" +
        '<td><span class="bdg bdg-' + cls + '">' + txt + "</span></td>" +
        '<td class="mini">' + esc(TIPOS[x.tipo] || x.tipo) + "</td>" +
        "<td>" + (x.activo_codigo ? '<span class="lnk">' + esc(x.activo_codigo) + "</span>" : "—") +
        (x.activo_nombre && x.activo_nombre !== x.activo_codigo ? '<br><span class="mini">' + esc(x.activo_nombre) + "</span>" : "") + "</td>" +
        '<td style="white-space:normal;min-width:260px">' + esc(x.mensaje) + "</td>" +
        '<td class="mini">' + esc(x.origen) + (x.demo ? ' <span class="bdg bdg-mut">demo</span>' : "") + "</td></tr>";
    }).join("") : '<tr><td colspan="6" class="mini">Ningún registro coincide con los filtros.</td></tr>';
    r.items.forEach((x) => e.vistos.add(x.id));
    const paginas = Math.max(1, Math.ceil(total / POR_PAGINA));
    el.querySelector("#rg-cuenta").textContent = num(total) + " registros" + (e.directo ? " · en directo, se actualiza cada 20 s" : "") +
      (nuevos ? " · " + nuevos + " nuevos" : "");
    el.querySelector("#rg-pag").textContent = "Página " + e.pagina + " de " + paginas;
    el.querySelector('[data-rg="ant"]').disabled = e.pagina <= 1;
    el.querySelector('[data-rg="sig"]').disabled = e.pagina >= paginas;
    tbody.querySelectorAll("tr[data-id]").forEach((tr) => {
      tr.onclick = () => detalle(r.items.find((x) => x.id === tr.dataset.id), vertical);
    });
  };
  const recargar = () => { e.pagina = 1; e.vistos = new Set(); pintarFilas(); };

  let t = null;
  el.querySelectorAll("[data-f]").forEach((inp) => {
    const k = inp.dataset.f;
    const leer = () => { f[k] = inp.type === "checkbox" ? inp.checked : inp.value.trim(); };
    if (inp.tagName === "INPUT" && inp.type === "text") {
      inp.oninput = () => { leer(); clearTimeout(t); t = setTimeout(recargar, 350); };
    } else {
      inp.onchange = () => { leer(); recargar(); };
    }
  });
  el.querySelector('[data-rg="limpiar"]').onclick = () => {
    e.filtros = { tipo: "", severidad: "", activo: "", buscar: "", desde: "", hasta: "", demo: true };
    render(el, vertical);
  };
  el.querySelector('[data-rg="ant"]').onclick = () => { if (e.pagina > 1) { e.pagina--; pintarFilas(); } };
  el.querySelector('[data-rg="sig"]').onclick = () => { e.pagina++; pintarFilas(); };
  el.querySelector('[data-rg="csv"]').onclick = async () => {
    try {
      const resp = await fetchAuth("/verticales/" + vertical + "/registros.csv?" + consulta(e, false));
      if (!resp.ok) throw new Error("error " + resp.status);
      const a = document.createElement("a");
      a.href = URL.createObjectURL(await resp.blob());
      a.download = "registros_" + vertical + ".csv";
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err) { UI.toast && UI.toast("No se pudo exportar: " + (err.message || err)); }
  };
  const btnDirecto = el.querySelector('[data-rg="directo"]');
  const pintarDirecto = () => {
    btnDirecto.style.background = e.directo ? "var(--ok-bg)" : "";
    btnDirecto.style.color = e.directo ? "var(--ok)" : "";
    btnDirecto.textContent = e.directo ? "● En directo (activo)" : "● En directo";
  };
  const tick = () => {
    if (!e.directo) return;
    if (!document.body.contains(el) || el.style.display === "none" || el.offsetParent === null) {
      e.temporizador = setTimeout(tick, DIRECTO_MS); // sección oculta: no consultar
      return;
    }
    if (e.pagina === 1) { pintarFilas(); pintarKpis(); }
    e.temporizador = setTimeout(tick, DIRECTO_MS);
  };
  btnDirecto.onclick = () => {
    e.directo = !e.directo;
    clearTimeout(e.temporizador);
    pintarDirecto();
    if (e.directo) { e.pagina = 1; tick(); }
  };
  pintarDirecto();
  clearTimeout(e.temporizador);
  if (e.directo) e.temporizador = setTimeout(tick, DIRECTO_MS);
  pintarKpis();
  pintarFilas();
}

function detalle(x, vertical) {
  if (!x) return;
  const [cls, txt] = SEV[x.severidad] || ["mut", x.severidad];
  const kv = (k, v) => '<div class="kv"><span class="k">' + k + '</span><span class="v">' + v + "</span></div>";
  const datos = x.datos && Object.keys(x.datos).length
    ? '<div class="dsec"><div class="t">Datos del registro</div>' +
      Object.entries(x.datos).map(([k, v]) => kv(esc(k), esc(typeof v === "object" ? JSON.stringify(v) : v))).join("") + "</div>"
    : "";
  UI.openDrawer(esc(TIPOS[x.tipo] || x.tipo) + " · " + esc(x.activo_codigo || NOMBRE[vertical]), fechaHora(x.momento) + " · " + hace(x.momento),
    '<div class="dsec"><div class="t">Registro</div>' +
    kv("Mensaje", esc(x.mensaje)) + kv("Severidad", '<span class="bdg bdg-' + cls + '">' + txt + "</span>") +
    kv("Vertical", esc(NOMBRE[vertical])) + kv("Activo", esc(x.activo_codigo || "—")) +
    (x.activo_nombre ? kv("Nombre", esc(x.activo_nombre)) : "") +
    kv("Origen", esc(x.origen) + (x.demo ? ' <span class="bdg bdg-mut">dato de demostración</span>' : "")) + "</div>" + datos +
    '<div class="dsec"><div class="t">Otros registros de este activo</div><button class="btn btn--sm" id="rg-mismo">Filtrar por ' + esc(x.activo_codigo || "este activo") + "</button></div>");
  const b = document.getElementById("rg-mismo");
  if (b) b.onclick = () => {
    const e = estado[vertical];
    if (!e || !x.activo_codigo) return;
    e.filtros.activo = x.activo_codigo;
    UI.closeDrawer();
    const el = document.querySelector("[data-registros='" + vertical + "']");
    if (el) render(el, vertical);
  };
}

window.__registrosRender = (el, vertical) => { el.dataset.registros = vertical; return render(el, vertical); };

/* Sección «Registros» en las verticales ligeras (makeVertical) */
function instalar() {
  const V4 = window.__V4;
  if (!V4 || !V4.ENE) { setTimeout(instalar, 200); return; }
  Object.entries(VERTICALES_LIGERAS).forEach(([clave, vertical]) => {
    const cfg = V4[clave];
    if (!cfg || cfg.sections.some((s) => s.id === "registros")) return;
    const pos = cfg.sections.findIndex((s) => s.id === "informes");
    cfg.sections.splice(pos < 0 ? cfg.sections.length : pos, 0, { id: "registros", n: "Registros", i: "bell" });
    const vista = document.getElementById(cfg.view);
    const main = vista && vista.querySelector("main");
    if (main && !document.getElementById(cfg.prefix + "registros")) {
      const sec = document.createElement("section");
      sec.className = cfg.cls;
      sec.id = cfg.prefix + "registros";
      sec.style.display = "none";
      const nota = main.querySelector(".note");
      main.insertBefore(sec, nota || null);
    }
    cfg.R.registros = (el) => window.__registrosRender(el, vertical);
    cfg.renderSidebar();
  });
}
instalar();
