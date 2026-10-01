/**
 * Modo kiosko del tótem físico (se activa con `?kiosko=1` en la URL).
 *
 * - Teclado en pantalla propio para el campo del asistente IA: en el tótem
 *   Windows arranca sin escritorio y el teclado táctil del sistema no aparece.
 * - Los enlaces externos (webs, redes sociales, teléfonos) no se abren en el
 *   navegador del tótem: se muestra un código QR para abrirlos en el móvil.
 *
 * Fuera del modo kiosko (móvil, PC) no hace nada: cada dispositivo usa su
 * propio teclado y los enlaces funcionan con normalidad.
 */

import { I18N } from "./i18n.js?v=25";

export const MODO_KIOSKO = new URLSearchParams(window.location.search).get("kiosko") === "1";

const QR_LIB = "https://unpkg.com/qrcode-generator@1.4.4/qrcode.js";

const FILAS_LETRAS = [
  ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
  ["a", "s", "d", "f", "g", "h", "j", "k", "l", "ñ"],
  ["{mayus}", "z", "x", "c", "v", "b", "n", "m", "{borrar}"],
  ["{simbolos}", ",", "{espacio}", ".", "{enviar}"],
];
const FILAS_SIMBOLOS = [
  ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
  ["á", "é", "í", "ó", "ú", "ü", "à", "è", "ç", "ß"],
  ["ä", "ö", "¿", "?", "¡", "!", "'", "-", "{borrar}"],
  ["{letras}", "@", "{espacio}", ".", "{enviar}"],
];

const t = (clave, defecto) => {
  const idioma = document.documentElement.lang || "es";
  return (I18N[idioma] && I18N[idioma][clave]) || I18N.es[clave] || defecto;
};

// ============================================================
// Teclado en pantalla
// ============================================================
let teclado = null;
let campo = null;
let capa = "letras";
let mayus = false;

function etiquetaTecla(tecla) {
  switch (tecla) {
    case "{mayus}": return { texto: "⇧", aria: t("teclado.mayus", "Mayúsculas") };
    case "{borrar}": return { texto: "⌫", aria: t("teclado.borrar", "Borrar") };
    case "{espacio}": return { texto: t("teclado.espacio", "espacio"), aria: t("teclado.espacio", "espacio") };
    case "{enviar}": return { texto: "↵", aria: t("teclado.enviar", "Enviar") };
    case "{simbolos}": return { texto: "?123", aria: t("teclado.simbolos", "Números y acentos") };
    case "{letras}": return { texto: "ABC", aria: t("teclado.letras", "Letras") };
    default: {
      const texto = mayus ? tecla.toUpperCase() : tecla;
      return { texto, aria: texto };
    }
  }
}

function pintarTeclado() {
  const filas = capa === "letras" ? FILAS_LETRAS : FILAS_SIMBOLOS;
  const cuerpo = teclado.querySelector(".tt-kb-teclas");
  cuerpo.innerHTML = "";
  for (const fila of filas) {
    const divFila = document.createElement("div");
    divFila.className = "tt-kb-fila";
    for (const tecla of fila) {
      const { texto, aria } = etiquetaTecla(tecla);
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className = "tt-kb-tecla";
      if (tecla.startsWith("{")) boton.classList.add(`tt-kb-tecla--${tecla.slice(1, -1)}`);
      if (tecla === "{mayus}" && mayus) boton.classList.add("is-on");
      boton.dataset.tecla = tecla;
      boton.textContent = texto;
      boton.setAttribute("aria-label", aria);
      divFila.appendChild(boton);
    }
    cuerpo.appendChild(divFila);
  }
  teclado.querySelector(".tt-kb-ocultar").setAttribute("aria-label", t("teclado.ocultar", "Ocultar teclado"));
}

function insertar(texto) {
  const inicio = campo.selectionStart ?? campo.value.length;
  const fin = campo.selectionEnd ?? inicio;
  campo.setRangeText(texto, inicio, fin, "end");
  campo.dispatchEvent(new Event("input", { bubbles: true }));
}

function borrar() {
  const inicio = campo.selectionStart ?? campo.value.length;
  const fin = campo.selectionEnd ?? inicio;
  if (inicio !== fin) campo.setRangeText("", inicio, fin, "end");
  else if (inicio > 0) campo.setRangeText("", inicio - 1, inicio, "end");
  campo.dispatchEvent(new Event("input", { bubbles: true }));
}

function pulsar(tecla) {
  switch (tecla) {
    case "{mayus}": mayus = !mayus; pintarTeclado(); return;
    case "{borrar}": borrar(); return;
    case "{espacio}": insertar(" "); return;
    case "{simbolos}": capa = "simbolos"; pintarTeclado(); return;
    case "{letras}": capa = "letras"; pintarTeclado(); return;
    case "{enviar}":
      ocultarTeclado();
      campo.form?.requestSubmit();
      return;
    default:
      insertar(mayus ? tecla.toUpperCase() : tecla);
      if (mayus) { mayus = false; pintarTeclado(); }
  }
}

function mostrarTeclado() {
  if (!teclado) return;
  capa = "letras";
  mayus = false;
  pintarTeclado();
  teclado.hidden = false;
  document.body.classList.add("tt-kb-abierto");
  document.body.style.setProperty("--kb-h", `${teclado.offsetHeight}px`);
  campo.closest("form")?.scrollIntoView({ block: "end" });
}

export function ocultarTeclado() {
  if (!teclado || teclado.hidden) return;
  teclado.hidden = true;
  document.body.classList.remove("tt-kb-abierto");
  campo?.blur();
}

