/**
 * Lógica de la interfaz del tótem turístico — rediseño v4 (Totem_Pantallas_v4).
 *
 * - Vistas: inicio (grid de categorías con conteos reales), listado por
 *   categoría con miniaturas, agenda de eventos por días, asistente IA
 *   conversacional, mapa del destino (Leaflet) y ficha de detalle.
 * - i18n a 4 idiomas, entrada/salida de voz, alto contraste y texto grande.
 * - Carga desde la API pública de la plataforma; sin backend cae al demo.
 * - Inactividad >60 s: vuelve al inicio en español (modo público).
 */

import { I18N, translateAll } from "./i18n.js?v=4";
import { DEMO_RESOURCES, DEMO_EVENTS, answerChatbotDemo } from "./demo-data.js";

// ============================================================
// Configuración
// ============================================================
const API_BASE = window.NIJAR_API_BASE
  || (window.location.origin.startsWith("http")
    ? `${window.location.origin}/api/v1`
    : "http://localhost:8000/api/v1");

const TOTEM_ID = document.body.dataset.totemId || "urn:ngsi-ld:Totem:nijar:rodalquilar";
const TOTEM_LAT = parseFloat(document.body.dataset.totemLat || "36.847");
const TOTEM_LON = parseFloat(document.body.dataset.totemLon || "-2.041");
const IDLE_MS = 60_000;

const VOICE_LOCALE = { es: "es-ES", en: "en-GB", de: "de-DE", fr: "fr-FR" };

// Categorías del home (diseño v4) → fuentes de datos reales
const CATS = [
  { id: "playas", icon: "🏖️", ic: "ic-sky", th: "th-playa", label: "categorias.playas", cnt: "count.lugares", res: ["playa"] },
  { id: "rutas", icon: "🥾", ic: "ic-sun", th: "th-ruta", label: "categorias.rutas", cnt: "count.rutas", res: ["ruta"] },
  { id: "patrimonio", icon: "🏛️", ic: "ic-sand", th: "th-patrimonio", label: "categorias.patrimonio", cnt: "count.sitios", res: ["monumento", "museo", "yacimiento"] },
  { id: "naturaleza", icon: "🌿", ic: "ic-green", th: "th-naturaleza", label: "categorias.naturaleza", cnt: "count.sitios", res: ["parque_natural", "mirador"] },
  { id: "gastronomia", icon: "🍽️", ic: "ic-rose", th: "th-gastro", label: "categorias.gastronomia", cnt: "count.sitios", srv: ["gastronomia_restaurante", "gastronomia_bar", "gastronomia_cafeteria"] },
  { id: "eventos", icon: "🎉", ic: "ic-violet", th: "th-evento", label: "categorias.eventos", cnt: "count.semana", events: true },
  { id: "alojamiento", icon: "🏠", ic: "ic-blue", th: "th-servicio", label: "categorias.alojamiento", cnt: "count.sitios", srv: ["alojamiento_hotel", "alojamiento_apartamento", "alojamiento_rural", "alojamiento_camping"] },
  { id: "artesania", icon: "🏺", ic: "ic-orange", th: "th-gastro", label: "categorias.artesania", cnt: "count.talleres", srv: ["comercio", "ocio_actividad", "ocio_alquiler"] },
  { id: "servicios", icon: "ℹ️", ic: "ic-gray", th: "th-servicio", label: "categorias.servicios", cnt: "count.sitios", res: ["oficina_turismo", "centro_visitantes", "punto_interes"], emergencias: true },
];

// ============================================================
// Estado
// ============================================================
let currentLang = localStorage.getItem("totem.lang") || "es";
let currentCat = null;
let currentChip = "todas";
let idleTimer = null;
let sessionId = `totem-${TOTEM_ID}-${Date.now()}`;
let serviciosCache = null;      // /tourism/services (se agrupa por tipo en cliente)
let mapaLeaflet = null;
let lastAnswer = "";

const $ = (s) => document.querySelector(s);
const dict = () => I18N[currentLang] || I18N.es;

// ============================================================
// Router de vistas
// ============================================================
const VIEWS = ["view-home", "view-list", "view-chat", "view-map"];
function showView(id) {
  VIEWS.forEach((v) => {
    const el = document.getElementById(v);
    if (!el) return;
    el.classList.toggle("is-on", v === id);
    el.hidden = v !== id;
  });
  window.scrollTo({ top: 0 });
  resetIdle();
}
document.querySelectorAll("[data-back]").forEach((b) => b.addEventListener("click", () => showView("view-home")));
$("#btn-home-brand").addEventListener("click", () => showView("view-home"));
$("#btn-open-chat").addEventListener("click", () => { showView("view-chat"); $("#chatbot-input").focus(); });
$("#btn-open-map").addEventListener("click", abrirMapa);

