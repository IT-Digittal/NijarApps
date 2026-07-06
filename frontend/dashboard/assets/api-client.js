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
  // Mismo origen que la página (la API sirve el dashboard bajo /dashboard).
  // El puerto 8000 solo aplica si se abre el HTML fuera del servidor (file://).
  return window.location.origin.startsWith("http")
    ? `${window.location.origin}/api/v1`
    : "http://localhost:8000/api/v1";
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

// Cache TTL para GET: evita repetir peticiones idénticas si navegas
// rápidamente entre secciones. La caché se invalida en mutaciones (POST/PUT/DELETE)
// y con `api.invalidateCache()`. TTL bajo para no servir datos rancios.
const _GET_CACHE_TTL_MS = 15_000;
const _getCache = new Map(); // key: path → { at, promise, data, error }

export function invalidateCache(prefix) {
  if (!prefix) { _getCache.clear(); return; }
  for (const k of _getCache.keys()) {
    if (k.startsWith(prefix)) _getCache.delete(k);
  }
}

// Decodifica el payload de un JWT sin verificar firma (el backend valida en cada
// petición). Sólo lo usamos para detectar expiración de forma proactiva.
function _jwtExp(token) {
  try {
    const [, payload] = token.split(".");
    if (!payload) return null;
    const b64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = b64 + "===".slice((b64.length + 3) % 4);
    return JSON.parse(atob(padded)).exp || null;
  } catch { return null; }
}
function _tokenExpiredSoon(token, marginSeconds = 30) {
  const exp = _jwtExp(token);
  if (!exp) return false; // sin exp lo tratamos como válido (evita loops)
  return exp * 1000 - Date.now() < marginSeconds * 1000;
}

async function _doFetch(path, { method = "GET", body, retry = true, cache = true } = {}) {
  const isGet = method === "GET";
  const cacheable = isGet && cache;

  if (cacheable) {
    const entry = _getCache.get(path);
    if (entry) {
      const fresh = Date.now() - entry.at < _GET_CACHE_TTL_MS;
      if (entry.promise) return entry.promise; // colapsa peticiones en vuelo
      if (fresh && !entry.error) return entry.data;
    }
  }

  const doIt = (async () => {
    // Refresh proactivo: si el access token ya caducó y tenemos refresh,
    // renovamos ANTES de disparar la petición para evitar tandas de 401
    // en la carga inicial con sesión rescatada.
    if (
      path !== "/auth/refresh" && path !== "/auth/login"
      && tokens.access && tokens.refresh && _tokenExpiredSoon(tokens.access)
    ) {
      await tryRefresh();
    }

    const headers = { "Content-Type": "application/json" };
    if (tokens.access) headers["Authorization"] = `Bearer ${tokens.access}`;

    const resp = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (resp.status === 401 && retry && tokens.refresh && path !== "/auth/refresh") {
      const refreshed = await tryRefresh();
      if (refreshed) return _doFetch(path, { method, body, retry: false, cache: false });
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
  })();

  if (cacheable) {
    _getCache.set(path, { at: Date.now(), promise: doIt });
    try {
      const data = await doIt;
      _getCache.set(path, { at: Date.now(), data });
      return data;
    } catch (err) {
      _getCache.delete(path);
      throw err;
    }
  }

  // Mutaciones: purga caché del recurso raíz para evitar stale reads
  if (!isGet) {
    const root = "/" + path.replace(/^\//, "").split("/")[0];
    invalidateCache(root);
  }
  return doIt;
}

// Colapso de refresh en vuelo: varias peticiones concurrentes que dispararon
// refresh comparten la misma promesa en lugar de encadenar N refresh a la vez.
let _refreshInFlight = null;
async function tryRefresh() {
  if (_refreshInFlight) return _refreshInFlight;
  _refreshInFlight = (async () => {
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
    } finally {
      _refreshInFlight = null;
    }
  })();
  return _refreshInFlight;
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

  // Acceso genérico (paneles que componen sus propias rutas, ej. panel-live.js)
  get(path) { return _doFetch(path); },

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
  nps() { return _doFetch("/data/social/kpis/nps"); },
  composicionLinguistica() {
    return _doFetch("/data/social/kpis/composicion-linguistica");
  },

  // Predicción (A.2/A.3)
  prediccionAfluencia(params = {}) {
    const q = new URLSearchParams(params).toString();
    return _doFetch(`/prediccion/afluencia${q ? `?${q}` : ""}`);
  },
  prediccionValidacion(params = {}) {
    const q = new URLSearchParams(params).toString();
    return _doFetch(`/prediccion/validacion${q ? `?${q}` : ""}`);
  },
  prediccionAnomalias(params = {}) {
    const q = new URLSearchParams(params).toString();
    return _doFetch(`/prediccion/anomalias${q ? `?${q}` : ""}`);
  },

  // Contexto histórico (backfill INE/Junta/AENA)
  contextoSerie(fuente, indicador, ambito) {
    const params = { fuente, indicador };
    if (ambito) params.ambito = ambito;
    const q = new URLSearchParams(params).toString();
    return _doFetch(`/data/contexto/series?${q}`);
  },
  factorExpansion(params = {}) {
    const q = new URLSearchParams(params).toString();
    return _doFetch(`/data/contexto/factor-expansion${q ? `?${q}` : ""}`);
  },

  // Tótems
  totemsUsage() { return _doFetch("/dashboards/totems/usage"); },
  totemsHealth() { return _doFetch("/dashboards/totems/health"); },

  // Chatbot
  chatbotTelemetry() { return _doFetch("/chatbot/telemetry"); },

  // Mantenimiento / ANS (C.1)
  monthlyReport(year, month) {
    return _doFetch(`/dashboards/reports/monthly?year=${year}&month=${month}`);
  },
  incidencias(params = {}) {
    const q = new URLSearchParams(params).toString();
    return _doFetch(`/incidencias${q ? `?${q}` : ""}`);
  },
  incidenciasANS(desde, hasta) {
    const q = new URLSearchParams({ desde, hasta }).toString();
    return _doFetch(`/incidencias/ans?${q}`);
  },

  // Ficha del cliente / Ayuntamiento (bloque 1)
  getCliente() { return _doFetch("/cliente"); },
  saveCliente(payload) {
    return _doFetch("/cliente", { method: "PUT", body: payload });
  },
  patchCliente(payload) {
    return _doFetch("/cliente", { method: "PATCH", body: payload });
  },

  // Campañas de promoción (bloque 9)
  listCampanas(params = {}) {
    const q = new URLSearchParams(params).toString();
    return _doFetch(`/campanas${q ? `?${q}` : ""}`);
  },
  getCampana(id) { return _doFetch(`/campanas/${id}`); },
  createCampana(payload) {
    return _doFetch("/campanas", { method: "POST", body: payload });
  },
  updateCampana(id, payload) {
    return _doFetch(`/campanas/${id}`, { method: "PUT", body: payload });
  },
  deleteCampana(id) {
    return _doFetch(`/campanas/${id}`, { method: "DELETE" });
  },
  campanaKpis(id) { return _doFetch(`/campanas/${id}/kpis`); },

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

  // ------------------ Usuarios (solo administrador_tic) ------------------
  listUsuarios() { return _doFetch("/usuarios"); },
  invitarUsuario(payload) {
    return _doFetch("/usuarios/invitar", { method: "POST", body: payload });
  },

  invalidateCache,
};

export function getCachedUser() {
  const raw = sessionStorage.getItem(STORAGE_KEY_USER);
  return raw ? JSON.parse(raw) : null;
}
