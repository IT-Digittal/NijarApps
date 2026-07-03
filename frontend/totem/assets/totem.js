/**
 * Lógica de la interfaz del tótem turístico.
 *
 * - Aplica i18n a 4 idiomas con persistencia local de la preferencia.
 * - Toggle de tamaño de texto y modo alto contraste.
 * - Carga POIs y eventos desde la API REST de la plataforma.
 * - Integra el chatbot multilingüe.
 * - Detecta inactividad >60s y vuelve al estado inicial (modo público).
 *
 * No requiere autenticación: el tótem usa un canal público de la API.
 *
 * MIGRACIÓN VISUAL: las clases Tailwind originales se han sustituido por
 * clases semánticas declaradas en totem.css, que consume design tokens.
 * Los estados visuales (active, error, vacío) se gestionan ahora vía
 * atributos ARIA y clases CSS dedicadas, no por clases utility.
 */

import { I18N, translateAll } from "./i18n.js?v=3";
import { DEMO_RESOURCES, DEMO_EVENTS, answerChatbotDemo } from "./demo-data.js";

// ============================================================
// Configuración
// ============================================================
// Mismo origen que la página (la API sirve el tótem bajo /totem). El puerto
// 8000 explícito solo aplica si se abre el HTML fuera del servidor (file://).
const API_BASE = window.NIJAR_API_BASE
  || (window.location.origin.startsWith("http")
    ? `${window.location.origin}/api/v1`
    : "http://localhost:8000/api/v1");

const TOTEM_ID = document.body.dataset.totemId || "urn:ngsi-ld:Totem:nijar:rodalquilar";
const TOTEM_LAT = parseFloat(document.body.dataset.totemLat || "36.847");
const TOTEM_LON = parseFloat(document.body.dataset.totemLon || "-2.041");
const IDLE_MS = 60_000; // 1 minuto sin interacción

// Códigos de idioma BCP-47 para los APIs de voz del navegador
const VOICE_LOCALE = { es: "es-ES", en: "en-GB", de: "de-DE", fr: "fr-FR" };

// Mapeo categoría → categoría URN del recurso
const CAT_MAP = {
  rutas: ["ruta"],
  playas: ["playa"],
  patrimonio: ["monumento", "yacimiento", "centro_visitantes"],
  servicios: ["punto_interes", "oficina_turismo"],
  emergencias: [],
};

// ============================================================
// State
// ============================================================
let currentLang = localStorage.getItem("totem.lang") || "es";
let currentCat = "rutas";
let idleTimer = null;
let sessionId = `totem-${TOTEM_ID}-${Date.now()}`;

// ============================================================
// i18n y selector de idioma
// ============================================================
function applyLanguage(lang) {
  currentLang = lang;
  localStorage.setItem("totem.lang", lang);
  translateAll(lang);
  // Estado visual gestionado por aria-pressed (CSS responde con
  // .lang-btn[aria-pressed="true"]). No tocamos clases.
  document.querySelectorAll(".lang-btn").forEach(btn => {
    btn.setAttribute("aria-pressed", String(btn.dataset.lang === lang));
  });
  document.documentElement.setAttribute("lang", lang);
  document.documentElement.setAttribute("data-language", lang);
  // Recarga contenidos en el nuevo idioma
  loadCategory(currentCat);
}

document.querySelectorAll(".lang-btn").forEach(btn => {
  btn.addEventListener("click", () => applyLanguage(btn.dataset.lang));
});

// ============================================================
// Accesibilidad: tamaño y contraste
// ============================================================
const textBtn = document.getElementById("text-size-toggle");
textBtn.addEventListener("click", () => {
  const enabled = document.body.classList.toggle("text-lg-mode");
  textBtn.setAttribute("aria-pressed", String(enabled));
});

const contrastBtn = document.getElementById("contrast-toggle");
contrastBtn.addEventListener("click", () => {
  const enabled = document.body.classList.toggle("high-contrast");
  contrastBtn.setAttribute("aria-pressed", String(enabled));
});

