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

import { I18N, translateAll } from "./i18n.js?v=28";
import { DEMO_RESOURCES, answerChatbotDemo } from "./demo-data.js";

// ============================================================
// Configuración
// ============================================================
const API_BASE = window.NIJAR_API_BASE
  || (window.location.origin.startsWith("http")
    ? `${window.location.origin}/api/v1`
    : "http://localhost:8000/api/v1");

/* Cada tótem se identifica en su URL de quiosco: …/totem/?totem=albaricoques
   (se recuerda en el equipo). Sin parámetro: el del atributo data-totem-id. */
const TOTEMS_CONOCIDOS = {
  rodalquilar: [36.847, -2.041],
  albaricoques: [36.8508, -2.1222],
};
const TOTEM_SLUG = (() => {
  let slug = "";
  try {
    slug = (new URLSearchParams(location.search).get("totem") || "").toLowerCase().replace(/[^a-z0-9_-]/g, "").slice(0, 40);
    if (slug) localStorage.setItem("totem.id", slug);
    else slug = localStorage.getItem("totem.id") || "";
  } catch { /* almacenamiento no disponible */ }
  return slug || (document.body.dataset.totemId || "rodalquilar").split(":").pop();
})();
const TOTEM_ID = `urn:ngsi-ld:Totem:nijar:${TOTEM_SLUG}`;
const TOTEM_LAT = TOTEMS_CONOCIDOS[TOTEM_SLUG]?.[0] ?? parseFloat(document.body.dataset.totemLat || "36.847");
const TOTEM_LON = TOTEMS_CONOCIDOS[TOTEM_SLUG]?.[1] ?? parseFloat(document.body.dataset.totemLon || "-2.041");
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
  /* Noticias: de fondo, la portada de la noticia más reciente (cargarFondoNoticias); mientras, foto local */
  { id: "noticias", label: "cat.noticias", icon: "eventos", th: "th-evento", bg: "../shared/cabo-de-gata-hero.jpg", noticias: true, heroSub: "sub.noticias", unit: "unit.noticias" },
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
let sessionId = `totem-${TOTEM_ID}-${Date.now()}`;  /* se renueva con cada visitante */
let serviciosCache = null;      // /tourism/services (se agrupa por tipo en cliente)
let mapaLeaflet = null;
let lastAnswer = "";

const $ = (s) => document.querySelector(s);
const dict = () => I18N[currentLang] || I18N.es;

// ============================================================
// Telemetría de uso: qué ve cada visitante (anónima)
// ============================================================
/* Cada visitante es una sesión: empieza con su primera acción y termina cuando
   el tótem vuelve al reposo por inactividad. Los eventos se envían en lotes a
   /dashboards/totems/eventos y el panel los lista en «Tótems (A.1)». */
const tele = (() => {
  const cola = [];
  let activa = false, inicio = 0, ultima = 0, nEventos = 0;
  let silencio = false; /* repintados por cambio de idioma: no son acciones nuevas */

  function enviar(usarBeacon = false) {
    if (!cola.length) return;
    const lotes = new Map(); /* un lote por sesión e idioma */
    for (const e of cola.splice(0)) {
      const clave = e.sesion + "|" + e.idioma;
      if (!lotes.has(clave)) lotes.set(clave, { sesion: e.sesion, idioma: e.idioma, eventos: [] });
      lotes.get(clave).eventos.push(e.datos);
    }
    for (const { sesion, idioma, eventos } of lotes.values()) {
      for (let i = 0; i < eventos.length; i += 50) {
        const cuerpo = JSON.stringify({ totem: TOTEM_SLUG, sesion_id: sesion, idioma, eventos: eventos.slice(i, i + 50) });
        const url = `${API_BASE}/dashboards/totems/eventos`;
        if (usarBeacon && navigator.sendBeacon) {
          navigator.sendBeacon(url, new Blob([cuerpo], { type: "application/json" }));
          continue;
        }
        fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: cuerpo, keepalive: true })
          .then((r) => { if (!r.ok && r.status >= 500) throw new Error(String(r.status)); })
          .catch(() => { /* sin red: se reintenta en el siguiente envío (con tope) */
            if (cola.length < 300) eventos.slice(i, i + 50).forEach((d) => cola.push({ sesion, idioma, datos: d }));
          });
      }
    }
  }

  function registrar(evento, datos = {}) {
    if (silencio) return;
    const ahora = Date.now();
    if (!activa) {
      activa = true; inicio = ahora; nEventos = 0;
      sessionId = `totem-${TOTEM_ID}-${ahora}`;
      cola.push({ sesion: sessionId, idioma: currentLang, datos: { evento: "inicio_sesion", ts: new Date(ahora).toISOString() } });
    }
    ultima = ahora;
    nEventos++;
    const limpio = { evento, ts: new Date(ahora).toISOString() };
    for (const [k, v] of Object.entries(datos)) {
      if (v == null || v === "") continue;
      limpio[k] = typeof v === "string" ? v.slice(0, k === "detalle" ? 300 : k === "contenido" ? 200 : 64) : v;
    }
    cola.push({ sesion: sessionId, idioma: currentLang, datos: limpio });
    if (cola.length >= 20) enviar();
  }

  function finSesion() {
    if (!activa) return;
    cola.push({ sesion: sessionId, idioma: currentLang, datos: {
      evento: "fin_sesion", ts: new Date(ultima).toISOString(),
      duracion_seg: Math.max(1, Math.round((ultima - inicio) / 1000)), detalle: `${nEventos} acciones`,
    } });
    activa = false;
    enviar();
  }

  setInterval(() => enviar(), 8000);
  window.addEventListener("pagehide", () => { finSesion(); enviar(true); });
  return { registrar, finSesion, callar: (v) => { silencio = v; } };
})();

// ============================================================
// Router de vistas
// ============================================================
const VIEWS = ["view-home", "view-list", "view-chat", "view-map", "view-explore", "view-avisos", "view-detail"];
function showView(id) {
  VIEWS.forEach((v) => {
    const el = document.getElementById(v);
    if (!el) return;
    el.classList.toggle("is-on", v === id);
    el.hidden = v !== id;
  });
  const destino = { "view-home": "inicio", "view-explore": "explorar", "view-map": "mapa", "view-avisos": "avisos" }[id];
  document.querySelectorAll(".v5-nav [data-ir]").forEach((b) => {
    if (b.dataset.ir === destino) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
  });
  window.scrollTo({ top: 0 });
  resetIdle();
}
document.querySelectorAll("[data-back]").forEach((b) => b.addEventListener("click", () => showView("view-home")));
$("#btn-home-brand").addEventListener("click", () => showView("view-home"));
document.querySelectorAll("#btn-open-chat, [data-open-chat]").forEach((b) =>
  b.addEventListener("click", () => { tele.registrar("chatbot", { seccion: "chatbot" }); showView("view-chat"); const inp = $("#chatbot-input"); if (inp) inp.focus(); })
);
$("#btn-open-map")?.addEventListener("click", abrirMapa);
document.querySelectorAll('[data-dock-action="empresas"]').forEach((b) =>
  b.addEventListener("click", () => abrirCategoria("empresas"))
);
document.querySelectorAll('[data-dock-action="agenda"]').forEach((b) =>
  b.addEventListener("click", () => abrirCategoria("eventos"))
);
document.querySelectorAll('[data-dock-action="social"]').forEach((b) =>
  b.addEventListener("click", () => { const d = $("#social-dialog"); if (d) { tele.registrar("redes", { seccion: "redes" }); d.showModal(); resetIdle(); } })
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
  renderHomeV5();
  pintarFechas();
  pintarMeteo();
  const listaVisible = !document.getElementById("view-list").hidden;
  tele.callar(true); /* repintado, no una acción nueva del visitante */
  if (currentCat && listaVisible) abrirCategoria(currentCat, currentChip);
  // Repintar la ficha abierta con el nuevo idioma (título, descripción, servicios, etiquetas…)
  if (dialog?.open && currentPoi) openDetail(currentPoi, currentPoiCat);
  tele.callar(false);
  resetChat();
}
document.querySelectorAll(".lang-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (btn.dataset.lang !== currentLang) tele.registrar("idioma", { detalle: btn.dataset.lang });
    applyLanguage(btn.dataset.lang);
  });
});

// ============================================================
// Accesibilidad: texto grande, contraste, skip
// ============================================================
const textBtn = $("#text-size-toggle");
textBtn.addEventListener("click", () => {
  const on = document.body.classList.toggle("text-lg-mode");
  textBtn.setAttribute("aria-pressed", String(on));
  tele.registrar("accesibilidad", { detalle: on ? "texto grande activado" : "texto grande desactivado" });
});
function toggleContrast() {
  const on = document.body.classList.toggle("high-contrast");
  $("#contrast-toggle").setAttribute("aria-pressed", String(on));
  $("#footer-contrast").setAttribute("aria-pressed", String(on));
}
const contrasteConTelemetria = () => {
  toggleContrast();
  tele.registrar("accesibilidad", { detalle: document.body.classList.contains("high-contrast") ? "alto contraste activado" : "alto contraste desactivado" });
};
$("#contrast-toggle").addEventListener("click", contrasteConTelemetria);
$("#footer-contrast").addEventListener("click", contrasteConTelemetria);
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
  const corta = now.toLocaleDateString(currentLang, { weekday: "short", day: "numeric", month: "short", year: "numeric" });
  const hp = $("#header-date-pill"); if (hp) hp.textContent = capitalize(corta.replace(/,/g, ""));
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
  const etiqueta = escapeHtml(cond || t["meteo.soleado"] || "Soleado");
  el.innerHTML =
    `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.4" fill="#E8742B"/><g stroke="#E8742B" stroke-width="2.2" stroke-linecap="round" fill="none"><path d="M12 2v2.4M12 19.6V22M4 12H1.6M22.4 12H20M5.1 5.1l1.7 1.7M17.2 17.2l1.7 1.7M18.9 5.1l-1.7 1.7M6.8 17.2l-1.7 1.7"/></g></svg>` +
    `<span class="tmp">${temp}°</span> <span class="wl">${etiqueta}</span>`;
  el.hidden = false;
}

