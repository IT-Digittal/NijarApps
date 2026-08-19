/**
 * Gemelo digital del destino — Fase 1.
 *
 * Dos vistas nuevas en la consola DTI:
 *  - «Gemelo vivo (2D)»: mapa único en tiempo real con TODOS los activos
 *    georreferenciados de la plataforma (recursos turísticos, sensores IoT,
 *    cuadros de alumbrado, contenedores, puntos de movilidad y cámaras),
 *    coloreados por estado, con capas conmutables y refresco automático.
 *  - «Vista 3D del territorio»: MapLibre GL con relieve real (DEM terrarium
 *    de AWS Open Data) e imagen satélite, con los activos superpuestos.
 *    Sin claves ni licencias: todo son fuentes abiertas.
 */

import { api, tokens } from "./api-client.js?v=18";

/* Base de la API para las llamadas que no son JSON (subida/descarga de ficheros) */
const API_BASE = (typeof window !== "undefined" && window.NIJAR_API_BASE)
  || window.location.origin + "/api/v1";

let U, UI, DTI;
let mapa2d = null;
let mapa3d = null;
let refrescoTimer = null;

const REFRESCO_MS = 60_000;
const CENTRO = [36.82, -2.1];
const CENTRO_3D = [-2.06, 36.79]; /* MapLibre usa [lon, lat] */

const VISTAS_3D = [
  { n: "Cabo de Gata", c: [-2.19, 36.72], z: 12.5, p: 62, b: 20 },
  { n: "San José", c: [-2.106, 36.76], z: 13.5, p: 60, b: -15 },
  { n: "Mónsul y Genoveses", c: [-2.14, 36.73], z: 13.8, p: 63, b: 40 },
  { n: "Rodalquilar", c: [-2.041, 36.847], z: 13.5, p: 58, b: 0 },
  { n: "Las Negras", c: [-2.0, 36.88], z: 13.5, p: 60, b: 10 },
  { n: "Níjar casco", c: [-2.207, 36.966], z: 13.5, p: 55, b: 0 },
];

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function sub(crumb, h1, p, acts) {
  return '<div class="subhead"><div><div class="crumb"><a onclick="UI.go(\'home\')">Plataforma</a> · <a onclick="UI.goD(\'resumen\')">DTI Turismo</a> · <b>' + esc(crumb) + "</b></div>" +
    "<h1>" + esc(h1) + "</h1><p>" + esc(p) + '</p></div><div class="acts">' + (acts || "") + "</div></div>";
}

function kpi(l, v, d, cls, ic, click) {
  const X = window.__UI2;
  return X && X.kpiCard ? X.kpiCard(l, v == null ? "—" : String(v), d, cls, ic, click || "") : "";
}

/* ---------------- carga y normalización de activos ---------------- */

function estadoDe(e) {
  const s = String(e || "").toLowerCase();
  if (!s || s === "desconocido") return "warn";
  if (s.startsWith("operat") || s === "online" || s === "ok" || s === "activo" || s === "activa" ||
      s === "active" || s === "verde" || s === "sin_bandera" ||
      s === "buena" || s === "razonable") return "ok"; /* EAQI 1-2 */
  if (s.includes("sin_comunicacion") || s.includes("error") || s.includes("fallo") || s === "offline" ||
      s.includes("averia") || s === "roja" ||
      s.includes("muy desfavorable") || s.includes("extremadamente")) return "err"; /* EAQI 5-6 */
  return "warn"; /* incluye bandera amarilla y EAQI 3-4 (moderada, desfavorable) */
}

const COLOR_ESTADO = { ok: "#12A150", warn: "#F0B429", err: "#E5484D" };

function coordsGeoJSON(o) {
  const u = o && o.ubicacion;
  if (u && u.coordinates && u.coordinates.length >= 2) return [u.coordinates[1], u.coordinates[0]];
  if (typeof o.latitud === "number" && typeof o.longitud === "number") return [o.latitud, o.longitud];
  if (o.latitud != null && o.longitud != null) return [parseFloat(o.latitud), parseFloat(o.longitud)];
  return null;
}

/* Recorre todas las páginas de un endpoint paginado (el gemelo debe mostrar
   el parque COMPLETO de dispositivos, no solo la primera página). */
async function cargarPaginado(ruta, pageSize = 200, maxPaginas = 10) {
  const primera = await api.get(ruta + "?page=1&page_size=" + pageSize);
  const items = (primera.items || []).slice();
  const total = primera.total ?? items.length;
  const paginas = Math.min(Math.ceil(total / pageSize), maxPaginas);
  if (paginas > 1) {
    const resto = await Promise.all(Array.from({ length: paginas - 1 }, (_, i) =>
      api.get(ruta + "?page=" + (i + 2) + "&page_size=" + pageSize).catch(() => null)));
    resto.forEach((p) => { if (p && p.items) items.push(...p.items); });
  }
  return { items, total };
}