// ============================================================
// Reloj
// ============================================================
function updateClock() {
  const now = new Date();
  document.getElementById("clock").textContent =
    now.toLocaleTimeString(currentLang, { hour: "2-digit", minute: "2-digit" });
}
setInterval(updateClock, 1000);
updateClock();

// ============================================================
// Categorías y carga de contenidos
// ============================================================
document.querySelectorAll(".cat-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".cat-btn").forEach(b =>
      b.setAttribute("aria-pressed", "false")
    );
    btn.setAttribute("aria-pressed", "true");
    currentCat = btn.dataset.cat;
    loadCategory(currentCat);
  });
});

async function loadCategory(cat) {
  const grid = document.getElementById("content-grid");
  grid.setAttribute("aria-busy", "true");
  grid.innerHTML = `<p class="content-loading" data-i18n="loading.contenido">${
    I18N[currentLang]?.["loading.contenido"] || "Cargando contenidos…"
  }</p>`;

  if (cat === "emergencias") {
    renderEmergencies(grid);
    grid.setAttribute("aria-busy", "false");
    return;
  }

  if (cat === "eventos") {
    await loadEvents(grid);
    grid.setAttribute("aria-busy", "false");
    return;
  }

  let items = [];
  try {
    for (const c of CAT_MAP[cat] || []) {
      const res = await fetch(
        `${API_BASE}/tourism/resources?categoria=${encodeURIComponent(c)}&publicado=true&page_size=10`
      );
      if (!res.ok) continue;
      const data = await res.json();
      items.push(...(data.items || []));
      if (items.length >= 12) break;
    }
  } catch {
    // Backend no disponible: caemos al dataset demo (siguiente paso).
  }
  if (items.length === 0) {
    items = DEMO_RESOURCES[cat] || [];
  }
  renderCards(grid, items.slice(0, 12));
  grid.setAttribute("aria-busy", "false");
}

function renderCards(grid, items) {
  grid.innerHTML = "";
  if (items.length === 0) {
    const empty = I18N[currentLang]?.["empty.contenido"] || "Sin contenidos disponibles";
    grid.innerHTML = `<p class="content-loading">${empty}</p>`;
    return;
  }
  for (const r of items) {
    const card = document.createElement("article");
    card.className = "poi-card";
    card.setAttribute("tabindex", "0");
    card.setAttribute("role", "button");
    card.setAttribute("aria-label", r.nombre);

    const nombre = r.nombre_i18n?.[currentLang] || r.nombre;
    const desc = r.descripcion_i18n?.[currentLang] || r.descripcion_corta || "";
    const cta = I18N[currentLang]?.["card.cta"] || "Ver más";
    const tag = tagLabel(r.categoria);

    card.innerHTML = `
      <div class="poi-image" style="${r.imagenes?.[0] ? `background-image:url('${escapeAttr(r.imagenes[0])}')` : ""}" aria-hidden="true">
        ${tag ? `<span class="poi-tag poi-tag--${escapeHtml(r.categoria || '')}">${escapeHtml(tag)}</span>` : ""}
      </div>
      <div class="poi-body">
        <h3>${escapeHtml(nombre)}</h3>
        <p>${escapeHtml(desc)}</p>
        <span class="poi-cta">
          <span>${cta}</span>
          <span class="arrow" aria-hidden="true">→</span>
        </span>
      </div>
    `;
    card.addEventListener("click", () => openDetail(r));
    card.addEventListener("keypress", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openDetail(r);
      }
    });
    grid.appendChild(card);
  }
}

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
  grid.innerHTML = items.map(it => `
    <article class="poi-card emergency-card" tabindex="0" role="region" aria-label="${escapeHtml(it.titulo)}">
      <div class="poi-body">
        <h3>${escapeHtml(it.titulo)}</h3>
        <p class="emergency-number">${escapeHtml(it.numero)}</p>
        <p>${escapeHtml(it.desc)}</p>
      </div>
    </article>
  `).join("");
}

