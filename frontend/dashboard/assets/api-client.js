/**
 * Cliente HTTP para la API REST de la plataforma DTI Níjar.
 *
 * Funciones:
 * - Login con email/contraseña → obtiene access_token + refresh_token.
 * - Almacena tokens en sessionStorage (no localStorage para evitar
 *   persistencia involuntaria entre sesiones de navegador).
 * - Auto-refresh transparente cuando un endpoint devuelve 401.
 * - Helpers tipados para cada área funcional consumida por el dashboard.
 */

const API_BASE = (() => {
  // Permite hospedar el dashboard separado del backend (ajustable por
  // el integrador via window.NIJAR_API_BASE en index.html si fuera necesario).
  if (typeof window !== "undefined" && window.NIJAR_API_BASE) {
    return window.NIJAR_API_BASE;
  }
  return `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;
})();

const STORAGE_KEY_ACCESS = "nijar.dti.access";
const STORAGE_KEY_REFRESH = "nijar.dti.refresh";
const STORAGE_KEY_USER = "nijar.dti.user";

export const tokens = {
  get access() { return sessionStorage.getItem(STORAGE_KEY_ACCESS); },
  get refresh() { return sessionStorage.getItem(STORAGE_KEY_REFRESH); },
  set(access, refresh) {
    sessionStorage.setItem(STORAGE_KEY_ACCESS, access);
    sessionStorage.setItem(STORAGE_KEY_REFRESH, refresh);
  },
  clear() {
    sessionStorage.removeItem(STORAGE_KEY_ACCESS);
    sessionStorage.removeItem(STORAGE_KEY_REFRESH);
    sessionStorage.removeItem(STORAGE_KEY_USER);
  },
};

export class ApiError extends Error {
  constructor(message, { status, code, body } = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.body = body;
  }
}

async function _doFetch(path, { method = "GET", body, retry = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (tokens.access) headers["Authorization"] = `Bearer ${tokens.access}`;

  const resp = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (resp.status === 401 && retry && tokens.refresh && path !== "/auth/refresh") {
    // Intento de refresh transparente y reintento
    const refreshed = await tryRefresh();
    if (refreshed) return _doFetch(path, { method, body, retry: false });
  }

  if (!resp.ok) {
    let payload = null;
    try { payload = await resp.json(); } catch { /* ignore */ }
    throw new ApiError(payload?.message || resp.statusText, {
      status: resp.status,
      code: payload?.code,
      body: payload,
    });
  }
  if (resp.status === 204) return null;
  return resp.json();
}

async function tryRefresh() {
  try {
    const data = await _doFetch("/auth/refresh", {
      method: "POST",
      body: { refresh_token: tokens.refresh },
      retry: false,
    });
    tokens.set(data.access_token, data.refresh_token);
    return true;
  } catch {
    tokens.clear();
    return false;
  }
}

// ----------------- Endpoints -----------------

export const api = {
  async login(email, password) {
    const data = await _doFetch("/auth/login", {
      method: "POST",
      body: { email, password },
      retry: false,
    });
    tokens.set(data.access_token, data.refresh_token);
    const user = await api.me();
    sessionStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user));
    return user;
  },

  async logout() {
    try { await _doFetch("/auth/logout", { method: "POST" }); } catch { /* ignore */ }
    tokens.clear();
  },

  me() { return _doFetch("/auth/me"); },

  // Smart Office
  smartOfficeOverview() { return _doFetch("/dashboards/smart-office/overview"); },
  environment(params = {}) {
    const q = new URLSearchParams(params).toString();
    return _doFetch(`/dashboards/smart-office/environment${q ? `?${q}` : ""}`);
  },

  // Big Data
  bigDataOverview() { return _doFetch("/dashboards/big-data/overview"); },
  sentimentSeries(params = {}) {
    const q = new URLSearchParams(params).toString();
    return _doFetch(`/data/social/kpis/sentiment${q ? `?${q}` : ""}`);
  },
  shareOfVoice() { return _doFetch("/data/social/kpis/share-of-voice"); },
  topTopics(limit = 10) {
    return _doFetch(`/data/social/topics?limit=${limit}`);
  },

  // Tótems
  totemsUsage() { return _doFetch("/dashboards/totems/usage"); },

  // Chatbot
  chatbotTelemetry() { return _doFetch("/chatbot/telemetry"); },

  // Mantenimiento / ANS (C.1)
  monthlyReport(year, month) {
    return _doFetch(`/dashboards/monthly-report?year=${year}&month=${month}`);
  },
  incidencias(params = {}) {
    const q = new URLSearchParams(params).toString();
    return _doFetch(`/incidencias${q ? `?${q}` : ""}`);
  },
  incidenciasANS(desde, hasta) {
    const q = new URLSearchParams({ desde, hasta }).toString();
    return _doFetch(`/incidencias/ans?${q}`);
  },

  // Sensores y recursos (para el mapa)
  listSensors(params = { page: 1, page_size: 200 }) {
    const q = new URLSearchParams(params).toString();
    return _doFetch(`/data/iot/sensors?${q}`);
  },
  listResources(params = { page: 1, page_size: 200 }) {
    const q = new URLSearchParams(params).toString();
    return _doFetch(`/tourism/resources?${q}`);
  },
  listEvents(params = { page: 1, page_size: 50 }) {
    const q = new URLSearchParams(params).toString();
    return _doFetch(`/tourism/events?${q}`);
  },
  createEvent(payload) {
    return _doFetch("/tourism/events", { method: "POST", body: payload });
  },
  createResource(payload) {
    return _doFetch("/tourism/resources", { method: "POST", body: payload });
  },
  updateResource(id, payload) {
    return _doFetch(`/tourism/resources/${id}`, { method: "PUT", body: payload });
  },
  deleteResource(id) {
    return _doFetch(`/tourism/resources/${id}`, { method: "DELETE" });
  },
};

export function getCachedUser() {
  const raw = sessionStorage.getItem(STORAGE_KEY_USER);
  return raw ? JSON.parse(raw) : null;
}