async function cargarActivos() {
  const fuentes = {
    turismo: ["/tourism/resources?page=1&page_size=200&publicado=true", "#1F6FE5", "Recursos turísticos",
      (d) => (d.items || []).map((r) => ({ nombre: r.nombre, estado: "ok", extra: r.categoria, obj: r }))],
    sensores: ["/data/iot/sensors?page=1&page_size=100", "#00A6C0", "Sensores IoT",
      (d) => (d.items || []).map((s) => ({ nombre: s.nombre, estado: s.estado, extra: s.tipo, obj: s }))],
    alumbrado: ["/verticales/alumbrado/cuadros", "#F0B429", "Alumbrado · cuadros",
      (d) => (d.items || d || []).map((c) => ({ nombre: c.nombre || c.codigo, estado: c.estado, extra: (c.circuitos != null ? c.circuitos + " circuitos" : ""), obj: c }))],
    residuos: [() => cargarPaginado("/verticales/residuos/contenedores"), "#7B5A3A", "Residuos · contenedores",
      (d) => (d.items || d || []).map((c) => ({ nombre: c.codigo || c.nombre, estado: c.estado, extra: (c.llenado_pct != null ? "llenado " + c.llenado_pct + "%" : c.fraccion), obj: c }))],
    movilidad: ["/verticales/movilidad/puntos", "#7C6BF0", "Movilidad",
      (d) => (d.items || d || []).map((p) => ({ nombre: p.nombre || p.codigo, estado: p.estado, extra: p.tipo, obj: p }))],
    seguridad: ["/verticales/seguridad/camaras", "#E2572B", "Seguridad · CCTV",
      (d) => (d.items || d || []).map((c) => ({ nombre: c.codigo || c.nombre, estado: c.estado, extra: c.tipo, obj: c }))],
    /* Verticales externas (Fase 4). Si el backend responde 503 (fuente sin
       configurar), la capa simplemente no aparece. */
    banderas: ["/gemelo/playas/banderas", "#0E9BD8", "Banderas de playa (IoT municipal)",
      (d) => (d.banderas || []).map((b) => ({ nombre: b.nombre, estado: b.estado,
        extra: "bandera: " + String(b.estado).replace(/_/g, " "), obj: b }))],
    aire: ["/gemelo/aire/estaciones", "#18794E", "Calidad del aire y meteo (Bettair)",
      (d) => (d.estaciones || []).map((e) => ({
        nombre: "Estación " + e.id,
        /* el estado es el nivel EAQI en texto (buena, moderada…); estadoDe() lo mapea al semáforo */
        estado: e.eaqi_texto || e.estado,
        extra: (e.temperatura_c != null ? e.temperatura_c.toFixed(1) + " °C" : "") +
          (e.eaqi != null ? " · aire: " + (e.eaqi_texto || e.eaqi) : ""),
        obj: {
          estacion: e.id, calidad_aire: e.eaqi_texto, temperatura_c: e.temperatura_c,
          humedad_pct: e.humedad_pct, no2_ugm3: e.no2_ugm3, o3_ugm3: e.o3_ugm3,
          pm25_ugm3: e.pm25_ugm3, pm10_ugm3: e.pm10_ugm3, medido_en: e.medido_en,
          latitud: e.latitud, longitud: e.longitud,
        },
      }))],
  };
  const claves = Object.keys(fuentes);
  const res = await Promise.allSettled(claves.map((k) => {
    const f = fuentes[k][0];
    return typeof f === "function" ? f() : api.get(f);
  }));
  const capas = [];
  claves.forEach((k, i) => {
    const [, color, nombre, mapear] = fuentes[k];
    let items = [];
    if (res[i].status === "fulfilled" && res[i].value) {
      items = mapear(res[i].value)
        .map((a) => ({ ...a, ll: coordsGeoJSON(a.obj), sem: estadoDe(a.estado) }))
        .filter((a) => a.ll);
    }
    capas.push({ id: k, nombre, color, items, disponible: res[i].status === "fulfilled" });
  });
  return capas;
}

/* Tipo de entidad (API de documentos) por capa del gemelo */
const TIPO_DOC_POR_CAPA = {
  turismo: "recurso", sensores: "sensor", alumbrado: "cuadro", residuos: "contenedor",
  movilidad: "movilidad", seguridad: "camara", banderas: "bandera", aire: "estacion_aire",
};

function idEntidad(a) {
  return String(a.obj.urn || a.obj.codigo || a.obj.id || a.obj.estacion || a.nombre);
}

function popupActivo(capa, a, docs) {
  const filas = Object.entries(a.obj)
    .filter(([k, v]) => v != null && v !== "" && typeof v !== "object" && !["id", "urn"].includes(k))
    .slice(0, 8)
    .map(([k, v]) => "<div style='font-size:12px'><b>" + esc(k.replace(/_/g, " ")) + ":</b> " + esc(String(v)) + "</div>")
    .join("");
  const tipo = TIPO_DOC_POR_CAPA[capa.id] || "otro";
  const eid = idEntidad(a);
  const n = (docs && docs[tipo + "::" + eid]) || 0;
  const adjuntos =
    "<div style='margin-top:7px;border-top:1px solid #E3E8F2;padding-top:6px'>" +
    "<a href='#' data-doc-tipo='" + esc(tipo) + "' data-doc-id='" + esc(eid) + "' data-doc-nombre='" + esc(a.nombre) + "'" +
    " data-doc-lat='" + (a.ll ? a.ll[0] : "") + "' data-doc-lon='" + (a.ll ? a.ll[1] : "") + "'" +
    " style='font-size:12px;font-weight:700;color:#1F6FE5;text-decoration:none'>&#128206; Documentos (" + n + ") · gestionar &raquo;</a></div>";
  return "<div style='min-width:190px'><div style='font-size:10.5px;font-weight:800;letter-spacing:.06em;color:#67769A'>" +
    esc(capa.nombre.toUpperCase()) + "</div><b style='font-size:14px'>" + esc(a.nombre) + "</b>" +
    "<div style='margin:4px 0'><span style='display:inline-block;width:9px;height:9px;border-radius:50%;background:" +
    COLOR_ESTADO[a.sem] + "'></span> " + esc(a.estado || "operativo") + (a.extra ? " · " + esc(a.extra) : "") + "</div>" + filas + adjuntos + "</div>";
}

/* Al pulsar «Documentos · gestionar» en cualquier popup (2D o 3D) se abre la
   vista de documentos filtrada por ese punto. */
let docFiltro = null;
document.addEventListener("click", (ev) => {
  const enlace = ev.target && ev.target.closest && ev.target.closest("[data-doc-tipo]");
  if (!enlace) return;
  ev.preventDefault();
  docFiltro = {
    tipo: enlace.dataset.docTipo,
    id: enlace.dataset.docId,
    nombre: enlace.dataset.docNombre,
    lat: parseFloat(enlace.dataset.docLat) || null,
    lon: parseFloat(enlace.dataset.docLon) || null,
  };
  if (window.UI && window.UI.goD) window.UI.goD("gd-docs");
});

/* Conteo de documentos por entidad para los popups: {"tipo::id": n} */
async function conteoDocumentos() {
  try {
    const d = await api.get("/documentos");
    const m = {};
    (d.items || []).forEach((x) => {
      const k = x.entidad_tipo + "::" + x.entidad_id;
      m[k] = (m[k] || 0) + 1;
    });
    return m;
  } catch { return {}; }
}