async function loadEvents(grid) {
  let items = [];
  try {
    const res = await fetch(`${API_BASE}/tourism/events?publicado=true&page_size=12`);
    if (res.ok) {
      const data = await res.json();
      items = data.items || [];
    }
  } catch {
    // Backend no disponible: usamos el dataset demo más abajo.
  }
  if (items.length === 0) {
    items = DEMO_EVENTS;
  }
  grid.innerHTML = "";
  for (const ev of items) {
    const nombre = ev.nombre_i18n?.[currentLang] || ev.nombre;
    const desc = ev.descripcion_i18n?.[currentLang] || ev.descripcion || "";
    const fecha = ev.fecha_inicio
      ? new Date(ev.fecha_inicio).toLocaleDateString(currentLang, {
          day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
        })
      : "";
    const card = document.createElement("article");
    card.className = "poi-card event-card";
    card.setAttribute("tabindex", "0");
    card.setAttribute("role", "button");
    card.setAttribute("aria-label", nombre);
    card.innerHTML = `
      <div class="poi-body">
        <span class="poi-tag">${escapeHtml(capitalize(String(ev.tipo || "")))}</span>
        <h3>${escapeHtml(nombre)}</h3>
        <p class="event-date">📅 ${escapeHtml(fecha)}</p>
        <p>${escapeHtml(desc)}</p>
        ${ev.direccion ? `<p class="event-place">📍 ${escapeHtml(ev.direccion)}</p>` : ""}
      </div>`;
    card.addEventListener("click", () => openDetail(ev));
    card.addEventListener("keypress", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openDetail(ev);
      }
    });
    grid.appendChild(card);
  }
}

// ============================================================
// Modal detalle POI — renderiza dinámicamente todos los campos
// presentes en el recurso/evento, con etiquetas i18n.
// ============================================================
const dialog = document.getElementById("poi-dialog");
const dialogTitle = document.getElementById("poi-title");
const dialogBody = document.getElementById("poi-body");
const dialogMeta = document.getElementById("poi-meta");
const dialogTag = document.getElementById("poi-tag");
const dialogImage = document.getElementById("poi-image");
const dialogTags = document.getElementById("poi-tags");
const dialogActions = document.getElementById("poi-actions");

// Lista declarativa: orden, icono, clave i18n del label y formato.
// "wide" indica filas que ocupan las dos columnas (texto largo).
const META_FIELDS = [
  { key: "fecha_inicio", icon: "📅", label: "info.fecha", format: "datetime" },
  { key: "direccion", icon: "📍", label: "info.direccion", wide: true },
  { key: "municipio", icon: "🏘️", label: "info.municipio" },
  { key: "distancia_km", icon: "📏", label: "info.distancia", format: "km" },
  { key: "duracion_min", icon: "⏱", label: "info.duracion", format: "duration" },
  { key: "desnivel_m", icon: "⛰️", label: "info.desnivel", format: "m" },
  { key: "dificultad", icon: "💪", label: "info.dificultad", format: "i18nVal", prefix: "val.dif_" },
  { key: "modalidad", icon: "🚴", label: "info.modalidad", format: "i18nArr", prefix: "val.mod_" },
  { key: "longitud_m", icon: "📏", label: "info.longitud", format: "m" },
  { key: "tipo_arena", icon: "🏖️", label: "info.tipo_arena", format: "i18n" },
  { key: "bandera_azul", icon: "🏁", label: "info.bandera_azul", format: "bool" },
  { key: "epoca", icon: "🏛️", label: "info.epoca", format: "i18n" },
  { key: "estilo", icon: "🎨", label: "info.estilo", format: "i18n" },
  { key: "bic", icon: "⭐", label: "info.bic", format: "bool" },
  { key: "horario", icon: "🕒", label: "info.horario", format: "horario", wide: true },
  { key: "precio", icon: "💶", label: "info.precio", format: "i18n" },
  { key: "telefono", icon: "📞", label: "info.telefono" },
  { key: "email", icon: "✉️", label: "info.email" },
  { key: "web", icon: "🌐", label: "info.web" },
  { key: "idiomas", icon: "🌍", label: "info.idiomas", format: "langs" },
  { key: "organizador", icon: "🏢", label: "info.organizador", format: "i18n" },
  { key: "aforo", icon: "👥", label: "info.aforo", format: "people" },
  { key: "temporada", icon: "🌤️", label: "info.temporada", format: "i18n", wide: true },
  { key: "servicios", icon: "🛎️", label: "info.servicios", format: "i18nList", wide: true },
  { key: "servicios_disponibles", icon: "🛎️", label: "info.servicios", format: "serviciosList", wide: true },
  { key: "accesibilidad", icon: "♿", label: "info.accesibilidad", format: "i18n", wide: true },
  { key: "recomendaciones", icon: "💡", label: "info.recomendaciones", format: "i18n", wide: true },
];

