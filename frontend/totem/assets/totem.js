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

import { I18N, translateAll } from "./i18n.js?v=24";
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

// ============================================================
// Iconografía plana vectorial (2D, sin emojis del sistema)
// ============================================================
const ICONS = {
  playa: '<circle cx="16.5" cy="7" r="3.2" fill="#F5C518"/><path d="M2 14c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0" stroke="#17B8C4" stroke-width="2.2" fill="none" stroke-linecap="round"/><path d="M2 18.5c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0" stroke="#0E9AA5" stroke-width="2.2" fill="none" stroke-linecap="round"/>',
  ruta: '<path d="M2 19L9 8l4 6 3-4 6 9z" fill="#1E9E6E"/><path d="M9 8l4 6 3-4" fill="#2FBF8A"/><circle cx="18" cy="5" r="2.4" fill="#F5C518"/><path d="M4 19h16" stroke="#7B5A3A" stroke-width="2" stroke-linecap="round" stroke-dasharray="2.5 2.5"/>',
  patrimonio: '<path d="M3 9l9-5 9 5z" fill="#0E3A78"/><path d="M5 10h2.6v8H5zM10.7 10h2.6v8h-2.6zM16.4 10H19v8h-2.6z" fill="#4A6FA5"/><path d="M3 18h18v2.4H3z" fill="#0E3A78"/><path d="M12 5.6l4.5 2.5h-9z" fill="#F5C518"/>',
  naturaleza: '<path d="M12 21c0-7 2-12 8-15 .5 8-2 13-8 15z" fill="#1E9E6E"/><path d="M12 21c0-5.5-1.5-9.5-6-12-.4 6.3 1.6 10.4 6 12z" fill="#57B87B"/><path d="M11 21.5h2V17h-2z" fill="#7B5A3A"/>',
  gastronomia: '<circle cx="13.5" cy="12" r="6.5" fill="#FBE3D8"/><circle cx="13.5" cy="12" r="3.6" fill="#E2572B"/><path d="M4 4v6M2.6 4v3.4a1.4 1.4 0 002.8 0V4" stroke="#0E3A78" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M4 10v10" stroke="#0E3A78" stroke-width="1.8" stroke-linecap="round"/><path d="M21.5 4c-1.8 1-2.6 3-2.6 5.5V20" stroke="#0E3A78" stroke-width="1.8" fill="none" stroke-linecap="round"/>',
  eventos: '<rect x="3" y="5" width="18" height="16" rx="2.5" fill="#EFEAFB"/><path d="M3 7.5A2.5 2.5 0 015.5 5h13A2.5 2.5 0 0121 7.5V10H3z" fill="#7C6BF0"/><path d="M8 3v4M16 3v4" stroke="#0E3A78" stroke-width="2" stroke-linecap="round"/><circle cx="8.5" cy="14" r="1.4" fill="#E2572B"/><circle cx="12" cy="14" r="1.4" fill="#F5C518"/><circle cx="15.5" cy="14" r="1.4" fill="#17B8C4"/><circle cx="8.5" cy="17.5" r="1.4" fill="#17B8C4"/><circle cx="12" cy="17.5" r="1.4" fill="#7C6BF0"/>',
  alojamiento: '<path d="M3 11l9-7 9 7v9a1.5 1.5 0 01-1.5 1.5h-15A1.5 1.5 0 013 20z" fill="#4A6FA5"/><path d="M3 11l9-7 9 7-1.6 1.2L12 6.2 4.6 12.2z" fill="#0E3A78"/><rect x="9.6" y="14" width="4.8" height="7.5" rx="1" fill="#F5C518"/>',
  artesania: '<path d="M9 3h6v2.6c0 1.6 3 2.6 3 6.4 0 4.5-2 9-6 9s-6-4.5-6-9c0-3.8 3-4.8 3-6.4z" fill="#E2572B"/><path d="M9 3h6v2.2H9z" fill="#B23F1B"/><path d="M8.2 12.5c.4 3 1.4 5.8 3.8 6.4" stroke="#F5A623" stroke-width="1.6" fill="none" stroke-linecap="round"/>',
  servicios: '<circle cx="12" cy="12" r="9.5" fill="#4A6FA5"/><circle cx="12" cy="7.6" r="1.5" fill="#fff"/><rect x="10.6" y="10.4" width="2.8" height="7" rx="1.4" fill="#fff"/>',
  emergencias: '<rect x="2.5" y="2.5" width="19" height="19" rx="5" fill="#E5484D"/><path d="M10.4 5.5h3.2v4.9h4.9v3.2h-4.9v4.9h-3.2v-4.9H5.5v-3.2h4.9z" fill="#fff"/>',
  bot: '<rect x="4" y="7" width="16" height="12" rx="4" fill="#fff"/><circle cx="9.2" cy="12.5" r="1.6" fill="#0E3A78"/><circle cx="14.8" cy="12.5" r="1.6" fill="#0E3A78"/><path d="M9.5 16h5" stroke="#0E3A78" stroke-width="1.6" stroke-linecap="round"/><path d="M12 4v3" stroke="#fff" stroke-width="2" stroke-linecap="round"/><circle cx="12" cy="3.4" r="1.4" fill="#F5C518"/>',
  usuario: '<circle cx="12" cy="8.4" r="4" fill="#0E3A78"/><path d="M4.5 20a7.5 7.5 0 0115 0z" fill="#0E3A78"/>',
  andar: '<circle cx="13" cy="4.6" r="2.1" fill="#0E3A78"/><path d="M13 7.5l-2.6 4.2 2.2 3-1.4 5.8M10.4 11.7L8 13.5M12.6 14.7l3 2.2 1.2 4M13 7.5l3.4 1.7 1.8 3" stroke="#0E3A78" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
  reloj: '<circle cx="12" cy="12" r="9" fill="#E4EAF6"/><circle cx="12" cy="12" r="9" stroke="#0E3A78" stroke-width="1.8" fill="none"/><path d="M12 6.8V12l3.4 2.4" stroke="#0E3A78" stroke-width="2" fill="none" stroke-linecap="round"/>',
  telefono: '<path d="M5.5 3h3.4l1.5 4.4-2.2 1.7a12.6 12.6 0 006.7 6.7l1.7-2.2L21 15.1v3.4A2.5 2.5 0 0118.5 21C10 20.4 3.6 14 3 5.5A2.5 2.5 0 015.5 3z" fill="#1E9E6E"/>',
  fecha: '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5" fill="#E4EAF6"/><path d="M3.5 7.5A2.5 2.5 0 016 5h12a2.5 2.5 0 012.5 2.5v2.6h-17z" fill="#0E3A78"/><path d="M8 3.2v3.4M16 3.2v3.4" stroke="#0E3A78" stroke-width="2" stroke-linecap="round"/><rect x="7" y="13" width="4" height="3.4" rx="0.8" fill="#F5C518"/>',
  precio: '<circle cx="12" cy="12" r="9.5" fill="#F5C518"/><path d="M15.6 8.6A4.6 4.6 0 108 15.4M6.8 10.6h5.4M6.8 13.4h4.6" stroke="#0E3A78" stroke-width="1.9" fill="none" stroke-linecap="round"/>',
  edificio: '<rect x="5" y="3.5" width="10" height="17" rx="1.2" fill="#4A6FA5"/><rect x="15" y="9" width="4.5" height="11.5" rx="1" fill="#0E3A78"/><path d="M7.4 6.5h2m3 0h-2m-3 3.4h2m3 0h-2m-3 3.4h2m3 0h-2" stroke="#fff" stroke-width="1.4" stroke-linecap="round"/>',
  lugar: '<path d="M12 2.5a7 7 0 017 7c0 5-7 12-7 12s-7-7-7-12a7 7 0 017-7z" fill="#E2572B"/><circle cx="12" cy="9.5" r="2.8" fill="#fff"/>',
  campana: '<path d="M12 3a6.5 6.5 0 016.5 6.5c0 4 1.6 5.4 1.6 5.4H3.9s1.6-1.4 1.6-5.4A6.5 6.5 0 0112 3z" fill="#F5C518"/><path d="M10 18.5a2.1 2.1 0 004 0" stroke="#0E3A78" stroke-width="1.8" fill="none" stroke-linecap="round"/>',
  accesible: '<circle cx="12" cy="4.6" r="2.1" fill="#0E3A78"/><path d="M12 7.5v5.5h5l2.4 5.5" stroke="#0E3A78" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 9.5h4.4" stroke="#0E3A78" stroke-width="2" stroke-linecap="round"/><path d="M14.6 14.5A5.3 5.3 0 116.7 12" stroke="#17B8C4" stroke-width="2" fill="none" stroke-linecap="round"/>',
  web: '<circle cx="12" cy="12" r="9" fill="#E4EAF6"/><circle cx="12" cy="12" r="9" stroke="#0E3A78" stroke-width="1.7" fill="none"/><path d="M3 12h18M12 3a14.5 14.5 0 010 18M12 3a14.5 14.5 0 000 18" stroke="#0E3A78" stroke-width="1.5" fill="none"/>',
  email: '<rect x="3" y="5.5" width="18" height="13" rx="2.4" fill="#17B8C4"/><path d="M4 7l8 6 8-6" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
  idea: '<path d="M12 3a6.2 6.2 0 00-3.4 11.4c.8.6 1.4 1.4 1.4 2.1h4c0-.7.6-1.5 1.4-2.1A6.2 6.2 0 0012 3z" fill="#F5C518"/><path d="M10 19h4M10.7 21h2.6" stroke="#0E3A78" stroke-width="1.7" stroke-linecap="round"/>',
  euro2: '<path d="M15.6 8.6A4.6 4.6 0 108 15.4M6.8 10.6h5.4M6.8 13.4h4.6" stroke="#E2572B" stroke-width="2" fill="none" stroke-linecap="round"/>',
};