/* ---------------- Leaflet / MapLibre desde CDN ---------------- */

function cargarScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = resolve;
    s.onerror = () => reject(new Error("No se pudo cargar " + src));
    document.head.appendChild(s);
  });
}

function cargarCss(href) {
  const l = document.createElement("link");
  l.rel = "stylesheet";
  l.href = href;
  document.head.appendChild(l);
}

async function leaflet() {
  if (window.L) return window.L;
  cargarCss("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css");
  await cargarScript("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js");
  return window.L;
}

async function maplibre() {
  if (window.maplibregl) return window.maplibregl;
  cargarCss("https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css");
  await cargarScript("https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js");
  return window.maplibregl;
}

/* ================= GEMELO VIVO (2D) ================= */

/* ---- Meteo pública (Open-Meteo) + últimas noticias del Ayuntamiento ---- */
function _fechaCorta(s) {
  if (!s) return "";
  try { return new Date(s).toLocaleDateString("es-ES", { day: "numeric", month: "short" }); }
  catch { return ""; }
}

async function pintarInfoGemelo() {
  const cont = document.getElementById("gd-info");
  if (!cont) return;

  const [meteo, noticias] = await Promise.all([
    api.get("/gemelo/meteo").catch(() => null),
    api.get("/noticias/turismo?page_size=5").catch(() => null),
  ]);

  let cardMeteo = "";
  if (meteo) {
    const prev = (meteo.prevision || []).slice(0, 3).map((d) =>
      '<div style="text-align:center;flex:1">' +
        '<div class="mini" style="color:var(--muted)">' + esc(_fechaCorta(d.fecha)) + "</div>" +
        '<div style="font-weight:600">' + esc(d.descripcion || "") + "</div>" +
        '<div class="mini">' + (d.temp_min_c != null ? Math.round(d.temp_min_c) + "°" : "—") +
        " / " + (d.temp_max_c != null ? Math.round(d.temp_max_c) + "°" : "—") + "</div>" +
      "</div>").join("");
    cardMeteo =
      '<div class="card" style="padding:16px">' +
        '<h3 style="margin:0 0 4px">El tiempo · Níjar</h3>' +
        '<div class="mini" style="color:var(--muted);margin-bottom:10px">Fuente pública Open-Meteo</div>' +
        '<div style="display:flex;align-items:baseline;gap:10px">' +
          '<span style="font-size:34px;font-weight:700">' +
          (meteo.temperatura_c != null ? Math.round(meteo.temperatura_c) + "°" : "—") + "</span>" +
          '<span style="font-weight:600">' + esc(meteo.descripcion || "") + "</span></div>" +
        '<div class="mini" style="color:var(--muted);margin:4px 0 12px">' +
          (meteo.humedad_pct != null ? "Humedad " + meteo.humedad_pct + "% · " : "") +
          (meteo.viento_kmh != null ? "Viento " + Math.round(meteo.viento_kmh) + " km/h " +
            esc(meteo.viento_cardinal || "") : "") + "</div>" +
        '<div style="display:flex;gap:8px">' + prev + "</div>" +
      "</div>";
  } else {
    cardMeteo = '<div class="card" style="padding:16px"><h3 style="margin:0 0 4px">El tiempo</h3>' +
      '<div class="mini" style="color:var(--muted)">Meteo no disponible ahora mismo.</div></div>';
  }

  let cardNoticias;
  const items = (noticias && noticias.items) || [];
  if (items.length) {
    const filas = items.map((n) =>
      '<a href="#" onclick="return false" style="display:flex;gap:10px;padding:8px 0;border-top:1px solid var(--border);text-decoration:none;color:inherit">' +
        (n.imagen_url
          ? '<img src="' + esc(n.imagen_url) + '" alt="" loading="lazy" style="width:56px;height:42px;object-fit:cover;border-radius:6px;flex:0 0 auto">'
          : "") +
        "<div><div style=\"font-weight:600;line-height:1.25\">" + esc(n.titulo || "") + "</div>" +
        '<div class="mini" style="color:var(--muted)">' + esc(_fechaCorta(n.fecha || n.publicado_en)) +
        (n.categorias && n.categorias.length ? " · " + esc(n.categorias[0]) : "") + "</div></div>" +
      "</a>").join("");
    cardNoticias =
      '<div class="card" style="padding:16px">' +
        '<h3 style="margin:0 0 4px">Últimas noticias de Turismo</h3>' +
        '<div class="mini" style="color:var(--muted);margin-bottom:4px">Fuente: web del Ayuntamiento (Strapi)</div>' +
        filas +
      "</div>";
  } else {
    cardNoticias = '<div class="card" style="padding:16px">' +
      '<h3 style="margin:0 0 4px">Últimas noticias de Turismo</h3>' +
      '<div class="mini" style="color:var(--muted)">No hay noticias disponibles ahora mismo.</div></div>';
  }

  cont.innerHTML = cardMeteo + cardNoticias;
}