function formatMeta(field, value) {
  const dict = I18N[currentLang] || I18N.es;
  const i18nVal = (v) => (v && typeof v === "object" && v[currentLang]) ? v[currentLang] : v;
  switch (field.format) {
    case "datetime": {
      const opts = { day: "2-digit", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" };
      return new Date(value).toLocaleString(currentLang, opts);
    }
    case "km":
      return `${value} km`;
    case "m":
      return `${value} m`;
    case "duration": {
      const h = Math.floor(value / 60);
      const m = value % 60;
      return h ? `${h} h ${m ? `${m} min` : ""}`.trim() : `${m} min`;
    }
    case "bool":
      return dict[value ? "val.si" : "val.no"];
    case "i18n":
      return i18nVal(value);
    case "i18nVal":
      return dict[`${field.prefix}${value}`] || capitalize(String(value));
    case "i18nArr":
      return value.map(v => dict[`${field.prefix}${v}`] || capitalize(String(v))).join(" · ");
    case "i18nList": {
      const arr = i18nVal(value);
      return Array.isArray(arr) ? arr.join(" · ") : arr;
    }
    case "langs":
      return value.map(l => String(l).toUpperCase()).join(" · ");
    case "people":
      return `${value}`;
    case "horario":
      if (typeof value === "string") return value;
      if (Array.isArray(value)) return value.join(" · ");
      if (value && typeof value === "object") {
        // Horario tipo {verano: "10-14", invierno: "10-15"}
        return Object.entries(value).map(([k, v]) => `${capitalize(k)}: ${v}`).join(" · ");
      }
      return "";
    case "serviciosList":
      // Traduce servicios como `totem_digital_inicio` a "Tótem digital (inicio)"
      if (!Array.isArray(value)) return String(value);
      return value.map(s => capitalize(String(s).replace(/_/g, " "))).join(" · ");
    default:
      return String(value);
  }
}

// Extrae [lat, lon] desde múltiples posibles formatos de la API.
function extractLatLon(item) {
  const lat = item.latitud ?? item.lat;
  const lon = item.longitud ?? item.lon ?? item.lng;
  if (typeof lat === "number" && typeof lon === "number") return [lat, lon];
  // GeoJSON Point: { type: "Point", coordinates: [lon, lat] }
  const coords = item.ubicacion?.coordinates || item.geometry?.coordinates;
  if (Array.isArray(coords) && coords.length >= 2) return [coords[1], coords[0]];
  return null;
}

function renderMeta(item) {
  dialogMeta.innerHTML = "";
  const dict = I18N[currentLang] || I18N.es;

  for (const field of META_FIELDS) {
    const value = item[field.key];
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value) && value.length === 0) continue;
    const label = dict[field.label] || field.label;
    const formatted = formatMeta(field, value);
    if (!formatted) continue;
    const row = document.createElement("div");
    row.className = "poi-dialog-meta-row" + (field.wide ? " is-wide" : "");
    row.innerHTML = `<dt aria-hidden="true">${field.icon}</dt><dd><strong>${escapeHtml(label)}:</strong> ${escapeHtml(formatted)}</dd>`;
    dialogMeta.appendChild(row);
  }

  // Coordenadas (siempre ancho completo si están)
  const latlon = extractLatLon(item);
  if (latlon) {
    const [lat, lon] = latlon;
    const label = dict["info.coordenadas"] || "Coordenadas";
    const row = document.createElement("div");
    row.className = "poi-dialog-meta-row is-wide";
    row.innerHTML = `<dt aria-hidden="true">🧭</dt><dd><strong>${escapeHtml(label)}:</strong> ${lat.toFixed(4)}, ${lon.toFixed(4)}</dd>`;
    dialogMeta.appendChild(row);
  }
}

