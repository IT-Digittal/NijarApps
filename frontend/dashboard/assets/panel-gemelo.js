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
  if (s.startsWith("operat") || s === "online" || s === "ok" || s === "activo" || s === "activa" ||
      s === "verde" || s === "sin_bandera") return "ok";
  if (s.includes("sin_comunicacion") || s.includes("error") || s.includes("fallo") || s === "offline" ||
      s.includes("averia") || s === "roja") return "err";
  return "warn"; /* incluye bandera amarilla */
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
    /* Vertical externa (Fase 4): plataforma IoT municipal vía ThingsBoard.
       Si el backend responde 503 (sin configurar), la capa simplemente no aparece. */
    banderas: ["/gemelo/playas/banderas", "#0E9BD8", "Banderas de playa (IoT municipal)",
      (d) => (d.banderas || []).map((b) => ({ nombre: b.nombre, estado: b.estado,
        extra: "bandera: " + String(b.estado).replace(/_/g, " "), obj: b }))],
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
    "Réplica digital operativa: los activos georreferenciados de la plataforma y de la vertical IoT municipal (banderas de playa y aforo del parque, vía ThingsBoard) sobre un único mapa en tiempo real, con refresco automático cada minuto.",
    '<button class="btn btn--pri" onclick="UI.goD(\'gd-3d\')">Vista 3D →</button>') +
    '<div class="grid g4" style="margin-bottom:16px" id="gd-kpis"></div>' +
    '<div class="card card--pad0" style="overflow:hidden"><div id="gemelo-2d" style="height:600px;width:100%"></div></div>' +
    '<div class="mini" style="color:var(--muted);margin-top:8px" id="gd-refresco"></div>';

  const [capas, aforo] = await Promise.all([
    cargarActivos(),
    api.get("/gemelo/parque/aforo").catch(() => null), /* 503 si la vertical no está configurada */
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
              properties: { color: a.sem === "ok" ? capa.color : COLOR_ESTADO[a.sem], html: popupActivo(capa, a) },
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

/* ================= SIMULADOR DE ESCENARIOS (Fase 3) ================= */

const ESCENARIOS = [
  {
    id: "cierre_monsul",
    n: "Cierre de acceso rodado a Mónsul",
    d: "Restricción del acceso en coche a la playa de Mónsul. Parte de los visitantes se desvía a Genoveses y otras calas; el resto desiste.",
    param: "Nivel de restricción",
    supuesto: "Supuestos: Mónsul concentra ~25% de las visitas de costa; el 60% de los desviados se redistribuye dentro del destino.",
    aplicar(base, p) {
      const f = 1 - 0.25 * (p / 100) * 0.4;
      return { serie: base.map((v) => Math.round(v * f)), nota: "Visitas redistribuidas a otras calas: " + Math.round(base.reduce((a, b) => a + b, 0) * 0.25 * (p / 100) * 0.6) };
    },
  },
  {
    id: "lanzadera",
    n: "Lanzadera San José – Genoveses",
    d: "Servicio de autobús lanzadera en temporada. Aumenta la capacidad de acogida los fines de semana y reduce la presión del parking.",
    param: "Frecuencia del servicio",
    supuesto: "Supuestos: la lanzadera eleva la afluencia de fin de semana hasta un +12% y elimina el cuello de botella del aparcamiento.",
    aplicar(base, p) {
      const serie = base.map((v, i) => Math.round(v * (i % 7 >= 5 ? 1 + 0.12 * (p / 100) : 1)));
      return { serie, nota: "Plazas de parking liberadas estimadas por día punta: " + Math.round(140 * (p / 100)) };
    },
  },
  {
    id: "evento",
    n: "Gran evento en Rodalquilar",
    d: "Festival o evento cultural puntual. Añade visitantes concentrados en torno al día del evento.",
    param: "Asistentes esperados",
    supuesto: "Supuestos: el evento se celebra a mitad del horizonte; el 30% de asistentes llega la víspera o se queda al día siguiente.",
    aplicar(base, p) {
      const serie = base.slice();
      const d = Math.floor(serie.length / 2);
      const asistentes = p * 30;
      serie[d] = Math.round(serie[d] + asistentes * 0.7);
      if (serie[d - 1] != null) serie[d - 1] = Math.round(serie[d - 1] + asistentes * 0.15);
      if (serie[d + 1] != null) serie[d + 1] = Math.round(serie[d + 1] + asistentes * 0.15);
      return { serie, nota: "Pico del evento: día " + (d + 1) + " del horizonte (+" + Math.round(asistentes * 0.7) + " visitas)" };
    },
  },
  {
    id: "ola_calor",
    n: "Ola de calor",
    d: "Episodio de temperaturas extremas. Sube la demanda de playas y baja la de senderismo; crece el riesgo de saturación.",
    param: "Intensidad del episodio",
    supuesto: "Supuestos: cada 10 puntos de intensidad elevan ~2,4% la afluencia de costa (histórico de veranos previos, pendiente de calibrar).",
    aplicar(base, p) {
      return { serie: base.map((v) => Math.round(v * (1 + 0.24 * (p / 100)))), nota: "Vigilar aforos de Genoveses y Mónsul en los días pico" };
    },
  },
];

async function renderSimulador(el) {
  el.innerHTML = sub("Simulador", "Simulador de escenarios «qué pasaría si»",
    "Fase 3 del gemelo: simula decisiones de gestión sobre la predicción real de afluencia de la plataforma y compara el resultado con la línea base.", "") +
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
    "Simula decisiones de gestión sobre la predicción real de afluencia (línea discontinua: base; línea sólida: escenario).", "") +
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