function icono(nombre, cls) {
  return `<svg class="tt-svg ${cls || ""}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[nombre] || ICONS.servicios}</svg>`;
}

/* Las banderas planas (SVG) van inline en index.html junto a cada botón */

// Categorías del home (rediseño Dirección) → 6 tiles del grid 2×3.
// - `res`: recursos con esa categoria de recurso_turistico
// - `srv`: servicios de esos tipos (agrupados desde /tourism/services)
// - `etiquetas`: recursos que llevan alguna de estas tags (case-insensitive)
// - `bg`: imagen de fondo del tile (path relativo). Si falla, cae a `solid`.
// - `solid`: color plano del tile cuando no hay foto.
const CATS = [
  { id: "playas",      label: "cat.playas_calas",      icon: "playa",       th: "th-playa",       bg: "../shared/tiles/playas.jpg",      res: ["playa"],              subchips: ["virgen", "familiar"],                        heroSub: "sub.playas",     unit: "unit.lugares" },
  { id: "cabo",        label: "cat.cabo_gata",         icon: "naturaleza",  th: "th-naturaleza",  bg: "../shared/tiles/cabo.jpg",        res: ["parque_natural"],     subchips: ["volcánico", "geología", "patrimonio"],       heroSub: "sub.cabo",       unit: "unit.lugares" },
  { id: "rutas",       label: "cat.rutas_senderos",    icon: "ruta",        th: "th-ruta",        bg: "../shared/tiles/rutas.jpg",       res: ["ruta"],               heroSub: "sub.rutas",      unit: "unit.rutas" },
  { id: "naturaleza",  label: "cat.naturaleza",        icon: "naturaleza",  th: "th-naturaleza",  bg: "../shared/tiles/naturaleza.jpg",  res: ["mirador"], etiquetas: ["naturaleza"], subchips: ["mirador"],       heroSub: "sub.naturaleza", unit: "unit.lugares" },
  { id: "ceramica",    label: "cat.ceramica_jarapas", icon: "artesania",   th: "th-gastro",      bg: "../shared/tiles/ceramica.jpg",    etiquetas: ["ceramica", "artesania", "jarapas"],                        heroSub: "sub.ceramica",   unit: "unit.talleres" },
  { id: "gastronomia", label: "cat.gastronomia",       icon: "gastronomia", th: "th-gastro",      bg: "../shared/tiles/gastronomia.jpg", srv: ["gastronomia_restaurante", "gastronomia_bar", "gastronomia_cafeteria"],           heroSub: "sub.gastro",     unit: "unit.locales" },
  /* Agenda y Empresas — se abren desde el dock inferior; no van en el grid del home */
  { id: "eventos",     label: "categorias.eventos",    icon: "eventos",     th: "th-evento",      hiddenFromGrid: true, events: true, heroSub: "sub.eventos", unit: "unit.eventos" },
  { id: "empresas",    label: "cat.empresas",          icon: "edificio",    th: "th-servicio",    hiddenFromGrid: true, empresas: true,
    sectores: ["gastronomia", "alojamiento", "ocio_activo", "comercio", "servicios"], heroSub: "sub.empresas", unit: "unit.locales" },
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
document.querySelectorAll("#btn-open-chat, [data-open-chat]").forEach((b) =>
  b.addEventListener("click", () => { showView("view-chat"); const inp = $("#chatbot-input"); if (inp) inp.focus(); })
);
$("#btn-open-map")?.addEventListener("click", abrirMapa);
document.querySelectorAll('[data-dock-action="empresas"]').forEach((b) =>
  b.addEventListener("click", () => abrirCategoria("empresas"))
);
document.querySelectorAll('[data-dock-action="agenda"]').forEach((b) =>
  b.addEventListener("click", () => abrirCategoria("eventos"))
);
document.querySelectorAll('[data-dock-action="social"]').forEach((b) =>
  b.addEventListener("click", () => { const d = $("#social-dialog"); if (d) { d.showModal(); resetIdle(); } })
);
{
  const sd = $("#social-dialog");
  if (sd) {
    $("#social-close")?.addEventListener("click", () => sd.close());
    sd.addEventListener("click", (e) => { if (e.target === sd) sd.close(); });
  }
}

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
  renderTicker();
  renderDestacado();
  pintarFechas();
  pintarMeteo();
  const listaVisible = !document.getElementById("view-list").hidden;
  if (currentCat && listaVisible) abrirCategoria(currentCat, currentChip);
  // Repintar la ficha abierta con el nuevo idioma (título, descripción, servicios, etiquetas…)
  if (dialog?.open && currentPoi) openDetail(currentPoi, currentPoiCat);
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
  const hhmm = now.toLocaleTimeString(currentLang, { hour: "2-digit", minute: "2-digit", hour12: false });
  ["#clock", "#header-clock", "#hero-time"].forEach((sel) => {
    const el = $(sel); if (el) el.textContent = hhmm;
  });
}
function pintarFechas() {
  const now = new Date();
  const larga = now.toLocaleDateString(currentLang, { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  const media = now.toLocaleDateString(currentLang, { weekday: "long", day: "numeric", month: "long" });
  const fd = $("#footer-date"); if (fd) fd.textContent = larga;
  const hp = $("#header-date-pill"); if (hp) hp.textContent = media;
  const hd = $("#hero-date"); if (hd) hd.textContent = media;
}
setInterval(updateClock, 1000);
updateClock();
pintarFechas();

// ============================================================
// El tiempo hoy (Open-Meteo, endpoint público /gemelo/meteo)
// ============================================================
const ICONO_SOL =
  '<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true"><circle cx="12" cy="12" r="4.4" fill="#F5C518"/>' +
  '<g stroke="#F5C518" stroke-width="2" stroke-linecap="round"><path d="M12 2.6v2.8M12 18.6v2.8M2.6 12h2.8M18.6 12h2.8M5.2 5.2l2 2M16.8 16.8l2 2M18.8 5.2l-2 2M7.2 16.8l-2 2"/></g></svg>';

let meteoCache = null;

/* Condiciones WMO (Open-Meteo) → texto corto multilingüe para el pill. */
const METEO_COND = {
  desp: { es: "Despejado", en: "Clear", de: "Klar", fr: "Dégagé" },
  parc: { es: "Poco nuboso", en: "Partly cloudy", de: "Teils bewölkt", fr: "Partiellement nuageux" },
  nub: { es: "Nublado", en: "Cloudy", de: "Bewölkt", fr: "Nuageux" },
  nieb: { es: "Niebla", en: "Fog", de: "Nebel", fr: "Brouillard" },
  llov: { es: "Llovizna", en: "Drizzle", de: "Nieselregen", fr: "Bruine" },
  lluv: { es: "Lluvia", en: "Rain", de: "Regen", fr: "Pluie" },
  chub: { es: "Chubascos", en: "Showers", de: "Schauer", fr: "Averses" },
  niev: { es: "Nieve", en: "Snow", de: "Schnee", fr: "Neige" },
  torm: { es: "Tormenta", en: "Storm", de: "Gewitter", fr: "Orage" },
};
function grupoWmo(c) {
  if (c == null) return null;
  if (c === 0) return "desp";
  if (c === 1 || c === 2) return "parc";
  if (c === 3) return "nub";
  if (c === 45 || c === 48) return "nieb";
  if (c >= 51 && c <= 57) return "llov";
  if (c >= 61 && c <= 67) return "lluv";
  if ((c >= 71 && c <= 77) || c === 85 || c === 86) return "niev";
  if (c >= 80 && c <= 82) return "chub";
  if (c >= 95) return "torm";
  return null;
}
function condicionMeteo(codigo) {
  const g = grupoWmo(codigo);
  if (!g) return null;
  const tr = METEO_COND[g];
  return tr[currentLang] || tr.es;
}

function pintarMeteo() {
  const el = $("#header-weather");
  if (!el) return;
  const t = dict();
  /* Fuente: Open-Meteo (endpoint público /gemelo/meteo). Si no hay red, se
   * mantiene un placeholder estacional para no romper el diseño de la home. */
  const m = meteoCache || { temp: 29, wmo: null };
  const temp = m.temp != null ? Math.round(m.temp) : 29;
  const cond = condicionMeteo(m.wmo);
  const etiqueta = escapeHtml((cond || t["meteo.soleado"] || "Soleado").toUpperCase());
  el.innerHTML =
    `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.4" fill="#E0912F"/><g stroke="#E0912F" stroke-width="2.2" stroke-linecap="round" fill="none"><path d="M12 2v2.4M12 19.6V22M4 12H1.6M22.4 12H20M5.1 5.1l1.7 1.7M17.2 17.2l1.7 1.7M18.9 5.1l-1.7 1.7M6.8 17.2l-1.7 1.7"/></g></svg>` +
    `<div><span class="tmp">${temp}°</span><span class="wl">${etiqueta}</span></div>`;
  el.hidden = false;
}

async function cargarMeteo() {
  try {
    const m = await apiGet("/gemelo/meteo");
    meteoCache = { temp: m.temperatura_c, wmo: m.codigo_wmo };
  } catch { meteoCache = null; } /* sin red: se usa el placeholder estacional */
  pintarMeteo();
}
cargarMeteo();
setInterval(cargarMeteo, 10 * 60 * 1000); /* Open-Meteo se refresca ~cada 15 min */

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
  const grid = $("#home-cats");
  if (!grid) return;
  grid.innerHTML = CATS.filter((c) => !c.hiddenFromGrid).map((c) => {
    const label = escapeHtml(t[c.label] || capitalize(c.id));
    const bgStyle = c.solid ? "" : ` style="background-image: url('${c.bg}');"`;
    const solidCls = c.solid ? ` is-solid${c.alt ? " is-alt" : ""}` : "";
    return (
      `<button class="tt-ptile${solidCls}" role="listitem" data-cat="${c.id}" aria-label="${label}"${bgStyle}>` +
        `<span class="psh" aria-hidden="true"></span>` +
        `<span class="plabel">${label}</span>` +
      `</button>`
    );
  }).join("");
  grid.querySelectorAll(".tt-ptile").forEach((b) =>
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
      } else if (c.res) {
        const totales = await Promise.all(c.res.map(async (cat) => {
          const d = await apiGet(`/tourism/resources?categoria=${cat}&publicado=true&page_size=1`);
          return d.total ?? 0;
        }));
        catCounts[c.id] = totales.reduce((a, b) => a + b, 0);
      } else {
        catCounts[c.id] = 0;
      }
    } catch { catCounts[c.id] = (DEMO_RESOURCES[c.id] || []).length || 0; }
  }));
  renderHomeCats();
}

