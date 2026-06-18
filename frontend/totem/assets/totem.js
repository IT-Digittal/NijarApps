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

import { I18N, translateAll } from "./i18n.js";

// ============================================================
// Configuración
// ============================================================
const API_BASE = window.NIJAR_API_BASE
  || `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;

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
// Reloj y meteo (lectura del último sensor meteo del propio tótem)
// ============================================================
function updateClock() {
  const now = new Date();
  document.getElementById("clock").textContent =
    now.toLocaleTimeString(currentLang, { hour: "2-digit", minute: "2-digit" });
}
setInterval(updateClock, 1000);
updateClock();

async function loadWeather() {
  // Meteo endpoint requires auth; totem is public, so we show a static label.
  document.getElementById("weather").textContent = "Cabo de Gata-Níjar";
}
loadWeather();
setInterval(loadWeather, 5 * 60_000); // cada 5 min

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

  try {
    const items = [];
    for (const c of CAT_MAP[cat] || []) {
      const res = await fetch(
        `${API_BASE}/tourism/resources?categoria=${encodeURIComponent(c)}&publicado=true&page_size=10`
      );
      if (!res.ok) continue;
      const data = await res.json();
      items.push(...(data.items || []));
      if (items.length >= 12) break;
    }
    renderCards(grid, items.slice(0, 12));
  } catch (err) {
    grid.innerHTML = `<p class="content-loading content-error">${escapeHtml(err.message)}</p>`;
  }
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
    const tag = r.categoria ? capitalize(String(r.categoria).replace(/_/g, " ")) : "";

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
  try {
    const res = await fetch(`${API_BASE}/tourism/events?publicado=true&page_size=12`);
    if (!res.ok) throw new Error("Error al cargar eventos");
    const data = await res.json();
    const items = data.items || [];
    if (items.length === 0) {
      grid.innerHTML = `<p class="content-loading">${
        I18N[currentLang]?.["empty.contenido"] || "Sin contenidos disponibles"
      }</p>`;
      return;
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
      card.innerHTML = `
        <div class="poi-body">
          <span class="poi-tag">${escapeHtml(capitalize(String(ev.tipo || "")))}</span>
          <h3>${escapeHtml(nombre)}</h3>
          <p class="event-date">📅 ${escapeHtml(fecha)}</p>
          <p>${escapeHtml(desc)}</p>
          ${ev.direccion ? `<p class="poi-dialog-meta">📍 ${escapeHtml(ev.direccion)}</p>` : ""}
        </div>`;
      grid.appendChild(card);
    }
  } catch (err) {
    grid.innerHTML = `<p class="content-loading content-error">${escapeHtml(err.message)}</p>`;
  }
}

// ============================================================
// Modal detalle POI
// ============================================================
const dialog = document.getElementById("poi-dialog");
const dialogTitle = document.getElementById("poi-title");
const dialogBody = document.getElementById("poi-body");
const dialogDir = document.getElementById("poi-direccion");

function openDetail(r) {
  dialogTitle.textContent = r.nombre_i18n?.[currentLang] || r.nombre;
  dialogBody.textContent = r.descripcion_i18n?.[currentLang] || r.descripcion_corta || "";
  dialogDir.textContent = r.direccion || "";
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
    if (!res.ok) throw new Error("Error en el chatbot");
    const data = await res.json();
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
  } catch (err) {
    output.textContent = `⚠️ ${err.message}`;
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
    `<li><strong>${p.orden}. ${escapeHtml(p.nombre)}</strong> <span class="planner-cat">${escapeHtml(capitalize(p.categoria.replace(/_/g, " ")))}</span></li>`
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
      `<li><strong>${escapeHtml(r.nombre)}</strong> <span class="planner-cat">${escapeHtml(capitalize(r.categoria.replace(/_/g, " ")))}</span></li>`
    ).join("");
    partes.push(`<h3 class="planner-subtitle">${t["rutas.recursos"]}</h3><ul class="planner-list">${recs}</ul>`);
  }
  plannerOut.innerHTML = partes.join("") || `<p>${t["rutas.empty"]}</p>`;
}

// ============================================================
// Inactividad
// ============================================================
function resetIdle() {
  if (idleTimer) clearTimeout(idleTimer);
  document.body.classList.remove("idle");
  idleTimer = setTimeout(() => {
    if (dialog.open) dialog.close();
    document.body.classList.add("idle");
    document.querySelector('.cat-btn[data-cat="rutas"]')?.click();
    document.getElementById("chatbot-output").textContent = "";
  }, IDLE_MS);
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

// ============================================================
// Inicialización
// ============================================================
applyLanguage(currentLang);
loadCategory(currentCat);
