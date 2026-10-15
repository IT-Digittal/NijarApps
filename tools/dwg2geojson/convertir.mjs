#!/usr/bin/env node
/**
 * DWG del Inventario Municipal de Bienes (Urbana) → GeoJSON para el gemelo 2D.
 *
 * Lee los DWG con LibreDWG (WebAssembly) y, de cada uno, genera un GeoJSON con
 * los bienes del inventario agrupados por categoría de la leyenda del plano.
 * Las coordenadas se dejan tal cual vienen (UTM en metros); la conversión a
 * WGS84 la hace PostGIS al importar (`nijar_dti.data.importar_inventario`).
 *
 * Reglas (deducidas de los planos «Inventario Municipal de Bienes · Urbana»):
 *  - Cada capa del DWG se asigna a una categoría por su nombre
 *    (Invent-borde-EQ → equipamiento, invent-viales-trama → red viaria…).
 *  - Los contornos cerrados (`*-borde`, LWPOLYLINE/POLYLINE) son los bienes
 *    individuales. Los sombreados (`*-trama`, HATCH) completan lo que no tenga
 *    contorno; un sombreado que repite un contorno ya leído se descarta.
 *  - Los anillos de un sombreado contenidos en otro son huecos (p. ej. las
 *    manzanas dentro del sombreado de la red viaria).
 *  - Los textos de `invent-tex` con forma de código (U-PB-1, V-VI-7, DS-VI-1)
 *    se asignan a los polígonos que los contienen; el resto de textos de esa
 *    capa («IGLESIA», «Puesta a disposición 44,67m²») se guardan como notas.
 *  - Se descarta el espacio papel (cajetín, leyenda, ventanas): todo lo que
 *    no tenga coordenadas UTM plausibles.
 *  - El núcleo se toma del cajetín («Núcleo: El Viso») o del nombre del fichero.
 *
 * Uso:
 *   node convertir.mjs <dwg o carpeta con DWG> <carpeta de salida>
 */

import fs from "fs";
import path from "path";

/* --------------------------------------------------------- categorías ---- */

export const CATEGORIAS = {
  equipamiento: "Equipamientos",
  edificio: "Edificios",
  residencial: "Residencial patrimonial",
  patrimonio_suelo: "Patrimonio público del suelo",
  espacio_libre: "Espacio libre público",
  peatonal_ajardinado: "Peatonal ajardinado",
  red_viaria: "Red viaria",
  aparcamiento: "Aparcamientos",
  infraestructura: "Infraestructuras",
  via_ferrea: "Vía férrea",
  via_pecuaria: "Vía pecuaria",
  parcela: "Parcelas",
};

/** Texto en minúsculas, sin tildes y con separadores normalizados. */
export function normalizar(t) {
  return String(t || "")
    .normalize("NFD").replace(/[̀-ͯ]/g, "")
    .toLowerCase().replace(/[\s_]+/g, "-");
}

/** Categoría del inventario a partir del nombre de la capa del DWG (o null). */
export function categoriaDeCapa(capa) {
  const c = normalizar(capa);
  if (!/invent|edificio|instalac|parcela|ferrea|pecuaria/.test(c)) return null;
  if (/-tex/.test(c)) return null;
  if (/ferrea/.test(c)) return "via_ferrea";
  if (/pecuaria/.test(c)) return "via_pecuaria";
  if (/elp-pa|borde-pa\b|trama-pa\b|-pa$/.test(c)) return "peatonal_ajardinado";
  if (/elp/.test(c)) return "espacio_libre";
  if (/aparc/.test(c)) return "aparcamiento";
  if (/viales/.test(c)) return "red_viaria";
  if (/pps/.test(c)) return "patrimonio_suelo";
  if (/resid/.test(c)) return "residencial";
  if (/edificio/.test(c)) return "edificio";
  if (/instalac|infraest/.test(c)) return "infraestructura";
  if (/-eq/.test(c)) return "equipamiento";
  if (/parcela/.test(c)) return "parcela";
  return null;
}

const RE_CODIGO = /^[A-Z]{1,4}-[A-Z]{1,4}-\d+[A-Z]?$/;