async function renderGemelo2D(el) {
  el.innerHTML = sub("Gemelo digital", "Gemelo vivo del destino",
    "Réplica digital operativa: los activos de la plataforma y de las verticales externas (IoT municipal con banderas de playa y aforo del parque; red Bettair de calidad del aire y meteorología) sobre un único mapa en tiempo real, con refresco automático cada minuto.",
    '<button class="btn btn--pri" onclick="UI.goD(\'gd-3d\')">Vista 3D →</button>') +
    '<div class="grid g4" style="margin-bottom:16px" id="gd-kpis"></div>' +
    '<div class="card card--pad0" style="overflow:hidden"><div id="gemelo-2d" style="height:600px;width:100%"></div></div>' +
    '<div class="mini" style="color:var(--muted);margin-top:8px" id="gd-refresco"></div>' +
    '<div class="grid g2" style="margin-top:16px" id="gd-info"></div>';

  const [capas, aforo, docs] = await Promise.all([
    cargarActivos(),
    api.get("/gemelo/parque/aforo").catch(() => null), /* 503 si la vertical no está configurada */
    conteoDocumentos(),
  ]);

  const total = capas.reduce((a, c) => a + c.items.length, 0);
  const enAlerta = capas.reduce((a, c) => a + c.items.filter((x) => x.sem !== "ok").length, 0);
  document.getElementById("gd-kpis").innerHTML =
    kpi("Activos en el gemelo", total, capas.filter((c) => c.items.length).length + " capas con datos", "ic-navy", "map") +
    kpi("Operativos", total - enAlerta, "Estado nominal", "ic-ok", "bolt") +
    kpi("Con incidencia", enAlerta, "Alerta o sin comunicación", "ic-coral", "warn") +
    (aforo && aforo.aforo_actual != null
      ? kpi("Aforo P.N. Cabo de Gata", aforo.aforo_actual + " vehículos",
          "Ahora dentro · " + (aforo.entradas_hoy != null ? aforo.entradas_hoy + " entradas hoy · " : "") + "IoT municipal en vivo", "ic-teal", "map")
      : kpi("Refresco", "60 s", "Telemetría de la plataforma en vivo", "ic-teal", "clock"));

  pintarInfoGemelo();

  let L;
  try {
    L = await leaflet();
  } catch (e) {
    document.getElementById("gemelo-2d").innerHTML =
      '<div class="mini" style="color:var(--err);padding:40px;text-align:center">No se pudo cargar el visor de mapa: ' + esc(e.message || e) + "</div>";
    return;
  }

  setTimeout(() => {
    const cont = document.getElementById("gemelo-2d");
    if (!cont || cont.dataset.iniciado) return;
    cont.dataset.iniciado = "1";
    mapa2d = L.map(cont, { preferCanvas: true }).setView(CENTRO, 11); /* canvas: fluido con ~800 marcadores */
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: "&copy; OpenStreetMap" }).addTo(mapa2d);

    const grupos = {};
    const puntos = [];
    capas.forEach((capa) => {
      if (!capa.disponible) return; /* fuente no configurada o caída: no listar la capa */
      const g = L.layerGroup();
      capa.items.forEach((a) => {
        puntos.push(a.ll);
        L.circleMarker(a.ll, {
          radius: 8, weight: 2.5, color: "#fff",
          fillColor: a.sem === "ok" ? capa.color : COLOR_ESTADO[a.sem], fillOpacity: 1,
        }).bindPopup(popupActivo(capa, a, docs)).addTo(g);
      });
      g.addTo(mapa2d);
      grupos[
        '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:' + capa.color + ';margin-right:4px"></span>' +
        capa.nombre + " (" + capa.items.length + ")"
      ] = g;
    });
    L.control.layers(null, grupos, { collapsed: false }).addTo(mapa2d);
    if (puntos.length) mapa2d.fitBounds(L.latLngBounds(puntos).pad(0.12));
    setTimeout(() => mapa2d.invalidateSize(), 150);
  }, 60);

  /* Refresco automático mientras la sección esté visible */
  if (refrescoTimer) clearInterval(refrescoTimer);
  refrescoTimer = setInterval(() => {
    const visible = document.getElementById("dv-gd-mapa");
    if (!visible || visible.style.display === "none") return;
    mapa2d = null;
    UI.rerenderD("gd-mapa");
  }, REFRESCO_MS);
  document.getElementById("gd-refresco").textContent =
    "Última actualización: " + new Date().toLocaleTimeString("es-ES") + " · el gemelo se actualiza automáticamente cada minuto.";
}

/* ================= VISTA 3D DEL TERRITORIO ================= */