// ============================================================
// i18n y selector de idioma
// ============================================================
function applyLanguage(lang) {
  currentLang = lang;
  localStorage.setItem("totem.lang", lang);
  translateAll(lang);
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.setAttribute("aria-pressed", String(btn.dataset.lang === lang));
  });
  renderHomeCats();
  pintarFechas();
  const listaVisible = !document.getElementById("view-list").hidden;
  if (currentCat && listaVisible) abrirCategoria(currentCat, currentChip);
  resetChat();
}
document.querySelectorAll(".lang-btn").forEach((btn) => {
  btn.addEventListener("click", () => applyLanguage(btn.dataset.lang));
});

// ============================================================
// Accesibilidad: texto grande, contraste, skip
// ============================================================
const textBtn = $("#text-size-toggle");
textBtn.addEventListener("click", () => {
  const on = document.body.classList.toggle("text-lg-mode");
  textBtn.setAttribute("aria-pressed", String(on));
});
function toggleContrast() {
  const on = document.body.classList.toggle("high-contrast");
  $("#contrast-toggle").setAttribute("aria-pressed", String(on));
  $("#footer-contrast").setAttribute("aria-pressed", String(on));
}
$("#contrast-toggle").addEventListener("click", toggleContrast);
$("#footer-contrast").addEventListener("click", toggleContrast);
$("#footer-voice").addEventListener("click", () => { if (lastAnswer) hablar(lastAnswer); });

