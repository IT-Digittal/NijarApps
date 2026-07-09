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

import { api } from "./api-client.js?v=18";

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
  if (s.startsWith("operat") || s === "online" || s === "ok" || s === "activo" || s === "activa") return "ok";
  if (s.includes("sin_comunicacion") || s.includes("error") || s.includes("fallo") || s === "offline" || s.includes("averia")) return "err";
  return "warn";
}

const COLOR_ESTADO = { ok: "#12A150", warn: "#F0B429", err: "#E5484D" };

function coordsGeoJSON(o) {
  const u = o && o.ubicacion;
  if (u && u.coordinates && u.coordinates.length >= 2) return [u.coordinates[1], u.coordinates[0]];
  if (typeof o.latitud === "number" && typeof o.longitud === "number") return [o.latitud, o.longitud];
  if (o.latitud != null && o.longitud != null) return [parseFloat(o.latitud), parseFloat(o.longitud)];
  return null;
}

async function cargarActivos() {
  const fuentes = {
    turismo: ["/tourism/resources?page=1&page_size=200&publicado=true", "#1F6FE5", "Recursos turísticos",
      (d) => (d.items || []).map((r) => ({ nombre: r.nombre, estado: "ok", extra: r.categoria, obj: r }))],
    sensores: ["/data/iot/sensors?page=1&page_size=100", "#00A6C0", "Sensores IoT",
      (d) => (d.items || []).map((s) => ({ nombre: s.nombre, estado: s.estado, extra: s.tipo, obj: s }))],
    alumbrado: ["/verticales/alumbrado/cuadros", "#F0B429", "Alumbrado · cuadros",
      (d) => (d.items || d || []).map((c) => ({ nombre: c.nombre || c.codigo, estado: c.estado, extra: (c.circuitos != null ? c.circuitos + " circuitos" : ""), obj: c }))],
    residuos: ["/verticales/residuos/contenedores?page_size=200", "#7B5A3A", "Residuos · contenedores",
      (d) => (d.items || d || []).map((c) => ({ nombre: c.codigo || c.nombre, estado: c.estado, extra: (c.llenado_pct != null ? "llenado " + c.llenado_pct + "%" : c.fraccion), obj: c }))],
    movilidad: ["/verticales/movilidad/puntos", "#7C6BF0", "Movilidad",
      (d) => (d.items || d || []).map((p) => ({ nombre: p.nombre || p.codigo, estado: p.estado, extra: p.tipo, obj: p }))],
    seguridad: ["/verticales/seguridad/camaras", "#E2572B", "Seguridad · CCTV",
      (d) => (d.items || d || []).map((c) => ({ nombre: c.codigo || c.nombre, estado: c.estado, extra: c.tipo, obj: c }))],
  };
  const claves = Object.keys(fuentes);
  const res = await Promise.allSettled(claves.map((k) => api.get(fuentes[k][0])));
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

function popupActivo(capa, a) {
  const filas = Object.entries(a.obj)
    .filter(([k, v]) => v != null && v !== "" && typeof v !== "object" && !["id", "urn"].includes(k))
    .slice(0, 8)
    .map(([k, v]) => "<div style='font-size:12px'><b>" + esc(k.replace(/_/g, " ")) + ":</b> " + esc(String(v)) + "</div>")
    .join("");
  return "<div style='min-width:190px'><div style='font-size:10.5px;font-weight:800;letter-spacing:.06em;color:#67769A'>" +
    esc(capa.nombre.toUpperCase()) + "</div><b style='font-size:14px'>" + esc(a.nombre) + "</b>" +
    "<div style='margin:4px 0'><span style='display:inline-block;width:9px;height:9px;border-radius:50%;background:" +
    COLOR_ESTADO[a.sem] + "'></span> " + esc(a.estado || "operativo") + (a.extra ? " · " + esc(a.extra) : "") + "</div>" + filas + "</div>";
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

async function renderGemelo2D(el) {
  el.innerHTML = sub("Gemelo digital", "Gemelo vivo del destino",
    "Réplica digital operativa (Fase 1): todos los activos georreferenciados de la plataforma sobre un único mapa en tiempo real, coloreados por estado y con refresco automático cada minuto.",
    '<button class="btn btn--pri" onclick="UI.goD(\'gd-3d\')">Vista 3D →</button>') +
    '<div class="grid g4" style="margin-bottom:16px" id="gd-kpis"></div>' +
    '<div class="card card--pad0" style="overflow:hidden"><div id="gemelo-2d" style="height:600px;width:100%"></div></div>' +
    '<div class="mini" style="color:var(--muted);margin-top:8px" id="gd-refresco"></div>';

  const capas = await cargarActivos();

  const total = capas.reduce((a, c) => a + c.items.length, 0);
  const enAlerta = capas.reduce((a, c) => a + c.items.filter((x) => x.sem !== "ok").length, 0);
  document.getElementById("gd-kpis").innerHTML =
    kpi("Activos en el gemelo", total, capas.filter((c) => c.items.length).length + " capas con datos", "ic-navy", "map") +
    kpi("Operativos", total - enAlerta, "Estado nominal", "ic-ok", "bolt") +
    kpi("Con incidencia", enAlerta, "Alerta o sin comunicación", "ic-coral", "warn") +
    kpi("Refresco", "60 s", "Telemetría de la plataforma en vivo", "ic-teal", "clock");

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
    mapa2d = L.map(cont).setView(CENTRO, 11);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: "&copy; OpenStreetMap" }).addTo(mapa2d);

    const grupos = {};
    const puntos = [];
    capas.forEach((capa) => {
      const g = L.layerGroup();
      capa.items.forEach((a) => {
        puntos.push(a.ll);
        L.circleMarker(a.ll, {
          radius: 8, weight: 2.5, color: "#fff",
          fillColor: a.sem === "ok" ? capa.color : COLOR_ESTADO[a.sem], fillOpacity: 1,
        }).bindPopup(popupActivo(capa, a)).addTo(g);
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

  let gl, capas;
  try {
    [gl, capas] = await Promise.all([maplibre(), cargarActivos()]);
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
        capas.forEach((capa) => {
          capa.items.forEach((a) => {
            const dot = document.createElement("div");
            dot.style.cssText = "width:14px;height:14px;border-radius:50%;border:2.5px solid #fff;box-shadow:0 1px 6px rgba(0,0,0,.5);background:" +
              (a.sem === "ok" ? capa.color : COLOR_ESTADO[a.sem]);
            const popup = new gl.Popup({ offset: 12 }).setHTML(popupActivo(capa, a));
            new gl.Marker({ element: dot }).setLngLat([a.ll[1], a.ll[0]]).setPopup(popup).addTo(mapa3d);
          });
        });
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
