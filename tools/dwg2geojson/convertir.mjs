#!/usr/bin/env node
/**
 * DWG del Inventario Municipal de Bienes (Urbana) → GeoJSON para el gemelo 2D.
 *
 * Lee los DWG con LibreDWG (WebAssembly) y, de cada uno, genera un GeoJSON con
 * los bienes del inventario agrupados por categoría de la leyenda del plano.
 * Las coordenadas se dejan tal cual vienen (UTM en metros); la conversión a
 * WGS84 la hace PostGIS al importar (`nijar_dti.data.importar_inventario`).
 *
 * La lógica está en `frontend/dashboard/assets/dwg2geojson.mjs`, compartida con
 * el importador del panel (Capas del gemelo), que hace lo mismo en el navegador.
 *
 * Uso:
 *   node convertir.mjs <dwg o carpeta con DWG> <carpeta de salida>
 */

import fs from "fs";
import path from "path";
import { convertirDatabase, normalizar } from "../../frontend/dashboard/assets/dwg2geojson.mjs";

export * from "../../frontend/dashboard/assets/dwg2geojson.mjs";

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