// ============================================================
// HOME: ticker de AVISOS municipales — CMS del panel (canal «totem»);
// el texto demo solo se usa si la API no está disponible.
// ============================================================
const AVISOS_DEMO = {
  es: [
    "Abierto el plazo de inscripción de la Escuela de Verano hasta el 15 de julio",
    "Corte de agua programado en San Isidro el martes de 9:00 a 13:00 por mejora de la red",
    "Nueva línea de autobús San José – Villa de Níjar los fines de semana",
    "Recogida de enseres a domicilio: solicita cita en el 950 360 012",
  ],
  en: [
    "Summer School registration open until 15 July",
    "Scheduled water cut in San Isidro on Tuesday 9:00 – 13:00 due to network works",
    "New weekend bus line San José – Villa de Níjar",
    "Bulky waste pickup on request: call 950 360 012",
  ],
  de: [
    "Anmeldung zur Sommerschule bis 15. Juli geöffnet",
    "Geplante Wasserabschaltung in San Isidro am Dienstag 9:00 – 13:00 wegen Netzarbeiten",
    "Neue Wochenendbuslinie San José – Villa de Níjar",
    "Sperrmüllabholung auf Anfrage: 950 360 012",
  ],
  fr: [
    "Inscriptions à l'École d'Été ouvertes jusqu'au 15 juillet",
    "Coupure d'eau programmée à San Isidro mardi 9h00 – 13h00 pour travaux sur le réseau",
    "Nouvelle ligne de bus le week-end San José – Villa de Níjar",
    "Ramassage d'encombrants à domicile : rendez-vous au 950 360 012",
  ],
};

