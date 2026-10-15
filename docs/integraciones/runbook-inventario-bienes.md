# Runbook · Inventario Municipal de Bienes (DWG) en el Gemelo vivo 2D

| | |
|---|---|
| **Objeto** | Cargar los planos del Inventario Municipal de Bienes · Urbana (actualización 2025) como capas reales del gemelo |
| **Entrada** | Un `.zip` con un **DWG por núcleo** (AutoCAD Map 3D, coordenadas UTM). Los PDF no se usan: son la impresión del plano, sin coordenadas |
| **Componentes** | `tools/dwg2geojson/convertir.mjs` (LibreDWG/WASM), `nijar_dti.data.importar_inventario`, `scripts/importar_inventario.sh` |
| **Resultado** | Grupo «Inventario de bienes» en el control de capas del Gemelo vivo 2D: una capa por categoría |

## 1. Carga (en el servidor)

```bash
cd ~/NijarApps
scripts/importar_inventario.sh ~/inventario.zip --dry-run   # comprobar sin guardar
scripts/importar_inventario.sh ~/inventario.zip             # guardar
```

El script descomprime los `.dwg`, los convierte a GeoJSON en un contenedor
`node:20-slim` desechable (no hay que instalar nada) e importa el resultado en
`nijar-dti-api`. Por cada DWG muestra el núcleo y los elementos por categoría.
Reimportar un núcleo **sustituye solo ese núcleo**.

Las líneas «Open dwg file with error code: …» son avisos de lectura de LibreDWG
(no fatales) y pueden ignorarse.

## 2. Sistema de coordenadas

Los DWG no indican su sistema de referencia. Por la cartografía base que usan
(Junta de Andalucía) se asume **ETRS89 / UTM 30N (EPSG:25830)**. El importador
muestra el centro de lo cargado; además, en el gemelo los polígonos deben
encajar con la ortofoto PNOA. Si aparecieran desplazados ~200 m hacia el
noreste, los planos estarían en ED50: reimportar con `--srid 23030`.

## 3. Cómo se interpreta cada DWG

| Capas del DWG | Categoría (capa del gemelo) |
|---|---|
| `Invent-borde-EQ`, `Invent-Trama-EQPTO` | Equipamientos |
| `edificio borde/trama` | Edificios |
| `Invent-borde-RESID`, `* Residencial` | Residencial patrimonial |
| `invent-borde/trama PPS` | Patrimonio público del suelo |
| `Invent-borde-ELP`, `Invent-Trama-ELP` | Espacio libre público |
| `invent-borde-PA`, `Invent-Trama-ELP-PA` | Peatonal ajardinado |
| `invent-viales-*` | Red viaria |
| `invent-trama-aparc` | Aparcamientos |
| `Instalac-*`, `invent-trama Infraest` | Infraestructuras |
| `invent-vía férrea *` | Vía férrea |
| `invent-via pecuaria-borde` | Vía pecuaria (línea) |
| `PARCELA` | Parcelas |
| `invent-tex` | Códigos (`U-PB-1`, `V-VI-7`, `DS-VI-1`) y notas |

Reglas:
- Los **contornos cerrados** (`*-borde`) son los bienes; los **sombreados**
  (`*-trama`) completan lo que no tenga contorno. Un sombreado que repite un
  contorno se descarta, salvo que tenga huecos (entonces sustituye al contorno).
- Los anillos de un sombreado contenidos en otro son **huecos** (las manzanas en
  el sombreado de la red viaria).
- Un contorno que cae en un hueco de un sombreado de su categoría es el **borde
  del hueco** (manzanas dibujadas en `invent-viales-borde`): se descarta. Un
  contorno de red viaria que contiene bienes de otras categorías es una
  **envolvente**: se descarta.
- Cada **código** se asigna a los polígonos que lo contienen (una parcela de
  equipamiento y su edificio comparten código); los demás textos de
  `invent-tex` («IGLESIA», «Puesta a disposición 44,67 m²») quedan como notas.
- Se ignora el espacio papel (cajetín, leyenda) y la «Base Cartografica».
- El núcleo se lee del cajetín («Núcleo: El Viso»).

## 4. Ficha en el mapa

Cada elemento muestra: núcleo, categoría, códigos, notas, superficie (m²,
calculada de la geometría) y fuente. El estilo de las capas (colores de la
leyenda del plano) se puede ajustar en el panel → «Capas del gemelo».

## 5. Pendiente / mejoras
- Si el Ayuntamiento aporta la **tabla del inventario** (Excel/BD: código,
  denominación, superficie registral, referencia catastral, uso), se puede unir
  por código para completar la ficha de cada bien.