/** Quita el formato MTEXT ({\H1.5x;U-PB-2}, {\fArial|b0;IGLESIA}, \P…). */
export function limpiarMtext(t) {
  return String(t || "")
    .replace(/\\P/g, " ")
    .replace(/\\[A-Za-z][^;\\{}]*;/g, "")
    .replace(/[{}]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

const MINUSCULAS = new Set(["de", "del", "la", "las", "los", "el", "y"]);

/** «TORRE DEL CAMPO-INDUSTRIAL GRANATILLA » → «Torre del Campo-Industrial Granatilla». */
export function nombreBonito(t) {
  const limpio = String(t || "").replace(/\s+/g, " ").trim();
  if (limpio !== limpio.toUpperCase()) return limpio;
  let primera = true;
  return limpio.toLowerCase().replace(/[^\s-]+/g, (w) => {
    const r = !primera && MINUSCULAS.has(w) ? w : w.charAt(0).toUpperCase() + w.slice(1);
    primera = false;
    return r;
  });
}

/** Núcleo a partir de los textos «Núcleo: …» del cajetín y del nombre del fichero. */
export function nombreNucleo(textosCajetin, nombreFichero) {
  const base = path.basename(nombreFichero)
    .replace(/\.dwg$/i, "").replace(/^[0-9a-f]{8}-/, "").replace(/[_\s]*\d{4}\s*$/, "").trim();
  const fichero = normalizar(base);
  const palabras = (t) => normalizar(t).split(/[^a-z0-9]+/).filter((w) => w.length > 2 && !MINUSCULAS.has(w));
  const candidatos = [...new Set(textosCajetin.map((t) => t.replace(/^n[uú]cleo\s*:\s*/i, "").trim()).filter(Boolean))];
  const coincide = candidatos.find((c) => palabras(c).length && palabras(c).every((w) => fichero.includes(w)));
  if (coincide) return nombreBonito(coincide);
  // «JABONERO EL» → «El Jabonero» (los ficheros ponen el artículo al final)
  const m = base.match(/^(.*\S)\s+(el|la|los|las)$/i);
  return nombreBonito(m ? `${m[2]} ${m[1]}` : base);
}

/* ------------------------------------------------------------ geometría ---- */

const plausible = (p) => p && p.x > 100000 && p.x < 900000 && p.y > 3000000 && p.y < 5000000;

export function area(anillo) {
  let a = 0;
  for (let i = 0, j = anillo.length - 1; i < anillo.length; j = i++) {
    a += (anillo[j][0] + anillo[i][0]) * (anillo[j][1] - anillo[i][1]);
  }
  return Math.abs(a / 2);
}

export function puntoEnAnillo([x, y], anillo) {
  let dentro = false;
  for (let i = 0, j = anillo.length - 1; i < anillo.length; j = i++) {
    const [xi, yi] = anillo[i];
    const [xj, yj] = anillo[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) dentro = !dentro;
  }
  return dentro;
}

/** Un punto dentro del anillo: su centroide o, si cae fuera (forma en L), el
 *  punto medio de una diagonal interior entre vértices. */
export function puntoInterior(anillo) {
  const c = centroide(anillo);
  if (puntoEnAnillo(c, anillo)) return c;
  for (let i = 0; i < anillo.length; i++) {
    for (let j = i + 2; j < anillo.length; j++) {
      const m = [(anillo[i][0] + anillo[j][0]) / 2, (anillo[i][1] + anillo[j][1]) / 2];
      if (puntoEnAnillo(m, anillo)) return m;
    }
  }
  return anillo[0];
}

function centroide(anillo) {
  let sx = 0, sy = 0;
  for (const [x, y] of anillo) { sx += x; sy += y; }
  return [sx / anillo.length, sy / anillo.length];
}

/** Punto en el polígono (con huecos). */
export function puntoEnPoligono(p, poligono) {
  if (!puntoEnAnillo(p, poligono[0])) return false;
  return !poligono.slice(1).some((hueco) => puntoEnAnillo(p, hueco));
}

function cerrar(anillo) {
  const a = anillo.filter((p, i) => i === 0 || p[0] !== anillo[i - 1][0] || p[1] !== anillo[i - 1][1]);
  if (a.length && (a[0][0] !== a[a.length - 1][0] || a[0][1] !== a[a.length - 1][1])) a.push([...a[0]]);
  return a;
}

const red = (v) => Math.round(v * 1000) / 1000; /* milímetros */

function arcoAPuntos(e, n = 12) {
  let a0 = e.startAngle, a1 = e.endAngle;
  const signo = e.isCCW ? 1 : -1;
  if (e.isCCW && a1 < a0) a1 += 2 * Math.PI;
  if (!e.isCCW && a0 < a1) a0 += 2 * Math.PI;
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const a = a0 + ((a1 - a0) * i) / n;
    pts.push([e.center.x + e.radius * Math.cos(signo * a), e.center.y + e.radius * Math.sin(signo * a)]);
  }
  return pts;
}

/** Anillos de un HATCH (aristas línea/arco o polilínea). */
export function anillosDeHatch(h) {
  const anillos = [];
  for (const p of h.boundaryPaths || []) {
    let pts = [];
    if (p.vertices && p.vertices.length) {
      pts = p.vertices.map((v) => [v.x, v.y]);
    } else {
      for (const e of p.edges || []) {
        if (e.type === 1 && e.start) pts.push([e.start.x, e.start.y]);
        else if (e.type === 2 && e.center) pts.push(...arcoAPuntos(e).slice(0, -1));
        else if (e.start) pts.push([e.start.x, e.start.y]);
      }
    }
    if (pts.length >= 3 && plausible({ x: pts[0][0], y: pts[0][1] })) {
      anillos.push(cerrar(pts.map(([x, y]) => [red(x), red(y)])));
    }
  }
  return anillos;
}

/** Agrupa anillos en polígonos: un anillo contenido en otro es su hueco. */
export function poligonosDeAnillos(anillos) {
  const orden = [...anillos].sort((a, b) => area(b) - area(a));
  const poligonos = [];
  for (const anillo of orden) {
    // Centro del anillo (no un vértice: los huecos suelen tocar el borde exterior)
    const c = puntoInterior(anillo);
    // El polígono más pequeño (ya visto) cuyo exterior contiene el anillo y que
    // no lo tenga dentro de uno de sus huecos: el anillo es un hueco suyo.
    // Una isla dentro de un hueco queda como polígono propio.
    const candidatos = poligonos.filter((pol) => puntoEnAnillo(c, pol[0]));
    const padre = candidatos[candidatos.length - 1];
    if (padre && !padre.slice(1).some((h) => puntoEnAnillo(c, h))) padre.push(anillo);
    else poligonos.push([anillo]);
  }
  return poligonos;
}

function verticesDePolilinea(e) {
  return (e.vertices || []).map((v) => [red(v.x), red(v.y)]);
}

function polilineaCerrada(e) {
  if (e.type === "LWPOLYLINE") return (e.flag & 512) !== 0 || (e.flag & 1) !== 0;
  return (e.flag & 1) !== 0;
}

/* -------------------------------------------------------------- lectura ---- */

/**
 * Convierte el «DwgDatabase» de libredwg-web en un FeatureCollection.
 * Exportada para los tests (no depende del WASM).
 */
export function convertirDatabase(db, nombreFichero) {
  const ents = db.entities || [];
  const textos = (e) => limpiarMtext(e.text ?? e.contents ?? "");

  // Núcleo: el del cajetín si coincide con el nombre del fichero (trae tildes
  // y artículo: «Los Grillos»); si no, el nombre del fichero (hay cajetines
  // heredados de otro plano, p. ej. «El Rodón» en el DWG de Campohermoso).
  const nucleo = nombreNucleo(ents.map(textos).filter((t) => /^n[uú]cleo\s*:/i.test(t)), nombreFichero);

  // 1) Contornos (bienes individuales) y sombreados por categoría
  const contornos = []; // {categoria, capa, anillo}
  const lineas = [];
  const sombreados = []; // {categoria, capa, poligono}
  const descartes = { abiertas: 0, fuera_de_coordenadas: 0 };
  for (const e of ents) {
    const cat = categoriaDeCapa(e.layer);
    if (!cat) continue;
    if (e.type === "HATCH") {
      for (const pol of poligonosDeAnillos(anillosDeHatch(e))) sombreados.push({ categoria: cat, capa: e.layer, poligono: pol });
    } else if (["LWPOLYLINE", "POLYLINE2D", "POLYLINE3D"].includes(e.type)) {
      const v = verticesDePolilinea(e);
      if (v.length < 2 || !plausible({ x: v[0][0], y: v[0][1] })) { descartes.fuera_de_coordenadas++; continue; }
      if (polilineaCerrada(e) && v.length >= 3) contornos.push({ categoria: cat, capa: e.layer, anillo: cerrar(v) });
      else if (cat === "via_pecuaria" || cat === "via_ferrea") lineas.push({ categoria: cat, capa: e.layer, linea: v });
      else descartes.abiertas++;
    }
  }

  // 2) Polígonos finales: contornos + sombreados que no repiten un contorno.
  //    Un sombreado «repite» un contorno de su categoría si su exterior tiene
  //    casi la misma superficie (±20 %) y su centro cae dentro. Si el sombreado
  //    tiene huecos (p. ej. la red viaria con las manzanas recortadas), es más
  //    fiel que el contorno exterior y lo sustituye.
  const poligonos = contornos.map((c) => ({ ...c, poligono: [c.anillo], origen: "contorno" }));
  for (const s of sombreados) {
    const c = centroide(s.poligono[0]);
    const a = area(s.poligono[0]);
    const i = poligonos.findIndex((p) => p.categoria === s.categoria && p.origen === "contorno" &&
      puntoEnAnillo(c, p.poligono[0]) && Math.abs(area(p.poligono[0]) / a - 1) < 0.2);
    if (i < 0) poligonos.push({ ...s, origen: "sombreado" });
    else if (s.poligono.length > 1) poligonos[i] = { ...s, origen: "sombreado" };
  }
  //    Un contorno de red viaria que contiene bienes de otras categorías no es
  //    una calle sino la envolvente de varias manzanas (en el plano la calle
  //    real es el sombreado con huecos): se descarta.
  //    Un contorno que cae dentro de un hueco de un sombreado de su misma
  //    categoría es el borde de ese hueco (p. ej. las manzanas y zonas verdes
  //    dibujadas en «invent-viales-borde»), no un bien: se descarta.
  descartes.bordes_de_huecos = 0;
  for (let i = poligonos.length - 1; i >= 0; i--) {
    const p = poligonos[i];
    if (p.origen !== "contorno") continue;
    const pi = puntoInterior(p.poligono[0]);
    const enHueco = poligonos.some((q) => q.origen === "sombreado" && q.categoria === p.categoria &&
      q.poligono.slice(1).some((h) => puntoEnAnillo(pi, h)));
    if (enHueco) { poligonos.splice(i, 1); descartes.bordes_de_huecos++; }
  }
  descartes.envolventes_viarias = 0;
  for (let i = poligonos.length - 1; i >= 0; i--) {
    const p = poligonos[i];
    if (p.categoria !== "red_viaria" || p.origen !== "contorno") continue;
    const envuelve = poligonos.some((q) => q !== p && q.categoria !== "red_viaria" &&
      puntoEnAnillo(centroide(q.poligono[0]), p.poligono[0]) && area(q.poligono[0]) < area(p.poligono[0]));
    if (envuelve) { poligonos.splice(i, 1); descartes.envolventes_viarias++; }
  }

  // 3) Códigos y notas (invent-tex) → polígonos que los contienen
  const etiquetas = ents
    .filter((e) => /^invent-tex/i.test(normalizar(e.layer)) && (e.type === "MTEXT" || e.type === "TEXT"))
    .map((e) => ({ texto: textos(e), p: e.insertionPoint || e.startPoint || e.position }))
    .filter((t) => t.texto && plausible(t.p));
  for (const pol of poligonos) {
    pol.codigos = new Set();
    pol.notas = new Set();
  }
  let sinPoligono = 0;
  for (const t of etiquetas) {
    const pt = [t.p.x, t.p.y];
    const contienen = poligonos.filter((pol) => puntoEnPoligono(pt, pol.poligono));
    if (!contienen.length) { sinPoligono++; continue; }
    const esCodigo = RE_CODIGO.test(t.texto);
    for (const pol of contienen) (esCodigo ? pol.codigos : pol.notas).add(t.texto);
  }

  // 3 bis) Restos lejos del núcleo (copias, ventanas o planos de situación en el
  //        espacio modelo): fuera si están a más de 6 km de la mediana del fichero
  const centroDe = (x) => (x.poligono ? puntoInterior(x.poligono[0]) : x.linea[0]);
  const mediana = (v) => { const o = [...v].sort((a, b) => a - b); return o[Math.floor(o.length / 2)]; };
  const todos = [...poligonos, ...lineas];
  descartes.lejos_del_nucleo = 0;
  let centro = null;
  if (todos.length) {
    centro = [mediana(todos.map((x) => centroDe(x)[0])), mediana(todos.map((x) => centroDe(x)[1]))];
    const lejos = (x) => Math.hypot(centroDe(x)[0] - centro[0], centroDe(x)[1] - centro[1]) > 6000;
    for (const lista of [poligonos, lineas]) {
      for (let i = lista.length - 1; i >= 0; i--) {
        if (lejos(lista[i])) { lista.splice(i, 1); descartes.lejos_del_nucleo++; }
      }
    }
  }

  // 4) GeoJSON (coordenadas UTM tal cual)
  const features = [];
  for (const pol of poligonos) {
    const codigos = [...pol.codigos].sort((a, b) => a.localeCompare(b, "es", { numeric: true }));
    features.push({
      type: "Feature",
      geometry: { type: "Polygon", coordinates: pol.poligono },
      properties: {
        nucleo,
        categoria: pol.categoria,
        categoria_nombre: CATEGORIAS[pol.categoria],
        codigos,
        notas: [...pol.notas],
        superficie_m2: Math.round(area(pol.poligono[0]) - pol.poligono.slice(1).reduce((s, h) => s + area(h), 0)),
        capa_dwg: pol.capa,
        origen: pol.origen,
      },
    });
  }
  for (const l of lineas) {
    features.push({
      type: "Feature",
      geometry: { type: "LineString", coordinates: l.linea },
      properties: { nucleo, categoria: l.categoria, categoria_nombre: CATEGORIAS[l.categoria], codigos: [], notas: [], capa_dwg: l.capa, origen: "linea" },
    });
  }
  const resumen = {};
  for (const f of features) resumen[f.properties.categoria] = (resumen[f.properties.categoria] || 0) + 1;
  return {
    type: "FeatureCollection",
    nucleo,
    fichero: path.basename(nombreFichero),
    crs_origen: "UTM (m); por defecto EPSG:25830 (ETRS89 / UTM 30N)",
    centro_utm: centro && centro.map((v) => Math.round(v)),
    resumen: { por_categoria: resumen, etiquetas: etiquetas.length, etiquetas_fuera_de_poligonos: sinPoligono, ...descartes },
    features,
  };
}

async function main() {
  const [entrada, salida] = process.argv.slice(2);
  if (!entrada || !salida) {
    console.error("Uso: node convertir.mjs <dwg o carpeta> <carpeta de salida>");
    process.exit(2);
  }
  const { Dwg_File_Type, LibreDwg } = await import("@mlightcad/libredwg-web");
  const wasm = path.join(path.dirname(new URL(import.meta.url).pathname), "node_modules/@mlightcad/libredwg-web/wasm/");
  const lib = await LibreDwg.create(wasm);
  const ficheros = fs.statSync(entrada).isDirectory()
    ? fs.readdirSync(entrada, { recursive: true }).map(String).filter((f) => /\.dwg$/i.test(f)).map((f) => path.join(entrada, f))
    : [entrada];
  fs.mkdirSync(salida, { recursive: true });
  let errores = 0;
  for (const f of ficheros.sort()) {
    try {
      const raw = lib.dwg_read_data(fs.readFileSync(f), Dwg_File_Type.DWG);
      const db = lib.convert(raw);
      lib.dwg_free(raw);
      const fc = convertirDatabase(db, f);
      const destino = path.join(salida, normalizar(fc.nucleo) + ".geojson");
      fs.writeFileSync(destino, JSON.stringify(fc));
      console.log(`✔ ${path.basename(f)} → ${path.basename(destino)} · núcleo «${fc.nucleo}» · ${fc.features.length} elementos · ` +
        JSON.stringify(fc.resumen));
    } catch (e) {
      errores++;
      console.error(`✘ ${path.basename(f)}: ${e.message || e}`);
    }
  }
  if (!ficheros.length) console.error("No se han encontrado ficheros .dwg");
  process.exit(errores || !ficheros.length ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
