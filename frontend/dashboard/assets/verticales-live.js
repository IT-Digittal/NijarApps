/**
 * Puente de datos reales de las verticales Smart City del panel (index.html).
 *
 * Complementa a panel-live.js (que cubre la vertical DTI): tras detectar la
 * sesión JWT que panel-live.js establece, carga los overviews y listados de
 * /api/v1/verticales y muta los objetos de datos demo de las otras 6
 * verticales (alumbrado, agua, residuos, movilidad, seguridad y energía).
 *
 * Reglas:
 *  - Solo se sobreescriben los campos con fuente real; el resto conserva el
 *    valor demo (las verticales están etiquetadas "Propuesta · demo").
 *  - Todos los accesos a objetos exportados por index.html van con guardas:
 *    window.__D / window.__U (alumbrado), window.__AGUA (agua) y
 *    window.__V4 (residuos, movilidad, seguridad, energía + datasets
 *    RS, RS_CONT, MV_PK, SG_CAMS, EN_ED y hook rerender por vertical).
 *  - Las listas se mutan EN SITIO (splice) porque los renderers capturan las
 *    referencias originales en closures.
 */

import { api } from "./api-client.js?v=18";

const CLAVE_ACCESO = "nijar.dti.access";
const INTERVALO_SESION_MS = 500;

/* ---------------- utilidades ---------------- */

/** Espera a que panel-live.js haya completado el login (token en sesión). */
function esperarSesion() {
  return new Promise((resolver) => {
    (function comprobar() {
      if (sessionStorage.getItem(CLAVE_ACCESO)) return resolver();
      setTimeout(comprobar, INTERVALO_SESION_MS);
    })();
  });
}

/** Asigna obj[campo] = valor solo si existe dato real. */
function pon(obj, campo, valor) {
  if (!obj || valor == null) return;
  if (typeof valor === "number" && !Number.isFinite(valor)) return;
  obj[campo] = valor;
}

function entero(v) { return v == null ? null : Math.round(v); }
function dec1(v) { return v == null ? null : Math.round(v * 10) / 10; }

/** Reemplaza el contenido de un array demo sin perder la referencia. */
function reemplazar(arr, nuevos) {
  arr.splice(0, arr.length);
  nuevos.forEach((x) => arr.push(x));
}

function nombreZona(id) {
  const U = window.__U;
  return U && U.zoneName ? U.zoneName(id) : (id || "");
}

/** Deducción de zona demo a partir del nombre real (para columnas "Zona"). */
function zonaPorNombre(nombre) {
  const n = (nombre || "").toLowerCase();
  if (n.indexOf("níjar") >= 0 || n.indexOf("nijar") >= 0) return "nijar";
  if (n.indexOf("san jos") >= 0) return "sanjose";
  if (n.indexOf("campohermoso") >= 0) return "campo";
  if (n.indexOf("rodalquilar") >= 0) return "roda";
  if (n.indexOf("negras") >= 0) return "negras";
  if (n.indexOf("albaricoques") >= 0) return "albar";
  return "";
}

/* ---------------- carga ---------------- */

async function cargar() {
  const rutas = {
    alumbrado: "/verticales/alumbrado/overview",
    cuadros: "/verticales/alumbrado/cuadros",
    agua: "/verticales/agua/overview",
    residuos: "/verticales/residuos/overview",
    contenedores: "/verticales/residuos/contenedores?page=1&page_size=200",
    movilidad: "/verticales/movilidad/overview",
    seguridad: "/verticales/seguridad/overview",
    energia: "/verticales/energia/overview",
    suministros: "/verticales/energia/suministros?page=1&page_size=100",
  };
  const claves = Object.keys(rutas);
  const res = await Promise.allSettled(claves.map((k) => api.get(rutas[k])));
  const d = {};
  claves.forEach((k, i) => { d[k] = res[i].status === "fulfilled" ? res[i].value : null; });
  return d;
}

/* ---------------- ALUMBRADO (window.__D) ---------------- */