// Chips de etiquetas informativas (parque-natural, senderismo, etc.).
function renderTags(item) {
  const raw = item.etiquetas || item.tags;
  if (!Array.isArray(raw) || raw.length === 0) {
    dialogTags.hidden = true;
    dialogTags.innerHTML = "";
    return;
  }
  // Descarta etiquetas redundantes con la categoría (p. ej. "playa" en un recurso de categoría playa).
  const cat = String(item.categoria || "").toLowerCase();
  const chips = raw
    .filter(t => String(t).toLowerCase() !== cat)
    .map(t => `<span class="tag-chip">#${escapeHtml(String(t))}</span>`)
    .join("");
  if (!chips) { dialogTags.hidden = true; dialogTags.innerHTML = ""; return; }
  dialogTags.innerHTML = chips;
  dialogTags.hidden = false;
}

// Botones de acción: mapa, teléfono, web, email.
function renderActions(item) {
  const dict = I18N[currentLang] || I18N.es;
  const actions = [];
  const latlon = extractLatLon(item);
  if (latlon) {
    const [lat, lon] = latlon;
    const nombre = encodeURIComponent(item.nombre_i18n?.[currentLang] || item.nombre || "");
    // OpenStreetMap es genérico y no requiere cuenta.
    const url = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=15/${lat}/${lon}`;
    actions.push(
      `<a class="action-btn" href="${url}" target="_blank" rel="noopener noreferrer" aria-label="${escapeHtml(dict["action.mapa"] || "Ver en el mapa")} ${nombre}">📍 ${escapeHtml(dict["action.mapa"] || "Ver en el mapa")}</a>`
    );
  }
  if (item.telefono) {
    const tel = String(item.telefono).replace(/\s+/g, "");
    actions.push(
      `<a class="action-btn action-btn--secondary" href="tel:${escapeAttr(tel)}">📞 ${escapeHtml(dict["action.llamar"] || "Llamar")}</a>`
    );
  }
  if (item.web) {
    actions.push(
      `<a class="action-btn action-btn--secondary" href="${escapeAttr(item.web)}" target="_blank" rel="noopener noreferrer">🌐 ${escapeHtml(dict["action.web"] || "Web")}</a>`
    );
  }
  if (item.email) {
    actions.push(
      `<a class="action-btn action-btn--secondary" href="mailto:${escapeAttr(item.email)}">✉️ ${escapeHtml(dict["action.email"] || "Email")}</a>`
    );
  }
  if (actions.length === 0) {
    dialogActions.hidden = true;
    dialogActions.innerHTML = "";
    return;
  }
  dialogActions.innerHTML = actions.join("");
  dialogActions.hidden = false;
}

function openDetail(r) {
  // Título y descripción (usa la versión larga si está, si no la corta).
  dialogTitle.textContent = r.nombre_i18n?.[currentLang] || r.nombre || "—";
  dialogBody.textContent =
    r.descripcion_i18n?.[currentLang] ||
    r.descripcion ||
    r.descripcion_corta ||
    "";

  // Etiqueta de categoría / tipo de evento
  const cat = r.categoria || r.tipo || "";
  if (cat) {
    dialogTag.textContent = capitalize(String(cat).replace(/_/g, " "));
    dialogTag.className = `poi-dialog-tag is-${cat}`;
    dialogTag.hidden = false;
  } else {
    dialogTag.hidden = true;
  }

  // Imagen principal o degradado por defecto
  const heroUrl = r.imagenes?.[0] || r.imagen || "";
  dialogImage.style.backgroundImage = heroUrl ? `url('${heroUrl}')` : "";

  // Metadatos dinámicos
  renderMeta(r);
  renderTags(r);
  renderActions(r);

  // Reset scroll del contenido cuando se reutiliza el diálogo
  dialog.querySelector(".poi-dialog-content")?.scrollTo({ top: 0 });

  dialog.showModal();
  resetIdle();
}

document.getElementById("poi-close").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (e) => {
  if (e.target === dialog) dialog.close();
});

// ============================================================
// Chatbot (endpoint /chatbot/query)
// ============================================================
const speakBtn = document.getElementById("chatbot-speak");
let lastAnswer = "";

document.getElementById("chatbot-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  await askChatbot(document.getElementById("chatbot-input").value.trim());
});

async function askChatbot(message) {
  const input = document.getElementById("chatbot-input");
  const output = document.getElementById("chatbot-output");
  if (!message) return;
  output.textContent = I18N[currentLang]?.["chatbot.thinking"] || "Pensando…";
  speakBtn?.classList.add("is-hidden");

  let data = null;
  try {
    const res = await fetch(`${API_BASE}/chatbot/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sesion_id: sessionId,
        canal: "totem",
        idioma: currentLang,
        pregunta: message,
      }),
    });
    if (res.ok) {
      data = await res.json();
    }
  } catch {
    // Sin backend: caemos al matcher demo más abajo (sin error en pantalla).
  }
  if (!data || !data.respuesta) {
    data = answerChatbotDemo(message, currentLang);
  }

  lastAnswer = data.respuesta || "—";
  output.textContent = lastAnswer;
  if (Array.isArray(data.sugerencias) && data.sugerencias.length) {
    const sug = document.createElement("p");
    sug.className = "chatbot-suggestions";
    sug.textContent = "💡 " + data.sugerencias.join(" · ");
    output.appendChild(sug);
  }
  input.value = "";
  // Texto a voz (TTS) — si el navegador lo soporta
  if ("speechSynthesis" in window) {
    speakBtn?.classList.remove("is-hidden");
    hablar(lastAnswer);
  }
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
speakBtn?.addEventListener("click", () => { if (lastAnswer) hablar(lastAnswer); });