function crearTeclado(input) {
  campo = input;
  campo.setAttribute("inputmode", "none");   // que el sistema no saque su propio teclado
  teclado = document.createElement("div");
  teclado.className = "tt-kb";
  teclado.hidden = true;
  teclado.setAttribute("role", "group");
  teclado.innerHTML = `
    <div class="tt-kb-barra">
      <button type="button" class="tt-kb-ocultar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>
      </button>
    </div>
    <div class="tt-kb-teclas"></div>`;
  document.body.appendChild(teclado);

  // Evita que el campo pierda el foco (y el cursor) al tocar las teclas.
  teclado.addEventListener("pointerdown", (e) => e.preventDefault());
  teclado.addEventListener("click", (e) => {
    if (e.target.closest(".tt-kb-ocultar")) { ocultarTeclado(); return; }
    const boton = e.target.closest("[data-tecla]");
    if (boton) pulsar(boton.dataset.tecla);
  });

  campo.addEventListener("focus", mostrarTeclado);
  document.addEventListener("pointerdown", (e) => {
    if (teclado.hidden) return;
    if (teclado.contains(e.target) || e.target === campo) return;
    ocultarTeclado();
  });
}

// ============================================================
// Enlaces externos → código QR
// ============================================================
let promesaQr = null;
function cargarQr() {
  if (!promesaQr) {
    promesaQr = new Promise((resolve, reject) => {
      if (window.qrcode) return resolve(window.qrcode);
      const js = document.createElement("script");
      js.src = QR_LIB;
      js.onload = () => resolve(window.qrcode);
      js.onerror = () => { promesaQr = null; reject(new Error("Generador QR no disponible")); };
      document.head.appendChild(js);
    });
  }
  return promesaQr;
}

function svgQr(qrcode, texto) {
  const qr = qrcode(0, "M");
  qr.addData(texto, "Byte");
  qr.make();
  const n = qr.getModuleCount();
  const margen = 2;
  let celdas = "";
  for (let fila = 0; fila < n; fila++) {
    for (let col = 0; col < n; col++) {
      if (qr.isDark(fila, col)) celdas += `M${col + margen} ${fila + margen}h1v1h-1z`;
    }
  }
  const lado = n + margen * 2;
  return `<svg viewBox="0 0 ${lado} ${lado}" shape-rendering="crispEdges" aria-hidden="true">`
    + `<rect width="${lado}" height="${lado}" fill="#fff"/><path d="${celdas}" fill="#0B2B57"/></svg>`;
}

let dialogoQr = null;
function crearDialogoQr() {
  dialogoQr = document.createElement("dialog");
  dialogoQr.className = "tt-qrdialog";
  dialogoQr.setAttribute("aria-labelledby", "qr-titulo");
  dialogoQr.innerHTML = `
    <button type="button" class="tt-social-close tt-qr-cerrar">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
    </button>
    <h2 id="qr-titulo"></h2>
    <p class="tt-qr-sub"></p>
    <div class="tt-qr-codigo"></div>
    <p class="tt-qr-url"></p>`;
  document.body.appendChild(dialogoQr);
  dialogoQr.querySelector(".tt-qr-cerrar").addEventListener("click", () => dialogoQr.close());
  dialogoQr.addEventListener("click", (e) => { if (e.target === dialogoQr) dialogoQr.close(); });
}

async function mostrarQr(href) {
  if (!dialogoQr) crearDialogoQr();
  const esTelefono = href.startsWith("tel:");
  const visible = esTelefono ? href.slice(4) : href.replace(/^https?:\/\//, "").replace(/\/$/, "");
  dialogoQr.querySelector(".tt-qr-cerrar").setAttribute("aria-label", t("kiosko.cerrar", "Cerrar"));
  dialogoQr.querySelector("#qr-titulo").textContent = esTelefono
    ? t("kiosko.qr_tel_titulo", "Llama desde tu móvil")
    : t("kiosko.qr_titulo", "Ábrelo en tu móvil");
  dialogoQr.querySelector(".tt-qr-sub").textContent = t("kiosko.qr_sub", "Escanea el código con la cámara de tu móvil");
  dialogoQr.querySelector(".tt-qr-url").textContent = visible;
  const codigo = dialogoQr.querySelector(".tt-qr-codigo");
  codigo.innerHTML = "";
  if (!dialogoQr.open) dialogoQr.showModal();
  try {
    codigo.innerHTML = svgQr(await cargarQr(), href);
  } catch {
    codigo.hidden = true;   // sin QR queda la dirección en texto
    return;
  }
  codigo.hidden = false;
}

function esEnlaceExterno(a) {
  const href = a.getAttribute("href") || "";
  if (/^(tel|mailto):/i.test(href)) return true;
  if (!/^https?:\/\//i.test(a.href)) return false;
  return a.target === "_blank" || new URL(a.href).host !== window.location.host;
}

// ============================================================
// Arranque
// ============================================================
export function iniciarKiosko() {
  if (!MODO_KIOSKO) return;
  document.body.classList.add("modo-kiosko");

  const input = document.getElementById("chatbot-input");
  if (input) crearTeclado(input);

  document.addEventListener("click", (e) => {
    const a = e.target.closest("a[href]");
    if (!a || !esEnlaceExterno(a)) return;
    e.preventDefault();
    mostrarQr(a.getAttribute("href").startsWith("tel:") ? a.getAttribute("href") : a.href);
  }, true);

  // Sin menú contextual (pulsación larga): evita «abrir en pestaña nueva», etc.
  document.addEventListener("contextmenu", (e) => e.preventDefault());
}

/** Cierra teclado y QR (al volver al inicio por inactividad). */
export function reiniciarKiosko() {
  ocultarTeclado();
  if (dialogoQr?.open) dialogoQr.close();
}