const SECCIONES_ALUMBRADO = [
  "resumen", "mapa", "inventario", "cuadros", "circuitos", "luminarias",
  "energia", "costes", "sostenibilidad",
];

function aplicarAlumbrado(ov, cuadros) {
  const D = window.__D;
  if (!D || !D.KPI) return;
  const K = D.KPI;

  if (ov) {
    pon(K, "total", ov.total_luminarias);
    pon(K, "oper", ov.operativas);
    pon(K, "fallo", ov.en_averia);
    pon(K, "sincom", ov.sin_comunicacion);
    pon(K, "cuadros", ov.cuadros_total);
    pon(K, "circuitos", ov.circuitos_total);
    pon(K, "kwInst", entero(ov.potencia_instalada_kw));
    pon(K, "kwhMonth", entero(ov.consumo_mes_kwh));
    pon(K, "saving", entero(ov.ahorro_energetico_pct));
    pon(K, "incOpen", ov.incidencias_abiertas);
    if (ov.consumo_mes_kwh != null && K.price) {
      K.costMonth = Math.round(ov.consumo_mes_kwh * K.price);
    }
    if (Array.isArray(ov.zonas) && ov.zonas.length) {
      K.zonas = ov.zonas.length;
      ov.zonas.forEach((zr) => {
        const z = D.zoneById && D.zoneById[zr.id];
        if (!z) return; /* sin coordenadas demo no se puede pintar */
        if (zr.nombre) z.name = zr.nombre;
        pon(z, "lum", zr.luminarias);
        pon(z, "led", zr.led);
        pon(z, "vsap", zr.vsap);
        pon(z, "solar", zr.solar);
      });
    }
  }

  if (Array.isArray(cuadros) && cuadros.length && D.cuadroByCode) {
    const ESTADO = { operativo: "operativo", alerta: "alerta", sin_comunicacion: "error" };
    cuadros.forEach((cr) => {
      const c = D.cuadroByCode[cr.codigo];
      if (!c) return; /* los cuadros nuevos no tienen posición en el mapa demo */
      if (cr.nombre) c.name = cr.nombre;
      if (cr.zona_id) c.zone = cr.zona_id;
      if (cr.ubicacion) c.location = cr.ubicacion;
      pon(c, "circuits", cr.circuitos);
      pon(c, "kw", dec1(cr.potencia_kw));
      if (cr.comunicaciones) c.comms = cr.comunicaciones;
      pon(c, "sla", cr.sla);
      if (cr.estado && ESTADO[cr.estado]) c.state = ESTADO[cr.estado];
      if (Array.isArray(cr.alarmas)) c.alarms = cr.alarmas;
      else if (cr.alarmas === null) c.alarms = [];
      c.anomalo = (c.alarms || []).some((a) => /an[oó]malo/i.test(a));
    });
  }
}

/* ---------------- AGUA (window.__AGUA) ---------------- */

function aplicarAgua(ov) {
  const A = window.__AGUA;
  if (!A || !A.W || !ov) return;
  const W = A.W;
  const K = W.KPI || {};

  pon(K, "contadores", ov.contadores);
  pon(K, "tele", ov.contadores_telelectura);
  pon(K, "sectores", ov.sectores);
  pon(K, "fugas", ov.fugas_detectadas);
  if (ov.rendimiento_medio_pct != null) {
    K.rend = dec1(ov.rendimiento_medio_pct);
    K.anr = dec1(100 - ov.rendimiento_medio_pct);
  }

  if (Array.isArray(ov.detalle) && ov.detalle.length && Array.isArray(W.SECTORES)) {
    const nuevos = ov.detalle.map((s) => {
      const conFuga = s.estado === "alerta" || (s.fugas_detectadas || 0) > 0;
      /* La API no expone caudal nocturno: se aproxima desde el caudal real de
         entrada (L/s → m³/h) para que el resaltado siga al estado real. */
      const qmin = dec1((s.caudal_entrada_ls || 0) * 3.6 * (conFuga ? 0.72 : 0.45)) || 0;
      const qminBase = conFuga ? (dec1(qmin / 1.6) || 0) : qmin;
      return {
        id: s.codigo,
        n: s.nombre,
        zone: zonaPorNombre(s.nombre),
        cont: s.contadores,
        qmin: qmin,
        qminBase: qminBase,
        rend: s.rendimiento_pct != null ? dec1(s.rendimiento_pct) : null,
        pres: s.presion_bar != null ? dec1(s.presion_bar) : null,
        st: conFuga ? "fuga" : "operativa",
        fuga: conFuga ? "Fuga detectada por análisis del caudal nocturno" : undefined,
      };
    });
    reemplazar(W.SECTORES, nuevos);
  }
}