async function renderGemelo3D(el) {
  el.innerHTML = sub("Gemelo 3D", "Vista 3D del territorio",
    "Relieve real del Parque Natural Cabo de Gata-Níjar (modelo digital de elevaciones + imagen satélite, fuentes abiertas) con los activos de la plataforma superpuestos. Arrastra con el botón derecho para rotar e inclinar.",
    VISTAS_3D.map((v, i) => '<button class="btn btn--sm" data-vista3d="' + i + '">' + esc(v.n) + "</button>").join("")) +
    '<div class="card card--pad0" style="overflow:hidden"><div id="gemelo-3d" style="height:640px;width:100%;background:#0b1c33"></div></div>' +
    '<div class="mini" style="color:var(--muted);margin-top:8px">Terreno: Terrain Tiles (AWS Open Data, Mapzen/USGS) · Imagen: Esri World Imagery · Sin licencias ni claves.</div>';

  let gl, capas, docs3d;
  try {
    [gl, capas, docs3d] = await Promise.all([maplibre(), cargarActivos(), conteoDocumentos()]);
  } catch (e) {
    document.getElementById("gemelo-3d").innerHTML =
      '<div class="mini" style="color:#fff;padding:40px;text-align:center">No se pudo cargar el visor 3D: ' + esc(e.message || e) + "</div>";
    return;
  }

  setTimeout(() => {
    const cont = document.getElementById("gemelo-3d");
    if (!cont || cont.dataset.iniciado) return;
    cont.dataset.iniciado = "1";
    try {
      mapa3d = new gl.Map({
        container: cont,
        center: CENTRO_3D,
        zoom: 12,
        pitch: 62,
        bearing: 15,
        maxPitch: 75,
        style: {
          version: 8,
          sources: {
            satelite: {
              type: "raster",
              tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
              tileSize: 256,
              maxzoom: 18,
              attribution: "Esri, Maxar, Earthstar Geographics",
            },
            dem: {
              type: "raster-dem",
              tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
              encoding: "terrarium",
              tileSize: 256,
              maxzoom: 13,
            },
          },
          layers: [{ id: "satelite", type: "raster", source: "satelite" }],
          terrain: { source: "dem", exaggeration: 1.35 },
        },
      });
      mapa3d.addControl(new gl.NavigationControl({ visualizePitch: true }));
      mapa3d.on("load", () => {
        mapa3d.setTerrain({ source: "dem", exaggeration: 1.35 });
        /* Fase 2: edificios 3D extruidos (huellas OSM vía OpenFreeMap, sin clave) */
        try {
          mapa3d.addSource("edificios", { type: "vector", url: "https://tiles.openfreemap.org/planet" });
          mapa3d.addLayer({
            id: "edificios-3d",
            type: "fill-extrusion",
            source: "edificios",
            "source-layer": "building",
            minzoom: 13,
            paint: {
              "fill-extrusion-color": "#EFE7D6",
              "fill-extrusion-height": ["coalesce", ["get", "render_height"], 4.5],
              "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0],
              "fill-extrusion-opacity": 0.9,
            },
          });
        } catch { /* sin edificios: el terreno sigue funcionando */ }
        /* Activos como capa de círculos WebGL: escala a cientos de puntos sin
           coste por marcador (los Marker DOM no aguantan el parque completo). */
        const features = [];
        capas.forEach((capa) => {
          capa.items.forEach((a) => {
            features.push({
              type: "Feature",
              geometry: { type: "Point", coordinates: [a.ll[1], a.ll[0]] },
              properties: { color: a.sem === "ok" ? capa.color : COLOR_ESTADO[a.sem], html: popupActivo(capa, a, docs3d) },
            });
          });
        });
        mapa3d.addSource("activos", { type: "geojson", data: { type: "FeatureCollection", features } });
        mapa3d.addLayer({
          id: "activos-puntos",
          type: "circle",
          source: "activos",
          paint: {
            "circle-radius": 6.5,
            "circle-color": ["get", "color"],
            "circle-stroke-width": 2,
            "circle-stroke-color": "#fff",
          },
        });
        mapa3d.on("click", "activos-puntos", (e) => {
          const f = e.features && e.features[0];
          if (f) new gl.Popup({ offset: 10 }).setLngLat(f.geometry.coordinates).setHTML(f.properties.html).addTo(mapa3d);
        });
        mapa3d.on("mouseenter", "activos-puntos", () => { mapa3d.getCanvas().style.cursor = "pointer"; });
        mapa3d.on("mouseleave", "activos-puntos", () => { mapa3d.getCanvas().style.cursor = ""; });
      });
    } catch (e) {
      cont.innerHTML = '<div class="mini" style="color:#fff;padding:40px;text-align:center">Este navegador no soporta WebGL para la vista 3D: ' + esc(e.message || e) + "</div>";
      return;
    }
  }, 60);

  el.querySelectorAll("[data-vista3d]").forEach((b) =>
    b.addEventListener("click", () => {
      const v = VISTAS_3D[Number(b.dataset.vista3d)];
      if (mapa3d && v) mapa3d.flyTo({ center: v.c, zoom: v.z, pitch: v.p, bearing: v.b, duration: 2600 });
    }));
}

/* ================= DOCUMENTOS DEL TERRITORIO ================= */

const NOMBRE_TIPO_DOC = {
  recurso: "Recurso turístico", sensor: "Sensor IoT", cuadro: "Cuadro de alumbrado",
  contenedor: "Contenedor", movilidad: "Movilidad", camara: "Cámara CCTV",
  bandera: "Bandera de playa", estacion_aire: "Estación de aire", otro: "Otro",
};

function tamanoLegible(b) {
  if (b == null) return "—";
  if (b < 1024) return b + " B";
  if (b < 1024 * 1024) return (b / 1024).toFixed(0) + " KB";
  return (b / (1024 * 1024)).toFixed(1) + " MB";
}

