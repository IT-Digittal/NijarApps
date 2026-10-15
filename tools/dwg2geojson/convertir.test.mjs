// Tests del convertidor DWG → GeoJSON (sin WASM: se prueba sobre un «DwgDatabase»
// sintético con la misma forma que devuelve libredwg-web).
// Ejecutar: node --test tools/dwg2geojson/
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  anillosDeHatch,
  area,
  categoriaDeCapa,
  convertirDatabase,
  limpiarMtext,
  nombreNucleo,
  poligonosDeAnillos,
} from "./convertir.mjs";

const X = 577000, Y = 4085000; // UTM plausibles (Pueblo Blanco)
const rect = (x0, y0, x1, y1) => [[X + x0, Y + y0], [X + x1, Y + y0], [X + x1, Y + y1], [X + x0, Y + y1]];
const lw = (layer, pts, flag = 512) => ({ type: "LWPOLYLINE", layer, flag, vertices: pts.map(([x, y]) => ({ x, y, bulge: 0 })) });
const hatch = (layer, ...anillos) => ({
  type: "HATCH", layer,
  boundaryPaths: anillos.map((r) => ({
    boundaryPathTypeFlag: 1,
    edges: r.map((p, i) => ({ type: 1, start: { x: p[0], y: p[1] }, end: { x: r[(i + 1) % r.length][0], y: r[(i + 1) % r.length][1] } })),
  })),
});
const mtext = (layer, text, x, y) => ({ type: "MTEXT", layer, text, insertionPoint: { x: X + x, y: Y + y, z: 0 } });

test("categoría por nombre de capa", () => {
  assert.equal(categoriaDeCapa("Invent-borde-EQ"), "equipamiento");
  assert.equal(categoriaDeCapa("Invent-Trama-EQPTO"), "equipamiento");
  assert.equal(categoriaDeCapa("Invent-Trama-ELP-PA"), "peatonal_ajardinado");
  assert.equal(categoriaDeCapa("invent-borde-PA"), "peatonal_ajardinado");
  assert.equal(categoriaDeCapa("Invent-borde-ELP"), "espacio_libre");
  assert.equal(categoriaDeCapa("invent-viales-trama"), "red_viaria");
  assert.equal(categoriaDeCapa("invent-trama PPS"), "patrimonio_suelo");
  assert.equal(categoriaDeCapa("invent Trama- Residencial"), "residencial");
  assert.equal(categoriaDeCapa("edificio borde"), "edificio");
  assert.equal(categoriaDeCapa("invent-vía ferrea borde"), "via_ferrea");
  assert.equal(categoriaDeCapa("invent-via pecuaria-borde"), "via_pecuaria");
  assert.equal(categoriaDeCapa("Instalac-trama"), "infraestructura");
  assert.equal(categoriaDeCapa("invent-tex"), null);
  assert.equal(categoriaDeCapa("Base Cartografica"), null);
  assert.equal(categoriaDeCapa("Cajetín"), null);
});

test("limpia el formato MTEXT", () => {
  assert.equal(limpiarMtext("{\\H1.5x;U-PB-2}"), "U-PB-2");
  assert.equal(limpiarMtext("{\\fArial|b1|i0|c0|p34;V-VI-4}"), "V-VI-4");
  assert.equal(limpiarMtext("Puesta a\\Pdisposición"), "Puesta a disposición");
});

test("sombreado con arco y huecos", () => {
  const h = {
    type: "HATCH", layer: "x", boundaryPaths: [{
      boundaryPathTypeFlag: 1,
      edges: [
        { type: 1, start: { x: X, y: Y } },
        { type: 2, center: { x: X + 10, y: Y }, radius: 10, startAngle: Math.PI, endAngle: 2 * Math.PI, isCCW: 1 },
        { type: 1, start: { x: X + 20, y: Y + 20 } },
      ],
    }],
  };
  const [anillo] = anillosDeHatch(h);
  assert.ok(anillo.length > 6, "el arco se discretiza");
  const pol = poligonosDeAnillos([rect(0, 0, 100, 100), rect(10, 10, 20, 20), rect(40, 40, 50, 50), rect(42, 42, 48, 48)]);
  assert.equal(pol.length, 2, "una isla dentro de un hueco es polígono propio");
  assert.equal(pol[0].length, 3, "exterior con dos huecos");
  assert.equal(area(rect(0, 0, 10, 10)), 100);
});