let avisosCms = null; /* null = API no disponible (cae al demo); [] = sin avisos → se oculta */

async function cargarAvisos() {
  try { avisosCms = await apiGet("/cms/publico/totem"); }
  catch { avisosCms = null; }
  renderTicker();
}

function renderTicker() {
  const el = $("#home-avisos");
  const track = $("#avisos-track");
  if (!el || !track) return;
  const items = avisosCms !== null
    ? avisosCms.map((a) => (a.titulo_i18n && a.titulo_i18n[currentLang]) || a.titulo).filter(Boolean)
    : (AVISOS_DEMO[currentLang] || AVISOS_DEMO.es);
  if (!items.length) { el.hidden = true; return; }
  /* Se duplica para garantizar loop continuo aunque el CSS dependa del ancho renderizado */
  track.textContent = items.concat(items).join("   •   ");
  el.hidden = false;
}
cargarAvisos();
setInterval(cargarAvisos, 5 * 60 * 1000); /* el gestor puede publicar avisos en cualquier momento */

// ============================================================
// HOME: tarjeta "Destacado esta semana" (próximo evento del CMS)
// ============================================================
let destacadoEvento = null;

function _fmtEvento(ev) {
  if (!ev) return "";
  const d = new Date(ev.fecha_inicio);
  const fecha = d.toLocaleDateString(currentLang, { day: "numeric", month: "short" });
  const hora = d.toLocaleTimeString(currentLang, { hour: "2-digit", minute: "2-digit", hour12: false });
  const dir = ev.direccion ? ` · ${ev.direccion}` : "";
  return `${fecha}${dir} · ${hora}`;
}