async function descargarDocumento(id, nombre) {
  const resp = await fetch(API_BASE + "/documentos/" + id + "/archivo", {
    headers: { Authorization: "Bearer " + tokens.access },
  });
  if (!resp.ok) throw new Error("HTTP " + resp.status);
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nombre || "documento";
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

async function renderDocumentos(el) {
  el.innerHTML = sub("Documentos", "Documentos del territorio",
    "Cargando…", "") + '<div class="card"><div class="mini" style="color:var(--muted);padding:20px 0;text-align:center">Cargando documentos…</div></div>';

  const filtro = docFiltro;
  docFiltro = null; /* se consume una vez: al volver a entrar se ve todo */
  const ruta = filtro
    ? "/documentos?entidad_tipo=" + encodeURIComponent(filtro.tipo) + "&entidad_id=" + encodeURIComponent(filtro.id)
    : "/documentos";

  let datos, capas;
  try {
    [datos, capas] = await Promise.all([
      api.get(ruta),
      filtro ? Promise.resolve(null) : cargarActivos(), /* selector de punto solo en vista global */
    ]);
  } catch (e) {
    el.innerHTML = sub("Documentos", "Documentos del territorio", "", "") +
      '<div class="card"><div class="mini" style="color:var(--err);padding:26px 0;text-align:center">No se pudo cargar el listado: ' + esc(e.message || e) + "</div></div>";
    return;
  }
  const filas = datos.items || [];

  /* Selector de punto (vista global): todos los activos del gemelo */
  let opciones = "";
  if (capas) {
    opciones = capas.map((capa) => {
      const tipo = TIPO_DOC_POR_CAPA[capa.id] || "otro";
      const opts = capa.items.map((a) =>
        '<option value="' + esc(tipo + "|" + idEntidad(a) + "|" + a.nombre + "|" + (a.ll ? a.ll[0] : "") + "|" + (a.ll ? a.ll[1] : "")) + '">' +
        esc(a.nombre) + "</option>").join("");
      return opts ? '<optgroup label="' + esc(capa.nombre) + '">' + opts + "</optgroup>" : "";
    }).join("");
  }

  const cabecera = filtro
    ? "Documentos de «" + esc(filtro.nombre) + "» (" + esc(NOMBRE_TIPO_DOC[filtro.tipo] || filtro.tipo) + ")"
    : "Todos los documentos adjuntos a puntos del mapa";

  el.innerHTML = sub("Documentos", "Documentos del territorio",
    "Fichas técnicas, fotos, planos o cualquier fichero adjunto a los puntos del gemelo digital. Se adjuntan desde aquí o desde la ficha de cada punto en el mapa 2D/3D.",
    filtro ? '<button class="btn" id="doc-quitar-filtro">Ver todos</button>' : "") +
    '<div class="grid c7-5" style="margin-bottom:16px">' +
    '<div class="card card--pad0"><div style="padding:16px 16px 4px" class="card__h"><div><div class="card__t">' + cabecera +
    '</div><div class="card__s">' + (datos.total ?? filas.length) + " documento(s)</div></div></div>" +
    '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Punto</th><th>Documento</th><th>Tamaño</th><th>Fecha</th><th></th></tr></thead><tbody id="doc-tbody">' +
    (filas.map((d, i) =>
      "<tr><td style='white-space:normal;min-width:150px'><b>" + esc(d.entidad_nombre) + "</b><div class='mini' style='color:var(--muted)'>" +
      esc(NOMBRE_TIPO_DOC[d.entidad_tipo] || d.entidad_tipo) + "</div></td>" +
      "<td style='white-space:normal;min-width:170px'>" + esc(d.nombre_archivo) +
      (d.descripcion ? "<div class='mini' style='color:var(--muted)'>" + esc(d.descripcion) + "</div>" : "") + "</td>" +
      "<td class='mini tnum'>" + tamanoLegible(d.tamano_bytes) + "</td>" +
      "<td class='mini tnum'>" + new Date(d.created_at).toLocaleDateString("es-ES") + "</td>" +
      "<td style='white-space:nowrap'><button class='btn btn--sm' data-doc-dl='" + i + "'>Descargar</button> " +
      "<button class='btn btn--sm' data-doc-del='" + i + "'>Eliminar</button></td></tr>").join("") ||
      "<tr><td colspan='5' class='mini' style='text-align:center;padding:22px'>Sin documentos todavía — adjunta el primero desde el formulario</td></tr>") +
    "</tbody></table></div></div>" +
    '<div class="card"><div class="card__h"><div><div class="card__t">Adjuntar documento</div><div class="card__s">Cualquier tipo de fichero · máx. 25 MB</div></div></div>' +
    '<form id="doc-form">' +
    (filtro
      ? '<div class="mini" style="margin-bottom:10px">Se adjuntará a: <b>' + esc(filtro.nombre) + "</b></div>"
      : '<label class="mini" style="color:var(--muted)">Punto del mapa</label><select id="doc-ent" required style="width:100%;border:1.5px solid var(--line);border-radius:10px;padding:9px 12px;font-size:13.5px;font-family:inherit;margin:4px 0 12px">' +
        '<option value="">— Elige un punto —</option>' + opciones + "</select>") +
    '<label class="mini" style="color:var(--muted)">Fichero</label>' +
    '<input type="file" id="doc-file" required style="width:100%;margin:4px 0 12px;font-size:13px">' +
    '<label class="mini" style="color:var(--muted)">Descripción (opcional)</label>' +
    '<input type="text" id="doc-desc" maxlength="500" placeholder="Ficha técnica, plano, foto…" style="width:100%;border:1.5px solid var(--line);border-radius:10px;padding:9px 12px;font-size:13.5px;font-family:inherit;margin:4px 0 14px">' +
    '<button class="btn btn--pri" type="submit" style="width:100%">Adjuntar al punto</button>' +
    '<div class="mini" id="doc-msg" style="color:var(--muted);margin-top:10px"></div></form></div></div>';

  const qf = el.querySelector("#doc-quitar-filtro");
  if (qf) qf.onclick = () => { docFiltro = null; UI.rerenderD("gd-docs"); };

  el.querySelectorAll("[data-doc-dl]").forEach((b) => {
    b.onclick = async () => {
      const d = filas[Number(b.dataset.docDl)];
      try { await descargarDocumento(d.id, d.nombre_archivo); }
      catch (e) { if (UI.toast) UI.toast("No se pudo descargar: " + (e.message || e)); }
    };
  });
  el.querySelectorAll("[data-doc-del]").forEach((b) => {
    b.onclick = async () => {
      const d = filas[Number(b.dataset.docDel)];
      if (!window.confirm('¿Eliminar "' + d.nombre_archivo + '" de ' + d.entidad_nombre + "?")) return;
      const resp = await fetch(API_BASE + "/documentos/" + d.id, {
        method: "DELETE", headers: { Authorization: "Bearer " + tokens.access },
      });
      if (resp.ok) { if (UI.toast) UI.toast("Documento eliminado"); docFiltro = filtro; UI.rerenderD("gd-docs"); }
      else if (UI.toast) UI.toast(resp.status === 403 ? "Tu rol no puede eliminar documentos" : "Error HTTP " + resp.status);
    };
  });

  el.querySelector("#doc-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const msg = el.querySelector("#doc-msg");
    let ent = filtro;
    if (!ent) {
      const v = el.querySelector("#doc-ent").value;
      if (!v) { msg.textContent = "Elige un punto del mapa."; return; }
      const [tipo, id, nombre, lat, lon] = v.split("|");
      ent = { tipo, id, nombre, lat: parseFloat(lat) || null, lon: parseFloat(lon) || null };
    }
    const fichero = el.querySelector("#doc-file").files[0];
    if (!fichero) { msg.textContent = "Elige un fichero."; return; }
    const fd = new FormData();
    fd.append("archivo", fichero);
    fd.append("entidad_tipo", ent.tipo);
    fd.append("entidad_id", ent.id);
    fd.append("entidad_nombre", ent.nombre);
    if (ent.lat != null) fd.append("latitud", String(ent.lat));
    if (ent.lon != null) fd.append("longitud", String(ent.lon));
    const desc = el.querySelector("#doc-desc").value.trim();
    if (desc) fd.append("descripcion", desc);
    msg.textContent = "Subiendo…";
    const resp = await fetch(API_BASE + "/documentos", {
      method: "POST", headers: { Authorization: "Bearer " + tokens.access }, body: fd,
    });
    if (resp.ok) {
      if (UI.toast) UI.toast("Documento adjuntado a " + ent.nombre);
      docFiltro = filtro; UI.rerenderD("gd-docs");
    } else {
      const cuerpo = await resp.json().catch(() => null);
      msg.textContent = resp.status === 403
        ? "Tu rol no puede adjuntar documentos (administrador, gestor u operador)."
        : "Error: " + ((cuerpo && cuerpo.detail) || "HTTP " + resp.status);
    }
  });
}