// ============================================================
// Reloj y fecha
// ============================================================
function updateClock() {
  const now = new Date();
  $("#clock").textContent = now.toLocaleTimeString(currentLang, { hour: "2-digit", minute: "2-digit", hour12: false });
}
function pintarFechas() {
  const now = new Date();
  const larga = now.toLocaleDateString(currentLang, { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  $("#footer-date").textContent = larga;
  $("#header-date-pill").textContent = now.toLocaleDateString(currentLang, { weekday: "long", day: "numeric", month: "long" });
}
setInterval(updateClock, 1000);
updateClock();
pintarFechas();

// ============================================================
// API helpers
// ============================================================
async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function getServicios() {
  if (serviciosCache) return serviciosCache;
  try {
    const data = await apiGet("/tourism/services?page=1&page_size=100");
    serviciosCache = data.items || [];
  } catch { serviciosCache = []; }
  return serviciosCache;
}

function haversineKm(lat, lon) {
  const R = 6371, rad = Math.PI / 180;
  const dLat = (lat - TOTEM_LAT) * rad, dLon = (lon - TOTEM_LON) * rad;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(TOTEM_LAT * rad) * Math.cos(lat * rad) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function extractLatLon(item) {
  const lat = item.latitud ?? item.lat;
  const lon = item.longitud ?? item.lon ?? item.lng;
  if (typeof lat === "number" && typeof lon === "number") return [lat, lon];
  const coords = item.ubicacion?.coordinates || item.geometry?.coordinates;
  if (Array.isArray(coords) && coords.length >= 2) return [coords[1], coords[0]];
  return null;
}

// ============================================================
// HOME: grid de categorías con conteos reales
// ============================================================
const catCounts = {};

function renderHomeCats() {
  const t = dict();
  $("#home-cats").innerHTML = CATS.map((c) => `
    <button class="tt-cat" role="listitem" data-cat="${c.id}" aria-label="${escapeHtml(t[c.label] || c.id)}">
      <span class="tt-cat-icon ${c.ic}" aria-hidden="true">${c.icon}</span>
      <h3>${escapeHtml(t[c.label] || capitalize(c.id))}</h3>
      <small>${catCounts[c.id] != null ? `${catCounts[c.id]} ${t[c.cnt] || ""}` : "…"}</small>
    </button>`).join("");
  document.querySelectorAll(".tt-cat").forEach((b) =>
    b.addEventListener("click", () => abrirCategoria(b.dataset.cat)));
}

async function cargarConteos() {
  const servicios = await getServicios();
  await Promise.all(CATS.map(async (c) => {
    try {
      if (c.events) {
        const d = await apiGet("/tourism/events?publicado=true&page_size=1");
        catCounts[c.id] = d.total ?? 0;
      } else if (c.srv) {
        catCounts[c.id] = servicios.filter((s) => c.srv.includes(s.tipo)).length;
      } else {
        const totales = await Promise.all(c.res.map(async (cat) => {
          const d = await apiGet(`/tourism/resources?categoria=${cat}&publicado=true&page_size=1`);
          return d.total ?? 0;
        }));
        catCounts[c.id] = totales.reduce((a, b) => a + b, 0);
      }
    } catch { catCounts[c.id] = (DEMO_RESOURCES[c.id] || []).length || 0; }
  }));
  renderHomeCats();
}

// ============================================================
// LISTADOS por categoría
// ============================================================
async function abrirCategoria(catId, chip = "todas") {
  const c = CATS.find((x) => x.id === catId);
  if (!c) return;
  currentCat = catId;
  currentChip = chip;
  const t = dict();

  $("#list-title").textContent = c.events && chip !== "emergencias" ? (t["agenda.title"] || "Agenda") : (t[c.label] || capitalize(catId));
  $("#list-count").textContent = catCounts[catId] != null ? `· ${catCounts[catId]}` : "";
  renderChips(c);
  showView("view-list");

  const grid = $("#content-grid");
  grid.setAttribute("aria-busy", "true");
  grid.innerHTML = `<p class="content-loading">${t["loading.contenido"] || "Cargando contenidos…"}</p>`;

  if (chip === "emergencias") { renderEmergencies(grid); grid.setAttribute("aria-busy", "false"); return; }
  if (c.events) { await renderAgenda(grid, chip); grid.setAttribute("aria-busy", "false"); return; }

  let items = [];
  if (c.srv) {
    const servicios = await getServicios();
    items = servicios.filter((s) => (chip === "todas" ? c.srv.includes(s.tipo) : s.tipo === chip));
  } else {
    const cats = chip === "todas" ? c.res : [chip];
    for (const cat of cats) {
      try {
        const d = await apiGet(`/tourism/resources?categoria=${encodeURIComponent(cat)}&publicado=true&page_size=20`);
        items.push(...(d.items || []));
      } catch { /* siguiente categoría */ }
    }
  }
  if (items.length === 0 && !c.srv) items = DEMO_RESOURCES[catId] || [];
  renderItems(grid, items, c);
  grid.setAttribute("aria-busy", "false");
}

function renderChips(c) {
  const t = dict();
  const wrap = $("#list-chips");
  const subs = c.srv || c.res || [];
  const chips = [`<button class="tt-chip" data-chip="todas" aria-pressed="${currentChip === "todas"}">${t["chips.todas"] || "Todas"}</button>`];
  if (subs.length > 1) {
    subs.forEach((s) => chips.push(
      `<button class="tt-chip" data-chip="${s}" aria-pressed="${currentChip === s}">${escapeHtml(tagLabel(s))}</button>`));
  }
  if (c.emergencias) {
    chips.push(`<button class="tt-chip" data-chip="emergencias" aria-pressed="${currentChip === "emergencias"}">🆘 ${t["categorias.emergencias"] || "Emergencias"}</button>`);
  }
  wrap.innerHTML = chips.join("");
  wrap.querySelectorAll(".tt-chip").forEach((b) =>
    b.addEventListener("click", () => abrirCategoria(c.id, b.dataset.chip)));
}

function itemCard(r, c) {
  const t = dict();
  const nombre = r.nombre_i18n?.[currentLang] || r.nombre;
  const desc = r.descripcion_i18n?.[currentLang] || r.descripcion_corta || r.descripcion || "";
  const latlon = extractLatLon(r);
  const km = latlon ? haversineKm(latlon[0], latlon[1]) : null;
  const tags = [];
  if ((r.etiquetas || []).some((e) => /parque/i.test(e)) || r.categoria === "parque_natural") {
    tags.push('<span class="tt-tag">Parque Natural</span>');
  }
  if (r.categoria) tags.push(`<span class="tt-tag tt-tag--info">${escapeHtml(tagLabel(r.categoria))}</span>`);
  else if (r.tipo) tags.push(`<span class="tt-tag tt-tag--info">${escapeHtml(tagLabel(r.tipo))}</span>`);
  if (r.accesibilidad) tags.push('<span class="tt-tag tt-tag--warn">♿ Accesible</span>');

  const meta = [];
  if (km != null) meta.push(`🚶 ${km < 1 ? Math.round(km * 1000) + " m" : km.toFixed(1) + " km"}`);
  if (r.horario && typeof r.horario === "string") meta.push(`🕒 ${escapeHtml(r.horario)}`);
  if (r.telefono) meta.push(`📞 ${escapeHtml(String(r.telefono))}`);

  const img = r.imagenes?.[0];
  return `
    <button class="tt-item" data-urn="${escapeAttr(r.urn || r.id || "")}">
      <span class="tt-thumb ${c.th}" aria-hidden="true">${img ? `<img src="${escapeAttr(img)}" alt="">` : '<span class="sun"></span>'}</span>
      <span class="tt-item-body">
        <span class="tt-item-tags">${tags.join("")}</span>
        <h3>${escapeHtml(nombre)}</h3>
        <span class="tt-item-sub">${escapeHtml(r.municipio || "")}${r.direccion ? " · " + escapeHtml(r.direccion) : ""}</span>
        ${meta.length ? `<span class="tt-item-meta">${meta.map((m) => `<span>${m}</span>`).join("")}</span>` : ""}
        ${!meta.length && desc ? `<span class="tt-item-sub">${escapeHtml(String(desc).slice(0, 110))}${String(desc).length > 110 ? "…" : ""}</span>` : ""}
      </span>
      <span class="tt-item-go" aria-hidden="true">›</span>
    </button>`;
}

function renderItems(grid, items, c) {
  const t = dict();
  if (!items.length) {
    grid.innerHTML = `<p class="content-loading">${t["empty.contenido"] || "Sin contenidos disponibles"}</p>`;
    return;
  }
  grid.innerHTML = items.map((r) => itemCard(r, c)).join("");
  grid.querySelectorAll(".tt-item").forEach((btn, i) => {
    btn.addEventListener("click", () => openDetail(items[i], c));
  });
}

// ============================================================
// AGENDA de eventos agrupada por días (diseño v4)
// ============================================================
async function renderAgenda(grid, chip) {
  const t = dict();
  let items = [];
  try {
    const d = await apiGet("/tourism/events?publicado=true&page_size=30");
    items = d.items || [];
  } catch { items = DEMO_EVENTS; }
  if (chip !== "todas") items = items.filter((e) => e.tipo === chip);
  items.sort((a, b) => new Date(a.fecha_inicio) - new Date(b.fecha_inicio));

  const hoy = new Date(); hoy.setHours(0, 0, 0, 0);
  const grupos = new Map();
  for (const ev of items) {
    const f = new Date(ev.fecha_inicio); f.setHours(0, 0, 0, 0);
    const k = f.getTime();
    if (!grupos.has(k)) grupos.set(k, []);
    grupos.get(k).push(ev);
  }
  if (!grupos.size) {
    grid.innerHTML = `<p class="content-loading">${t["empty.contenido"] || "Sin eventos programados"}</p>`;
    return;
  }

  const tiposChips = [...new Set(items.map((e) => e.tipo).filter(Boolean))];
  $("#list-chips").innerHTML =
    `<button class="tt-chip" data-chip="todas" aria-pressed="${chip === "todas"}">${t["chips.todas"] || "Todas"}</button>` +
    tiposChips.map((x) => `<button class="tt-chip" data-chip="${x}" aria-pressed="${chip === x}">${escapeHtml(capitalize(x))}</button>`).join("");
  $("#list-chips").querySelectorAll(".tt-chip").forEach((b) =>
    b.addEventListener("click", () => abrirCategoria("eventos", b.dataset.chip)));

  let html = "";
  for (const [ts, evs] of grupos) {
    const f = new Date(Number(ts));
    const esHoy = f.getTime() === hoy.getTime();
    const titulo = f.toLocaleDateString(currentLang, { weekday: "long", day: "numeric", month: "long" });
    html += `<div class="tt-dayhead ${esHoy ? "is-hoy" : ""}">${esHoy ? `<span class="hoy">${t["agenda.hoy"] || "HOY"}</span>` : ""}${capitalize(titulo)}</div>`;
    html += evs.map((ev) => {
      const nombre = ev.nombre_i18n?.[currentLang] || ev.nombre;
      const hora = new Date(ev.fecha_inicio).toLocaleTimeString(currentLang, { hour: "2-digit", minute: "2-digit" });
      const dia = new Date(ev.fecha_inicio);
      return `
        <button class="tt-item" data-ev="${escapeAttr(ev.urn || ev.id || "")}">
          <span class="tt-dateblock ${esHoy ? "is-hoy" : ""}" aria-hidden="true">
            <b>${dia.getDate()}</b>
            <small>${dia.toLocaleDateString(currentLang, { month: "short" }).toUpperCase()} · ${dia.toLocaleDateString(currentLang, { weekday: "short" }).toUpperCase()}</small>
          </span>
          <span class="tt-item-body">
            <span class="tt-item-tags">
              ${ev.tipo ? `<span class="tt-tag tt-tag--rose">${escapeHtml(capitalize(ev.tipo))}</span>` : ""}
              ${ev.direccion ? `<span class="tt-tag tt-tag--info">${escapeHtml(ev.direccion)}</span>` : ""}
            </span>
            <h3>${escapeHtml(nombre)}</h3>
            <span class="tt-item-meta"><span>🕒 ${hora}</span>${ev.precio ? `<span>💶 ${escapeHtml(String(ev.precio))}</span>` : ""}${ev.organizador ? `<span>🏢 ${escapeHtml(ev.organizador)}</span>` : ""}</span>
          </span>
          <span class="tt-item-go" aria-hidden="true">›</span>
        </button>`;
    }).join("");
  }
  grid.innerHTML = html;
  const flat = [...grupos.values()].flat();
  grid.querySelectorAll(".tt-item").forEach((btn, i) =>
    btn.addEventListener("click", () => openDetail(flat[i], CATS.find((x) => x.id === "eventos"))));
}

// ============================================================
// EMERGENCIAS
// ============================================================
function renderEmergencies(grid) {
  const items = currentLang === "es" ? [
    { titulo: "Emergencias generales", numero: "112", desc: "Atención multilingüe 24/7" },
    { titulo: "Salvamento Marítimo", numero: "900 202 202", desc: "Emergencias en el mar" },
    { titulo: "Centro de salud Níjar", numero: "+34 950 38 12 50", desc: "Atención sanitaria" },
    { titulo: "Guardia Civil", numero: "062", desc: "Seguridad ciudadana" },
  ] : [
    { titulo: "Emergency", numero: "112", desc: "Multilingual 24/7" },
    { titulo: "Maritime Rescue", numero: "900 202 202", desc: "Sea emergency" },
    { titulo: "Health Centre Níjar", numero: "+34 950 38 12 50", desc: "Medical care" },
    { titulo: "Police (Guardia Civil)", numero: "062", desc: "Public safety" },
  ];
  grid.innerHTML = items.map((it) => `
    <div class="tt-item emergency-card" role="region" aria-label="${escapeHtml(it.titulo)}">
      <span class="tt-thumb th-servicio" aria-hidden="true" style="display:grid;place-items:center;font-size:44px">🆘</span>
      <span class="tt-item-body">
        <h3>${escapeHtml(it.titulo)}</h3>
        <p class="emergency-number">${escapeHtml(it.numero)}</p>
        <span class="tt-item-sub">${escapeHtml(it.desc)}</span>
      </span>
    </div>`).join("");
}

// ============================================================
// FICHA DE DETALLE (modal, diseño v4)
// ============================================================
const dialog = $("#poi-dialog");

const META_FIELDS = [
  { key: "fecha_inicio", icon: "📅", label: "info.fecha", format: "datetime" },
  { key: "direccion", icon: "📍", label: "info.direccion", wide: true },
  { key: "municipio", icon: "🏘️", label: "info.municipio" },
  { key: "horario", icon: "🕒", label: "info.horario", format: "horario", wide: true },
  { key: "precio", icon: "💶", label: "info.precio", format: "i18n" },
  { key: "telefono", icon: "📞", label: "info.telefono" },
  { key: "email", icon: "✉️", label: "info.email" },
  { key: "web", icon: "🌐", label: "info.web" },
  { key: "organizador", icon: "🏢", label: "info.organizador", format: "i18n" },
  { key: "capacidad_aforo", icon: "👥", label: "info.aforo", format: "people" },
  { key: "servicios_disponibles", icon: "🛎️", label: "info.servicios", format: "serviciosList", wide: true },
  { key: "accesibilidad", icon: "♿", label: "info.accesibilidad", format: "acc", wide: true },
];

function formatMeta(field, value) {
  switch (field.format) {
    case "datetime":
      return new Date(value).toLocaleString(currentLang, { day: "2-digit", month: "long", hour: "2-digit", minute: "2-digit" });
    case "people": return `${value}`;
    case "i18n": return (value && typeof value === "object" && value[currentLang]) ? value[currentLang] : String(value);
    case "horario":
      if (typeof value === "string") return value;
      if (Array.isArray(value)) return value.join(" · ");
      if (value && typeof value === "object") return Object.entries(value).map(([k, v]) => `${capitalize(k)}: ${v}`).join(" · ");
      return "";
    case "serviciosList":
      return Array.isArray(value) ? value.map((s) => capitalize(String(s).replace(/_/g, " "))).join(" · ") : String(value);
    case "acc":
      if (value && typeof value === "object") return Object.entries(value).map(([k, v]) => `${capitalize(k.replace(/_/g, " "))}: ${v === true ? "✓" : v}`).join(" · ");
      return String(value);
    default: return String(value);
  }
}

function openDetail(r, c) {
  const t = dict();
  const nombre = r.nombre_i18n?.[currentLang] || r.nombre || "—";
  $("#poi-title").textContent = nombre;
  $("#poi-body").textContent = r.descripcion_i18n?.[currentLang] || r.descripcion || r.descripcion_corta || "";

  // Hero: imagen real o degradado por tipo
  const hero = $("#poi-image");
  const img = r.imagenes?.[0];
  hero.className = `tt-dialog-hero ${c ? c.th : "th-playa"}`;
  hero.style.backgroundImage = img ? `url('${img}')` : "";

  // Badge superior
  const cat = r.categoria || r.tipo || "";
  const tag = $("#poi-tag");
  if (cat) { tag.textContent = tagLabel(cat); tag.hidden = false; } else tag.hidden = true;

  // Tarjetas de datos rápidos
  const stats = [];
  const latlon = extractLatLon(r);
  if (latlon) {
    const km = haversineKm(latlon[0], latlon[1]);
    stats.push(["🚶", t["info.distancia"] || "Distancia", km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(1)} km`]);
  }
  if (r.municipio) stats.push(["🏘️", t["info.municipio"] || "Municipio", r.municipio]);
  if (r.fecha_inicio) stats.push(["📅", t["info.fecha"] || "Fecha", new Date(r.fecha_inicio).toLocaleDateString(currentLang, { day: "2-digit", month: "short" })]);
  if (r.precio) stats.push(["💶", t["info.precio"] || "Precio", formatMeta({ format: "i18n" }, r.precio)]);
  else if (cat) stats.push(["🏷️", "Categoría", tagLabel(cat)]);
  $("#poi-stats").innerHTML = stats.slice(0, 4).map(([ic, l, v]) =>
    `<div class="tt-stat"><span class="ic" aria-hidden="true">${ic}</span><small>${escapeHtml(String(l).toUpperCase())}</small><b>${escapeHtml(String(v))}</b></div>`).join("");

  // Metadatos
  const meta = $("#poi-meta");
  meta.innerHTML = "";
  for (const field of META_FIELDS) {
    const value = r[field.key];
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value) && value.length === 0) continue;
    const formatted = formatMeta(field, value);
    if (!formatted) continue;
    const row = document.createElement("div");
    row.className = "poi-dialog-meta-row" + (field.wide ? " is-wide" : "");
    row.innerHTML = `<dt aria-hidden="true">${field.icon}</dt><dd><strong>${escapeHtml(dict()[field.label] || field.label)}:</strong> ${escapeHtml(formatted)}</dd>`;
    meta.appendChild(row);
  }
  meta.parentElement.style.display = meta.children.length ? "" : "none";

  // Etiquetas
  const tagsEl = $("#poi-tags");
  const raw = (r.etiquetas || []).filter((x) => String(x).toLowerCase() !== String(cat).toLowerCase());
  tagsEl.innerHTML = raw.map((x) => `<span class="tag-chip">#${escapeHtml(String(x))}</span>`).join("");
  tagsEl.hidden = !raw.length;

  // Acciones
  const actions = [];
  if (latlon) {
    actions.push(`<button class="action-btn" id="poi-goto-map">📍 ${escapeHtml(dict()["action.mapa"] || "Ver en el mapa")}</button>`);
  }
  if (r.telefono) actions.push(`<a class="action-btn action-btn--secondary" href="tel:${escapeAttr(String(r.telefono).replace(/\s+/g, ""))}">📞 ${escapeHtml(dict()["action.llamar"] || "Llamar")}</a>`);
  if (r.web) actions.push(`<a class="action-btn action-btn--secondary" href="${escapeAttr(r.web)}" target="_blank" rel="noopener noreferrer">🌐 Web</a>`);
  const actEl = $("#poi-actions");
  actEl.innerHTML = actions.join("");
  actEl.hidden = !actions.length;
  const goMap = $("#poi-goto-map");
  if (goMap) goMap.addEventListener("click", () => { dialog.close(); abrirMapa(latlon); });

  dialog.querySelector(".poi-dialog-content")?.scrollTo({ top: 0 });
  dialog.showModal();
  resetIdle();
}

$("#poi-close").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });

// ============================================================
// MAPA DEL DESTINO (Leaflet + datos reales)
// ============================================================
function cargarLeaflet() {
  return new Promise((resolve, reject) => {
    if (window.L) return resolve(window.L);
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    document.head.appendChild(css);
    const js = document.createElement("script");
    js.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    js.onload = () => resolve(window.L);
    js.onerror = () => reject(new Error("Leaflet no disponible"));
    document.head.appendChild(js);
  });
}

const COLOR_CAT = { playa: "#17B8C4", ruta: "#1E9E6E", monumento: "#7C6BF0", mirador: "#F5C518", parque_natural: "#2E7D4F", museo: "#E2572B", yacimiento: "#A66B2E" };

async function abrirMapa(centro) {
  showView("view-map");
  try {
    const [L, recursos] = await Promise.all([
      cargarLeaflet(),
      apiGet("/tourism/resources?page=1&page_size=200&publicado=true").then((d) => d.items || []).catch(() => []),
    ]);
    const cont = $("#totem-map");
    if (!mapaLeaflet) {
      mapaLeaflet = L.map(cont, { zoomControl: true }).setView([36.82, -2.1], 11);
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 17, attribution: "&copy; OpenStreetMap" }).addTo(mapaLeaflet);
      const pts = [];
      recursos.forEach((r) => {
        const ll = extractLatLon(r);
        if (!ll) return;
        pts.push(ll);
        L.circleMarker(ll, {
          radius: 11, weight: 3, color: "#fff",
          fillColor: COLOR_CAT[r.categoria] || "#0E3A78", fillOpacity: 1,
        }).on("click", () => mostrarSheet(r)).addTo(mapaLeaflet);
      });
      if (pts.length) mapaLeaflet.fitBounds(L.latLngBounds(pts).pad(0.15));
    }
    setTimeout(() => mapaLeaflet.invalidateSize(), 120);
    if (Array.isArray(centro)) mapaLeaflet.setView(centro, 14);
  } catch {
    $("#totem-map").innerHTML = `<p class="content-loading">${dict()["empty.contenido"] || "Mapa no disponible sin conexión"}</p>`;
  }
  resetIdle();
}

function mostrarSheet(r) {
  const t = dict();
  const nombre = r.nombre_i18n?.[currentLang] || r.nombre;
  const sheet = $("#map-sheet");
  sheet.innerHTML = `
    <span class="tt-tag tt-tag--warn">${escapeHtml(tagLabel(r.categoria || ""))}</span>
    <h3>${escapeHtml(nombre)}</h3>
    <span class="tt-item-sub">${escapeHtml(r.municipio || "")}${r.direccion ? " · " + escapeHtml(r.direccion) : ""}</span>
    <div class="tt-mapsheet-actions">
      <button class="tt-cta" id="sheet-ficha">→ ${escapeHtml(t["map.verficha"] || "Ver ficha")}</button>
      <button class="tt-cta tt-cta--ghost" id="sheet-cerrar">✕</button>
    </div>`;
  sheet.classList.remove("is-hidden");
  $("#sheet-ficha").addEventListener("click", () => {
    const c = CATS.find((x) => (x.res || []).includes(r.categoria)) || CATS[0];
    openDetail(r, c);
  });
  $("#sheet-cerrar").addEventListener("click", () => sheet.classList.add("is-hidden"));
  resetIdle();
}

// ============================================================
// ASISTENTE IA (chat conversacional, diseño v4)
// ============================================================
const chatLog = $("#chat-log");
const speakBtn = $("#chatbot-speak");

function resetChat() {
  const t = dict();
  chatLog.innerHTML = `
    <div class="tt-msg tt-msg--bot">
      <span class="tt-avatar tt-avatar--bot" aria-hidden="true">🤖</span>
      <div class="tt-bubble">${escapeHtml(t["chat.welcome"] || "¡Hola! ¿Qué te apetece hacer hoy?")}</div>
    </div>`;
}

function burbuja(texto, esUsuario) {
  const div = document.createElement("div");
  div.className = `tt-msg ${esUsuario ? "tt-msg--user" : "tt-msg--bot"}`;
  div.innerHTML = `
    <span class="tt-avatar ${esUsuario ? "tt-avatar--user" : "tt-avatar--bot"}" aria-hidden="true">${esUsuario ? "👤" : "🤖"}</span>
    <div class="tt-bubble"></div>`;
  div.querySelector(".tt-bubble").textContent = texto;
  chatLog.appendChild(div);
  div.scrollIntoView({ behavior: "smooth", block: "end" });
  return div.querySelector(".tt-bubble");
}

$("#chatbot-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  await askChatbot($("#chatbot-input").value.trim());
});

