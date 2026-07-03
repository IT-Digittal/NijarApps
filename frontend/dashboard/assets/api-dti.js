/**
 * Cliente de API de la Plataforma DTI Níjar.
 *
 * Módulo autónomo listo para cablear el panel transversal a los datos reales
 * del backend (verticales, fuentes de datos, exportaciones y KPIs de turismo).
 * No depende del resto del panel: se puede importar donde haga falta.
 *
 *   import { api, auth } from "./api-dti.js";
 *   await auth.login("admin@nijar.es", "…");
 *   const kpis = await api.alumbrado.overview();
 *
 * Mientras no haya backend disponible, el panel sigue funcionando con sus
 * datos demo; este cliente es el punto de integración cuando se despliegue.
 */

const BASE = (() => {
  // Permite servir el panel bajo /dashboard y llamar a /api/v1 del mismo host.
  const o = window.location.origin;
  return o.startsWith("http") ? `${o}/api/v1` : "/api/v1";
})();

const TOKEN_KEY = "dti_access_token";

function token() {
  return sessionStorage.getItem(TOKEN_KEY);
}

async function req(path, { method = "GET", body, raw = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  const t = token();
  if (t) headers.Authorization = `Bearer ${t}`;
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  if (raw) return res; // para descargas (CSV)
  return res.status === 204 ? null : res.json();
}

function qs(params = {}) {
  const p = Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== ""));
  const s = new URLSearchParams(p).toString();
  return s ? `?${s}` : "";
}

export const auth = {
  async login(email, password) {
    const data = await req("/auth/login", { method: "POST", body: { email, password } });
    if (data?.access_token) sessionStorage.setItem(TOKEN_KEY, data.access_token);
    return data;
  },
  logout() { sessionStorage.removeItem(TOKEN_KEY); },
  isLoggedIn() { return !!token(); },
  me() { return req("/auth/me"); },
};

// Descarga un CSV de un endpoint .csv y dispara la descarga en el navegador.
async function download(path, filename) {
  const res = await req(path, { raw: true });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}

export const api = {
  // -------- Verticales Smart City --------
  alumbrado: {
    overview: () => req("/verticales/alumbrado/overview"),
    zonas: () => req("/verticales/alumbrado/zonas"),
    cuadros: () => req("/verticales/alumbrado/cuadros"),
    luminarias: (p = {}) => req(`/verticales/alumbrado/luminarias${qs(p)}`),
    exportLuminarias: () => download("/verticales/alumbrado/luminarias.csv", "alumbrado_luminarias.csv"),
    exportCuadros: () => download("/verticales/alumbrado/cuadros.csv", "alumbrado_cuadros.csv"),
  },
  agua: {
    overview: () => req("/verticales/agua/overview"),
    sectores: () => req("/verticales/agua/sectores"),
    exportSectores: () => download("/verticales/agua/sectores.csv", "agua_sectores.csv"),
  },
  residuos: {
    overview: () => req("/verticales/residuos/overview"),
    contenedores: (p = {}) => req(`/verticales/residuos/contenedores${qs(p)}`),
    exportContenedores: () => download("/verticales/residuos/contenedores.csv", "residuos_contenedores.csv"),
  },
  movilidad: {
    overview: () => req("/verticales/movilidad/overview"),
    puntos: () => req("/verticales/movilidad/puntos"),
    exportPuntos: () => download("/verticales/movilidad/puntos.csv", "movilidad_puntos.csv"),
  },
  seguridad: {
    overview: () => req("/verticales/seguridad/overview"),
    camaras: () => req("/verticales/seguridad/camaras"),
    exportCamaras: () => download("/verticales/seguridad/camaras.csv", "seguridad_camaras.csv"),
  },
  energia: {
    overview: () => req("/verticales/energia/overview"),
    suministros: (p = {}) => req(`/verticales/energia/suministros${qs(p)}`),
    exportSuministros: () => download("/verticales/energia/suministros.csv", "energia_suministros.csv"),
  },

  // -------- Fuentes de datos / integraciones --------
  integraciones: {
    fuentes: (p = {}) => req(`/integraciones/fuentes${qs(p)}`),
    resumen: () => req("/integraciones/resumen"),
    exportFuentes: () => download("/integraciones/fuentes.csv", "fuentes_datos_nijar.csv"),
  },

  // -------- DTI Turismo (KPIs ya backend-driven) --------
  turismo: {
    smartOffice: () => req("/dashboards/smart-office/overview"),
    bigData: () => req("/dashboards/big-data/overview"),
    totemsUsage: () => req("/dashboards/totems/usage"),
    totemsHealth: () => req("/dashboards/totems/health"),
    chatbotTelemetry: () => req("/chatbot/telemetry"),
    cliente: () => req("/cliente"),
    campanas: () => req("/campanas"),
  },
};

export default { api, auth };