/* ---------------- RESIDUOS (window.__V4.RS / RS_CONT) ---------------- */

function aplicarResiduos(ov, pagina) {
  const V4 = window.__V4;
  if (!V4) return;

  if (V4.RS && ov) {
    pon(V4.RS, "cont", ov.total);
    pon(V4.RS, "sensor", ov.con_sensor);
    pon(V4.RS, "llenado", entero(ov.llenado_medio_pct));
    pon(V4.RS, "rutas", ov.rutas);
  }

  const items = pagina && Array.isArray(pagina.items) ? pagina.items : [];
  const conSensor = items.filter((c) => c.tiene_sensor && c.llenado_pct != null);
  if (Array.isArray(V4.RS_CONT) && conSensor.length) {
    const FRACCION = { organica: "Orgánica", envases: "Envases", papel: "Papel", vidrio: "Vidrio", resto: "Resto" };
    conSensor.sort((a, b) => b.llenado_pct - a.llenado_pct);
    reemplazar(V4.RS_CONT, conSensor.slice(0, 6).map((c) => ({
      id: c.codigo,
      n: (nombreZona(c.zona_id) || c.zona_id) + (c.ruta ? " · ruta " + c.ruta : ""),
      fr: FRACCION[c.fraccion] || c.fraccion,
      fill: c.llenado_pct,
      ult: "—", /* la API no expone la marca temporal de la última lectura */
      st: c.llenado_pct > 90 ? "alerta" : c.llenado_pct > 80 ? "vigilancia" : "operativa",
    })));
  }
}

/* ---------------- MOVILIDAD (window.__V4.MV_PK) ---------------- */

const CLAVES_PARKING = [
  [/genoveses/i, "PK-GEN"],
  [/m[oó]nsul/i, "PK-MON"],
  [/san jos[ée]/i, "PK-SJO"],
  [/rodalquilar/i, "PK-ROD"],
  [/negras/i, "PK-NEG"],
];

function aplicarMovilidad(ov) {
  const V4 = window.__V4;
  if (!V4 || !Array.isArray(V4.MV_PK) || !ov || !Array.isArray(ov.detalle)) return;
  const usados = new Set();
  ov.detalle.filter((p) => p.tipo === "parking").forEach((p) => {
    const regla = CLAVES_PARKING.find((r) => !usados.has(r[1]) && r[0].test(p.nombre || ""));
    const fila = regla ? V4.MV_PK.find((x) => x.id === regla[1]) : null;
    const estado = p.estado === "alerta" ? "alerta" : "operativa";
    if (fila) {
      /* Se conserva el id demo (PK-GEN…) porque el mapa y los KPI del resumen
         enlazan UI.parkingDetail con esos ids. */
      usados.add(fila.id);
      if (p.nombre) fila.n = p.nombre;
      pon(fila, "pl", p.capacidad);
      pon(fila, "oc", p.valor_actual);
      fila.st = estado;
    } else if (p.capacidad > 0) {
      V4.MV_PK.push({
        id: p.codigo,
        n: p.nombre || p.codigo,
        pl: p.capacidad,
        oc: p.valor_actual || 0,
        st: estado,
      });
    }
  });
}