/* ================= SIMULADOR DE ESCENARIOS (Fase 3) ================= */

/* Eventos reales del calendario del municipio (petición del Ayuntamiento).
   Cada uno reparte su asistencia sobre la predicción base con el perfil de
   días propio del evento; el deslizador fija la asistencia esperada respecto
   a la escala documentada en los supuestos. */
function picoEvento(base, dias) {
  /* dias = [[desplazamiento respecto al centro del horizonte, peso], …] */
  const serie = base.slice();
  const centro = Math.floor(serie.length / 2);
  dias.forEach(([off, extra]) => {
    const i = centro + off;
    if (serie[i] != null) serie[i] = Math.round(serie[i] + extra);
  });
  return serie;
}

const ESCENARIOS = [
  {
    id: "desembarco_pirata",
    n: "Desembarco Pirata (San José · marzo)",
    d: "Recreación histórica del desembarco berberisco en la bahía de San José: mercado, pasacalles y batalla en la playa. Gran pico el día grande con arrastre de víspera y domingo.",
    param: "Asistencia esperada",
    supuesto: "Supuestos: 100% ≈ 6.000 asistentes (70% el día grande, 15% la víspera, 15% el domingo). Se proyecta sobre el centro del horizonte; el evento real es en marzo. Elasticidades pendientes de calibrar con la primera edición medida.",
    aplicar(base, p) {
      const a = 6000 * (p / 100);
      return {
        serie: picoEvento(base, [[-1, a * 0.15], [0, a * 0.7], [1, a * 0.15]]),
        nota: "Refuerzo recomendado: parking disuasorio y lanzadera a San José · pico +" + Math.round(a * 0.7) + " visitas",
      };
    },
  },
  {
    id: "noche_velas",
    n: "Noche de las Velas (Rodalquilar)",
    d: "Miles de velas iluminan el poblado minero de Rodalquilar en una sola noche de verano, con música y comercio local abierto.",
    param: "Asistencia esperada",
    supuesto: "Supuestos: 100% ≈ 5.000 asistentes concentrados en una única noche (85% el día, 15% la víspera). Elasticidades pendientes de calibrar.",
    aplicar(base, p) {
      const a = 5000 * (p / 100);
      return {
        serie: picoEvento(base, [[-1, a * 0.15], [0, a * 0.85]]),
        nota: "Concentración nocturna en un núcleo pequeño: plan de tráfico y aparcamiento en la ctra. del Playazo · pico +" + Math.round(a * 0.85) + " visitas",
      };
    },
  },
  {
    id: "festival_chio",
    n: "Conciertos de Campohermoso · Festival Chío",
    d: "Ciclo de conciertos en Campohermoso durante varias noches consecutivas, con público local y de municipios vecinos.",
    param: "Asistencia esperada",
    supuesto: "Supuestos: 100% ≈ 9.000 asistentes acumulados en 3 noches (30% · 40% · 30%). Elasticidades pendientes de calibrar.",
    aplicar(base, p) {
      const a = 9000 * (p / 100);
      return {
        serie: picoEvento(base, [[-1, a * 0.3], [0, a * 0.4], [1, a * 0.3]]),
        nota: "Tres noches seguidas en Campohermoso: reforzar limpieza y transporte nocturno · noche punta +" + Math.round(a * 0.4) + " visitas",
      };
    },
  },
  {
    id: "expolevante",
    n: "ExpoLevante (bienal · agricultura)",
    d: "Feria bienal de la agricultura intensiva en Campohermoso: expositores, profesionales del sector y público general durante cuatro jornadas.",
    param: "Asistencia esperada",
    supuesto: "Supuestos: 100% ≈ 40.000 visitantes acumulados en 4 jornadas diurnas (reparto 20% · 30% · 30% · 20%). Se celebra cada 2 años. Elasticidades pendientes de calibrar.",
    aplicar(base, p) {
      const a = 40000 * (p / 100);
      return {
        serie: picoEvento(base, [[-1, a * 0.2], [0, a * 0.3], [1, a * 0.3], [2, a * 0.2]]),
        nota: "Perfil profesional + general en horario diurno: presión sobre restauración y accesos de Campohermoso · jornada punta +" + Math.round(a * 0.3) + " visitas",
      };
    },
  },
  {
    id: "nijar_cup",
    n: "Níjar Cup / SuperCup (fútbol base)",
    d: "Campeonato de fútbol base con equipos desplazados: partidos durante varios días y familias alojadas en el municipio toda la semana.",
    param: "Asistencia esperada",
    supuesto: "Supuestos: 100% ≈ 3.500 personas/día (jugadores, técnicos y familias) durante 5 jornadas seguidas — demanda sostenida, no un pico. Elasticidades pendientes de calibrar.",
    aplicar(base, p) {
      const a = 3500 * (p / 100);
      return {
        serie: picoEvento(base, [[-2, a], [-1, a], [0, a], [1, a], [2, a]]),
        nota: "Demanda sostenida 5 días: ocupación hotelera y restauración en todo el municipio · +" + Math.round(a) + " visitas/día",
      };
    },
  },
];

