/**
 * Mapa GIS real del panel DTI (sustituye al SVG ficticio del demo).
 *
 * Leaflet + OpenStreetMap con las coordenadas reales de la base de datos:
 * recursos turísticos publicados (por categoría) y sensores IoT. Capas
 * conmutables y ficha al pulsar cada elemento.
 */

import { api } from "./api-client.js?v=17";

const CENTRO_NIJAR = [36.85, -2.13];
const COLOR_CATEGORIA = {
  playa: "#1F6FE5", ruta: "#12A150", monumento: "#7C6BF0", mirador: "#F0B429",
  centro_visitantes: "#17BEBB", parque_natural: "#2D8F4F", museo: "#E58A40",
  yacimiento: "#A66B2E", punto_interes: "#67769A", oficina_turismo: "#003B7A",
};

function cargarLeaflet() {
  return new Promise((resolve, reject) => {
    if (window.L) return resolve(window.L);
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    document.head.appendChild(css);
    const js = document.createElement("script");
    js.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    js.onload = () => resolve(window.L);
    js.onerror = () => reject(new Error("No se pudo cargar Leaflet"));
    document.head.appendChild(js);
  });
}

function coordsDe(obj) {
  const u = obj && obj.ubicacion;
  if (!u || !u.coordinates || u.coordinates.length < 2) return null;
  return [u.coordinates[1], u.coordinates[0]]; /* GeoJSON es [lon, lat] */
}

async function renderMapaReal(el) {
  el.innerHTML =
    '<div class="subhead"><div><div class="crumb"><a onclick="UI.go(\'home\')">Plataforma</a> · <a onclick="UI.goD(\'resumen\')">DTI Turismo</a> · <b>Mapa GIS</b></div>' +
    "<h1>Mapa GIS del destino</h1><p>Capa geográfica real de la plataforma: recursos turísticos publicados y sensores IoT georreferenciados desde la base de datos (WGS84).</p></div></div>" +
    '<div class="card card--pad0" style="overflow:hidden"><div id="mapa-real" style="height:560px;width:100%"></div></div>';

  let L, recursos = [], sensores = [];
  try {
    const [leaflet, res, sens] = await Promise.all([
      cargarLeaflet(),
      api.get("/tourism/resources?page=1&page_size=200&publicado=true").catch(() => null),
      api.get("/data/iot/sensors?page=1&page_size=100").catch(() => null),
    ]);
    L = leaflet;
    recursos = (res && res.items) || [];
    sensores = (sens && sens.items) || [];
  } catch (e) {
    el.querySelector("#mapa-real").innerHTML =
      '<div class="mini" style="color:var(--err);padding:40px;text-align:center">No se pudo inicializar el mapa: ' + (e.message || e) + "</div>";
    return;
  }

  /* El contenedor se muestra justo después del render: esperar un tick
     para que Leaflet calcule bien el tamaño. */
  setTimeout(() => {
    const cont = document.getElementById("mapa-real");
    if (!cont || cont.dataset.iniciado) return;
    cont.dataset.iniciado = "1";

    const mapa = L.map(cont).setView(CENTRO_NIJAR, 11);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap",
    }).addTo(mapa);

    const capaRecursos = L.layerGroup();
    const puntos = [];
    recursos.forEach((r) => {
      const c = coordsDe(r);
      if (!c) return;
      puntos.push(c);
      L.circleMarker(c, {
        radius: 8, weight: 2, color: "#fff",
        fillColor: COLOR_CATEGORIA[r.categoria] || "#67769A", fillOpacity: 0.95,
      }).bindPopup(
        "<b>" + r.nombre + "</b><br><span style='color:#67769A'>" + r.categoria.replace(/_/g, " ") +
        (r.direccion ? " · " + r.direccion : "") + "</span>" +
        (r.descripcion_corta ? "<br>" + r.descripcion_corta : ""),
      ).addTo(capaRecursos);
    });

    const capaSensores = L.layerGroup();
    sensores.forEach((s) => {
      const c = coordsDe(s);
      if (!c) return;
      puntos.push(c);
      L.marker(c, {
        icon: L.divIcon({
          className: "",
          html: '<div style="width:14px;height:14px;border-radius:4px;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.35);background:' +
            ((s.estado || "").startsWith("operat") ? "#12A150" : "#E5484D") + '"></div>',
          iconSize: [14, 14],
        }),
      }).bindPopup(
        "<b>" + s.nombre + "</b><br><span style='color:#67769A'>" + s.tipo +
        " · " + (s.estado || "desconocido") + (s.descripcion_ubicacion ? "<br>" + s.descripcion_ubicacion : "") + "</span>",
      ).addTo(capaSensores);
    });

    capaRecursos.addTo(mapa);
    capaSensores.addTo(mapa);
    const capas = {};
    capas["Recursos turísticos (" + capaRecursos.getLayers().length + ")"] = capaRecursos;
    capas["Sensores IoT (" + capaSensores.getLayers().length + ")"] = capaSensores;
    L.control.layers(null, capas, { collapsed: false }).addTo(mapa);

    if (puntos.length) mapa.fitBounds(L.latLngBounds(puntos).pad(0.15));
    setTimeout(() => mapa.invalidateSize(), 150);
  }, 60);
}

/* Sustituir el renderer del demo cuando el panel esté inicializado */
(function init() {
  const DTI = window.__DTI;
  if (!DTI || !DTI.DR) return setTimeout(init, 300);
  DTI.DR.mapa = renderMapaReal;
  if (window.UI && window.UI.rerenderD) window.UI.rerenderD("mapa");
})();