/* ---------------- SEGURIDAD (window.__V4.SG_CAMS) ---------------- */

function aplicarSeguridad(ov) {
  const V4 = window.__V4;
  if (!V4 || !Array.isArray(V4.SG_CAMS) || !ov || !Array.isArray(ov.detalle) || !ov.detalle.length) return;
  const TIPO = { fija: "Fija", domo: "Domo", lpr: "Lectura de matrículas (LPR)" };
  reemplazar(V4.SG_CAMS, ov.detalle.map((c) => ({
    id: c.codigo,
    n: c.nombre,
    an: (TIPO[c.tipo] || "Cámara") + (c.con_analitica ? " · con analítica" : " · sin analítica"),
    st: c.estado === "sin_comunicacion" ? "sin comunicación" : "operativa",
  })));
}

/* ---------------- ENERGÍA (window.__V4.EN_ED) ---------------- */

function aplicarEnergia(ov, pagina) {
  /* El overview de energía no tiene hueco en el renderer demo (los KPI del
     resumen están literales en el HTML); solo se conecta el listado. */
  void ov;
  const V4 = window.__V4;
  const lista = pagina && Array.isArray(pagina.items) ? pagina.items : [];
  if (!V4 || !Array.isArray(V4.EN_ED) || !lista.length) return;

  const porEdificio = new Map();
  lista.forEach((s) => {
    const nombre = (s.edificio || "Edificio municipal").replace(/\s*\(CUPS \d+\)$/, "");
    const acc = porEdificio.get(nombre) || { kwh: 0, fv: false };
    acc.kwh += s.consumo_mes_kwh || 0;
    acc.fv = acc.fv || !!s.tiene_fotovoltaica;
    porEdificio.set(nombre, acc);
  });
  const top = Array.from(porEdificio.entries())
    .sort((a, b) => b[1].kwh - a[1].kwh)
    .slice(0, 6);
  reemplazar(V4.EN_ED, top.map((par, i) => ({
    id: "ED-0" + (i + 1),
    n: par[0],
    kwh: Math.round(par[1].kwh),
    base: Math.round(par[1].kwh), /* la API no expone línea base → deriva 0 % */
    fv: par[1].fv,
    st: "operativa",
  })));
}

/* ---------------- re-render ---------------- */

function refrescar() {
  const UI = window.UI;
  /* Alumbrado: invalida las secciones afectadas (render perezoso). */
  if (UI && typeof UI.rerender === "function") {
    SECCIONES_ALUMBRADO.forEach((id) => UI.rerender(id));
  }
  /* Agua */
  if (UI && typeof UI.rerenderA === "function") {
    ["resumen", "sectores"].forEach((id) => UI.rerenderA(id));
  }
  /* Verticales ligeras: requieren el hook cfg.rerender exportado en
     makeVertical (si no existe, basta con haber mutado antes del primer
     render, que es perezoso). */
  const V4 = window.__V4;
  if (V4) {
    const plan = [
      ["RES", ["resumen", "contenedores"]],
      ["MOV", ["resumen", "parkings"]],
      ["SEG", ["resumen", "camaras"]],
      ["ENE", ["resumen", "edificios"]],
    ];
    plan.forEach((par) => {
      const v = V4[par[0]];
      if (v && typeof v.rerender === "function") par[1].forEach((id) => v.rerender(id));
    });
  }
}

/* ---------------- arranque ---------------- */

(async function init() {
  try {
    await esperarSesion();
    const d = await cargar();
    aplicarAlumbrado(d.alumbrado, d.cuadros);
    aplicarAgua(d.agua);
    aplicarResiduos(d.residuos, d.contenedores);
    aplicarMovilidad(d.movilidad);
    aplicarSeguridad(d.seguridad);
    aplicarEnergia(d.energia, d.suministros);
    refrescar();
    console.info("verticales-live: datos reales de /verticales aplicados");
  } catch (e) {
    console.error("verticales-live: error cargando datos reales", e);
  }
})();