async function askChatbot(message) {
  const input = $("#chatbot-input");
  if (!message) return;
  burbuja(message, true);
  input.value = "";
  const pensando = burbuja(dict()["chatbot.thinking"] || "Pensando…", false);
  speakBtn.classList.add("is-hidden");

  let data = null;
  try {
    const res = await fetch(`${API_BASE}/chatbot/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sesion_id: sessionId, canal: "totem", idioma: currentLang, pregunta: message }),
    });
    if (res.ok) data = await res.json();
  } catch { /* fallback demo */ }
  if (!data || !data.respuesta) data = answerChatbotDemo(message, currentLang);

  lastAnswer = data.respuesta || "—";
  pensando.textContent = lastAnswer;
  if (Array.isArray(data.sugerencias) && data.sugerencias.length) {
    const sug = document.createElement("p");
    sug.className = "chatbot-suggestions";
    sug.textContent = "💡 " + data.sugerencias.join(" · ");
    pensando.appendChild(sug);
  }
  $("#chatbot-output").textContent = lastAnswer;   /* lector de pantalla */
  if ("speechSynthesis" in window) {
    speakBtn.classList.remove("is-hidden");
    hablar(lastAnswer);
  }
  pensando.parentElement.scrollIntoView({ behavior: "smooth", block: "end" });
  resetIdle();
}

// --- Texto a voz (TTS) ---
function hablar(texto) {
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(texto);
    u.lang = VOICE_LOCALE[currentLang] || "es-ES";
    window.speechSynthesis.speak(u);
  } catch { /* TTS no disponible */ }
}
speakBtn.addEventListener("click", () => { if (lastAnswer) hablar(lastAnswer); });

// --- Voz a texto (STT) ---
const voiceBtn = $("#chatbot-voice");
const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRec && voiceBtn) {
  voiceBtn.classList.remove("is-hidden");
  const recognition = new SpeechRec();
  recognition.continuous = false;
  recognition.interimResults = false;
  let escuchando = false;
  voiceBtn.addEventListener("click", () => {
    if (escuchando) { recognition.stop(); return; }
    recognition.lang = VOICE_LOCALE[currentLang] || "es-ES";
    try { recognition.start(); } catch { /* ya iniciado */ }
  });
  recognition.addEventListener("start", () => {
    escuchando = true;
    voiceBtn.setAttribute("aria-pressed", "true");
    $("#chatbot-input").placeholder = dict()["chatbot.listening"] || "Escuchando…";
  });
  recognition.addEventListener("end", () => {
    escuchando = false;
    voiceBtn.setAttribute("aria-pressed", "false");
  });
  recognition.addEventListener("result", (ev) => {
    const texto = ev.results?.[0]?.[0]?.transcript || "";
    if (texto) { $("#chatbot-input").value = texto; askChatbot(texto); }
  });
}

// ============================================================
// Planificador y recomendaciones (tarjetas dentro del chat)
// ============================================================
function recoCard(titulo, filas) {
  const card = document.createElement("div");
  card.className = "tt-reco-card";
  card.innerHTML = `<h4>${escapeHtml(titulo.toUpperCase())}</h4><ol>${filas}</ol>`;
  chatLog.appendChild(card);
  card.scrollIntoView({ behavior: "smooth", block: "end" });
}

$("#plan-route-btn").addEventListener("click", async () => {
  const t = dict();
  const pensando = burbuja(t["rutas.loading"] || "Calculando…", false);
  try {
    const res = await fetch(`${API_BASE}/rutas/planificar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat: TOTEM_LAT, lon: TOTEM_LON, max_paradas: 5, modo: "bici", idioma: currentLang }),
    });
    if (!res.ok) throw new Error("no disponible");
    const data = await res.json();
    if (!data.paradas?.length) { pensando.textContent = t["rutas.empty"] || "No hay propuestas disponibles."; return; }
    const km = (data.distancia_total_m / 1000).toFixed(1);
    pensando.textContent = `${t["rutas.distancia"] || "Distancia"}: ${km} km · ${t["rutas.duracion"] || "Duración"}: ${data.duracion_desplazamiento_min} min`;
    recoCard(t["rutas.plan"] || "Ruta sugerida",
      data.paradas.map((p) => `<li><strong>${p.orden}. ${escapeHtml(p.nombre)}</strong><span class="planner-cat">${escapeHtml(tagLabel(p.categoria))}</span></li>`).join(""));
  } catch { pensando.textContent = t["rutas.empty"] || "No hay propuestas disponibles."; }
  resetIdle();
});

