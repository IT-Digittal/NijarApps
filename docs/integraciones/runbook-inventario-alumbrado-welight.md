# Runbook · Inventario de alumbrado (plataforma WeLight)

El Ayuntamiento recibe de WeLight un Excel «Inventory para Níjar» con el
inventario completo del alumbrado público: **una fila por punto de luz**
(luminaria, soporte, equipo, lámpara y cuadro de mando). La versión de octubre
de 2026 tiene 10.184 puntos de luz en 224 cuadros de mando y 36 núcleos, con
189 CUPS y 555,8 kW instalados (91,5 % LED, 664 VSAP y 69 halogenuro metálico).

La telegestión de los cuadros figura como dispositivo **UCA de SOL-X** (14
puntos con WELLNESS): SOL-X es el fabricante de la telegestión punto a punto.

## Qué hace la importación

Sustituye las tablas de alumbrado de demostración (`alumbrado_zonas`,
`alumbrado_cuadros`, `alumbrado_luminarias`) por el inventario real:

- **Zona** = núcleo, tomado del nombre del cuadro («SAN ISIDRO - CM 022»). Los
  cuadros sin núcleo en el nombre se asignan al núcleo más cercano (se avisa).
- **Cuadro** = cada «PANEL NAME»: código `CM-001…` por orden alfabético, CUPS,
  potencia instalada (suma de lámparas) y telegestión declarada.
- **Luminaria** = cada fila: código `WL-<identificador>`, tecnología (LED, VSAP,
  HM, desconocida), potencia, año de instalación, coordenadas y consumo mensual
  **estimado** (potencia × 4.100 h/año ÷ 12).
- Los suministros de Datadis ya cargados cuyo CUPS aparece en un cuadro se marcan
  `tipo = "alumbrado"`, para que su consumo cuente en Alumbrado y no en Edificios.

El inventario **no trae telemetría**: los cuadros quedan con
`comunicaciones = "sin telemetría"`. La Vista de Gobierno muestra el inventario
como real y deja averías, disponibilidad y alarmas como «Al integrar
(telegestión SOL-X)» en lugar de inventarlas.

## Cómo importarlo

```bash
# 1. Comprobar el fichero (no toca la BD)
docker compose cp Inventario_Nijar.xlsx api:/tmp/inventario.xlsx
docker compose exec api python -m nijar_dti.workers.importar_inventario_alumbrado /tmp/inventario.xlsx --dry-run

# 2. Importar (sustituye el inventario de alumbrado actual)
docker compose exec api python -m nijar_dti.workers.importar_inventario_alumbrado /tmp/inventario.xlsx
```

Repetir con cada nuevo Excel de WeLight. El fichero es del cliente: no se sube
al repositorio.

## Siguiente paso: telegestión SOL-X

Pedir a WeLight / SOL-X acceso (API o exportación periódica) al estado de los
cuadros UCA: encendidos, alarmas, comunicaciones y consumos por cuadro. Con eso
se podrá rellenar `estado`, `alarmas` y `comunicaciones` y la fuente FD-008
pasará a operativa.