async function cargarMeteo() {
  try {
    /* Cada tótem pide el tiempo de SU ubicación (data-totem-lat/lon). */
    const q = Number.isFinite(TOTEM_LAT) && Number.isFinite(TOTEM_LON)
      ? `?lat=${TOTEM_LAT}&lon=${TOTEM_LON}` : "";
    const m = await apiGet(`/gemelo/meteo${q}`);
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
  /* no-store: el tótem no se recarga nunca; evita servir listados viejos de caché */
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

let serviciosCacheTs = 0;
/* Todos los servicios publicados (paginado: la gastronomía importada de
 * OpenStreetMap supera los 200). Caché de 1 h: el tótem no se recarga nunca. */
async function getServicios() {
  if (serviciosCache && Date.now() - serviciosCacheTs < 60 * 60 * 1000) return serviciosCache;
  const todos = [];
  try {
    for (let page = 1; page <= 5; page++) {
      const data = await apiGet(`/tourism/services?publicado=true&page=${page}&page_size=200`);
      todos.push(...(data.items || []));
      if (todos.length >= (data.total ?? 0) || !(data.items || []).length) break;
    }
    serviciosCache = todos;
    serviciosCacheTs = Date.now();
  } catch { if (!serviciosCache) serviciosCache = todos; }
  return serviciosCache;
}

/* Ordena por cercanía al tótem (los que no tienen coordenadas, al final). */
function porCercania(items) {
  const d = (r) => { const ll = extractLatLon(r); return ll ? haversineKm(ll[0], ll[1]) : Infinity; };
  return items.map((r) => [d(r), r]).sort((a, b) => a[0] - b[0]).map((x) => x[1]);
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
let fondoNoticias = null;   /* portada de la última noticia con imagen (Strapi) */

/* Accesos de la home (rediseño v5): icono sobre degradado + título. Son las
 * categorías reales del tótem; Noticias se abre desde su bloque y el resto de
 * categorías desde «Explorar». */
const TILES_HOME = [
  { cat: "cabo", grad: ["#F7A55E", "#E0702A"], ico: "paisaje" },
  { cat: "rutas", grad: ["#6FA55B", "#3F7A34"], ico: "senderista" },
  { cat: "naturaleza", grad: ["#3D8FDB", "#1F63B5"], ico: "hoja" },
  { cat: "playas", grad: ["#36BFD0", "#138FA6"], ico: "ola" },
  { cat: "eventos", grad: ["#F0645A", "#D13C36"], ico: "calendario", label: "dock.agenda" },
  { cat: "ceramica", grad: ["#F8C04A", "#E8962A"], ico: "vasija" },
  { cat: "gastronomia", grad: ["#B5703F", "#8A4A22"], ico: "cubiertos" },
  { cat: "empresas", grad: ["#8C6BD8", "#6143B5"], ico: "tienda" },
];
const ICONOS_TILE = {
  paisaje: '<rect x="4" y="7" width="40" height="34" rx="7" fill="none" stroke="#fff" stroke-width="3.4"/><circle cx="31" cy="17" r="4.5" fill="#fff"/><path d="M7 37l11-13 8 9 6-6 10 10" fill="none" stroke="#fff" stroke-width="3.4" stroke-linejoin="round"/>',
  senderista: '<circle cx="27" cy="8" r="4.5" fill="#fff"/><path d="M19 44l5-14 6 6v8M17 26l4-9 9 4 4 7M22 17l-4 11" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><path d="M36 22v22" stroke="#fff" stroke-width="3" stroke-linecap="round"/>',
  hoja: '<path d="M38 8C20 8 8 18 8 32c0 4 1 7 3 9 18 1 29-13 27-33z" fill="#fff"/><path d="M11 41c6-10 13-17 22-23" stroke="#1F63B5" stroke-width="3" stroke-linecap="round" fill="none"/>',
  ola: '<path d="M4 30c5-5 9-5 14 0s9 5 14 0 9-5 12-2M4 39c5-5 9-5 14 0s9 5 14 0 9-5 12-2" fill="none" stroke="#fff" stroke-width="3.6" stroke-linecap="round"/><path d="M10 22c4-9 15-13 24-8-7 0-11 3-12 9" fill="none" stroke="#fff" stroke-width="3.6" stroke-linecap="round"/>',
  calendario: '<rect x="6" y="10" width="36" height="32" rx="6" fill="#fff"/><path d="M6 19h36" stroke="#D13C36" stroke-width="3"/><path d="M15 5v9M33 5v9" stroke="#fff" stroke-width="4" stroke-linecap="round"/><g fill="#D13C36"><rect x="12" y="25" width="6" height="5" rx="1"/><rect x="21" y="25" width="6" height="5" rx="1"/><rect x="30" y="25" width="6" height="5" rx="1"/><rect x="12" y="33" width="6" height="5" rx="1"/><rect x="21" y="33" width="6" height="5" rx="1"/></g>',
  vasija: '<path d="M17 6h14M19 6v6c-7 4-10 10-10 17 0 8 6 13 15 13s15-5 15-13c0-7-3-13-10-17V6" fill="#fff"/><path d="M12 26h24M11 32h26" stroke="#E8962A" stroke-width="2.6"/>',
  cubiertos: '<path d="M14 5v14a5 5 0 0010 0V5M19 5v38" fill="none" stroke="#fff" stroke-width="3.6" stroke-linecap="round"/><path d="M34 5c-5 4-6 12-6 18h6v20" fill="none" stroke="#fff" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/>',
  tienda: '<circle cx="24" cy="24" r="19" fill="#fff"/><circle cx="24" cy="15" r="3" fill="#6143B5"/><path d="M24 21v15" stroke="#6143B5" stroke-width="5" stroke-linecap="round"/>',
};
const CHEVRON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';

function renderHomeCats() {
  const t = dict();
  const grid = $("#home-cats");
  if (!grid) return;
  grid.innerHTML = TILES_HOME.map((x) => {
    const c = CATS.find((k) => k.id === x.cat);
    if (!c) return "";
    const label = escapeHtml(t[x.label || c.label] || capitalize(c.id));
    return (
      `<button class="v5-tile" role="listitem" data-cat="${c.id}" aria-label="${label}">` +
        `<span class="v5-tile-ico" style="background:linear-gradient(160deg,${x.grad[0]},${x.grad[1]})" aria-hidden="true">` +
          `<svg viewBox="0 0 48 48">${ICONOS_TILE[x.ico]}</svg></span>` +
        `<span class="v5-tile-lab">${label}${CHEVRON}</span>` +
      `</button>`
    );
  }).join("");
  grid.querySelectorAll(".v5-tile").forEach((b) =>
    b.addEventListener("click", () => abrirCategoria(b.dataset.cat)));
  renderExplora();
}

/* Fondo del recuadro Noticias: la portada de la noticia más reciente que tenga
 * imagen. Se precarga antes de aplicarla para no dejar el recuadro en blanco. */
async function cargarFondoNoticias() {
  let url = null;
  try {
    const d = await apiGet("/noticias?page_size=6");
    url = ((d.items || []).find((n) => n.imagen_url) || {}).imagen_url || null;
  } catch { return; }
  if (!url || url === fondoNoticias) return;
  const img = new Image();
  img.onload = () => {
    fondoNoticias = url;
    const tile = document.querySelector('.tt-ptile[data-cat="noticias"]');
    if (tile) tile.style.backgroundImage = `url('${url.replace(/'/g, "%27")}')`;
  };
  img.src = url;
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

/* Solo eventos vigentes: los que aún no han terminado (fecha_fin >= ahora).
 * Sin este filtro la API devuelve los más antiguos primero y la agenda se
 * quedaba anclada en eventos ya pasados. */
function desdeAhora() {
  return encodeURIComponent(new Date().toISOString());   /* UTC con "Z" */
}

async function cargarDestacado() {
  try {
    const d = await apiGet(`/tourism/events?publicado=true&page_size=1&desde=${desdeAhora()}`);
    destacadoEvento = (d.items && d.items[0]) || null;
  } catch { destacadoEvento = null; }
  /* Sin eventos en el CMS: se destaca lo último de la agenda cultural municipal */
  if (!destacadoEvento) {
    const cultura = await cargarAgendaCultural(1);
    destacadoEvento = cultura[0] ? { ...cultura[0], _noticia: true } : null;
  }
  renderDestacado();
}

/* Agenda cultural: la web municipal la publica como noticias de la categoría
 * «Cultura» (Strapi). El backend la recarga sola cada hora. */
async function cargarAgendaCultural(n) {
  try {
    const d = await apiGet(`/noticias/agenda?page_size=${n || 12}`);
    return d.items || [];
  } catch { return []; }
}

function renderDestacado() {
  const wrap = $("#home-feat");
  if (!wrap || !destacadoEvento) { if (wrap) wrap.hidden = true; return; }
  const ev = destacadoEvento;
  let img = "", lugar = "", desc = "";
  if (ev._noticia) {
    $("#feat-title").textContent = ev.titulo || "";
    $("#feat-sub").textContent = fmtFechaNoticia(ev.fecha || ev.publicado_en);
    img = ev.imagen_url || "";
    desc = stripHtml(ev.resumen || ev.extracto || ev.contenido || "");
  } else {
    const nombre = (ev.nombre_i18n && ev.nombre_i18n[currentLang]) || ev.nombre;
    $("#feat-title").textContent = nombre;
    const d = new Date(ev.fecha_inicio);
    $("#feat-sub").textContent = d.toLocaleDateString(currentLang, { weekday: "short", day: "numeric", month: "long" }) +
      " · " + d.toLocaleTimeString(currentLang, { hour: "2-digit", minute: "2-digit", hour12: false });
    lugar = ev.direccion || ev.lugar || "";
    desc = (ev.descripcion_i18n && ev.descripcion_i18n[currentLang]) || ev.descripcion || "";
    /* la API guarda las imágenes como lista de URLs (texto); se admite también {url} */
    const primera = ev.imagenes && ev.imagenes[0];
    img = (typeof primera === "string" ? primera : primera && primera.url) || "";
  }
  $("#feat-lugar").textContent = lugar;
  $("#feat-lugar-row").hidden = !lugar;
  $("#feat-desc").textContent = desc;
  const fill = $("#feat-image");
  if (fill) fill.style.backgroundImage = img ? `url('${img.replace(/'/g, "%27")}')` : "";
  wrap.hidden = false;
  $("#feat-open").onclick = () => (ev._noticia ? openNoticia(ev) : abrirCategoria("eventos"));
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
// HOME v5: Explora, asistente, mapa, lugar recomendado, noticias y QR
// ============================================================
/* Foto real por categoría (primera imagen de sus recursos); mientras, la del tile */
const fotoCategoria = {};
async function cargarFotosCategorias() {
  await Promise.all(CATS.filter((c) => c.res).map(async (c) => {
    try {
      const d = await apiGet(`/tourism/resources?categoria=${encodeURIComponent(c.res[0])}&publicado=true&page_size=40`);
      const r = (d.items || []).find((x) => primeraImagen(x));
      if (r) fotoCategoria[c.id] = primeraImagen(r);
    } catch { /* se queda la foto del tile */ }
  }));
  renderExplora();
  if (!document.getElementById("view-explore").hidden) renderExplorar();
}

function primeraImagen(r) {
  const x = r && r.imagenes && r.imagenes[0];
  const url = typeof x === "string" ? x : x && x.url;
  return url && /\.(jpe?g|png|webp)(\?|$)|\/thumb\/|^\.\.\//i.test(url) ? url : null;
}

function tarjetaExplora(c) {
  const t = dict();
  const foto = (c.noticias && fondoNoticias) || fotoCategoria[c.id] || c.bg || "";
  const titulo = c.events ? (t["agenda.title"] || "Agenda") : (t[c.label] || capitalize(c.id));
  return `<button class="v5-xcard" data-cat="${c.id}" style="background-image:url('${escapeAttr(foto)}')">` +
    `<span class="v5-xcard-t"><strong>${escapeHtml(titulo)}</strong><small>${escapeHtml(t[c.heroSub] || "")}</small></span>` +
    `<span class="v5-xcard-go" aria-hidden="true">${CHEVRON}</span></button>`;
}

function renderExplora() {
  const cont = $("#home-explora");
  if (!cont) return;
  cont.innerHTML = ["playas", "cabo", "naturaleza"].map((id) => tarjetaExplora(CATS.find((c) => c.id === id))).join("");
  cont.querySelectorAll("[data-cat]").forEach((b) => b.addEventListener("click", () => abrirCategoria(b.dataset.cat)));
}

function renderExplorar() {
  const cont = $("#explore-grid");
  if (!cont) return;
  cont.innerHTML = CATS.map(tarjetaExplora).join("");
  cont.querySelectorAll("[data-cat]").forEach((b) => b.addEventListener("click", () => abrirCategoria(b.dataset.cat)));
}

function abrirExplorar() {
  tele.registrar("seccion", { seccion: "explorar" });
  renderExplorar();
  showView("view-explore");
}

/* Avisos: los del CMS (canal tótem) + teléfonos de emergencia */
function abrirAvisos() {
  tele.registrar("seccion", { seccion: "avisos" });
  const t = dict();
  const lista = $("#avisos-lista");
  const avisos = (avisosCms || []).map((a) => ({
    titulo: (a.titulo_i18n && a.titulo_i18n[currentLang]) || a.titulo,
    texto: stripHtml((a.contenido_i18n && a.contenido_i18n[currentLang]) || a.contenido || a.resumen || ""),
  })).filter((a) => a.titulo);
  const campana = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 17V11a6 6 0 0112 0v6l2 2H4z" fill="#F5A623"/><path d="M10 21h4" stroke="#F5A623" stroke-width="2" stroke-linecap="round"/></svg>';
  lista.innerHTML = avisos.length
    ? avisos.map((a) => `<div class="v5-aviso">${campana}<div><strong>${escapeHtml(a.titulo)}</strong>${a.texto ? `<p>${escapeHtml(a.texto)}</p>` : ""}</div></div>`).join("")
    : `<div class="v5-vacio">${escapeHtml(t["v5.sin_avisos"] || "No hay avisos activos en este momento.")}</div>`;
  renderEmergencies($("#avisos-emergencias"));
  showView("view-avisos");
}

/* Asistente desde la home: abre el chat y lanza la pregunta */
function preguntarDesdeHome(texto) {
  if (!texto) return;
  showView("view-chat");
  askChatbot(texto);
}
$("#home-ia-form")?.addEventListener("submit", (e) => {
  e.preventDefault();
  const inp = $("#home-ia-input");
  const q = inp.value.trim();
  inp.value = "";
  if (q) preguntarDesdeHome(q);
  else { showView("view-chat"); $("#chatbot-input")?.focus(); }
});
document.querySelectorAll(".v5-ia-chips [data-ia]").forEach((b) => b.addEventListener("click", () => {
  const t = dict();
  if (b.dataset.ia === "recomendar") { showView("view-chat"); $("#recommend-btn").click(); }
  else if (b.dataset.ia === "ruta") { showView("view-chat"); $("#plan-route-btn").click(); }
  else preguntarDesdeHome(t["v5.q_playas"] || "¿Cuáles son las mejores playas?");
}));

/* Botón «Voz» de la cabecera: pregunta al asistente hablando (o abre el chat) */
$("#voice-toggle")?.addEventListener("click", () => {
  tele.registrar("accesibilidad", { detalle: "voz" });
  showView("view-chat");
  const mic = $("#chatbot-voice");
  if (mic && !mic.classList.contains("is-hidden")) mic.click();
  else $("#chatbot-input")?.focus();
});

/* Navegación (barra inferior y botones «Ver…») */
document.addEventListener("click", (e) => {
  const b = e.target.closest && e.target.closest("[data-ir]");
  if (!b) return;
  const ir = b.dataset.ir;
  if (ir === "inicio") showView("view-home");
  else if (ir === "explorar") abrirExplorar();
  else if (ir === "mapa") abrirMapa();
  else if (ir === "avisos") abrirAvisos();
  else if (ir === "agenda") abrirCategoria("eventos");
  else if (ir === "noticias") abrirCategoria("noticias");
});
document.querySelector(".v5-nav [data-qr-movil]")?.addEventListener("click", () => mostrarQR("https://www.nijar.es", "Ayuntamiento de Níjar"));

/* QR estáticos de la home y de la barra */
function pintarQrHome() {
  document.querySelectorAll("[data-qr-home]").forEach((el) => { if (!el.innerHTML) el.innerHTML = qrSvg(el.dataset.qrHome); });
}

/* Mini mapa del destino: no interactivo; al pulsarlo se abre el mapa completo */
const NUCLEOS_MAPA = [ /* nombre, lat, lon, color, lado de la etiqueta */
  ["Níjar", 36.966, -2.207, "#E8742B", "right"], ["Rodalquilar", 36.847, -2.041, "#155E8C", "left"],
  ["Las Negras", 36.876, -2.004, "#155E8C", "right"], ["San José", 36.763, -2.107, "#155E8C", "right"],
  ["Cabo de Gata", 36.722, -2.193, "#E8742B", "left"],
];
let miniMapa = null;
async function pintarMiniMapa() {
  const cont = $("#home-mapa");
  if (!cont || miniMapa) return;
  let L;
  try { L = await cargarLeaflet(); } catch { return; }
  const div = document.createElement("div");
  cont.appendChild(div);
  miniMapa = L.map(div, {
    zoomControl: false, attributionControl: true, dragging: false, scrollWheelZoom: false,
    doubleClickZoom: false, boxZoom: false, keyboard: false, touchZoom: false, tap: false,
  }).setView([36.85, -2.11], 10);
  miniMapa.attributionControl.setPrefix(false);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 17, attribution: "&copy; OpenStreetMap" }).addTo(miniMapa);
  NUCLEOS_MAPA.forEach(([nombre, lat, lon, color, lado]) => {
    L.marker([lat, lon], {
      interactive: false,
      icon: L.divIcon({
        className: "", iconSize: [30, 40], iconAnchor: [15, 38],
        html: `<svg viewBox="0 0 24 32" width="30" height="40"><path d="M12 31s10-10 10-18a10 10 0 10-20 0c0 8 10 18 10 18z" fill="${color}" stroke="#fff" stroke-width="2"/><circle cx="12" cy="13" r="4" fill="#fff"/></svg>`,
      }),
    }).bindTooltip(nombre, { permanent: true, direction: lado, offset: [lado === "left" ? -8 : 8, -20], className: "v5-pin-lab" }).addTo(miniMapa);
  });
  miniMapa.fitBounds(L.latLngBounds(NUCLEOS_MAPA.map((n) => [n[1], n[2]])).pad(0.18));
  setTimeout(() => miniMapa.invalidateSize(), 200);
}

/* Lugar recomendado: un recurso real con foto, cercano al tótem, que cambia cada día */
let recoActual = null;
const SERVICIOS_ICONOS = [
  [/parking|aparcamiento/i, "parking", '<rect x="3" y="3" width="18" height="18" rx="4" fill="#155E8C"/><path d="M9.5 17V7h3.2a3 3 0 010 6H9.5" fill="none" stroke="#fff" stroke-width="2.2"/>'],
  [/accesib|adaptad|movilidad.reducida|silla/i, "accesible", '<circle cx="12" cy="4.5" r="2" fill="#155E8C"/><path d="M10 8v6h5l2 5M10 11h5M8.5 12.5a5 5 0 106 6.5" fill="none" stroke="#155E8C" stroke-width="2" stroke-linecap="round"/>'],
  [/mirador/i, "mirador", '<circle cx="7" cy="15" r="4" fill="none" stroke="#0B2B57" stroke-width="2"/><circle cx="17" cy="15" r="4" fill="none" stroke="#0B2B57" stroke-width="2"/><path d="M5 11l2-6h3l1 6M19 11l-2-6h-3l-1 6M11 15h2" fill="none" stroke="#0B2B57" stroke-width="2"/>'],
  [/restaura|chiringuito|gastronom|bar\b/i, "restauracion", '<path d="M7 3v8a3 3 0 006 0V3M10 3v18M18 3c-3 2-3 7-3 10h3v8" fill="none" stroke="#E2572B" stroke-width="2" stroke-linecap="round"/>'],
  [/parque.natural|natural|protegid/i, "natural", '<path d="M19 4C10 4 5 9 5 16c0 2 .5 3 1.5 4C15 20 20 13 19 4z" fill="#2E8B57"/>'],
  [/virgen|cala|playa/i, "virgen", '<path d="M2 15c3-3 6-3 9 0s6 3 9 0M2 19c3-3 6-3 9 0s6 3 9 0" fill="none" stroke="#1F8FD0" stroke-width="2" stroke-linecap="round"/>'],
  [/senderismo|sendero|ruta/i, "senderismo", '<circle cx="13" cy="4" r="2" fill="#2E8B57"/><path d="M10 21l2-6 3 3v3M9 12l2-4 4 2 2 3M11 8l-2 5" fill="none" stroke="#2E8B57" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'],
  [/fotograf|iconic/i, "fotografia", '<rect x="3" y="7" width="18" height="13" rx="3" fill="none" stroke="#7C4FC4" stroke-width="2"/><circle cx="12" cy="13.5" r="3.5" fill="none" stroke="#7C4FC4" stroke-width="2"/><path d="M8 7l2-3h4l2 3" fill="none" stroke="#7C4FC4" stroke-width="2"/>'],
  [/familia|familiar/i, "familias", '<circle cx="8" cy="7" r="2.5" fill="#155E8C"/><circle cx="16" cy="7" r="2.5" fill="#155E8C"/><path d="M4 20v-6a4 4 0 018 0v6M12 20v-6a4 4 0 018 0v6" fill="#155E8C"/>'],
  [/snorkel|buceo/i, "snorkel", '<rect x="3" y="8" width="14" height="8" rx="4" fill="none" stroke="#155E8C" stroke-width="2"/><path d="M20 4v11a4 4 0 01-4 4h-2" fill="none" stroke="#155E8C" stroke-width="2" stroke-linecap="round"/>'],
];
function serviciosDe(r) {
  const fuentes = [].concat(r.servicios_disponibles || [], r.etiquetas || [], Object.keys(r.accesibilidad || {}));
  const t = dict();
  const vistos = new Set();
  const out = [];
  fuentes.forEach((f) => {
    const m = SERVICIOS_ICONOS.find(([re]) => re.test(String(f)));
    if (m && !vistos.has(m[1])) { vistos.add(m[1]); out.push({ id: m[1], svg: m[2], label: t["serv." + m[1]] || m[1] }); }
  });
  return out.slice(0, 4);
}

async function cargarRecomendado() {
  try {
    const d = await apiGet("/tourism/resources?publicado=true&page_size=200");
    const conFoto = porCercania((d.items || []).filter((r) => primeraImagen(r) && ["playa", "mirador", "parque_natural", "ruta", "monumento"].includes(r.categoria)));
    const candidatos = conFoto.slice(0, 10);
    if (!candidatos.length) return;
    const dia = Math.floor(Date.now() / 86400000);
    recoActual = candidatos[dia % candidatos.length];
    renderRecomendado();
  } catch { /* sin recomendado: el bloque queda oculto */ }
}
function renderRecomendado() {
  const r = recoActual;
  const wrap = $("#home-reco");
  if (!wrap || !r) return;
  $("#reco-img").style.backgroundImage = `url('${primeraImagen(r).replace(/'/g, "%27")}')`;
  $("#reco-nombre").textContent = r.nombre_i18n?.[currentLang] || r.nombre;
  $("#reco-lugar").textContent = [r.direccion, r.municipio].filter(Boolean).join(", ") || "Níjar";
  $("#reco-desc").textContent = r.descripcion_i18n?.[currentLang] || r.descripcion_corta || r.descripcion || "";
  $("#reco-servs").innerHTML = serviciosDe(r).map((x) => `<span class="v5-serv"><svg viewBox="0 0 24 24" aria-hidden="true">${x.svg}</svg>${escapeHtml(x.label)}</span>`).join("");
  const cat = CATS.find((c) => (c.res || []).includes(r.categoria)) || CATS[0];
  $("#reco-open").onclick = () => openDetail(r, cat);
  $("#reco-mas").onclick = () => abrirCategoria(cat.id);
  wrap.hidden = false;
}

/* Actualidad municipal: la noticia más reciente (con foto si la hay) */
let noticiaHome = null;
async function cargarNoticiaHome() {
  try {
    const d = await apiGet("/noticias?page_size=6");
    const items = d.items || [];
    noticiaHome = items.find((n) => n.imagen_url) || items[0] || null;
  } catch { noticiaHome = null; }
  renderNoticiaHome();
}
function renderNoticiaHome() {
  const wrap = $("#home-news");
  if (!wrap || !noticiaHome) return;
  const n = noticiaHome;
  $("#news-img").style.backgroundImage = n.imagen_url ? `url('${n.imagen_url.replace(/'/g, "%27")}')` : "url('../shared/cabo-de-gata-hero.jpg')";
  $("#news-titulo").textContent = n.titulo || "";
  $("#news-fecha").textContent = fmtFechaNoticia(n.fecha || n.publicado_en);
  $("#news-open").onclick = () => openNoticia(n);
  wrap.hidden = false;
}

function renderHomeV5() {
  renderExplora();
  renderRecomendado();
  renderNoticiaHome();
}

// ============================================================
// LISTADOS por categoría
// ============================================================
const TRAZO_SVG = '<svg viewBox="0 0 220 24" class="v5-trazo" aria-hidden="true"><path d="M4 16c50-10 120-14 212-6" fill="none" stroke="#E8742B" stroke-width="4" stroke-linecap="round"/></svg>';

/* Foto de cabecera de una categoría: la real de sus recursos o la del tile */
function fotoDeCategoria(c) {
  return (c.noticias && fondoNoticias) || fotoCategoria[c.id] || c.bg || "../shared/cabo-de-gata-hero.jpg";
}
function ponerFoto(el, url) {
  if (el) el.style.setProperty("--foto", url ? `url('${String(url).replace(/'/g, "%27")}')` : "none");
}
function lemaHtml(clave) {
  const lema = dict()[clave];
  return lema ? escapeHtml(lema) + TRAZO_SVG : "";
}

async function abrirCategoria(catId, chip = "todas") {
  const c = CATS.find((x) => x.id === catId);
  if (!c) return;
  tele.registrar("seccion", { seccion: catId, detalle: chip !== "todas" ? chip : null });
  currentCat = catId;
  currentChip = chip;
  const t = dict();

  const titulo = c.events && chip !== "emergencias" ? (t["agenda.title"] || "Agenda") : (t[c.label] || capitalize(catId));
  $("#list-title").textContent = titulo;
  $("#list-miga").textContent = titulo;
  const n = catCounts[catId];
  const unit = t[c.unit || "unit.lugares"] || "lugares";
  $("#list-count").textContent = n != null ? `${n} ${unit}` : "";
  const heroTxt = $("#list-hero-txt");
  if (heroTxt) heroTxt.textContent = t[c.heroSub || "hero.destino_generico"] || "Cabo de Gata · Níjar";
  $("#list-lema").innerHTML = lemaHtml("lema." + c.id);
  ponerFoto($("#list-hero"), fotoDeCategoria(c));
  const buscador = $("#list-buscar");
  buscador.value = "";
  buscador.placeholder = (t["v5.buscar_en"] || "Buscar en {x}…").replace("{x}", titulo.toLowerCase());
  $("#list-sin-resultados").hidden = true;
  $("#list-mapa-card").hidden = true;
  $("#list-consejos").hidden = true;
  renderChips(c);
  showView("view-list");

  const grid = $("#content-grid");
  grid.setAttribute("aria-busy", "true");
  grid.innerHTML = `<p class="content-loading">${t["loading.contenido"] || "Cargando contenidos…"}</p>`;
  const fin = (items) => { grid.setAttribute("aria-busy", "false"); finalizarListado(c, items, titulo); };

  if (chip === "emergencias") { renderEmergencies(grid); return fin(null); }
  if (c.events) { await renderAgenda(grid, chip); return fin(null); }
  if (c.empresas) { await renderEmpresas(grid, chip); return fin(null); }
  if (c.noticias) { await renderNoticias(grid); return fin(null); }

  let items = [];
  const cerca = chip === "cerca";
  const filtro = cerca ? "todas" : chip;
  // Sub-chip por etiqueta (playas, cabo, naturaleza): siempre se cargan todos los items de la categoría y luego se filtra por tag en cliente.
  const chipEsSubchip = c.subchips && c.subchips.includes(filtro);
  if (c.srv) {
    const servicios = await getServicios();
    items = porCercania(servicios.filter((s) => (filtro === "todas" ? c.srv.includes(s.tipo) : s.tipo === filtro)));
  } else if (c.res || c.etiquetas) {
    const cats = c.res ? (chipEsSubchip ? c.res : (filtro === "todas" ? c.res : [filtro])) : [];
    for (const cat of cats) {
      try {
        const d = await apiGet(`/tourism/resources?categoria=${encodeURIComponent(cat)}&publicado=true&page_size=100`);
        items.push(...(d.items || []));
      } catch { /* siguiente categoría */ }
    }
    /* Filtro por etiquetas: sin endpoint dedicado, se filtra en cliente sobre todos los recursos */
    if (c.etiquetas && c.etiquetas.length) {
      try {
        const d = await apiGet(`/tourism/resources?publicado=true&page_size=200`);
        const tagSet = c.etiquetas.map((x) => x.toLowerCase());
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
    items = items.filter((r) => (r.etiquetas || []).some((e) => String(e).toLowerCase() === filtro.toLowerCase()));
  }
  if (cerca) items = porCercania(items);
  // Banderas de playa en vivo (solo para la categoría playas)
  if (c.id === "playas") await cargarBanderas();
  renderItems(grid, items, c);
  fin(items);
}

/* Mapa y consejos al pie del listado */
function finalizarListado(c, items, titulo) {
  const t = dict();
  pintarConsejos($("#list-consejos"), c.id);
  const pts = (items || []).map((r) => ({ ll: extractLatLon(r), nombre: r.nombre_i18n?.[currentLang] || r.nombre })).filter((x) => x.ll);
  const card = $("#list-mapa-card");
  if (pts.length) {
    $("#list-mapa-t").textContent = (t["v5.mapa_de"] || "Mapa: {x}").replace("{x}", titulo);
    card.hidden = false;
    miniMapaEn("lista", $("#list-mapa"), pts);
  } else card.hidden = true;
  filtrarListado();
}

/* Buscador del listado: filtra las tarjetas visibles por su texto */
function normTexto(x) {
  return String(x || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
}
function filtrarListado() {
  const q = normTexto($("#list-buscar").value.trim());
  const tarjetas = [...$("#content-grid").querySelectorAll(".v5-rcard, .tt-item")];
  let visibles = 0;
  tarjetas.forEach((el) => {
    const ok = !q || normTexto(el.textContent).includes(q);
    el.hidden = !ok;
    if (ok) visibles++;
  });
  $("#list-sin-resultados").hidden = !(q && tarjetas.length && !visibles);
}
$("#list-buscar").addEventListener("input", () => { filtrarListado(); resetIdle(); });

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
    `<p class="v5-nota">${escapeHtml(t["empresas.aviso"] || "Espacio de empresas colaboradoras del destino")}</p>` +
    items.map((e, i) => empresaCard(e, i)).join("");

  /* Impresión: la tarjeta se ha mostrado en pantalla */
  registrarMetricasEmpresas(items.map((e) => ({ empresa_id: e.id, tipo: "impresion", n: 1 })));
  /* Toque: el visitante pulsa la tarjeta */
  grid.querySelectorAll("[data-emp-id]").forEach((card) =>
    card.addEventListener("click", () =>
      registrarMetricasEmpresas([{ empresa_id: card.dataset.empId, tipo: "toque", n: 1 }])));
  grid.querySelectorAll("[data-web]").forEach((b) => b.addEventListener("click", () =>
    mostrarQR(b.dataset.web, b.closest(".v5-rcard").querySelector(".v5-rcard-t").textContent)));
}

function empresaCard(e, index) {
  const t = dict();
  const desc = e.descripcion_i18n?.[currentLang] || e.descripcion || "";
  const primera = e.imagenes && e.imagenes[0];
  const img = (typeof primera === "string" ? primera : primera && primera.url) || "";
  const lugar = [e.direccion, e.nucleo].filter(Boolean).join(", ");
  const contacto = [e.telefono, e.web ? String(e.web).replace(/^https?:\/\//, "") : null].filter(Boolean).join(" · ");
  const sector = t["sector." + e.sector] || String(e.sector || "").replace(/_/g, " ");
  return `
    <article class="v5-rcard${e.destacado ? " is-dest" : ""}" data-emp-id="${escapeAttr(e.id)}" data-n="${index}">
      <span class="v5-rcard-img${img ? "" : " is-vacia"}" style="--foto:url('${escapeAttr(img)}')" aria-hidden="true">
        ${e.destacado ? `<span class="v5-rcard-badge">${escapeHtml(t["empresas.destacada"] || "Destacada")}</span>` : ""}
      </span>
      <span class="v5-rcard-b">
        <strong class="v5-rcard-t">${escapeHtml(e.nombre)}</strong>
        ${lugar ? `<span class="v5-ico-l v5-rcard-lugar">${ICO_PIN}${escapeHtml(lugar)}</span>` : ""}
        ${desc ? `<span class="v5-rcard-d">${escapeHtml(desc)}</span>` : ""}
        <span class="v5-rchips">${sector ? `<span class="v5-rchip">${escapeHtml(sector)}</span>` : ""}${contacto ? `<span class="v5-rchip">${escapeHtml(contacto)}</span>` : ""}</span>
        ${e.web ? `<span class="v5-rcard-pie"><button class="v5-ficha" data-web="${escapeAttr(e.web)}">${escapeHtml(t["action.web_movil"] || "Web en tu móvil")}${CHEVRON}</button></span>` : ""}
      </span>
    </article>`;
}

const ICO_PIN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 22s7-6.3 7-12a7 7 0 10-14 0c0 5.7 7 12 7 12z" fill="#0B2B57"/><circle cx="12" cy="10" r="2.6" fill="#fff"/></svg>';
const ICONOS_CHIP = {
  todas: '<path d="M2 15c3-3 6-3 9 0s6 3 9 0M2 19c3-3 6-3 9 0s6 3 9 0M7 10c2-4 7-5 10-2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
  virgen: '<path d="M19 4C10 4 5 9 5 16c0 2 .5 3 1.5 4C15 20 20 13 19 4z" fill="#2E8B57"/>',
  familiar: '<circle cx="8" cy="7" r="2.5" fill="#155E8C"/><circle cx="16" cy="7" r="2.5" fill="#155E8C"/><path d="M4 20v-6a4 4 0 018 0v6M12 20v-6a4 4 0 018 0v6" fill="#155E8C"/>',
  "volcánico": '<path d="M3 20l6-10 3 4 2-3 7 9z" fill="#B5703F"/><path d="M11 6c1-2 3-2 4-1" stroke="#B5703F" stroke-width="2" fill="none" stroke-linecap="round"/>',
  "geología": '<path d="M4 18l4-8 5 3 3-6 4 11z" fill="#8A6A4A"/>',
  patrimonio: '<path d="M4 20h16M6 20V10h12v10M4 10l8-6 8 6M10 20v-5h4v5" fill="none" stroke="#7C4FC4" stroke-width="2" stroke-linejoin="round"/>',
  mirador: '<circle cx="7" cy="15" r="4" fill="none" stroke="#0B2B57" stroke-width="2"/><circle cx="17" cy="15" r="4" fill="none" stroke="#0B2B57" stroke-width="2"/><path d="M5 11l2-6h3l1 6M19 11l-2-6h-3l-1 6" fill="none" stroke="#0B2B57" stroke-width="2"/>',
  cerca: '<path d="M12 22s7-6.3 7-12a7 7 0 10-14 0c0 5.7 7 12 7 12z" fill="#E8742B"/><circle cx="12" cy="10" r="2.6" fill="#fff"/>',
  gastro: '<path d="M7 3v8a3 3 0 006 0V3M10 3v18M18 3c-3 2-3 7-3 10h3v8" fill="none" stroke="#B5703F" stroke-width="2" stroke-linecap="round"/>',
};
ICONOS_CHIP.rejilla = '<rect x="4" y="4" width="7" height="7" rx="2" fill="currentColor"/><rect x="13" y="4" width="7" height="7" rx="2" fill="currentColor"/><rect x="4" y="13" width="7" height="7" rx="2" fill="currentColor"/><rect x="13" y="13" width="7" height="7" rx="2" fill="currentColor"/>';
function iconoChip(id) {
  if (id === "todas" && currentCat !== "playas") id = "rejilla";
  const k = ICONOS_CHIP[id] ? id : /^gastronomia_/.test(id) ? "gastro" : null;
  return k ? `<svg viewBox="0 0 24 24" aria-hidden="true">${ICONOS_CHIP[k]}</svg>` : "";
}

function renderChips(c) {
  const t = dict();
  const wrap = $("#list-chips");
  // Prioridad: subchips por etiqueta (playas, cabo, naturaleza) > srv > res > sectores.
  const subs = c.subchips || c.srv || c.res || c.sectores || [];
  const chip = (id, label) =>
    `<button class="v5-fchip" data-chip="${escapeAttr(id)}" aria-pressed="${currentChip === id}">${iconoChip(id)}<span>${escapeHtml(label)}</span></button>`;
  const chips = [chip("todas", t["chips.todas"] || "Todas")];
  if (subs.length > 1 || (c.subchips && c.subchips.length >= 1)) {
    subs.forEach((s) => {
      let label;
      if (c.subchips) label = t[`chip.${s}`] || capitalize(s);
      else if (c.sectores) label = t["sector." + s] || s.replace(/_/g, " ");
      else label = tagLabel(s);
      chips.push(chip(s, label));
    });
  }
  /* Ordenar por cercanía al tótem (lugares y servicios con coordenadas) */
  if (c.res || c.srv) chips.push(chip("cerca", t["v5.cerca"] || "Cerca de mí"));
  if (c.emergencias) chips.push(chip("emergencias", t["categorias.emergencias"] || "Emergencias"));
  wrap.innerHTML = chips.join("");
  wrap.querySelectorAll(".v5-fchip").forEach((b) =>
    b.addEventListener("click", () => abrirCategoria(c.id, b.dataset.chip)));
}

// ============================================================
// Estado de banderas de playa en vivo (IoT municipal, /gemelo/playas/banderas)
// ============================================================
const FLAG_LABEL = {
  verde: { es: "Baño libre", en: "Safe bathing", de: "Baden erlaubt", fr: "Baignade autorisée" },
  amarilla: { es: "Precaución", en: "Caution", de: "Vorsicht", fr: "Prudence" },
  roja: { es: "Baño prohibido", en: "No bathing", de: "Baden verboten", fr: "Baignade interdite" },
  sin_bandera: { es: "Sin bandera", en: "No flag", de: "Keine Flagge", fr: "Pas de drapeau" },
};
const FLAG_COLOR = { verde: "#2e7d32", amarilla: "#f5a623", roja: "#c0392b", sin_bandera: "#9aa0a6" };

function normNombre(s) {
  return String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
    .replace(/\b(playa|cala|de|del|la|el|los|las)\b/g, "").replace(/[^a-z0-9]/g, "");
}

let banderasCache = null; /* { nombreNormalizado: estado } · null = aún no cargado */

async function cargarBanderas() {
  try {
    const d = await apiGet("/gemelo/playas/banderas");
    const map = {};
    (d.banderas || []).forEach((b) => { const k = normNombre(b.nombre); if (k) map[k] = b.estado; });
    banderasCache = map;
  } catch { banderasCache = {}; } /* ThingsBoard no configurado: sin banderas, sin error */
  return banderasCache;
}

function estadoBandera(nombre) {
  if (!banderasCache) return null;
  const k = normNombre(nombre);
  if (!k) return null;
  if (banderasCache[k]) return banderasCache[k];
  for (const bk in banderasCache) {
    if (bk && (k.includes(bk) || bk.includes(k))) return banderasCache[bk];
  }
  return null;
}

function badgeBandera(nombre) {
  const est = estadoBandera(nombre);
  if (!est || est === "desconocido" || !FLAG_COLOR[est]) return "";
  const color = FLAG_COLOR[est];
  const tr = FLAG_LABEL[est];
  const lab = (tr && (tr[currentLang] || tr.es)) || est;
  const txt = est === "amarilla" ? "#3a2f00" : "#fff";
  return `<span class="tt-flag" style="display:inline-flex;align-items:center;gap:5px;margin-top:7px;` +
    `padding:3px 10px;border-radius:999px;font-size:13px;font-weight:700;background:${color};color:${txt}">` +
    `<svg viewBox="0 0 24 24" width="13" height="13" aria-hidden="true"><path d="M6 3v18" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/><path d="M6.5 4h10l-2.4 3 2.4 3h-10z" fill="currentColor"/></svg>` +
    escapeHtml(lab.toUpperCase()) + `</span>`;
}

function itemCard(r, c, index) {
  const t = dict();
  const nombre = r.nombre_i18n?.[currentLang] || r.nombre;
  const desc = r.descripcion_i18n?.[currentLang] || r.descripcion_corta || r.descripcion || "";
  const latlon = extractLatLon(r);
  const km = latlon ? haversineKm(latlon[0], latlon[1]) : null;
  const lugar = [r.direccion, r.municipio].filter(Boolean).join(", ");
  const dist = km != null ? (km < 1 ? Math.round(km * 1000) + " m" : km.toFixed(1) + " km") : "";
  const img = primeraImagen(r) || "";
  const flag = c && c.id === "playas" ? badgeBandera(nombre) : "";
  const servs = serviciosDe(r).map((x) => `<span class="v5-rchip"><svg viewBox="0 0 24 24" aria-hidden="true">${x.svg}</svg>${escapeHtml(x.label)}</span>`).join("");
  return `
    <article class="v5-rcard" data-n="${index}">
      <button class="v5-rcard-img${img ? "" : " is-vacia " + (c.th || "")}" style="--foto:url('${escapeAttr(img)}')" data-abrir aria-label="${escapeAttr(nombre)}">
        ${flag ? `<span class="v5-rcard-flag">${flag}</span>` : ""}
        <span class="v5-rcard-go" aria-hidden="true">${CHEVRON}</span>
      </button>
      <span class="v5-rcard-b">
        <strong class="v5-rcard-t">${escapeHtml(nombre)}</strong>
        ${lugar || dist ? `<span class="v5-ico-l v5-rcard-lugar">${ICO_PIN}${escapeHtml([lugar, dist].filter(Boolean).join(" · "))}</span>` : ""}
        ${desc ? `<span class="v5-rcard-d">${escapeHtml(desc)}</span>` : ""}
        ${servs ? `<span class="v5-rchips">${servs}</span>` : ""}
        <span class="v5-rcard-pie"><button class="v5-ficha" data-abrir>${escapeHtml(t["v5.ver_ficha"] || "Ver ficha")}${CHEVRON}</button></span>
      </span>
    </article>`;
}

function renderItems(grid, items, c) {
  const t = dict();
  if (!items.length) {
    grid.innerHTML = `<p class="content-loading">${t["empty.contenido"] || "Sin contenidos disponibles"}</p>`;
    return;
  }
  grid.innerHTML = items.map((r, i) => itemCard(r, c, i)).join("");
  grid.querySelectorAll(".v5-rcard").forEach((card) => {
    const r = items[Number(card.dataset.n)];
    card.querySelectorAll("[data-abrir]").forEach((b) => b.addEventListener("click", () => openDetail(r, c)));
  });
}

// ============================================================
// NOTICIAS del Ayuntamiento (Strapi, todas las categorías)
// ============================================================
function fmtFechaNoticia(s) {
  if (!s) return "";
  try { return capitalize(new Date(s).toLocaleDateString(currentLang, { day: "numeric", month: "long", year: "numeric" })); }
  catch { return ""; }
}

function stripHtml(html) {
  return String(html || "")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<\/(p|div|h[1-6]|li)>/gi, "\n")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/gi, " ").replace(/&amp;/gi, "&")
    .replace(/[ \t]+/g, " ").replace(/\n{2,}/g, "\n\n").trim();
}

function noticiaCard(n, index) {
  const t = dict();
  const img = n.imagen_url || "";
  const fecha = fmtFechaNoticia(n.fecha || n.publicado_en);
  const cat = (n.categorias && n.categorias[0]) || "";
  const desc = stripHtml(n.descripcion || n.resumen || "");
  return `
    <article class="v5-rcard v5-rcard--noticia" data-slug="${escapeAttr(n.slug || "")}" data-n="${index}">
      <button class="v5-rcard-img${img ? "" : " is-vacia th-evento"}" style="--foto:url('${escapeAttr(img)}')" data-abrir aria-label="${escapeAttr(n.titulo || "")}">
        ${cat ? `<span class="v5-rcard-badge">${escapeHtml(cat)}</span>` : ""}
        <span class="v5-rcard-go" aria-hidden="true">${CHEVRON}</span>
      </button>
      <span class="v5-rcard-b">
        <strong class="v5-rcard-t">${escapeHtml(n.titulo || "")}</strong>
        ${fecha ? `<span class="v5-ico-l v5-rcard-lugar"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="3" fill="none" stroke="#E8742B" stroke-width="2"/><path d="M3 10h18M8 3v4M16 3v4" stroke="#E8742B" stroke-width="2" stroke-linecap="round"/></svg>${escapeHtml(fecha)}</span>` : ""}
        ${desc ? `<span class="v5-rcard-d">${escapeHtml(desc)}</span>` : ""}
        <span class="v5-rcard-pie"><button class="v5-ficha" data-abrir>${escapeHtml(t["v5.leer"] || "Leer noticia")}${CHEVRON}</button></span>
      </span>
    </article>`;
}

function enlazarNoticias(grid, items) {
  grid.querySelectorAll(".v5-rcard--noticia").forEach((card) => {
    const n = items[Number(card.dataset.n)];
    card.querySelectorAll("[data-abrir]").forEach((b) => b.addEventListener("click", () => openNoticia(n)));
  });
}

async function renderNoticias(grid) {
  const t = dict();
  const chipsEl = $("#list-chips");
  if (chipsEl) chipsEl.innerHTML = ""; /* las noticias no llevan filtros */
  let items = [];
  try {
    const d = await apiGet("/noticias?page_size=12");
    items = d.items || [];
  } catch { items = []; }
  const cnt = $("#list-count");
  if (cnt) cnt.textContent = items.length ? `${items.length} ${t["unit.noticias"] || "noticias"}` : "";
  if (!items.length) {
    grid.innerHTML = `<p class="content-loading">${t["empty.contenido"] || "Sin contenidos disponibles"}</p>`;
    return;
  }
  grid.innerHTML = items.map((n, i) => noticiaCard(n, i)).join("");
  enlazarNoticias(grid, items);
}

async function openNoticia(n) {
  tele.registrar("noticia", { seccion: currentCat === "eventos" ? "eventos" : "noticias", contenido_id: n.id != null ? String(n.id) : null, contenido: n.titulo });
  const t = dict();
  currentPoi = null; /* las noticias no se repintan al cambiar de idioma */
  currentPoiCat = null;
  $("#det-miga").textContent = [t["v5.inicio"] || "Inicio", t["cat.noticias"] || "Noticias"].join(" · ");
  $("#det-titulo").textContent = n.titulo || "—";
  $("#det-sub").textContent = [fmtFechaNoticia(n.fecha || n.publicado_en), (n.categorias || []).join(" · ")].filter(Boolean).join(" · ");
  $("#det-lema").innerHTML = "";
  ponerFoto($("#det-hero"), n.imagen_url || "../shared/cabo-de-gata-hero.jpg");
  $("#det-credito").hidden = true;
  const badge = $("#det-badge");
  badge.style.background = ""; badge.style.color = "";
  const cat0 = n.categorias && n.categorias[0];
  badge.textContent = cat0 ? String(cat0).toUpperCase() : "";
  badge.hidden = !cat0;
  $("#det-lugar").hidden = true;
  /* Cuerpo: descripción de inmediato; se completa con el contenido por slug. */
  $("#poi-body").textContent = stripHtml(n.descripcion || "");
  $("#det-stats").innerHTML = "";
  $("#det-acc").innerHTML = "";
  ["#det-serv", "#det-galeria", "#det-mapa-card", "#det-consejos", "#det-llegar", "#det-para"].forEach((id) => { $(id).hidden = true; });
  dialog.showModal();
  if (typeof resetIdle === "function") resetIdle();
  try {
    if (n.slug) {
      const d = await apiGet(`/noticias/${encodeURIComponent(n.slug)}`);
      if (d && d.contenido) $("#poi-body").textContent = stripHtml(d.contenido);
    }
  } catch { /* se queda con la descripción */ }
}

// ============================================================
// AGENDA de eventos agrupada por días (diseño v4)
// ============================================================
async function renderAgenda(grid, chip) {
  const t = dict();
  let items = [];
  const [eventosRes, cultura] = await Promise.all([
    apiGet(`/tourism/events?publicado=true&page_size=50&desde=${desdeAhora()}`).catch(() => null),
    chip === "todas" ? cargarAgendaCultural(12) : Promise.resolve([]),
  ]);
  items = (eventosRes && eventosRes.items) || [];
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
  if (!grupos.size && !cultura.length) {
    grid.innerHTML = `<p class="content-loading">${t["empty.contenido"] || "Sin eventos programados"}</p>`;
    return;
  }

  const tiposChips = [...new Set(items.map((e) => e.tipo).filter(Boolean))];
  $("#list-chips").innerHTML =
    `<button class="v5-fchip" data-chip="todas" aria-pressed="${chip === "todas"}"><span>${t["chips.todas"] || "Todas"}</span></button>` +
    tiposChips.map((x) => {
      const label = t[`tipo_evento.${x}`] || capitalize(x);
      return `<button class="v5-fchip" data-chip="${x}" aria-pressed="${chip === x}"><span>${escapeHtml(label)}</span></button>`;
    }).join("");
  $("#list-chips").querySelectorAll(".v5-fchip").forEach((b) =>
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
  if (cultura.length) {
    html += `<div class="tt-dayhead">${escapeHtml(t["agenda.cultural"] || "Agenda cultural del Ayuntamiento")}</div>`;
    html += `<div class="v5-cards v5-cards--anidadas">${cultura.map((n, i) => noticiaCard(n, i)).join("")}</div>`;
  }
  grid.innerHTML = html;
  const flat = [...grupos.values()].flat();
  grid.querySelectorAll(".tt-item").forEach((btn, i) =>
    btn.addEventListener("click", () => openDetail(flat[i], CATS.find((x) => x.id === "eventos"))));
  enlazarNoticias(grid, cultura);
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
/* La ficha es una vista más (con la cabecera y la barra del tótem). Este objeto
   mantiene la interfaz del antiguo <dialog> (open, showModal, close) que usa el
   resto del código: idioma, inactividad, QR, mapa… */
let vistaAntesDeFicha = "view-home";
const dialog = {
  get open() { return !document.getElementById("view-detail").hidden; },
  showModal() {
    const actual = VIEWS.find((v) => !document.getElementById(v).hidden);
    if (actual && actual !== "view-detail") vistaAntesDeFicha = actual;
    showView("view-detail");
  },
  close() {
    if (this.open) showView(vistaAntesDeFicha || "view-home");
    currentPoi = null;
    currentPoiCat = null;
  },
  querySelector: (sel) => document.getElementById("view-detail").querySelector(sel),
};

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

/* Iconos de la ficha */
const ICO_DET = {
  distancia: '<path d="M3 12h18M7 8l-4 4 4 4M17 8l4 4-4 4" fill="none" stroke="#155E8C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  fecha: '<rect x="3" y="5" width="18" height="16" rx="3" fill="none" stroke="#E8742B" stroke-width="2"/><path d="M3 10h18M8 3v4M16 3v4" stroke="#E8742B" stroke-width="2" stroke-linecap="round"/>',
  horario: '<circle cx="12" cy="12" r="9" fill="none" stroke="#155E8C" stroke-width="2"/><path d="M12 7v5l3 2" stroke="#155E8C" stroke-width="2" stroke-linecap="round"/>',
  precio: '<path d="M15.6 8.6A4.6 4.6 0 108 15.4M6.8 10.6h5.4M6.8 13.4h4.6" fill="none" stroke="#2E8B57" stroke-width="2" stroke-linecap="round"/>',
  aforo: '<circle cx="9" cy="8" r="3" fill="#155E8C"/><path d="M3 20v-2a6 6 0 0112 0v2M16 5a3 3 0 010 6M18 20v-2a5 5 0 00-3-4.6" fill="none" stroke="#155E8C" stroke-width="2"/>',
  categoria: '<path d="M4 4h7l9 9-7 7-9-9z" fill="none" stroke="#7C4FC4" stroke-width="2" stroke-linejoin="round"/><circle cx="8" cy="8" r="1.6" fill="#7C4FC4"/>',
  telefono: '<path d="M5 3h4l2 5-3 2a12 12 0 006 6l2-3 5 2v4a2 2 0 01-2 2A17 17 0 013 5a2 2 0 012-2z" fill="none" stroke="#155E8C" stroke-width="2" stroke-linejoin="round"/>',
  email: '<rect x="3" y="5" width="18" height="14" rx="2.5" fill="none" stroke="#155E8C" stroke-width="2"/><path d="M3.5 6l8.5 7 8.5-7" fill="none" stroke="#155E8C" stroke-width="2"/>',
  web: '<circle cx="12" cy="12" r="9" fill="none" stroke="#155E8C" stroke-width="2"/><path d="M3 12h18M12 3a14 14 0 010 18M12 3a14 14 0 000 18" fill="none" stroke="#155E8C" stroke-width="1.6"/>',
  organizador: '<path d="M4 21V9l8-5 8 5v12M9 21v-6h6v6" fill="none" stroke="#155E8C" stroke-width="2" stroke-linejoin="round"/>',
  aviso: '<circle cx="12" cy="12" r="10" fill="#F5A623"/><path d="M12 7v6" stroke="#fff" stroke-width="2.6" stroke-linecap="round"/><circle cx="12" cy="16.8" r="1.5" fill="#fff"/>',
  movil: '<rect x="6" y="2" width="12" height="20" rx="2.5" fill="none" stroke="#155E8C" stroke-width="2"/><path d="M10.5 18.5h3" stroke="#155E8C" stroke-width="2" stroke-linecap="round"/>',
  mapa: '<path d="M9 20l-6-2V4l6 2 6-2 6 2v14l-6-2-6 2zM9 6v14M15 4v14" fill="none" stroke="#155E8C" stroke-width="2" stroke-linejoin="round"/>',
  coche: '<path d="M4 16v-4l2-5h12l2 5v4M3 16h18v3H3zM7 19v2M17 19v2" fill="none" stroke="#155E8C" stroke-width="2" stroke-linejoin="round"/><circle cx="7.5" cy="14" r="1" fill="#155E8C"/><circle cx="16.5" cy="14" r="1" fill="#155E8C"/>',
};
const svgDe = (cuerpo) => `<svg viewBox="0 0 24 24" aria-hidden="true">${cuerpo}</svg>`;
/* Etiquetas que describen para quién es el lugar (bloque «Recomendado para») */
const IDS_RECOMENDADO = new Set(["familias", "fotografia", "senderismo", "snorkel"]);

function serviciosTodos(r) {
  const fuentes = [].concat(r.servicios_disponibles || [], r.etiquetas || [], Object.keys(r.accesibilidad || {}));
  const t = dict();
  const vistos = new Set();
  const out = [];
  fuentes.forEach((f) => {
    const m = SERVICIOS_ICONOS.find(([re]) => re.test(String(f)));
    if (m && !vistos.has(m[1])) { vistos.add(m[1]); out.push({ id: m[1], svg: m[2], label: t["serv." + m[1]] || m[1] }); }
  });
  return out;
}

function fmtDistancia(km) {
  return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(1).replace(".", currentLang === "en" ? "." : ",")} km`;
}

function openDetail(r, c) {
  if (r !== currentPoi || !dialog.open) {
    tele.registrar("ficha", { seccion: c?.id || currentCat, contenido_id: r.id != null ? String(r.id) : null, contenido: r.nombre || r.titulo });
  }
  currentPoi = r;
  currentPoiCat = c;
  const t = dict();
  const nombre = r.nombre_i18n?.[currentLang] || r.nombre || "—";
  const catTitulo = c ? (c.events ? (t["agenda.title"] || "Agenda") : (t[c.label] || capitalize(c.id))) : "";
  $("#det-miga").textContent = [t["v5.inicio"] || "Inicio", catTitulo, nombre].filter(Boolean).join(" · ");
  $("#det-titulo").textContent = nombre;
  const descLarga = r.descripcion_i18n?.[currentLang] || r.descripcion || r.descripcion_corta || "";
  /* Bajo el título: la descripción corta si es distinta del texto principal; si no, tipo y municipio */
  const tipoLugar = r.categoria ? String(tagLabel(r.categoria)) : "";
  $("#det-sub").textContent = r.descripcion_corta && r.descripcion_corta !== descLarga
    ? r.descripcion_corta
    : [tipoLugar, r.municipio].filter(Boolean).join(" · ");
  $("#det-lema").innerHTML = c ? lemaHtml("lema." + c.id) : "";

  // Hero: foto real del recurso (o la de su categoría)
  const fotos = (r.imagenes || []).map((x) => (typeof x === "string" ? x : x && x.url)).filter(Boolean);
  ponerFoto($("#det-hero"), fotos[0] || (c ? fotoDeCategoria(c) : "../shared/cabo-de-gata-hero.jpg"));
  /* Crédito de la foto (Wikimedia Commons: autor · licencia), obligatorio por la licencia CC */
  const textoCredito = fotos[0] && r.enlaces_externos && r.enlaces_externos.imagen_credito;
  $("#det-credito").textContent = textoCredito ? "📷 " + textoCredito : "";
  $("#det-credito").hidden = !textoCredito;

  // Distintivo: bandera de playa en vivo o «Parque Natural»
  const cat = r.categoria || r.tipo || "";
  const badge = $("#det-badge");
  const estFlag = (c && c.id === "playas") || cat === "playa" ? estadoBandera(nombre) : null;
  badge.style.background = ""; badge.style.color = "";
  if (estFlag && FLAG_COLOR[estFlag]) {
    const tr = FLAG_LABEL[estFlag];
    badge.textContent = (t["info.bandera"] || "BANDERA") + " " + String(estFlag).toUpperCase() + " · " + String((tr && (tr[currentLang] || tr.es)) || estFlag).toUpperCase();
    badge.style.background = FLAG_COLOR[estFlag];
    badge.style.color = estFlag === "amarilla" ? "#3a2f00" : "#fff";
    badge.hidden = false;
  } else if ((r.etiquetas || []).some((e) => /parque/i.test(e)) || cat === "parque_natural") {
    badge.textContent = t["badge.parque_natural"] || "ÍCONO DEL PARQUE NATURAL";
    badge.hidden = false;
  } else badge.hidden = true;

  // Información general
  const lugar = [r.direccion, r.municipio].filter(Boolean).join(", ");
  const lugarEl = $("#det-lugar");
  lugarEl.innerHTML = lugar ? ICO_PIN + `<b>${escapeHtml(lugar)}</b>` : "";
  lugarEl.hidden = !lugar;
  $("#poi-body").textContent = descLarga;
  const latlon = extractLatLon(r);
  const km = latlon ? haversineKm(latlon[0], latlon[1]) : null;
  const stats = [];
  if (km != null) stats.push(["distancia", fmtDistancia(km), t["info.desde_totem"] || "desde el tótem"]);
  if (r.fecha_inicio) {
    const f = new Date(r.fecha_inicio);
    stats.push(["fecha", f.toLocaleDateString(currentLang, { weekday: "short", day: "numeric", month: "long" }), f.toLocaleTimeString(currentLang, { hour: "2-digit", minute: "2-digit", hour12: false })]);
  }
  if (r.horario) { const h = formatMeta({ format: "horario" }, r.horario); if (h) stats.push(["horario", h, t["info.horario"] || "Horario"]); }
  if (r.precio) stats.push(["precio", formatMeta({ format: "i18n" }, r.precio), t["info.precio"] || "Precio"]);
  if (r.capacidad_aforo) stats.push(["aforo", String(r.capacidad_aforo), t["info.aforo"] || "Aforo"]);
  if (cat && stats.length < 4) stats.push(["categoria", String(tagLabel(cat)), t["v5.tipo"] || "Tipo"]);
  $("#det-stats").innerHTML = stats.slice(0, 4).map(([ico, v, l]) =>
    `<div class="v5-stat">${svgDe(ICO_DET[ico])}<span><b>${escapeHtml(v)}</b><small>${escapeHtml(l)}</small></span></div>`).join("");
  const destinoQr = latlon ? `https://www.google.com/maps/dir/?api=1&destination=${latlon[0]},${latlon[1]}` : null;
  const acc = [];
  if (destinoQr) acc.push(`<button class="v5-boton v5-boton--solid" data-det="llegar">${svgDe('<path d="M3 11l18-8-8 18-2-8z" fill="#fff"/>')}${escapeHtml(t["cta.como_llegar"] || "Cómo llegar")}${CHEVRON}</button>`);
  if (latlon) acc.push(`<button class="v5-boton" data-det="mapa">${svgDe(ICO_DET.mapa)}${escapeHtml(t["action.mapa"] || "Ver en el mapa")}${CHEVRON}</button>`);
  if (r.web) acc.push(`<button class="v5-boton" data-det="web">${svgDe(ICO_DET.web)}${escapeHtml(t["action.web_movil"] || "Web en tu móvil")}${CHEVRON}</button>`);
  $("#det-acc").innerHTML = acc.join("");

  // Características y servicios (datos reales del recurso)
  const servs = serviciosTodos(r);
  const feats = servs.filter((x) => !IDS_RECOMENDADO.has(x.id)).map((x) => [x.svg, x.label]);
  if (r.telefono) feats.push([ICO_DET.telefono, String(r.telefono)]);
  if (r.email) feats.push([ICO_DET.email, String(r.email)]);
  if (r.organizador) feats.push([ICO_DET.organizador, formatMeta({ format: "i18n" }, r.organizador)]);
  if (Array.isArray(r.servicios_disponibles)) {
    r.servicios_disponibles.forEach((sv) => {
      if (SERVICIOS_ICONOS.some(([re]) => re.test(String(sv)))) return;
      const label = t[`servicio.${sv}`] || I18N.es?.[`servicio.${sv}`];
      if (label) feats.push([ICO_DET.categoria, label]);
    });
  }
  $("#det-feats").innerHTML = feats.map(([svg, l]) => `<div class="v5-feat">${svgDe(svg)}<span>${escapeHtml(l)}</span></div>`).join("");
  const aviso = (estFlag === "roja" || estFlag === "amarilla")
    ? (FLAG_LABEL[estFlag][currentLang] || FLAG_LABEL[estFlag].es)
    : (r.metadata_adicional && (r.metadata_adicional.aviso_i18n?.[currentLang] || r.metadata_adicional.aviso)) || "";
  $("#det-aviso").innerHTML = aviso ? svgDe(ICO_DET.aviso) + `<span>${escapeHtml(aviso)}</span>` : "";
  $("#det-aviso").hidden = !aviso;
  $("#det-serv").hidden = !feats.length && !aviso;

  // Galería (si hay varias fotos): al tocar una, pasa a la cabecera
  const galeria = fotos.filter((u) => /\.(jpe?g|png|webp)(\?|$)|\/thumb\//i.test(u));
  $("#det-fotos").innerHTML = galeria.map((u, i) =>
    `<button class="v5-foto" style="--foto:url('${escapeAttr(u)}')" data-foto="${i}" aria-label="${escapeAttr(nombre)} · ${i + 1}"></button>`).join("");
  $("#det-galeria").hidden = galeria.length < 2;
  $("#det-fotos").querySelectorAll("[data-foto]").forEach((b) =>
    b.addEventListener("click", () => ponerFoto($("#det-hero"), galeria[Number(b.dataset.foto)])));

  // Mapa y ubicación
  $("#det-mapa-card").hidden = !latlon;
  if (latlon) miniMapaEn("ficha", $("#det-mapa"), [{ ll: latlon, nombre }], 13);

  // Consejos de la categoría
  pintarConsejos($("#det-consejos"), c ? c.id : null);

  // Cómo llegar: distancia real desde este tótem + indicaciones en el móvil
  const llegar = [];
  if (km != null) llegar.push(["coche", t["v5.desde_aqui"] || "Desde este tótem", (t["v5.a_km"] || "A {d} en línea recta").replace("{d}", fmtDistancia(km)), null]);
  if (destinoQr) llegar.push(["movil", t["v5.indicaciones"] || "Indicaciones en tu móvil", t["v5.indicaciones_s"] || "Escanea el QR y sigue la ruta", "llegar"]);
  if (latlon) llegar.push(["mapa", t["action.mapa"] || "Ver en el mapa", t["v5.mapa_s"] || "Situado en el mapa del destino", "mapa"]);
  $("#det-llegar-items").innerHTML = llegar.map(([ico, tit, sub, accion]) =>
    `<${accion ? `button data-det="${accion}"` : "div"} class="v5-llegar-i">${svgDe(ICO_DET[ico])}<span><b>${escapeHtml(tit)}</b><small>${escapeHtml(sub)}</small></span></${accion ? "button" : "div"}>`).join("");
  $("#det-llegar").hidden = !llegar.length;

  // Recomendado para… (según sus etiquetas)
  const para = servs.filter((x) => IDS_RECOMENDADO.has(x.id));
  $("#det-para-items").innerHTML = para.map((x) => `<div class="v5-para-i">${svgDe(x.svg)}<span>${escapeHtml(x.label)}</span></div>`).join("");
  $("#det-para").hidden = !para.length;

  // Acciones
  $("#view-detail").querySelectorAll("[data-det]").forEach((b) => {
    b.onclick = () => {
      if (b.dataset.det === "llegar") mostrarQR(destinoQr, (t["cta.como_llegar"] || "Cómo llegar") + " · " + nombre);
      else if (b.dataset.det === "mapa") { dialog.close(); abrirMapa(latlon); }
      else if (b.dataset.det === "web") mostrarQR(r.web, nombre);
    };
  });
  $("#det-mapa-abrir").onclick = () => { dialog.close(); abrirMapa(latlon); };
  $("#det-mapa").onclick = () => { dialog.close(); abrirMapa(latlon); };

  if (!dialog.open) dialog.showModal();
  resetIdle();
}

$("#poi-close").addEventListener("click", () => dialog.close());

/* Mini mapas no interactivos (listado y ficha): al pulsarlos se abre el mapa completo */
const minimapas = {};
async function miniMapaEn(clave, cont, puntos, zoom) {
  if (!cont) return;
  let L;
  try { L = await cargarLeaflet(); } catch { return; }
  if (minimapas[clave]) { minimapas[clave].remove(); delete minimapas[clave]; }
  cont.innerHTML = "";
  const div = document.createElement("div");
  cont.appendChild(div);
  const m = L.map(div, {
    zoomControl: false, dragging: false, scrollWheelZoom: false, doubleClickZoom: false,
    boxZoom: false, keyboard: false, touchZoom: false, tap: false,
  });
  minimapas[clave] = m;
  m.attributionControl.setPrefix(false);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 17, attribution: "&copy; OpenStreetMap" }).addTo(m);
  puntos.forEach((p, i) => {
    L.marker(p.ll, {
      interactive: false,
      icon: L.divIcon({
        className: "", iconSize: [28, 38], iconAnchor: [14, 36],
        html: `<svg viewBox="0 0 24 32" width="28" height="38"><path d="M12 31s10-10 10-18a10 10 0 10-20 0c0 8 10 18 10 18z" fill="${i % 3 === 0 ? "#E8742B" : "#155E8C"}" stroke="#fff" stroke-width="2"/><circle cx="12" cy="13" r="4" fill="#fff"/></svg>`,
      }),
    }).addTo(m);
  });
  if (puntos.length === 1) {
    m.setView(puntos[0].ll, zoom || 13);
    L.tooltip({ permanent: true, direction: "right", offset: [10, -20], className: "v5-pin-lab" })
      .setLatLng(puntos[0].ll).setContent(escapeHtml(puntos[0].nombre || "")).addTo(m);
  } else {
    m.fitBounds(L.latLngBounds(puntos.map((p) => p.ll)).pad(0.2));
  }
  setTimeout(() => m.invalidateSize(), 200);
}

/* «Consejos para tu visita»: textos generales según el tipo de lugar */
const CONSEJOS_POR_CAT = { playas: "mar", cabo: "monte", rutas: "monte", naturaleza: "monte" };
const ICO_CONSEJO = [
  '<path d="M19 4C10 4 5 9 5 16c0 2 .5 3 1.5 4C15 20 20 13 19 4z" fill="#2E8B57"/>',
  '<circle cx="12" cy="12" r="4.4" fill="#F5B731"/><g stroke="#F5B731" stroke-width="2" stroke-linecap="round"><path d="M12 2v2.4M12 19.6V22M4 12H1.6M22.4 12H20M5.1 5.1l1.7 1.7M17.2 17.2l1.7 1.7M18.9 5.1l-1.7 1.7M6.8 17.2l-1.7 1.7"/></g>',
  '<path d="M3 8h11a3 3 0 10-3-3M3 12h15a3 3 0 11-3 3M3 16h8" fill="none" stroke="#155E8C" stroke-width="2" stroke-linecap="round"/>',
  '<circle cx="8" cy="7" r="2.5" fill="#E8742B"/><circle cx="16" cy="7" r="2.5" fill="#E8742B"/><path d="M4 20v-6a4 4 0 018 0v6M12 20v-6a4 4 0 018 0v6" fill="#E8742B"/>',
];
function pintarConsejos(el, catId) {
  if (!el) return;
  const t = dict();
  const set = CONSEJOS_POR_CAT[catId] || "visita";
  const items = [1, 2, 3, 4].map((i) => String(t[`tip.${set}.${i}`] || "").split("|")).filter((x) => x[0]);
  if (!items.length) { el.hidden = true; return; }
  el.innerHTML =
    `<div class="v5-card-h"><span class="v5-badge v5-badge--orange" aria-hidden="true">${svgDe('<path d="M9 18h6M10 21h4M12 3a6 6 0 00-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0012 3z" fill="#fff"/>')}</span>` +
    `<h3>${escapeHtml(t["v5.consejos"] || "Consejos para tu visita")}</h3></div>` +
    items.map(([tit, txt], i) => `<div class="v5-tip">${svgDe(ICO_CONSEJO[i % ICO_CONSEJO.length])}<span><b>${escapeHtml(tit)}</b>${txt ? `<small>${escapeHtml(txt)}</small>` : ""}</span></div>`).join("");
  el.hidden = false;
}

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
  tele.registrar("mapa", { seccion: "mapa", detalle: Array.isArray(centro) ? "desde una ficha" : null });
  showView("view-map");
  try {
    const [L, recursos] = await Promise.all([
      cargarLeaflet(),
      apiGet("/tourism/resources?page=1&page_size=200&publicado=true").then((d) => d.items || []).catch(() => []),
    ]);
    const cont = $("#totem-map");
    if (!mapaLeaflet) {
      mapaLeaflet = L.map(cont, { zoomControl: true }).setView([36.82, -2.1], 11);
      mapaLeaflet.attributionControl.setPrefix(false); /* el prefijo «Leaflet» es un enlace externo */
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
  tele.registrar("mapa_punto", { seccion: "mapa", contenido_id: r.id != null ? String(r.id) : null, contenido: r.nombre });
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

const ROBOT_SVG = '<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="9" y="14" width="30" height="24" rx="9" fill="#2C7BD6"/><rect x="13" y="19" width="22" height="14" rx="7" fill="#fff"/><circle cx="19" cy="26" r="2.6" fill="#0B2B57"/><circle cx="29" cy="26" r="2.6" fill="#0B2B57"/><path d="M24 14V8" stroke="#2C7BD6" stroke-width="3" stroke-linecap="round"/><circle cx="24" cy="7" r="3" fill="#E8742B"/><path d="M20 31.5h8" stroke="#0B2B57" stroke-width="2" stroke-linecap="round"/></svg>';

function resetChat() {
  const t = dict();
  chatLog.innerHTML = "";
  burbuja(t["chat.welcome"] || "¡Hola! ¿Qué te apetece hacer hoy?", false);
}

/* Burbuja de la conversación. Devuelve el elemento del texto (el resto del
   código cambia su textContent cuando llega la respuesta). */
function burbuja(texto, esUsuario, pensando = false) {
  const div = document.createElement("div");
  div.className = `v5-msg ${esUsuario ? "v5-msg--yo" : "v5-msg--bot"}`;
  div.innerHTML = (esUsuario ? "" : `<span class="v5-msg-av" aria-hidden="true">${ROBOT_SVG}</span>`) +
    `<div class="v5-msg-b"><div class="v5-msg-t"></div></div>`;
  const txt = div.querySelector(".v5-msg-t");
  if (pensando) {
    txt.innerHTML = `<span class="v5-puntos" aria-label="${escapeAttr(texto)}"><i></i><i></i><i></i></span>`;
  } else txt.textContent = texto;
  chatLog.appendChild(div);
  div.scrollIntoView({ behavior: "smooth", block: "end" });
  return txt;
}

$("#chatbot-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  await askChatbot($("#chatbot-input").value.trim());
});
document.querySelectorAll(".v5-chat-sug [data-pregunta]").forEach((b) => b.addEventListener("click", () => {
  const t = dict();
  askChatbot(t[b.dataset.pregunta] || b.textContent.trim());
}));

/* «¿Te ha sido útil?»: alimenta la satisfacción del asistente en el panel */
function pedirValoracion(contenedor, interaccionId) {
  if (!interaccionId) return;
  const t = dict();
  const fila = document.createElement("div");
  fila.className = "v5-util";
  fila.innerHTML = `<span>${escapeHtml(t["v5.util"] || "¿Te ha sido útil?")}</span>` +
    `<button type="button" data-util="1" aria-label="${escapeAttr(t["v5.util_si"] || "Sí")}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 11v9H4v-9zM7 11l4-7c1.5 0 2.5 1 2.2 2.6L12.6 10H19a2 2 0 012 2.3l-1.2 6A2 2 0 0117.8 20H7" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg></button>` +
    `<button type="button" data-util="0" aria-label="${escapeAttr(t["v5.util_no"] || "No")}"><svg viewBox="0 0 24 24" aria-hidden="true" style="transform:rotate(180deg)"><path d="M7 11v9H4v-9zM7 11l4-7c1.5 0 2.5 1 2.2 2.6L12.6 10H19a2 2 0 012 2.3l-1.2 6A2 2 0 0117.8 20H7" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg></button>`;
  fila.querySelectorAll("[data-util]").forEach((b) => b.addEventListener("click", () => {
    const util = b.dataset.util === "1";
    fetch(`${API_BASE}/chatbot/feedback`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sesion_id: sessionId, interaccion_id: interaccionId, util }),
    }).catch(() => {});
    tele.registrar("valoracion_chatbot", { seccion: "chatbot", detalle: util ? "util" : "no util" });
    fila.innerHTML = `<span>${escapeHtml(t["v5.gracias"] || "¡Gracias por tu valoración!")}</span>`;
    resetIdle();
  }));
  contenedor.appendChild(fila);
}

async function askChatbot(message) {
  const input = $("#chatbot-input");
  if (!message) return;
  tele.registrar("pregunta_chatbot", { seccion: "chatbot", detalle: message }); /* antes de la consulta: abre sesión */
  burbuja(message, true);
  input.value = "";
  const pensando = burbuja(dict()["chatbot.thinking"] || "Pensando…", false, true);
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
  const caja = pensando.parentElement;
  /* Preguntas relacionadas: se pueden tocar para seguir la conversación */
  if (Array.isArray(data.sugerencias) && data.sugerencias.length) {
    const sug = document.createElement("div");
    sug.className = "v5-msg-sug";
    data.sugerencias.slice(0, 4).forEach((x) => {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = x;
      b.addEventListener("click", () => askChatbot(x));
      sug.appendChild(b);
    });
    caja.appendChild(sug);
  }
  pedirValoracion(caja, data.interaccion_id);
  $("#chatbot-output").textContent = lastAnswer;   /* lector de pantalla */
  /* La voz del servidor no depende de speechSynthesis: se ofrece siempre */
  speakBtn.classList.remove("is-hidden");
  hablar(lastAnswer);
  caja.parentElement.scrollIntoView({ behavior: "smooth", block: "end" });
  resetIdle();
}

// --- Texto a voz (TTS) ---
// Primero la voz neuronal del backend (/chatbot/tts, voz humana y natural).
// Solo si el servidor no la ofrece se usa una voz del navegador, y nunca las
// voces sintéticas tipo eSpeak (las de los tótems Linux suenan robóticas): en
// ese caso el asistente responde solo por texto.
let ttsAudio = null;
let ttsTurno = 0;   /* descarta audios de respuestas anteriores que lleguen tarde */

async function hablar(texto) {
  pararVoz();
  const turno = ++ttsTurno;
  const r = await hablarServidor(texto, turno);
  if (r !== "error" || turno !== ttsTurno) return;
  hablarNavegador(texto);
}

function pararVoz() {
  try { window.speechSynthesis?.cancel(); } catch { /* sin TTS de navegador */ }
  if (ttsAudio) { ttsAudio.pause(); ttsAudio = null; }
}

/** Devuelve "ok", "bloqueado" (audio listo pero autoplay denegado) o "error". */
async function hablarServidor(texto, turno) {
  let blob;
  for (let intento = 0; intento < 2 && !blob; intento++) {
    try {
      const res = await fetch(`${API_BASE}/chatbot/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto: texto.slice(0, 800), idioma: currentLang, canal: "totem" }),
      });
      if (res.ok) blob = await res.blob();
      else {
        console.warn("TTS servidor no disponible:", res.status);
        if (res.status === 503) break;   /* sin configurar: no reintentar */
      }
    } catch (e) { console.warn("TTS servidor: fallo de red", e); }
  }
  if (!blob) return "error";
  if (turno !== ttsTurno) return "ok";   /* ya hay otra respuesta en curso */
  const audio = new Audio(URL.createObjectURL(blob));
  audio.addEventListener("ended", () => URL.revokeObjectURL(audio.src));
  ttsAudio = audio;
  try {
    await audio.play();
    return "ok";
  } catch (e) {
    /* Autoplay denegado: el audio natural queda listo para el botón "Escuchar";
       no se cae a la voz robótica del navegador. */
    console.warn("TTS: reproducción bloqueada", e);
    return "bloqueado";
  }
}

function esVozRobotica(v) {
  const n = (v.name || "").toLowerCase();
  return n.includes("espeak") || n.includes("robot") || n.includes("festival") || n.includes("pico");
}

function mejorVoz(locale) {
  const voces = window.speechSynthesis.getVoices() || [];
  const idioma = locale.slice(0, 2);
  const candidatas = voces.filter((v) => (v.lang || "").toLowerCase().startsWith(idioma) && !esVozRobotica(v));
  if (!candidatas.length) return null;
  // Preferencia: voces neuronales ("natural", "online", Google) primero
  const rango = (v) => {
    const n = (v.name || "").toLowerCase();
    if (n.includes("natural") || n.includes("online") || n.includes("neural")) return 0;
    if (n.includes("google")) return 1;
    if (n.includes("microsoft")) return 2;
    return 5;
  };
  candidatas.sort((a, b) => rango(a) - rango(b) ||
    ((b.lang || "").toLowerCase() === locale.toLowerCase() ? 1 : 0) -
    ((a.lang || "").toLowerCase() === locale.toLowerCase() ? 1 : 0));
  return candidatas[0];
}

function hablarNavegador(texto) {
  try {
    const locale = VOICE_LOCALE[currentLang] || "es-ES";
    const voz = mejorVoz(locale);
    if (!voz) return;   /* solo voces robóticas: mejor respuesta solo en texto */
    const u = new SpeechSynthesisUtterance(texto);
    u.lang = locale;
    u.voice = voz;
    u.rate = 1;
    window.speechSynthesis.speak(u);
  } catch { /* TTS no disponible */ }
}
speakBtn.addEventListener("click", () => {
  /* Si el audio natural ya está cargado (p. ej. autoplay bloqueado), se reproduce tal cual */
  if (ttsAudio && ttsAudio.paused && ttsAudio.currentTime === 0) {
    ttsAudio.play().catch(() => {});
    return;
  }
  if (lastAnswer) hablar(lastAnswer);
});

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
/* Tarjeta de sugerencias dentro del chat. `items`: [{ id, nombre, sub, tipo }]
   tipo «recurso» o «evento»: al tocarlo se abre su ficha. */
function recoCard(titulo, items) {
  const card = document.createElement("div");
  card.className = "v5-msg v5-msg--bot";
  card.innerHTML = `<span class="v5-msg-av" aria-hidden="true">${ROBOT_SVG}</span>` +
    `<div class="v5-msg-b v5-reco-chat"><h4>${escapeHtml(titulo)}</h4><ol></ol></div>`;
  const ol = card.querySelector("ol");
  items.forEach((it, i) => {
    const li = document.createElement("li");
    li.innerHTML = `<button type="button"><span class="n">${i + 1}</span><span class="tx"><b>${escapeHtml(it.nombre)}</b>` +
      `${it.sub ? `<small>${escapeHtml(it.sub)}</small>` : ""}</span>${it.id ? CHEVRON : ""}</button>`;
    const btn = li.querySelector("button");
    if (it.id) btn.addEventListener("click", () => abrirSugerencia(it));
    else btn.disabled = true;
    ol.appendChild(li);
  });
  chatLog.appendChild(card);
  card.scrollIntoView({ behavior: "smooth", block: "end" });
}

async function abrirSugerencia(it) {
  try {
    if (it.tipo === "evento") {
      const ev = await apiGet(`/tourism/events/${encodeURIComponent(it.id)}`);
      openDetail(ev, CATS.find((x) => x.id === "eventos"));
    } else {
      const r = await apiGet(`/tourism/resources/${encodeURIComponent(it.id)}`);
      const cat = CATS.find((c) => (c.res || []).includes(r.categoria)) || null;
      openDetail(r, cat);
    }
  } catch { /* sin conexión: se queda en el chat */ }
}

$("#plan-route-btn").addEventListener("click", async () => {
  tele.registrar("ruta_planificada", { seccion: "chatbot" });
  const t = dict();
  const pensando = burbuja(t["rutas.loading"] || "Calculando…", false, true);
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
      data.paradas.map((p) => ({ id: p.id, tipo: "recurso", nombre: p.nombre, sub: `${tagLabel(p.categoria)} · ${fmtDistancia(p.distancia_acumulada_m / 1000)}` })));
  } catch { pensando.textContent = t["rutas.empty"] || "No hay propuestas disponibles."; }
  resetIdle();
});

$("#recommend-btn").addEventListener("click", async () => {
  tele.registrar("recomendaciones", { seccion: "chatbot" });
  const t = dict();
  const pensando = burbuja(t["rutas.loading"] || "Calculando…", false, true);
  try {
    const res = await fetch(`${API_BASE}/rutas/recomendaciones?idioma=${currentLang}`);
    if (!res.ok) throw new Error("no disponible");
    const data = await res.json();
    pensando.textContent = t["rutas.recomend"] || "¿Qué visitar hoy?";
    if (data.eventos?.length) {
      recoCard(t["rutas.eventos"] || "Eventos próximos", data.eventos.map((e) => {
        const f = e.fecha_inicio ? new Date(e.fecha_inicio).toLocaleDateString(currentLang, { weekday: "short", day: "numeric", month: "short" }) : "";
        return { id: e.id, tipo: "evento", nombre: e.nombre, sub: [f, e.direccion].filter(Boolean).join(" · ") };
      }));
    }
    if (data.recursos?.length) {
      recoCard(t["rutas.recursos"] || "Lugares recomendados", data.recursos.map((r) =>
        ({ id: r.id, tipo: "recurso", nombre: r.nombre, sub: [tagLabel(r.categoria), r.motivo].filter(Boolean).join(" · ") })));
    }
    if (!data.eventos?.length && !data.recursos?.length) pensando.textContent = t["rutas.empty"] || "Sin recomendaciones ahora mismo.";
  } catch { pensando.textContent = t["rutas.empty"] || "Sin recomendaciones ahora mismo."; }
  resetIdle();
});

// ============================================================
// Inactividad — vuelve al estado inicial tras IDLE_MS
// ============================================================
function goToIdleState() {
  tele.finSesion(); /* el siguiente visitante será otra sesión */
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
cargarFondoNoticias();
setInterval(cargarFondoNoticias, 60 * 60 * 1000); /* sigue a la noticia más reciente */
renderTicker();
cargarHeroFoto();
resetChat();
cargarConteos();
cargarDestacado();
setInterval(cargarDestacado, 30 * 60 * 1000); /* el tótem no se recarga: refresco del destacado */
/* Home v5 */
pintarQrHome();
cargarFotosCategorias();
cargarRecomendado();
cargarNoticiaHome();
pintarMiniMapa();
setInterval(cargarNoticiaHome, 60 * 60 * 1000);
setInterval(cargarRecomendado, 60 * 60 * 1000); /* cambia de lugar recomendado cada día */


// ============================================================
// MODO QUIOSCO: el tótem nunca navega fuera de su propia URL
// ============================================================
// Los enlaces externos se ofrecen como código QR para abrirlos en el móvil
// del visitante. Además, una guarda global bloquea cualquier enlace externo,
// tel:/mailto: o window.open que pudiera colarse desde un contenido.
function qrSvg(texto) {
  if (typeof window.qrcode !== "function") return "";
  window.qrcode.stringToBytes = window.qrcode.stringToBytesFuncs["UTF-8"];
  const qr = window.qrcode(0, "M");
  qr.addData(String(texto));
  qr.make();
  return qr.createSvgTag({ cellSize: 6, margin: 2, scalable: true });
}

function urlLegible(url) {
  return String(url || "").replace(/^https?:\/\//, "").replace(/\/$/, "");
}

function mostrarQR(url, titulo) {
  const d = $("#qr-dialog");
  if (!d || !url) return;
  const destino = /^https?:\/\//i.test(url) ? url : "https://" + url;
  tele.registrar("qr", { seccion: currentCat || (dialog?.open ? currentPoiCat?.id : null) || "general", contenido: titulo || null, detalle: destino });
  $("#qr-title").textContent = titulo || urlLegible(destino);
  $("#qr-code").innerHTML = qrSvg(destino);
  $("#qr-url").textContent = urlLegible(destino);
  if (!d.open) d.showModal();
  if (typeof resetIdle === "function") resetIdle();
}

(function instalarModoQuiosco() {
  $("#qr-close")?.addEventListener("click", () => $("#qr-dialog").close());
  $("#qr-dialog")?.addEventListener("click", (e) => { if (e.target.id === "qr-dialog") e.target.close(); });
  document.querySelectorAll("[data-qr]").forEach((el) => {
    const hueco = el.querySelector(".tt-social-qr");
    if (hueco) hueco.innerHTML = qrSvg(el.dataset.qr);
  });
  const esExterno = (a) => {
    const href = a.getAttribute("href") || "";
    if (!href || href.startsWith("#")) return false;
    try { return new URL(href, location.href).origin !== location.origin; } catch { return true; }
  };
  const bloquear = (e) => {
    const a = e.target.closest && e.target.closest("a[href]");
    if (!a || !esExterno(a)) return;
    e.preventDefault();
    e.stopPropagation();
    const href = a.getAttribute("href");
    if (/^https?:/i.test(href)) mostrarQR(href, a.textContent.trim());
  };
  document.addEventListener("click", bloquear, true);
  document.addEventListener("auxclick", bloquear, true);
  window.open = () => null;
})();