$("#recommend-btn").addEventListener("click", async () => {
  const t = dict();
  const pensando = burbuja(t["rutas.loading"] || "Calculando…", false);
  try {
    const res = await fetch(`${API_BASE}/rutas/recomendaciones?idioma=${currentLang}`);
    if (!res.ok) throw new Error("no disponible");
    const data = await res.json();
    pensando.textContent = t["rutas.recomend"] || "¿Qué visitar hoy?";
    if (data.eventos?.length) {
      recoCard(t["rutas.eventos"] || "Eventos próximos", data.eventos.map((e) => {
        const f = e.fecha_inicio ? new Date(e.fecha_inicio).toLocaleDateString(currentLang, { day: "2-digit", month: "short" }) : "";
        return `<li><strong>${escapeHtml(e.nombre)}</strong><span class="planner-cat">${escapeHtml(f)}</span></li>`;
      }).join(""));
    }
    if (data.recursos?.length) {
      recoCard(t["rutas.recursos"] || "Lugares recomendados", data.recursos.map((r) =>
        `<li><strong>${escapeHtml(r.nombre)}</strong><span class="planner-cat">${escapeHtml(tagLabel(r.categoria))}</span></li>`).join(""));
    }
    if (!data.eventos?.length && !data.recursos?.length) pensando.textContent = t["rutas.empty"] || "Sin recomendaciones ahora mismo.";
  } catch { pensando.textContent = t["rutas.empty"] || "Sin recomendaciones ahora mismo."; }
  resetIdle();
});