// --- Voz a texto (STT) — Web Speech API ---
const voiceBtn = document.getElementById("chatbot-voice");
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
    document.getElementById("chatbot-input").placeholder =
      I18N[currentLang]?.["chatbot.listening"] || "Escuchando…";
  });
  recognition.addEventListener("end", () => {
    escuchando = false;
    voiceBtn.setAttribute("aria-pressed", "false");
  });
  recognition.addEventListener("result", (ev) => {
    const texto = ev.results?.[0]?.[0]?.transcript || "";
    if (texto) {
      document.getElementById("chatbot-input").value = texto;
      askChatbot(texto);
    }
  });
}

// ============================================================
// Planificador de rutas y recomendaciones
// ============================================================
const plannerOut = document.getElementById("planner-output");

document.getElementById("plan-route-btn")?.addEventListener("click", async () => {
  plannerOut.textContent = I18N[currentLang]?.["rutas.loading"] || "Calculando…";
  try {
    const res = await fetch(`${API_BASE}/rutas/planificar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lat: TOTEM_LAT, lon: TOTEM_LON, max_paradas: 5, modo: "bici", idioma: currentLang,
      }),
    });
    if (!res.ok) throw new Error("Error al planificar la ruta");
    renderRuta(await res.json());
  } catch (err) {
    plannerOut.textContent = `⚠️ ${err.message}`;
  }
  resetIdle();
});

document.getElementById("recommend-btn")?.addEventListener("click", async () => {
  plannerOut.textContent = I18N[currentLang]?.["rutas.loading"] || "Calculando…";
  try {
    const res = await fetch(`${API_BASE}/rutas/recomendaciones?idioma=${currentLang}`);
    if (!res.ok) throw new Error("Error al cargar recomendaciones");
    renderRecomendaciones(await res.json());
  } catch (err) {
    plannerOut.textContent = `⚠️ ${err.message}`;
  }
  resetIdle();
});

function renderRuta(data) {
  const t = I18N[currentLang] || I18N.es;
  if (!data.paradas || data.paradas.length === 0) {
    plannerOut.textContent = t["rutas.empty"] || "No hay propuestas disponibles.";
    return;
  }
  const km = (data.distancia_total_m / 1000).toFixed(1);
  const pasos = data.paradas.map(p =>
    `<li><strong>${p.orden}. ${escapeHtml(p.nombre)}</strong> <span class="planner-cat">${escapeHtml(tagLabel(p.categoria))}</span></li>`
  ).join("");
  plannerOut.innerHTML = `
    <p class="planner-summary">${t["rutas.distancia"]}: ${km} km · ${t["rutas.duracion"]}: ${data.duracion_desplazamiento_min} min</p>
    <ol class="planner-list">${pasos}</ol>`;
}

function renderRecomendaciones(data) {
  const t = I18N[currentLang] || I18N.es;
  const partes = [];
  if (data.eventos?.length) {
    const evs = data.eventos.map(e => {
      const f = e.fecha_inicio ? new Date(e.fecha_inicio).toLocaleDateString(currentLang, { day: "2-digit", month: "short" }) : "";
      return `<li><strong>${escapeHtml(e.nombre)}</strong> <span class="planner-cat">${escapeHtml(f)}</span></li>`;
    }).join("");
    partes.push(`<h3 class="planner-subtitle">${t["rutas.eventos"]}</h3><ul class="planner-list">${evs}</ul>`);
  }
  if (data.recursos?.length) {
    const recs = data.recursos.map(r =>
      `<li><strong>${escapeHtml(r.nombre)}</strong> <span class="planner-cat">${escapeHtml(tagLabel(r.categoria))}</span></li>`
    ).join("");
    partes.push(`<h3 class="planner-subtitle">${t["rutas.recursos"]}</h3><ul class="planner-list">${recs}</ul>`);
  }
  plannerOut.innerHTML = partes.join("") || `<p>${t["rutas.empty"]}</p>`;
}

// ============================================================
// Inactividad — vuelve al estado inicial tras IDLE_MS sin uso
// ============================================================
function goToIdleState() {
  if (dialog.open) dialog.close();

  // Categoría por defecto (Rutas) sin disparar listeners globales
  currentCat = "rutas";
  document.querySelectorAll(".cat-btn").forEach(b =>
    b.setAttribute("aria-pressed", String(b.dataset.cat === currentCat))
  );

  // Limpia salidas de chatbot, planificador y aviso destacado
  document.getElementById("chatbot-output").textContent = "";
  lastAnswer = "";
  speakBtn?.classList.add("is-hidden");
  if (plannerOut) plannerOut.innerHTML = "";
  document.getElementById("featured")?.classList.add("is-hidden");

  // Idioma a ES (default) y recarga categoría inicial
  if (currentLang !== "es") {
    applyLanguage("es"); // ya llama a loadCategory
  } else {
    loadCategory(currentCat);
  }

  // Resetea modos de accesibilidad (siguiente usuario empieza limpio)
  if (document.body.classList.contains("text-lg-mode")) {
    document.body.classList.remove("text-lg-mode");
    textBtn?.setAttribute("aria-pressed", "false");
  }
  if (document.body.classList.contains("high-contrast")) {
    document.body.classList.remove("high-contrast");
    contrastBtn?.setAttribute("aria-pressed", "false");
  }

  // Overlay tenue de "en reposo" (se quita en la próxima interacción)
  document.body.classList.add("idle");
}

function resetIdle() {
  if (idleTimer) clearTimeout(idleTimer);
  document.body.classList.remove("idle");
  idleTimer = setTimeout(goToIdleState, IDLE_MS);
}

["click", "keydown", "touchstart", "scroll"].forEach(evt =>
  window.addEventListener(evt, resetIdle, { passive: true })
);
resetIdle();

// ============================================================
// Helpers
// ============================================================
function escapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
function escapeAttr(s) {
  return escapeHtml(s).replace(/`/g, "&#96;");
}
function capitalize(s) {
  return String(s || "").charAt(0).toUpperCase() + String(s || "").slice(1);
}

// Traduce el nombre de una categoría al idioma activo (fallback: ES → texto crudo).
function tagLabel(categoria) {
  if (!categoria) return "";
  return I18N[currentLang]?.[`tag.${categoria}`]
    || I18N.es?.[`tag.${categoria}`]
    || capitalize(String(categoria).replace(/_/g, " "));
}

// ============================================================
// Inicialización
// ============================================================
// applyLanguage() invoca internamente loadCategory(currentCat) — no repetir aquí.
applyLanguage(currentLang);