async function cargarDestacado() {
  try {
    const d = await apiGet("/tourism/events?publicado=true&page_size=1");
    destacadoEvento = (d.items && d.items[0]) || null;
  } catch { destacadoEvento = (DEMO_EVENTS && DEMO_EVENTS[0]) || null; }
  renderDestacado();
}

function renderDestacado() {
  const wrap = $("#home-feat");
  if (!wrap || !destacadoEvento) { if (wrap) wrap.hidden = true; return; }
  const ev = destacadoEvento;
  const nombre = (ev.nombre_i18n && ev.nombre_i18n[currentLang]) || ev.nombre;
  $("#feat-title").textContent = nombre;
  $("#feat-sub").textContent = _fmtEvento(ev);
  /* la API guarda las imágenes como lista de URLs (texto); se admite también {url} */
  const primera = ev.imagenes && ev.imagenes[0];
  const img = (typeof primera === "string" ? primera : primera && primera.url) || "";
  const fill = $("#feat-image");
  if (fill) fill.style.backgroundImage = img ? `url('${img}')` : "";
  wrap.hidden = false;
  wrap.onclick = () => abrirCategoria("eventos");
}

// ============================================================
// HOME: foto del hero (recurso destacado con imagen)
// ============================================================
async function cargarHeroFoto() {
  const img = $("#hero-photo");
  if (!img) return;
  /* Foto local del Cabo de Gata (acantilados sobre el mar). Cuando el CMS
   * tenga imagen del recurso destacado se sustituye con `r.imagenes[0].url`. */
  img.src = "../shared/cabo-de-gata-hero.jpg";
  img.alt = "Cabo de Gata";
  img.hidden = false;
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
  const n = catCounts[catId];
  const unit = t[c.unit || "unit.lugares"] || "lugares";
  $("#list-count").textContent = n != null ? `${n} ${unit}` : "";
  const heroTxt = $("#list-hero-txt");
  if (heroTxt) heroTxt.textContent = t[c.heroSub || "hero.destino_generico"] || "Cabo de Gata · Níjar";
  renderChips(c);
  showView("view-list");

  const grid = $("#content-grid");
  grid.setAttribute("aria-busy", "true");
  grid.innerHTML = `<p class="content-loading">${t["loading.contenido"] || "Cargando contenidos…"}</p>`;

  if (chip === "emergencias") { renderEmergencies(grid); grid.setAttribute("aria-busy", "false"); return; }
  if (c.events) { await renderAgenda(grid, chip); grid.setAttribute("aria-busy", "false"); return; }
  if (c.empresas) { await renderEmpresas(grid, chip); grid.setAttribute("aria-busy", "false"); return; }

  let items = [];
  // Sub-chip por etiqueta (playas, cabo, naturaleza): siempre se cargan todos los items de la categoría y luego se filtra por tag en cliente.
  const chipEsSubchip = c.subchips && c.subchips.includes(chip);
  if (c.srv) {
    const servicios = await getServicios();
    items = servicios.filter((s) => (chip === "todas" ? c.srv.includes(s.tipo) : s.tipo === chip));
  } else if (c.res || c.etiquetas) {
    const cats = c.res ? (chipEsSubchip ? c.res : (chip === "todas" ? c.res : [chip])) : [];
    for (const cat of cats) {
      try {
        const d = await apiGet(`/tourism/resources?categoria=${encodeURIComponent(cat)}&publicado=true&page_size=20`);
        items.push(...(d.items || []));
      } catch { /* siguiente categoría */ }
    }
    /* Filtro por etiquetas: sin endpoint dedicado, se filtra en cliente sobre todos los recursos */
    if (c.etiquetas && c.etiquetas.length) {
      try {
        const d = await apiGet(`/tourism/resources?publicado=true&page_size=100`);
        const tagSet = c.etiquetas.map((t) => t.toLowerCase());
        const matches = (d.items || []).filter((r) => (r.etiquetas || []).some((e) => tagSet.includes(String(e).toLowerCase())));
        /* deduplica por id */
        const seen = new Set(items.map((x) => x.id));
        matches.forEach((m) => { if (!seen.has(m.id)) items.push(m); });
      } catch { /* mantén lo que haya */ }
    }
  }
  if (items.length === 0 && !c.srv) items = DEMO_RESOURCES[catId] || [];
  // Aplica el filtro de sub-chip por etiqueta en cliente
  if (chipEsSubchip) {
    items = items.filter((r) => (r.etiquetas || []).some((e) => String(e).toLowerCase() === chip.toLowerCase()));
  }
  renderItems(grid, items, c);
  grid.setAttribute("aria-busy", "false");
}

// ============================================================
// EMPRESAS: apartado de publicidad (anunciantes del panel)
// ============================================================
let empresasCache = null;

/* Métricas de visibilidad (facturación de campañas): lote anónimo al backend.
   Fallo silencioso — la publicidad nunca puede romper el tótem. */