// ============================================================
// Inactividad — vuelve al estado inicial tras IDLE_MS
// ============================================================
function goToIdleState() {
  if (dialog.open) dialog.close();
  $("#map-sheet").classList.add("is-hidden");
  currentCat = null;
  currentChip = "todas";
  lastAnswer = "";
  speakBtn.classList.add("is-hidden");
  $("#featured")?.classList.add("is-hidden");
  showView("view-home");
  if (currentLang !== "es") applyLanguage("es");
  else resetChat();
  if (document.body.classList.contains("text-lg-mode")) {
    document.body.classList.remove("text-lg-mode");
    textBtn.setAttribute("aria-pressed", "false");
  }
  if (document.body.classList.contains("high-contrast")) toggleContrast();
  document.body.classList.add("idle");
}

function resetIdle() {
  if (idleTimer) clearTimeout(idleTimer);
  document.body.classList.remove("idle");
  idleTimer = setTimeout(goToIdleState, IDLE_MS);
}
["click", "keydown", "touchstart", "scroll"].forEach((evt) =>
  window.addEventListener(evt, resetIdle, { passive: true }));
resetIdle();

// ============================================================
// Helpers
// ============================================================
function escapeHtml(s) {
  return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
function escapeAttr(s) { return escapeHtml(s).replace(/`/g, "&#96;"); }
function capitalize(s) { return String(s || "").charAt(0).toUpperCase() + String(s || "").slice(1); }
function tagLabel(categoria) {
  if (!categoria) return "";
  return dict()[`tag.${categoria}`] || I18N.es?.[`tag.${categoria}`] || capitalize(String(categoria).replace(/_/g, " "));
}

// ============================================================
// Inicialización
// ============================================================
translateAll(currentLang);
document.querySelectorAll(".lang-btn").forEach((btn) =>
  btn.setAttribute("aria-pressed", String(btn.dataset.lang === currentLang)));
renderHomeCats();
resetChat();
cargarConteos();
