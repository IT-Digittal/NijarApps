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
const IDLE_MS = 60_000; // 1 minuto sin interacción

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
// Chatbot
// ============================================================
document.getElementById("chatbot-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("chatbot-input");
  const output = document.getElementById("chatbot-output");
  const message = input.value.trim();
  if (!message) return;
  output.textContent = I18N[currentLang]?.["chatbot.thinking"] || "Pensando…";
  try {
    const res = await fetch(`${API_BASE}/chatbot/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        canal: "totem",
        mensaje: message,
        idioma: currentLang,
      }),
    });
    if (!res.ok) throw new Error("Error en el chatbot");
    const data = await res.json();
    output.textContent = data.respuesta || "—";
    input.value = "";
  } catch (err) {
    output.textContent = `⚠️ ${err.message}`;
  }
  resetIdle();
});

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