function registrarMetricasEmpresas(eventos) {
  if (!eventos.length) return;
  fetch(`${API_BASE}/publicidad/publico/metricas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ eventos }),
  }).catch(() => {});
}

async function renderEmpresas(grid, chip = "todas") {
  const t = dict();
  if (!empresasCache) {
    try { empresasCache = await apiGet("/publicidad/publico/totem"); }
    catch { empresasCache = []; } /* sin backend: apartado vacío, sin datos inventados */
  }
  catCounts.empresas = empresasCache.length;
  const items = empresasCache.filter((e) => chip === "todas" || e.sector === chip);
  $("#list-count").textContent = `${items.length} ${t["unit.locales"] || "locales"}`;
  if (!items.length) {
    grid.innerHTML = `<p class="content-loading">${t["empty.contenido"] || "Sin contenidos disponibles"}</p>`;
    return;
  }
  grid.innerHTML =
    `<p class="tt-emp-aviso">${escapeHtml(t["empresas.aviso"] || "Espacio de empresas colaboradoras del destino")}</p>` +
    items.map((e, i) => empresaCard(e, i)).join("");

  /* Impresión: la tarjeta se ha mostrado en pantalla */
  registrarMetricasEmpresas(items.map((e) => ({ empresa_id: e.id, tipo: "impresion", n: 1 })));
  /* Toque: el visitante pulsa la tarjeta */
  grid.querySelectorAll(".tt-emp[data-emp-id]").forEach((card) =>
    card.addEventListener("click", () =>
      registrarMetricasEmpresas([{ empresa_id: card.dataset.empId, tipo: "toque", n: 1 }])));
}

function empresaCard(e, index) {
  const t = dict();
  const desc = e.descripcion_i18n?.[currentLang] || e.descripcion || "";
  const primera = e.imagenes && e.imagenes[0];
  const img = (typeof primera === "string" ? primera : primera && primera.url) || "";
  const thumbBg = img
    ? `background-image: url('${escapeAttr(img)}'); background-size: cover; background-position: center;`
    : "";
  const meta = [e.nucleo, e.direccion].filter(Boolean).join(" · ");
  const contacto = [e.telefono, e.web ? String(e.web).replace(/^https?:\/\//, "") : null]
    .filter(Boolean).join(" · ");
  return `
    <div class="tt-lb tt-emp${e.destacado ? " is-dest" : ""}" data-emp-id="${escapeAttr(e.id)}">
      <span class="tt-lb-num" aria-hidden="true">${String(index + 1).padStart(2, "0")}</span>
      <span class="tt-lb-thumb th-servicio" style="${thumbBg}" aria-hidden="true"></span>
      <span class="tt-lb-body">
        <span class="tt-lb-title">${escapeHtml(e.nombre)}
          ${e.destacado ? `<span class="tt-emp-badge">${escapeHtml(t["empresas.destacada"] || "Destacada")}</span>` : ""}
          <span class="tt-tag tt-tag--info">${escapeHtml(t["sector." + e.sector] || String(e.sector).replace(/_/g, " "))}</span>
        </span>
        ${desc ? `<span class="tt-lb-sub">${escapeHtml(desc)}</span>` : ""}
        ${meta || contacto ? `<span class="tt-lb-sub">${escapeHtml(meta)}${meta && contacto ? " · " : ""}${escapeHtml(contacto)}</span>` : ""}
      </span>
    </div>`;
}

function renderChips(c) {
  const t = dict();
  const wrap = $("#list-chips");
  // Prioridad: subchips por etiqueta (playas, cabo, naturaleza) > srv > res > sectores.
  const subs = c.subchips || c.srv || c.res || c.sectores || [];
  const chips = [`<button class="tt-chip" data-chip="todas" aria-pressed="${currentChip === "todas"}">${t["chips.todas"] || "Todas"}</button>`];
  if (subs.length > 1 || (c.subchips && c.subchips.length >= 1)) {
    subs.forEach((s) => {
      let label;
      if (c.subchips) label = t[`chip.${s}`] || capitalize(s);
      else if (c.sectores) label = t["sector." + s] || s.replace(/_/g, " ");
      else label = tagLabel(s);
      chips.push(`<button class="tt-chip" data-chip="${s}" aria-pressed="${currentChip === s}">${escapeHtml(label)}</button>`);
    });
  }
  if (c.emergencias) {
    chips.push(`<button class="tt-chip tt-chip--ico" data-chip="emergencias" aria-pressed="${currentChip === "emergencias"}">${icono("emergencias", "tt-svg--tag")} ${t["categorias.emergencias"] || "Emergencias"}</button>`);
  }
  wrap.innerHTML = chips.join("");
  wrap.querySelectorAll(".tt-chip").forEach((b) =>
    b.addEventListener("click", () => abrirCategoria(c.id, b.dataset.chip)));
}

function itemCard(r, c, index) {
  const nombre = r.nombre_i18n?.[currentLang] || r.nombre;
  const desc = r.descripcion_i18n?.[currentLang] || r.descripcion_corta || r.descripcion || "";
  const latlon = extractLatLon(r);
  const km = latlon ? haversineKm(latlon[0], latlon[1]) : null;
  const sub = [r.municipio, r.direccion].filter(Boolean).join(" · ") || (desc ? String(desc).slice(0, 90) + (String(desc).length > 90 ? "…" : "") : "");
  const meta = [];
  if (km != null) meta.push(km < 1 ? Math.round(km * 1000) + " m" : km.toFixed(1) + " km");
  if (r.horario && typeof r.horario === "string") meta.push(escapeHtml(r.horario));
  const img = r.imagenes?.[0];
  const num = String((index ?? 0) + 1).padStart(2, "0");
  const thumbBg = img
    ? `background-image: url('${escapeAttr(img)}'); background-size: cover; background-position: center;`
    : "";
  return `
    <button class="tt-lb" data-urn="${escapeAttr(r.urn || r.id || "")}">
      <span class="tt-lb-num" aria-hidden="true">${num}</span>
      <span class="tt-lb-thumb ${c.th}" style="${thumbBg}" aria-hidden="true"></span>
      <span class="tt-lb-body">
        <span class="tt-lb-title">${escapeHtml(nombre)}</span>
        <span class="tt-lb-sub">${escapeHtml(sub)}${meta.length ? " · " + meta.join(" · ") : ""}</span>
      </span>
      <span class="tt-lb-go" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg>
      </span>
    </button>`;
}

function renderItems(grid, items, c) {
  const t = dict();
  if (!items.length) {
    grid.innerHTML = `<p class="content-loading">${t["empty.contenido"] || "Sin contenidos disponibles"}</p>`;
    return;
  }
  grid.innerHTML = items.map((r, i) => itemCard(r, c, i)).join("");
  grid.querySelectorAll(".tt-lb").forEach((btn, i) => {
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
    tiposChips.map((x) => {
      const label = t[`tipo_evento.${x}`] || capitalize(x);
      return `<button class="tt-chip" data-chip="${x}" aria-pressed="${chip === x}">${escapeHtml(label)}</button>`;
    }).join("");
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
              ${ev.tipo ? `<span class="tt-tag tt-tag--rose">${escapeHtml(t[`tipo_evento.${ev.tipo}`] || capitalize(ev.tipo))}</span>` : ""}
              ${ev.direccion ? `<span class="tt-tag tt-tag--info">${escapeHtml(ev.direccion)}</span>` : ""}
            </span>
            <h3>${escapeHtml(nombre)}</h3>
            <span class="tt-item-meta"><span>${icono("reloj")} ${hora}</span>${ev.precio ? `<span>${icono("precio")} ${escapeHtml(String(ev.precio))}</span>` : ""}${ev.organizador ? `<span>${icono("edificio")} ${escapeHtml(ev.organizador)}</span>` : ""}</span>
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
      <span class="tt-thumb th-servicio" aria-hidden="true" style="display:grid;place-items:center">${icono("emergencias", "tt-svg--xl")}</span>
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
  { key: "fecha_inicio", icon: "fecha", label: "info.fecha", format: "datetime" },
  { key: "direccion", icon: "lugar", label: "info.direccion", wide: true },
  { key: "municipio", icon: "alojamiento", label: "info.municipio" },
  { key: "horario", icon: "reloj", label: "info.horario", format: "horario", wide: true },
  { key: "precio", icon: "precio", label: "info.precio", format: "i18n" },
  { key: "telefono", icon: "telefono", label: "info.telefono" },
  { key: "email", icon: "email", label: "info.email" },
  { key: "web", icon: "web", label: "info.web" },
  { key: "organizador", icon: "edificio", label: "info.organizador", format: "i18n" },
  { key: "capacidad_aforo", icon: "usuario", label: "info.aforo", format: "people" },
  { key: "servicios_disponibles", icon: "campana", label: "info.servicios", format: "serviciosList", wide: true },
  { key: "accesibilidad", icon: "accesible", label: "info.accesibilidad", format: "acc", wide: true },
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
      return Array.isArray(value)
        ? value.map((s) => dict()[`servicio.${s}`] || I18N.es?.[`servicio.${s}`] || capitalize(String(s).replace(/_/g, " "))).join(" · ")
        : String(value);
    case "acc":
      if (value && typeof value === "object") return Object.entries(value).map(([k, v]) => `${capitalize(k.replace(/_/g, " "))}: ${v === true ? "✓" : v}`).join(" · ");
      return String(value);
    default: return String(value);
  }
}

let currentPoi = null;
let currentPoiCat = null;

function openDetail(r, c) {
  currentPoi = r;
  currentPoiCat = c;
  const t = dict();
  const nombre = r.nombre_i18n?.[currentLang] || r.nombre || "—";
  $("#poi-title").textContent = nombre;
  $("#poi-body").textContent = r.descripcion_i18n?.[currentLang] || r.descripcion || r.descripcion_corta || "";

  // Breadcrumb superior con la categoría (ej. "PLAYAS Y CALAS")
  const bc = $("#poi-breadcrumb");
  if (bc) bc.textContent = c ? String(t[c.label] || capitalize(c.id)).toUpperCase() : "";

  // Subtítulo del hero: municipio · dirección · longitud si aplica
  const sub = $("#poi-sub");
  if (sub) {
    const parts = [r.municipio, r.direccion].filter(Boolean);
    if (r.longitud_m) parts.push(`${r.longitud_m} m`);
    sub.textContent = parts.join(" · ");
  }

  // Hero: imagen real o color azul institucional
  const hero = $("#poi-image");
  const img = r.imagenes?.[0];
  hero.style.backgroundImage = img ? `url('${img}')` : "";

  // Badge superior naranja (kicker sobre el hero, ej. "ÍCONO DEL PARQUE NATURAL")
  const cat = r.categoria || r.tipo || "";
  const badgeText = (r.etiquetas || []).some((e) => /parque/i.test(e)) || cat === "parque_natural"
    ? (t["badge.parque_natural"] || "ÍCONO DEL PARQUE NATURAL")
    : cat ? String(tagLabel(cat)).toUpperCase() : "";
  const tag = $("#poi-tag");
  if (badgeText) { tag.textContent = badgeText; tag.hidden = false; } else tag.hidden = true;

  // 3 tarjetas de stats en fila (formato simple: label + valor)
  const stats = [];
  if (r.longitud_m || r.longitud) stats.push([t["info.longitud"] || "Longitud", `${r.longitud_m || r.longitud} m`]);
  const latlon = extractLatLon(r);
  if (latlon) {
    const km = haversineKm(latlon[0], latlon[1]);
    stats.push([t["info.distancia"] || "Distancia", km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(1)} km`]);
  }
  if (r.acceso) stats.push([t["info.acceso"] || "Acceso", r.acceso]);
  else if (r.horario && typeof r.horario === "string") stats.push([t["info.horario"] || "Horario", r.horario]);
  if (r.temporada) stats.push([t["info.temporada"] || "Temporada", r.temporada]);
  else if (r.servicios_disponibles && Array.isArray(r.servicios_disponibles) && r.servicios_disponibles.length) stats.push([t["info.servicios"] || "Servicios", `${r.servicios_disponibles.length}`]);
  else if (r.fecha_inicio) stats.push([t["info.fecha"] || "Fecha", new Date(r.fecha_inicio).toLocaleDateString(currentLang, { day: "2-digit", month: "short" })]);
  $("#poi-stats").innerHTML = stats.slice(0, 3).map(([l, v]) =>
    `<div class="tt-poistat"><small>${escapeHtml(String(l).toUpperCase())}</small><b>${escapeHtml(String(v))}</b></div>`).join("");

  // CTA azul "CÓMO LLEGAR" (si tenemos dirección o municipio + coordenadas)
  const cta = $("#poi-cta");
  if (cta) {
    const dest = r.direccion || r.municipio || "";
    let extra = "";
    if (latlon) {
      const km = haversineKm(latlon[0], latlon[1]);
      extra = km < 1 ? ` · ${Math.round(km * 1000)} m ${t["info.desde_totem"] || "desde el tótem"}` : ` · ${km.toFixed(1)} km ${t["info.desde_totem"] || "desde el tótem"}`;
    }
    if (dest || latlon) {
      cta.innerHTML =
        `<span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.5a7 7 0 017 7c0 5-7 12-7 12s-7-7-7-12a7 7 0 017-7z"/><circle cx="12" cy="9.5" r="2.6"/></svg></span>` +
        `<span class="txt"><small>${escapeHtml(t["cta.como_llegar"] || "Cómo llegar")}</small><strong>${escapeHtml(dest)}${extra}</strong></span>`;
      cta.hidden = false;
      cta.onclick = latlon ? (() => { dialog.close(); abrirMapa(latlon); }) : null;
      cta.style.cursor = latlon ? "pointer" : "default";
    } else { cta.hidden = true; }
  }

  // Metadatos (tarjeta secundaria)
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
    row.innerHTML = `<dt aria-hidden="true">${icono(field.icon, "tt-svg--meta")}</dt><dd><strong>${escapeHtml(dict()[field.label] || field.label)}:</strong> ${escapeHtml(formatted)}</dd>`;
    meta.appendChild(row);
  }
  const metaCard = $("#poi-meta-card");
  if (metaCard) metaCard.hidden = meta.children.length === 0;

  // Etiquetas (traducidas por tagLabel(); en formato hashtag y minúsculas)
  const tagsEl = $("#poi-tags");
  const raw = (r.etiquetas || []).filter((x) => String(x).toLowerCase() !== String(cat).toLowerCase());
  tagsEl.innerHTML = raw.map((x) => `<span class="tag-chip">#${escapeHtml(String(tagLabel(x)).toLowerCase())}</span>`).join("");
  tagsEl.hidden = !raw.length;

  // Acciones
  const actions = [];
  if (latlon) {
    actions.push(`<button class="action-btn" id="poi-goto-map">${icono("lugar", "tt-svg--btn")} ${escapeHtml(dict()["action.mapa"] || "Ver en el mapa")}</button>`);
  }
  if (r.telefono) actions.push(`<a class="action-btn action-btn--secondary" href="tel:${escapeAttr(String(r.telefono).replace(/\s+/g, ""))}">${icono("telefono", "tt-svg--btn")} ${escapeHtml(dict()["action.llamar"] || "Llamar")}</a>`);
  if (r.web) actions.push(`<a class="action-btn action-btn--secondary" href="${escapeAttr(r.web)}" target="_blank" rel="noopener noreferrer">${icono("web", "tt-svg--btn")} Web</a>`);
  const actEl = $("#poi-actions");
  actEl.innerHTML = actions.join("");
  actEl.hidden = !actions.length;
  const goMap = $("#poi-goto-map");
  if (goMap) goMap.addEventListener("click", () => { dialog.close(); abrirMapa(latlon); });

  if (!dialog.open) {
    dialog.querySelector(".poi-dialog-content")?.scrollTo({ top: 0 });
    dialog.showModal();
  }
  resetIdle();
}

$("#poi-close").addEventListener("click", () => { dialog.close(); currentPoi = null; currentPoiCat = null; });
dialog.addEventListener("click", (e) => { if (e.target === dialog) { dialog.close(); currentPoi = null; currentPoiCat = null; } });

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
      <span class="tt-avatar tt-avatar--bot" aria-hidden="true">${icono("bot", "tt-svg--avatar")}</span>
      <div class="tt-bubble">${escapeHtml(t["chat.welcome"] || "¡Hola! ¿Qué te apetece hacer hoy?")}</div>
    </div>`;
}

function burbuja(texto, esUsuario) {
  const div = document.createElement("div");
  div.className = `tt-msg ${esUsuario ? "tt-msg--user" : "tt-msg--bot"}`;
  div.innerHTML = `
    <span class="tt-avatar ${esUsuario ? "tt-avatar--user" : "tt-avatar--bot"}" aria-hidden="true">${icono(esUsuario ? "usuario" : "bot", "tt-svg--avatar")}</span>
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
    sug.innerHTML = `${icono("idea", "tt-svg--tag")} ${escapeHtml(data.sugerencias.join(" · "))}`;
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
renderTicker();
cargarHeroFoto();
resetChat();
cargarConteos();
cargarDestacado();