test("convierte un DWG sintético con las reglas del inventario", () => {
  const db = {
    entities: [
      { type: "TEXT", layer: "Cajetín", text: "Núcleo: Pueblo Blanco", startPoint: { x: 5, y: 5 } },
      // espacio papel (leyenda): fuera de coordenadas UTM → se ignora
      hatch("Invent-Trama-EQPTO", [[0, 0], [10, 0], [10, 10], [0, 10]]),
      // equipamiento: contorno + sombreado duplicado → uno solo
      lw("Invent-borde-EQ", rect(0, 0, 50, 40)),
      hatch("Invent-Trama-EQPTO", rect(0.2, 0.2, 49.8, 39.8)),
      // edificio dentro del equipamiento
      lw("edificio borde", rect(10, 10, 20, 20)),
      // red viaria: sombreado con hueco (manzana) + contorno del hueco + envolvente
      hatch("invent-viales-trama", rect(70, -100, 300, 300), rect(100, 100, 200, 200)),
      lw("invent-viales-borde", rect(100, 100, 200, 200)),
      lw("invent-viales-borde", rect(-5, -5, 60, 50)),
      // calle abierta (no se carga) y vía pecuaria (línea)
      lw("invent-viales-borde", rect(400, 400, 410, 410), 0),
      lw("invent-via pecuaria-borde", [[X - 300, Y], [X + 600, Y]], 4),
      // códigos y notas
      mtext("invent-tex", "{\\H1.5x;U-PB-3}", 15, 15),
      mtext("invent-tex", "V-PB-5", 250, 250),
      mtext("invent-tex", "SEGÚN IRYDA", 30, 30),
    ],
  };
  const fc = convertirDatabase(db, "/x/PUEBLOBLANCO_2025.dwg");
  assert.equal(fc.nucleo, "Pueblo Blanco");
  const por = (cat) => fc.features.filter((f) => f.properties.categoria === cat);
  assert.equal(por("equipamiento").length, 1);
  assert.equal(por("edificio").length, 1);
  const viaria = por("red_viaria");
  assert.equal(viaria.length, 1, "sin el borde del hueco ni la envolvente");
  assert.equal(viaria[0].geometry.coordinates.length, 2, "con la manzana como hueco");
  assert.deepEqual(viaria[0].properties.codigos, ["V-PB-5"]);
  assert.deepEqual(por("equipamiento")[0].properties.codigos, ["U-PB-3"]);
  assert.deepEqual(por("edificio")[0].properties.codigos, ["U-PB-3"]);
  assert.deepEqual(por("equipamiento")[0].properties.notas, ["SEGÚN IRYDA"]);
  assert.equal(por("via_pecuaria")[0].geometry.type, "LineString");
  assert.equal(fc.resumen.abiertas, 1);
  assert.equal(fc.resumen.bordes_de_huecos, 1);
  assert.equal(fc.resumen.envolventes_viarias, 1);
});

test("sin cajetín, el núcleo sale del nombre del fichero", () => {
  const fc = convertirDatabase({ entities: [lw("Invent-borde-EQ", rect(0, 0, 5, 5))] }, "0149f6c7-VISO_2025.dwg");
  assert.equal(fc.nucleo, "Viso");
});

test("nombre del núcleo: cajetín solo si coincide con el fichero", () => {
  assert.equal(nombreNucleo(["Núcleo: El Rodón"], "CAMPOHERMOSO-INDUSTRIAL STA OLALLA 2025.dwg"),
    "Campohermoso-Industrial Sta Olalla");
  assert.equal(nombreNucleo(["Núcleo: TORRE DEL CAMPO-INDUSTRIAL GRANATILLA "], "TORRE DEL CAMPO-INDUSTRIAL GRANATILLA 2025.dwg"),
    "Torre del Campo-Industrial Granatilla");
  assert.equal(nombreNucleo(["Núcleo: Los Grillos"], "GRILLOS LOS 2025.dwg"), "Los Grillos");
  assert.equal(nombreNucleo(["Núcleo: Fernán Pérez"], "FERNAN PEREZ 2025.dwg"), "Fernán Pérez");
  assert.equal(nombreNucleo([], "JABONERO EL  2025.dwg"), "El Jabonero");
});

test("descarta restos a más de 6 km del núcleo", () => {
  const db = { entities: [
    lw("Invent-borde-EQ", rect(0, 0, 10, 10)),
    lw("Invent-borde-EQ", rect(20, 0, 30, 10)),
    lw("Invent-borde-EQ", rect(9000, 9000, 9010, 9010)),
  ] };
  const fc = convertirDatabase(db, "x.dwg");
  assert.equal(fc.features.length, 2);
  assert.equal(fc.resumen.lejos_del_nucleo, 1);
});