async function renderSimulador(el) {
  el.innerHTML = sub("Simulador", "Simulador de escenarios «qué pasaría si»",
    "Los grandes eventos del calendario del municipio simulados sobre la predicción real de afluencia de la plataforma, comparando el resultado con la línea base.", "") +
    '<div class="card"><div class="mini" style="color:var(--muted);padding:20px 0;text-align:center">Cargando la predicción base…</div></div>';

  let base = null;
  try {
    const af = await api.get("/prediccion/afluencia?metrica=totem&horizonte_dias=14");
    base = (af.puntos || []).map((p) => p.valor_estimado ?? p.prediccion ?? p.valor ?? 0);
  } catch { /* sin predicción */ }

  if (!base || !base.length || !base.some((v) => v > 0)) {
    el.innerHTML = sub("Simulador", "Simulador de escenarios",
      "Fase 3 del gemelo digital.") +
      '<div class="card"><div class="mini" style="color:var(--muted);padding:26px 0;text-align:center">El simulador necesita la predicción de afluencia y aún no hay histórico suficiente para generarla.</div></div>';
    return;
  }

  const opciones = ESCENARIOS.map((e, i) => '<option value="' + i + '">' + esc(e.n) + "</option>").join("");
  el.innerHTML = sub("Simulador", "Simulador de escenarios «qué pasaría si»",
    "Eventos del calendario del municipio sobre la predicción real de afluencia (línea discontinua: base; línea sólida: escenario).", "") +
    '<div class="grid c7-5" style="margin-bottom:16px">' +
    '<div class="card"><div class="card__h"><div><div class="card__t">Escenario</div><div class="card__s" id="sim-desc"></div></div></div>' +
    '<select id="sim-esc" style="width:100%;border:1.5px solid var(--line);border-radius:10px;padding:10px 12px;font-size:14px;font-family:inherit;margin-bottom:14px">' + opciones + "</select>" +
    '<label class="mini" style="color:var(--muted)"><span id="sim-param-label">Intensidad</span>: <b id="sim-param-val">50</b>%</label>' +
    '<input type="range" id="sim-param" min="10" max="100" value="50" style="width:100%;margin:6px 0 14px">' +
    '<button class="btn btn--pri" id="sim-run" style="width:100%">Simular escenario</button>' +
    '<div class="mini" id="sim-supuesto" style="color:var(--muted);margin-top:12px"></div></div>' +
    '<div class="card"><div class="card__h"><div><div class="card__t">Impacto estimado</div><div class="card__s">Sobre los próximos 14 días</div></div></div><div id="sim-kpis" class="mini" style="color:var(--muted)">Ejecuta una simulación para ver el impacto.</div></div>' +
    "</div>" +
    '<div class="card"><div class="card__h"><div><div class="card__t">Afluencia prevista · base vs escenario</div><div class="card__s">Predicción real del modelo de la plataforma como línea base</div></div></div><div id="sim-chart">' +
    (U ? U.areaChart(base, { color: "blue", hpx: 190, h: 200 }) : "") + "</div></div>" +
    '<div class="mini" style="color:var(--muted);margin-top:8px">Simulador paramétrico (Fase 3 inicial): la línea base procede del modelo de predicción real; las elasticidades de cada escenario son supuestos documentados, pendientes de calibración con los datos de la primera temporada completa.</div>';

  const sel = el.querySelector("#sim-esc");
  const slider = el.querySelector("#sim-param");
  const pintarMeta = () => {
    const e = ESCENARIOS[Number(sel.value)];
    el.querySelector("#sim-desc").textContent = e.d;
    el.querySelector("#sim-param-label").textContent = e.param;
    el.querySelector("#sim-supuesto").textContent = e.supuesto;
  };
  pintarMeta();
  sel.addEventListener("change", pintarMeta);
  slider.addEventListener("input", () => { el.querySelector("#sim-param-val").textContent = slider.value; });

  el.querySelector("#sim-run").addEventListener("click", () => {
    const e = ESCENARIOS[Number(sel.value)];
    const p = Number(slider.value);
    const { serie, nota } = e.aplicar(base, p);
    const totalBase = base.reduce((a, b) => a + b, 0);
    const totalEsc = serie.reduce((a, b) => a + b, 0);
    const delta = totalBase ? ((totalEsc - totalBase) / totalBase) * 100 : 0;
    const pico = Math.max.apply(null, serie);
    const diaPico = serie.indexOf(pico) + 1;
    el.querySelector("#sim-chart").innerHTML = U.areaChart(serie, { color: delta >= 0 ? "teal" : "gold", hpx: 190, h: 200, compare: base });
    el.querySelector("#sim-kpis").innerHTML =
      '<div class="kv"><span class="k">Visitas base (14 días)</span><span class="v tnum">' + U.fmt(totalBase) + "</span></div>" +
      '<div class="kv"><span class="k">Visitas con escenario</span><span class="v tnum">' + U.fmt(totalEsc) + "</span></div>" +
      '<div class="kv"><span class="k">Variación</span><span class="v tnum" style="color:' + (delta >= 0 ? "var(--ok)" : "var(--err)") + '">' + (delta >= 0 ? "+" : "") + delta.toFixed(1) + "%</span></div>" +
      '<div class="kv"><span class="k">Pico del escenario</span><span class="v tnum">' + U.fmt(pico) + " (día " + diaPico + ")</span></div>" +
      '<div class="kv" style="align-items:flex-start"><span class="k">Lectura</span><span class="v mini" style="max-width:60%;text-align:right">' + esc(nota) + "</span></div>";
  });
}

/* ---------------- registro en la consola DTI ---------------- */

(function init() {
  DTI = window.__DTI;
  UI = window.UI;
  U = window.__U;
  if (!DTI || !DTI.DSECTIONS || !DTI.renderDSidebar || !UI) return setTimeout(init, 300);

  const main = document.getElementById("dti-main");
  const secciones = [
    { g: "Gemelo digital" },
    { id: "gd-mapa", n: "Gemelo vivo (2D)", i: "map", r: renderGemelo2D },
    { id: "gd-3d", n: "Vista 3D del territorio", i: "globe", r: renderGemelo3D },
    { id: "gd-sim", n: "Simulador de escenarios", i: "chart", r: renderSimulador },
    { id: "gd-docs", n: "Documentos del territorio", i: "folder", r: renderDocumentos },
  ];
  secciones.forEach((s) => {
    if (s.g) { DTI.DSECTIONS.push({ g: s.g }); return; }
    DTI.DSECTIONS.push({ id: s.id, n: s.n, i: s.i });
    DTI.DR[s.id] = s.r;
    if (main && !document.getElementById("dv-" + s.id)) {
      const sec = document.createElement("section");
      sec.className = "dview";
      sec.id = "dv-" + s.id;
      main.insertBefore(sec, main.lastElementChild);
    }
  });
  DTI.renderDSidebar();
})();
