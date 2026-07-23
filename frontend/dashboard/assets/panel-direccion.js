/**
 * Cuadro de Mando de Dirección (perfil ejecutivo / político).
 *
 * Módulo de nivel superior, al estilo del módulo de Administración: crea su
 * propia vista `view-direccion`, una tarjeta en el lanzador (visible para quien
 * tenga el permiso `ver_resumen_municipal`) y, si el usuario es del rol
 * `direccion_gobierno`, redirige aquí tras el login. Visión resumida y no
 * técnica: estado global, semáforo por vertical, alertas, recomendaciones e
 * impacto (económico, ciudadano, ambiental).
 */

import { api, getCachedUser } from "./api-client.js?v=18";

let UI, U2, UI2;

/* ---------------- utilidades ---------------- */

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function icono(n) { return window.icon ? window.icon(n) : ""; }
function tienePermiso(p) {
  const u = getCachedUser && getCachedUser();
  if (!u) return false;
  if (!Array.isArray(u.permisos)) return true; // compat
  return u.permisos.includes(p);
}
function eur(n) { return (n == null ? "—" : Number(n).toLocaleString("es-ES") + " €"); }

function fmtNum(v) {
  v = Number(v);
  if (Math.abs(v) >= 1e9) return (v / 1e9).toFixed(1).replace(".", ",") + " mM";
  if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(1).replace(".", ",") + " M";
  return v.toLocaleString("es-ES");
}

/* Bloque de comparativa interanual (turismo, datos oficiales). Para el turismo,
   una subida es positiva (verde); una bajada, negativa (rojo). */
function bloqueInteranual(kpis, titulo, claves) {
  const lista = (kpis || []).filter((k) => !claves || claves.includes(k.clave));
  if (!lista.length) return "";
  return '<div class="card" style="margin-bottom:16px"><div class="card__h"><div>' +
    '<div class="card__t">' + esc(titulo) + "</div>" +
    '<div class="card__s">Frente al mismo periodo del año pasado · fuentes oficiales (INE / Junta / AENA)</div></div>' +
    '<span class="ai-chip">✦ interanual</span></div><div class="grid g4">' +
    lista.map((k) => {
      // Color según si el cambio es POSITIVO para la gestión (depende de 'sentido').
      let col = "var(--muted)";
      if (k.tendencia !== "estable" && k.sentido !== "neutro") {
        const subeBueno = k.sentido !== "bajar_bueno";
        const positivo = (k.tendencia === "sube") === subeBueno;
        col = positivo ? "var(--ok)" : "var(--err)";
      }
      const fl = k.tendencia === "sube" ? "▲" : (k.tendencia === "baja" ? "▼" : "▬");
      const sign = k.variacion_pct > 0 ? "+" : "";
      return '<div class="card" style="box-shadow:none;border:1.5px solid var(--line)">' +
        '<div class="mini" style="color:var(--muted)">' + esc(k.nombre) + "</div>" +
        '<div class="tnum" style="font-size:22px;font-weight:800;margin-top:4px;color:' + col + '">' + fl + " " + sign + k.variacion_pct + "%</div>" +
        '<div class="mini tnum" style="margin-top:4px">' + fmtNum(k.valor) + (k.unidad ? " " + esc(k.unidad) : "") +
        ' <span style="color:var(--muted)">(' + esc(k.periodo) + ")</span></div>" +
        '<div class="mini" style="color:var(--muted)">Año pasado: ' + fmtNum(k.valor_anterior) + " (" + esc(k.periodo_anterior) + ")</div></div>";
    }).join("") + "</div></div>";
}

const ESTADO_BDG = {
  verde: '<span class="bdg bdg-ok">Correcto</span>',
  ambar: '<span class="bdg bdg-warn">Atención</span>',
  rojo: '<span class="bdg bdg-err">Crítico</span>',
};
const ESTADO_GLOBAL_TXT = { correcto: "Correcto", atencion: "Requiere atención", critico: "Crítico" };
const NIVEL_BDG = {
  critico: '<span class="bdg bdg-err">crítico</span>',
  alto: '<span class="bdg bdg-err">alto</span>',
  medio: '<span class="bdg bdg-warn">medio</span>',
  bajo: '<span class="bdg bdg-info">bajo</span>',
};
const PRIO_BDG = {
  critica: '<span class="bdg bdg-err">Crítica</span>',
  alta: '<span class="bdg bdg-warn">Alta</span>',
  media: '<span class="bdg bdg-info">Media</span>',
  informativa: '<span class="bdg bdg-mut">Informativa</span>',
};

function dsub(h1, p) {
  return '<div class="subhead"><div><div class="crumb"><a onclick="UI.go(\'home\')">Plataforma</a> · <b>Dirección</b></div>' +
    "<h1>" + esc(h1) + "</h1><p>" + esc(p) + "</p></div></div>";
}
function estimadoTag() {
  return ' <span class="bdg bdg-mut" title="Valor estimado a partir de factores configurables">estimado</span>';
}

/* ---------------- estética "tipo web" (tótem) ---------------- */

/* Fondos de los tiles de servicio: foto del territorio donde encaja de forma
   natural y degradado temático en el resto (no hay foto de alumbrado, residuos
   o seguridad en la librería compartida). */
const OVERLAY_TILE = "linear-gradient(180deg,rgba(9,24,52,.14) 32%,rgba(7,17,38,.85) 100%)";
const TILE_BG = {
  turismo: OVERLAY_TILE + ",url('../shared/tiles/cabo.jpg')",
  agua: OVERLAY_TILE + ",url('../shared/tiles/playas.jpg')",
  movilidad: OVERLAY_TILE + ",url('../shared/tiles/rutas.jpg')",
  energia: OVERLAY_TILE + ",url('../shared/tiles/naturaleza.jpg')",
  alumbrado: "radial-gradient(circle at 80% 16%,rgba(255,199,90,.5),transparent 55%),linear-gradient(160deg,#14284f,#3c5b9b)",
  residuos: "linear-gradient(160deg,#0d3b2e,#2e7d5b)",
  seguridad: "linear-gradient(160deg,#1b2438,#46587e)",
};
const TILE_BG_DEF = "linear-gradient(160deg,#1c2a4a,#3d5586)";

const FRASE_TILE = {
  verde: "Funciona con normalidad",
  ambar: "Necesita seguimiento",
  rojo: "Requiere una decisión",
};
const COLOR_GLOBAL = { correcto: "#3ddc7f", atencion: "#ffc247", critico: "#ff6a5c" };

function frasePortada(r) {
  const n = (r.areas_alerta || []).length;
  if (r.estado_texto === "critico") return "Hay servicios que requieren una decisión hoy";
  if (r.estado_texto === "atencion") {
    return n
      ? "Níjar funciona bien, con " + n + (n === 1 ? " área" : " áreas") + " en seguimiento"
      : "Níjar funciona bien, con aspectos en seguimiento";
  }
  return "Níjar funciona hoy con normalidad";
}

const DIR_CSS = `
#view-direccion .dir-hero{position:relative;border-radius:20px;overflow:hidden;color:#fff;padding:26px 150px 24px 28px;margin-bottom:18px;background-image:linear-gradient(115deg,rgba(7,20,44,.88) 0%,rgba(10,30,66,.6) 48%,rgba(8,22,48,.3) 100%),url('../shared/cabo-de-gata-hero.jpg');background-size:cover;background-position:center;box-shadow:0 18px 40px rgba(10,25,50,.22)}
#view-direccion .dir-hero-top{display:flex;align-items:center;gap:10px;font-size:11.5px;letter-spacing:.13em;text-transform:uppercase;font-weight:700;opacity:.94}
#view-direccion .dir-hero-top img{width:26px;height:32px;filter:drop-shadow(0 2px 6px rgba(0,0,0,.45))}
#view-direccion .dir-hero h2{color:#fff;margin:14px 0 6px;font-size:clamp(24px,3vw,33px);font-weight:800;line-height:1.16;max-width:640px;text-shadow:0 2px 14px rgba(0,0,0,.35)}
#view-direccion .dir-hero-sub{font-size:13.5px;opacity:.86;max-width:600px}
#view-direccion .dir-vivo{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}
#view-direccion .dir-chip{display:flex;flex-direction:column;gap:2px;padding:9px 15px;border-radius:14px;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.26);backdrop-filter:blur(8px);min-width:104px}
#view-direccion .dir-chip b{font-size:19px;font-weight:800;font-variant-numeric:tabular-nums}
#view-direccion .dir-chip span{font-size:10.5px;opacity:.85;letter-spacing:.02em;text-transform:uppercase}
#view-direccion .dir-score{position:absolute;top:24px;right:26px;width:102px;height:102px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:conic-gradient(var(--dir-col) calc(var(--dir-val)*1%),rgba(255,255,255,.16) 0)}
#view-direccion .dir-score::before{content:"";position:absolute;inset:9px;border-radius:50%;background:rgba(7,18,40,.82)}
#view-direccion .dir-score>div{position:relative;text-align:center;line-height:1.05}
#view-direccion .dir-sect{display:flex;align-items:baseline;justify-content:space-between;gap:10px;flex-wrap:wrap;margin:2px 2px 10px}
#view-direccion .dir-sect h3{margin:0;font-size:17px;font-weight:800}
#view-direccion .dir-sect span{font-size:12.5px;color:var(--muted)}
#view-direccion .dir-tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(225px,1fr));gap:14px;margin-bottom:20px}
#view-direccion .dir-tile{position:relative;min-height:170px;border:0;border-radius:16px;overflow:hidden;cursor:pointer;color:#fff;padding:16px;display:flex;flex-direction:column;justify-content:flex-end;align-items:flex-start;text-align:left;font-family:inherit;background-size:cover;background-position:center;transition:transform .18s ease,box-shadow .18s ease}
#view-direccion .dir-tile:hover{transform:translateY(-3px);box-shadow:0 14px 30px rgba(10,25,50,.32)}
#view-direccion .dir-tile-ico{position:absolute;top:12px;right:12px;opacity:.32;pointer-events:none}
#view-direccion .dir-tile-ico svg{width:42px;height:42px}
#view-direccion .dir-estado{display:inline-flex;align-items:center;gap:7px;font-size:11px;font-weight:800;letter-spacing:.07em;text-transform:uppercase;text-shadow:0 1px 6px rgba(0,0,0,.4)}
#view-direccion .dir-dot{width:11px;height:11px;border-radius:50%;flex:none}
#view-direccion .dir-dot--verde{background:#3ddc7f;box-shadow:0 0 10px 2px rgba(61,220,127,.75)}
#view-direccion .dir-dot--ambar{background:#ffc247;box-shadow:0 0 10px 2px rgba(255,194,71,.8)}
#view-direccion .dir-dot--rojo{background:#ff6a5c;box-shadow:0 0 10px 2px rgba(255,106,92,.85)}
#view-direccion .dir-tile h3{color:#fff;margin:7px 0 4px;font-size:19px;font-weight:800;text-shadow:0 1px 8px rgba(0,0,0,.45)}
#view-direccion .dir-frase{font-size:12.5px;opacity:.9;line-height:1.45;text-shadow:0 1px 6px rgba(0,0,0,.4)}
#view-direccion .dir-week{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px;margin-bottom:20px}
#view-direccion .dir-wcard{position:relative;overflow:hidden;border-radius:16px;padding:16px;background:var(--card,#fff);border:1.5px solid var(--line)}
#view-direccion .dir-wcard::before{content:"";position:absolute;top:0;left:0;right:0;height:4px;background:var(--dir-acc,#2563b0)}
#view-direccion .dir-wcard h4{display:flex;align-items:center;gap:8px;margin:2px 0 10px;font-size:12.5px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
#view-direccion .dir-ev{display:flex;gap:10px;align-items:center;padding:7px 0;border-bottom:1px dashed var(--line)}
#view-direccion .dir-ev:last-of-type{border-bottom:0}
#view-direccion .dir-ev-fecha{min-width:44px;text-align:center;border-radius:10px;padding:5px 4px;background:#eef3fb;color:#0e3a78;font-weight:800;line-height:1.05}
#view-direccion .dir-ev-fecha small{display:block;font-size:9.5px;letter-spacing:.08em;text-transform:uppercase}
#view-direccion .dir-impacto{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:14px;margin-bottom:20px}
#view-direccion .dir-icard{border-radius:16px;padding:18px;color:#fff;box-shadow:0 10px 26px rgba(10,25,50,.18)}
#view-direccion .dir-icard span{font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;opacity:.85;font-weight:700}
#view-direccion .dir-icard b{display:block;font-size:27px;font-weight:800;margin:6px 0 4px}
#view-direccion .dir-icard .mini{opacity:.85}
#view-direccion .dir-icard--eco{background:linear-gradient(135deg,#0e3a78,#2563b0)}
#view-direccion .dir-icard--ciu{background:linear-gradient(135deg,#0e6f66,#17a394)}
#view-direccion .dir-icard--amb{background:linear-gradient(135deg,#155e38,#2f9e5f)}
#view-direccion .dir-vhero{position:relative;border-radius:16px;overflow:hidden;color:#fff;padding:20px;margin-bottom:16px;min-height:118px;display:flex;flex-direction:column;justify-content:flex-end;background-size:cover;background-position:center}
#view-direccion .dir-vhero h3{color:#fff;margin:6px 0 3px;font-size:22px;font-weight:800;text-shadow:0 1px 8px rgba(0,0,0,.45)}
@media (max-width:760px){#view-direccion .dir-hero{padding-right:28px}#view-direccion .dir-score{position:static;margin-top:14px}}
`;

function inyectarEstilos() {
  if (document.getElementById("dir-css")) return;
  const st = document.createElement("style");
  st.id = "dir-css";
  st.textContent = DIR_CSS;
  document.head.appendChild(st);
}

/* ---------------- pantalla: Resumen municipal ---------------- */

async function renderResumen(el) {
  inyectarEstilos();
  el.innerHTML = dsub("Cuadro de Mando de Dirección · Smart City Níjar",
    "Visión ejecutiva de los servicios inteligentes municipales: estado global, impacto, alertas relevantes y recomendaciones para la toma de decisiones.") +
    '<div class="card"><div class="mini" style="color:var(--muted);padding:26px 0;text-align:center">Cargando…</div></div>';

  let r, recs;
  try {
    [r, recs] = await Promise.all([datosResumen(), datosRecs()]);
  } catch (e) {
    el.innerHTML = dsub("Cuadro de Mando de Dirección", "Visión ejecutiva municipal.") +
      '<div class="card"><div class="mini" style="color:var(--muted);text-align:center;padding:26px 0">' +
      (e && e.status === 403 ? "Tu rol no tiene acceso al cuadro de mando de dirección." : "Error: " + esc(e && e.message || e)) + "</div></div>";
    return;
  }
  // Datos vivos y de contexto (mejor esfuerzo: si una fuente no está, se omite)
  const [aire, aforo, eventos, avisos] = await Promise.all([
    api.get("/gemelo/aire/resumen").catch(() => null),
    api.get("/gemelo/parque/aforo").catch(() => null),
    api.get("/tourism/events?publicado=true&page_size=4").catch(() => null),
    api.get("/cms/publico/totem").catch(() => null),
  ]);
  const im = r.impacto;

  let h = dsub("Cuadro de Mando de Dirección · Smart City Níjar",
    "Visión ejecutiva de los servicios inteligentes municipales: estado global, impacto, alertas relevantes y recomendaciones para la toma de decisiones.");

  // Portada: héroe fotográfico con el estado del municipio en una frase + datos vivos
  const hoy = new Date().toLocaleDateString("es-ES", { weekday: "long", day: "numeric", month: "long" });
  const chip = (v, l) => '<div class="dir-chip"><b>' + v + "</b><span>" + l + "</span></div>";
  let chips = chip(r.servicios_ok + " / " + r.servicios_total, "servicios en verde");
  if (aire && aire.temperatura_media_c != null) {
    chips += chip(Math.round(aire.temperatura_media_c) + "°", "aire " + esc(aire.eaqi_peor_texto || "—"));
  }
  if (aforo && aforo.aforo_actual != null) chips += chip(fmtNum(aforo.aforo_actual), "ahora en el Parque");
  chips += chip(String(r.incidencias_criticas), "incidencias críticas") +
    chip(r.satisfaccion_pct != null ? r.satisfaccion_pct + "%" : "—", "satisfacción ciudadana");

  h += '<div class="dir-hero"><div class="dir-hero-top"><img src="../shared/escudo-nijar.svg" alt="">' +
    "Ayuntamiento de Níjar · Smart City · " + esc(hoy) + "</div>" +
    "<h2>" + esc(frasePortada(r)) + "</h2>" +
    '<div class="dir-hero-sub">' + r.servicios_ok + " de " + r.servicios_total +
    " servicios municipales en correcto estado · disponibilidad media del " + r.disponibilidad_media_pct.toFixed(1) + "%</div>" +
    '<div class="dir-score" style="--dir-val:' + r.estado_global + ";--dir-col:" + (COLOR_GLOBAL[r.estado_texto] || "#3ddc7f") + '">' +
    '<div><div style="font-size:26px;font-weight:800">' + r.estado_global + '</div><div style="font-size:10px;opacity:.8">de 100</div></div></div>' +
    '<div class="dir-vivo">' + chips + "</div></div>";

  // Rejilla de servicios: un tile fotográfico por vertical con su semáforo
  h += '<div class="dir-sect"><h3>Los servicios del municipio, de un vistazo</h3><span>Toca un servicio para abrir su detalle</span></div>' +
    '<div class="dir-tiles">' +
    r.semaforo.map((s) => {
      const v = VERTICALES.find((x) => x.clave === s.clave);
      const id = v ? v.id : null;
      return '<button class="dir-tile" style="background-image:' + (TILE_BG[id] || TILE_BG_DEF) + '"' +
        (id ? ' onclick="UI.goDir(\'' + id + '\')"' : "") + ">" +
        '<span class="dir-tile-ico">' + icono(s.icono) + "</span>" +
        '<span class="dir-estado"><span class="dir-dot dir-dot--' + s.estado + '"></span>' + (FRASE_TILE[s.estado] || "") + "</span>" +
        "<h3>" + esc(s.nombre) + '</h3><span class="dir-frase">' + esc(s.indicador_clave) + "</span></button>";
    }).join("") + "</div>";

  // Esta semana en Níjar: agenda, comunicación en tótems y propuesta de la IA
  const evs = ((eventos && eventos.items) || []).slice(0, 3);
  const aviso = avisos && avisos.length ? avisos[0] : null;
  const ordenPrio = { critica: 0, alta: 1, media: 2, informativa: 3 };
  const recTop = (recs || []).slice().sort((a, b) => (ordenPrio[a.prioridad] ?? 9) - (ordenPrio[b.prioridad] ?? 9))[0];

  h += '<div class="dir-sect"><h3>Esta semana en Níjar</h3><span>Agenda del destino, comunicación en tótems y propuesta destacada</span></div>' +
    '<div class="dir-week">' +
    '<div class="dir-wcard" style="--dir-acc:#2563b0"><h4>' + icono("clock") + "Próximos eventos</h4>" +
    (evs.length ? evs.map((e) => {
      const d = new Date(e.fecha_inicio);
      const mesTxt = d.toLocaleDateString("es-ES", { month: "short" }).replace(".", "");
      return '<div class="dir-ev"><span class="dir-ev-fecha">' + d.getDate() + "<small>" + esc(mesTxt) + "</small></span>" +
        "<div><b>" + esc(e.nombre) + '</b><div class="mini" style="color:var(--muted)">' + esc(e.direccion || e.tipo || "") + "</div></div></div>";
    }).join("") : '<div class="mini" style="color:var(--muted);padding:8px 0">Sin eventos próximos publicados.</div>') + "</div>" +
    '<div class="dir-wcard" style="--dir-acc:#e0912f"><h4>' + icono("totem") + "En los tótems ahora</h4>" +
    (aviso ? "<b>" + esc(aviso.titulo) + "</b>" +
      (aviso.cuerpo ? '<div class="mini" style="color:var(--muted);margin-top:6px">' + esc(String(aviso.cuerpo).slice(0, 140)) + "</div>" : "") +
      '<div class="mini" style="margin-top:8px;color:var(--muted)">Aviso visible en las pantallas del destino.</div>' :
      '<div class="mini" style="color:var(--muted);padding:8px 0">No hay avisos activos en los tótems.</div>') + "</div>" +
    '<div class="dir-wcard" style="--dir-acc:#17a394"><h4>' + icono("chat") + "Propuesta de la IA</h4>" +
    (recTop ? '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' + (PRIO_BDG[recTop.prioridad] || "") +
      '<span class="bdg bdg-info">' + esc(recTop.area) + "</span></div>" +
      '<b style="display:block;margin-top:8px">' + esc(recTop.titulo) + "</b>" +
      '<div class="mini" style="color:var(--muted);margin-top:6px">' + esc(recTop.accion) + "</div>" +
      '<button class="btn btn--sm" style="margin-top:10px" onclick="UI.goDir(\'recomendaciones\')">Ver todas</button>' :
      '<div class="mini" style="color:var(--muted);padding:8px 0">Sin propuestas pendientes.</div>') + "</div></div>";

  // Alertas relevantes
  h += '<div class="card" style="margin-bottom:16px"><div class="card__h"><div><div class="card__t">Alertas relevantes para Dirección</div>' +
    '<div class="card__s">Solo lo importante para la decisión, no incidencias técnicas</div></div></div>' +
    (r.alertas.length ? r.alertas.map((a) =>
      '<div style="border-left:3px solid var(--warn);padding:8px 12px;margin:8px 0;background:var(--bg);border-radius:0 8px 8px 0">' +
      "<div>" + (NIVEL_BDG[a.nivel] || "") + ' <b>' + esc(a.area) + "</b></div>" +
      '<div class="mini" style="margin-top:4px">' + esc(a.motivo) + "</div>" +
      '<div class="mini" style="color:var(--muted);margin-top:2px">Impacto: ' + esc(a.impacto) + "</div>" +
      '<div class="mini" style="margin-top:2px">→ ' + esc(a.recomendacion) + "</div></div>").join("") :
      '<div class="mini" style="color:var(--muted);padding:14px 0;text-align:center">Sin alertas relevantes.</div>') + "</div>";

  // Lo que la Smart City aporta al municipio (tarjetas visuales de impacto)
  h += '<div class="dir-sect"><h3>Lo que la Smart City aporta al municipio</h3><span>Estimaciones a partir de los datos de la plataforma</span></div>' +
    '<div class="dir-impacto">' +
    '<div class="dir-icard dir-icard--eco"><span>Ahorro estimado este mes</span><b>' + eur(im.economico.ahorro_estimado_eur_mes) + "</b>" +
    '<div class="mini">Coste energético del mes: ' + eur(im.economico.coste_energetico_mes_eur) + " · valor estimado</div></div>" +
    '<div class="dir-icard dir-icard--ciu"><span>Ciudadanía</span><b>' + (im.ciudadano.satisfaccion_pct != null ? im.ciudadano.satisfaccion_pct + "%" : "—") + "</b>" +
    '<div class="mini">Satisfacción (proxy) · NPS ' + (im.ciudadano.nps ?? "—") + " · " + im.ciudadano.menciones_mes + " menciones este mes</div></div>" +
    '<div class="dir-icard dir-icard--amb"><span>Sostenibilidad</span><b>' + im.ambiental.co2_evitado_t_anio + " t CO₂/año</b>" +
    '<div class="mini">Evitadas (estimado) · autoconsumo FV ' + im.ambiental.autoconsumo_pct.toFixed(0) + "% · " +
    Number(im.ambiental.consumo_energetico_kwh_mes).toLocaleString("es-ES") + " kWh/mes</div></div></div>";

  // Comparativa interanual del turismo (datos oficiales)
  h += bloqueInteranual(r.interanual_turismo, "Turismo · evolución interanual", ["viajeros", "gasto", "pasajeros_aena"]);

  el.innerHTML = h;
  if (U2 && U2.animateBars) U2.animateBars(el);
}

/* ---------------- bootstrap del módulo ---------------- */

/* ---------------- caché compartida de resumen + recomendaciones ---------------- */

let _resumen = null;
let _recs = null;
async function datosResumen(force) {
  if (force || !_resumen) _resumen = await api.getResumenDireccion();
  return _resumen;
}
async function datosRecs(force) {
  if (force || !_recs) _recs = await api.getRecomendacionesDireccion().catch(() => []);
  return _recs;
}
function invalidarRecs() { _recs = null; }

const ESTADO_REC = {
  pendiente: "Pendiente", en_revision: "En revisión", aceptada: "Aceptada",
  descartada: "Descartada", ejecutada: "Ejecutada",
};

/* ---------------- vistas ejecutivas por vertical ---------------- */

const VERTICALES = [
  { id: "turismo", nombre: "Turismo inteligente", icono: "totem", clave: "dti", area: "turismo",
    preguntas: ["¿Está aumentando el interés turístico?", "¿Qué se está diciendo del destino en redes?", "¿Dónde conviene reforzar la promoción?"] },
  { id: "alumbrado", nombre: "Alumbrado público", icono: "bulb", clave: "alumbrado", ep: "/verticales/alumbrado/overview", area: "alumbrado",
    preguntas: ["¿Qué zonas tienen más problemas de alumbrado?", "¿Qué actuaciones deben priorizarse?", "¿Dónde se puede ahorrar más energía?"] },
  { id: "agua", nombre: "Ciclo del agua", icono: "drop", clave: "agua", ep: "/verticales/agua/overview", area: "agua",
    preguntas: ["¿Dónde se consume más agua?", "¿Existen fugas o pérdidas relevantes?", "¿Qué zonas necesitan intervención?"] },
  { id: "residuos", nombre: "Residuos", icono: "trash", clave: "residuos", ep: "/verticales/residuos/overview", area: "residuos",
    preguntas: ["¿Dónde se llenan antes los contenedores?", "¿Hay riesgo de desbordamiento?", "¿Se puede reducir el coste de recogida?"] },
  { id: "movilidad", nombre: "Movilidad", icono: "car", clave: "movilidad", ep: "/verticales/movilidad/overview", area: "movilidad",
    preguntas: ["¿Dónde se concentran los visitantes?", "¿Hay saturación en aparcamientos?", "¿Debe activarse algún aviso ciudadano?"] },
  { id: "seguridad", nombre: "Seguridad", icono: "cam", clave: "seguridad", ep: "/verticales/seguridad/overview", area: "seguridad",
    preguntas: ["¿Qué dispositivos están fuera de servicio?", "¿Existe riesgo en espacios públicos?", "¿Qué actuaciones preventivas se recomiendan?"] },
  { id: "energia", nombre: "Energía municipal", icono: "bolt", clave: "energia", ep: "/verticales/energia/overview", area: "energia",
    preguntas: ["¿Qué edificios consumen más?", "¿Qué ahorro genera el autoconsumo?", "¿Dónde conviene invertir?"] },
];

function _kpisVertical(id, ov, extra) {
  const k = (l, v, d, cls, ic) => (UI2 && UI2.kpiCard ? UI2.kpiCard(l, esc(String(v)), d, cls, ic, "") : "");
  const n = (x, dec) => (x == null ? "—" : Number(x).toLocaleString("es-ES", { maximumFractionDigits: dec ?? 0 }));
  if (id === "turismo") {
    const bd = ov, uso = extra || {};
    return k("Menciones del mes", n(bd.menciones_ultimo_mes), "En redes y reseñas", "ic-navy", "globe") +
      k("Sentimiento medio", bd.sentimiento_medio != null ? bd.sentimiento_medio.toFixed(2) : "—", "Percepción del destino", "ic-teal", "chart") +
      k("Interacciones en tótems", n(uso.interacciones_total), "Sesiones únicas: " + n(uso.sesiones_unicas), "ic-violet", "totem") +
      k("Fuentes activas", n(bd.fuentes_activas), "Canales monitorizados", "ic-blue", "chart");
  }
  if (id === "alumbrado") return k("Disponibilidad", n(ov.disponibilidad_pct, 1) + "%", "Servicio operativo", "ic-ok", "bulb") +
    k("Incidencias abiertas", n(ov.incidencias_abiertas), "Requieren seguimiento", ov.incidencias_abiertas ? "ic-coral" : "ic-ok", "wrench") +
    k("Consumo mensual", n(ov.consumo_mes_kwh) + " kWh", "Red de alumbrado", "ic-teal", "bolt") +
    k("Ahorro energético", n(ov.ahorro_energetico_pct, 1) + "%", "Frente a VSAP", "ic-gold", "leaf");
  if (id === "agua") return k("Fugas detectadas", n(ov.fugas_detectadas), "Sectores afectados", ov.fugas_detectadas ? "ic-gold" : "ic-ok", "drop") +
    k("Rendimiento medio", n(ov.rendimiento_medio_pct, 0) + "%", "Eficiencia de la red", "ic-teal", "chart") +
    k("Sectores en alerta", n(ov.sectores_en_alerta), "Consumo anómalo", "ic-coral", "bell") +
    k("Telelectura", n(ov.pct_telelectura, 0) + "%", "Contadores telemedidos", "ic-blue", "chart");
  if (id === "residuos") return k("Llenado medio", n(ov.llenado_medio_pct, 0) + "%", "Contenedores con sensor", "ic-teal", "trash") +
    k("Llenado alto (≥80%)", n(ov.llenado_alto), "Riesgo de desbordamiento", ov.llenado_alto >= 20 ? "ic-gold" : "ic-ok", "bell") +
    k("Con sensor", n(ov.con_sensor), "De " + n(ov.total) + " contenedores", "ic-navy", "chart") +
    k("Rutas", n(ov.rutas), "Optimizadas por llenado", "ic-blue", "map");
  if (id === "movilidad") return k("Tráfico actual", n(ov.trafico_actual_veh_h) + " veh/h", "Accesos monitorizados", "ic-navy", "car") +
    k("Ocupación parking", n(ov.ocupacion_parking_pct, 0) + "%", n(ov.plazas_ocupadas) + " / " + n(ov.plazas_totales) + " plazas", ov.ocupacion_parking_pct >= 90 ? "ic-gold" : "ic-ok", "car") +
    k("Puntos de recarga EV", n(ov.puntos_recarga_ev), "Tomas libres: " + n(ov.tomas_ev_libres), "ic-teal", "bolt") +
    k("Aforos", n(ov.aforos), "Puntos de conteo", "ic-blue", "chart");
  if (id === "seguridad") return k("Cámaras online", n(ov.pct_online, 0) + "%", n(ov.online) + " de " + n(ov.camaras), "ic-ok", "cam") +
    k("Sin comunicación", n(ov.sin_comunicacion), "Dispositivos a revisar", ov.sin_comunicacion ? "ic-coral" : "ic-ok", "bell") +
    k("Con analítica", n(ov.con_analitica), "Detección automática", "ic-violet", "chart") +
    k("Retención", n(ov.retencion_dias) + " días", "Grabaciones", "ic-blue", "clock");
  if (id === "energia") return k("Consumo mensual", n(ov.consumo_mes_kwh) + " kWh", n(ov.edificios) + " edificios", "ic-navy", "bolt") +
    k("Autoconsumo FV", n(ov.autoconsumo_pct, 0) + "%", n(ov.cups_con_fotovoltaica) + " CUPS con FV", "ic-ok", "leaf") +
    k("Coste mensual", n(ov.coste_mes_eur) + " €", "Factura estimada", "ic-gold", "euro") +
    k("Coste medio", n(ov.coste_medio_kwh, 3) + " €/kWh", "Precio unitario", "ic-teal", "chart");
  return "";
}

function renderVertical(id) {
  return async function (el) {
    const cfg = VERTICALES.find((v) => v.id === id);
    el.innerHTML = dsub(cfg.nombre + " · Resumen de Dirección", "Cargando…") +
      '<div class="card"><div class="mini" style="color:var(--muted);padding:26px 0;text-align:center">Cargando…</div></div>';
    let ov, extra, resumen, recs;
    try {
      if (id === "turismo") {
        [ov, extra] = await Promise.all([api.get("/dashboards/big-data/overview"), api.get("/dashboards/totems/usage").catch(() => ({}))]);
      } else {
        ov = await api.get(cfg.ep);
      }
      [resumen, recs] = await Promise.all([datosResumen(), datosRecs()]);
    } catch (e) {
      el.innerHTML = dsub(cfg.nombre, "Resumen de dirección") +
        '<div class="card"><div class="mini" style="color:var(--muted);text-align:center;padding:26px 0">' +
        (e && e.status === 403 ? "Tu rol no tiene acceso a esta vertical." : "Error: " + esc(e && e.message || e)) + "</div></div>";
      return;
    }
    const sem = (resumen.semaforo || []).find((s) => s.clave === cfg.clave);
    const recsArea = (recs || []).filter((r) => (r.area || "").toLowerCase().includes(cfg.area));

    let h = dsub(cfg.nombre + " · Resumen de Dirección",
      "Visión resumida para la toma de decisiones. Estado del servicio, indicadores clave y recomendaciones.");
    // Cabecera fotográfica coherente con la portada (estética tótem)
    h += '<div class="dir-vhero" style="background-image:' + (TILE_BG[id] || TILE_BG_DEF) + '">' +
      '<span class="dir-tile-ico">' + icono(cfg.icono) + "</span>" +
      (sem ? '<span class="dir-estado"><span class="dir-dot dir-dot--' + sem.estado + '"></span>' + (FRASE_TILE[sem.estado] || "") + "</span>" : "") +
      "<h3>" + esc(cfg.nombre) + "</h3>" +
      (sem ? '<span class="dir-frase">' + esc(sem.indicador_clave) + "</span>" : "") + "</div>";
    if (sem) {
      h += '<div class="card" style="margin-bottom:16px"><div class="mini"><b>Recomendación:</b> ' +
        esc(sem.recomendacion) + "</div></div>";
    }
    h += '<div class="grid g4" style="margin-bottom:16px">' + _kpisVertical(id, ov, extra) + "</div>";
    // Comparativa interanual REAL de la vertical (histórico mensual de 2 años).
    const ivVert = (resumen.interanual_verticales || []).filter((k) => k.vertical === id);
    if (ivVert.length) h += bloqueInteranual(ivVert, "Evolución interanual (vs mismo mes año pasado)", null);
    // Turismo: series oficiales del contexto. Movilidad: proxy aeropuerto (AENA).
    if (id === "turismo") {
      h += bloqueInteranual(resumen.interanual_turismo, "Evolución interanual del turismo", null);
    } else if (id === "movilidad") {
      h += bloqueInteranual(resumen.interanual_turismo, "Presión turística (proxy: aeropuerto de Almería)", ["pasajeros_aena"]);
    }
    h += '<div class="grid g2">' +
      '<div class="card"><div class="card__t">Preguntas que responde</div><ul style="margin:10px 0 0;padding-left:18px;font-size:13.5px;line-height:1.9">' +
      cfg.preguntas.map((p) => "<li>" + esc(p) + "</li>").join("") + "</ul></div>" +
      '<div class="card"><div class="card__h"><div><div class="card__t">Recomendaciones</div></div><span class="ai-chip">✦ IA</span></div>' +
      (recsArea.length ? recsArea.map((r) =>
        '<div style="border-left:3px solid var(--blue);padding:6px 12px;margin:8px 0;background:var(--bg);border-radius:0 8px 8px 0">' +
        '<div>' + (PRIO_BDG[r.prioridad] || "") + " <b>" + esc(r.titulo) + "</b></div>" +
        '<div class="mini" style="margin-top:4px">' + esc(r.accion) + "</div></div>").join("") :
        '<div class="mini" style="color:var(--muted);padding:10px 0">Sin recomendaciones específicas para esta área.</div>') + "</div></div>";
    el.innerHTML = h;
    if (U2 && U2.animateBars) U2.animateBars(el);
  };
}

/* ---------------- pantalla: Recomendaciones IA (con estados) ---------------- */

async function renderRecomendaciones(el) {
  el.innerHTML = dsub("Recomendaciones de la IA", "Cargando…") +
    '<div class="card"><div class="mini" style="color:var(--muted);padding:26px 0;text-align:center">Cargando…</div></div>';
  let recs;
  try { recs = await datosRecs(true); }
  catch (e) {
    el.innerHTML = dsub("Recomendaciones de la IA", "Propuestas para la toma de decisiones") +
      '<div class="card"><div class="mini" style="color:var(--muted);text-align:center;padding:26px 0">' +
      (e && e.status === 403 ? "Tu rol no tiene acceso a las recomendaciones." : "Error: " + esc(e && e.message || e)) + "</div></div>";
    return;
  }
  const opciones = (sel) => Object.keys(ESTADO_REC).map((k) =>
    '<option value="' + k + '"' + (k === sel ? " selected" : "") + ">" + ESTADO_REC[k] + "</option>").join("");

  el.innerHTML = dsub("Recomendaciones de la IA",
    "Propuestas priorizadas. Marca el estado de cada una (aceptada, descartada, ejecutada…) y deja un comentario de dirección.") +
    '<div class="grid g2">' + recs.map((r) =>
      '<div class="card" data-clave="' + esc(r.clave) + '"><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
      (PRIO_BDG[r.prioridad] || "") + '<span class="bdg bdg-info">' + esc(r.area) + '</span><span class="bdg bdg-mut" data-badge>' + ESTADO_REC[r.estado] + "</span></div>" +
      '<div style="font-weight:700;margin-top:8px">' + esc(r.titulo) + "</div>" +
      '<div class="mini" style="color:var(--muted);margin-top:6px">' + esc(r.justificacion) + "</div>" +
      '<div class="mini" style="margin-top:4px"><b>Acción:</b> ' + esc(r.accion) + "</div>" +
      '<div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;align-items:center">' +
      '<select data-estado ' + INPUT_MINI + ">" + opciones(r.estado) + "</select>" +
      '<input data-coment placeholder="Comentario de dirección…" value="' + esc(r.comentario || "") + '" ' + INPUT_MINI + ' style="flex:1;min-width:160px">' +
      '<button class="btn btn--sm btn--pri" data-guardar>Guardar</button></div></div>').join("") + "</div>";

  el.querySelectorAll("[data-clave]").forEach((card) => {
    const clave = card.getAttribute("data-clave");
    card.querySelector("[data-guardar]").onclick = async () => {
      const estado = card.querySelector("[data-estado]").value;
      const comentario = card.querySelector("[data-coment]").value.trim();
      try {
        await api.actualizarRecomendacion(clave, { estado, comentario: comentario || null });
        card.querySelector("[data-badge]").textContent = ESTADO_REC[estado];
        invalidarRecs();
        UI.toast("Recomendación actualizada");
      } catch (e) { UI.toast("Error: " + (e && e.message || e)); }
    };
  });
}

const INPUT_MINI = 'style="border:1.5px solid var(--line);border-radius:8px;padding:6px 9px;font-size:12.5px;font-family:inherit"';

/* ---------------- Informe de Dirección (imprimible → PDF) ---------------- */

async function abrirInforme() {
  let r, recs;
  try { [r, recs] = await Promise.all([datosResumen(true), datosRecs(true)]); }
  catch (e) { UI.toast("No se pudo generar el informe: " + (e && e.message || e)); return; }
  const im = r.impacto;
  const fila = (a, b) => '<tr><td style="padding:4px 8px;border-bottom:1px solid #e5e5e5">' + a + '</td><td style="padding:4px 8px;border-bottom:1px solid #e5e5e5;text-align:right">' + b + "</td></tr>";
  const semTxt = { verde: "Correcto", ambar: "Atención", rojo: "Crítico" };

  const cuerpo =
    '<div style="display:flex;justify-content:space-between;align-items:baseline;border-bottom:2px solid #003B7A;padding-bottom:8px">' +
    '<h1 style="margin:0;font-size:20px;color:#003B7A">Informe de Dirección · Smart City Níjar</h1>' +
    '<div style="font-size:12px;color:#555">Estado global: <b>' + r.estado_global + "/100</b></div></div>" +
    '<p style="font-size:12.5px;color:#333">Visión ejecutiva de los servicios inteligentes municipales para la toma de decisiones.</p>' +
    '<h2 style="font-size:14px;color:#003B7A;margin:14px 0 6px">Semáforo por servicio</h2>' +
    '<table style="width:100%;border-collapse:collapse;font-size:12.5px">' +
    r.semaforo.map((s) => fila(esc(s.nombre) + " — " + esc(s.indicador_clave), "<b>" + semTxt[s.estado] + "</b>")).join("") + "</table>" +
    '<h2 style="font-size:14px;color:#003B7A;margin:14px 0 6px">Impacto (estimado)</h2>' +
    '<table style="width:100%;border-collapse:collapse;font-size:12.5px">' +
    fila("Ahorro estimado / mes", eur(im.economico.ahorro_estimado_eur_mes)) +
    fila("CO₂ evitado", im.ambiental.co2_evitado_t_anio + " t/año") +
    fila("Satisfacción ciudadana (proxy)", (im.ciudadano.satisfaccion_pct ?? "—") + "%") +
    fila("Incidencias críticas", r.incidencias_criticas) + "</table>" +
    '<h2 style="font-size:14px;color:#003B7A;margin:14px 0 6px">Recomendaciones y próximas actuaciones</h2>' +
    '<ol style="font-size:12.5px;line-height:1.7;padding-left:18px">' +
    recs.map((x) => "<li><b>[" + x.prioridad + "]</b> " + esc(x.titulo) + " — " + esc(x.accion) + " <i>(" + ESTADO_REC[x.estado] + ")</i></li>").join("") + "</ol>" +
    '<div style="margin-top:16px;font-size:11px;color:#888">Generado por la Plataforma DTI de Níjar · Exp. 18962/2025</div>';

  let dlg = document.getElementById("informe-direccion");
  if (dlg) dlg.remove();
  dlg = document.createElement("div");
  dlg.id = "informe-direccion";
  dlg.innerHTML =
    '<style>@media print{body>*:not(#informe-direccion){display:none!important}#informe-direccion{position:static!important;box-shadow:none!important}#informe-direccion .no-print{display:none!important}}</style>' +
    '<div class="no-print" style="display:flex;gap:8px;justify-content:flex-end;margin-bottom:12px">' +
    '<button class="btn" id="informe-cerrar">Cerrar</button>' +
    '<button class="btn btn--pri" id="informe-imprimir">Imprimir / Guardar PDF</button></div>' +
    '<div id="informe-hoja" style="background:#fff;color:#111;padding:28px;border-radius:8px;max-width:800px;margin:0 auto;box-shadow:var(--sh-lg)">' + cuerpo + "</div>";
  dlg.style.cssText = "position:fixed;inset:0;z-index:9999;overflow:auto;padding:24px;background:rgba(15,25,45,.55);font-family:var(--ff)";
  document.body.appendChild(dlg);
  dlg.querySelector("#informe-cerrar").onclick = () => dlg.remove();
  dlg.querySelector("#informe-imprimir").onclick = () => window.print();
}

const SECCIONES = [
  { id: "resumen", n: "Resumen municipal", i: "chart", r: renderResumen },
  ...VERTICALES.map((v) => ({ id: v.id, n: v.nombre, i: v.icono, r: renderVertical(v.id) })),
  { id: "recomendaciones", n: "Recomendaciones IA", i: "chat", r: renderRecomendaciones },
];
const R = {};
let rendered = {};
let cur = null;
let instalado = false;
let redirigido = false;

function construirVista() {
  if (document.getElementById("view-direccion")) return;
  const home = document.getElementById("view-home");
  if (!home) return;
  inyectarEstilos();
  const div = document.createElement("div");
  div.className = "view";
  div.id = "view-direccion";
  div.innerHTML = '<div class="app"><aside class="sidebar" id="dir-sidebar"></aside>' +
    '<main class="main" id="dir-main">' +
    SECCIONES.map((s) => '<section class="dirview" id="dir-' + s.id + '"></section>').join("") +
    "</main></div>";
  home.insertAdjacentElement("afterend", div);
  SECCIONES.forEach((s) => { R[s.id] = s.r; });
}

function renderSidebar() {
  const sb = document.getElementById("dir-sidebar");
  if (!sb) return;
  let h = '<div class="sb-head"><div class="sb-title">' + icono("chart") + " Dirección</div>" +
    '<div class="sb-sub">Cuadro de mando ejecutivo</div></div><div class="sb-g">Gobierno</div>';
  SECCIONES.forEach((s) => {
    h += '<button class="sb-it" data-dirsec="' + s.id + '" onclick="UI.goDir(\'' + s.id + '\')">' + icono(s.i) + s.n + "</button>";
  });
  if (tienePermiso("generar_informes")) {
    h += '<div class="sb-g">Informes</div>' +
      '<button class="sb-it" onclick="UI.informeDireccion()">' + icono("doc") + "Generar informe</button>";
  }
  sb.innerHTML = h;
}

function tarjetaHTML() {
  return '<div class="vcard vcard--on" data-dircard onclick="UI.enterDireccion()">' +
    '<div class="vi ic-navy">' + icono("chart") + "</div>" +
    "<h3>Vista de Gobierno</h3><p>Cuadro de mando de dirección: estado global del municipio, semáforo por servicio, alertas relevantes y recomendaciones de la IA para la toma de decisiones.</p>" +
    '<div class="vfoot"><span class="bdg bdg-info">Perfil directivo</span>' +
    '<button class="btn btn--sm btn--pri">Abrir cuadro de mando</button></div></div>';
}

function inyectarTarjeta() {
  const cont = document.getElementById("home-verticals");
  if (!cont) return;
  const ya = cont.querySelector("[data-dircard]");
  if (!tienePermiso("ver_resumen_municipal")) { if (ya) ya.remove(); return; }
  if (!ya) cont.insertAdjacentHTML("afterbegin", tarjetaHTML());
}

function instalar() {
  if (instalado) return;
  UI = window.UI; U2 = window.__U; UI2 = window.__UI2;
  if (!UI || !UI._VIEWS || !UI2) return;
  construirVista();
  renderSidebar();
  if (UI._VIEWS.indexOf("view-direccion") === -1) UI._VIEWS.push("view-direccion");

  UI.goDir = function (id) {
    UI._showV("view-direccion");
    const ctx = document.getElementById("tb-ctx");
    if (ctx) ctx.style.display = "flex";
    const pill = document.getElementById("tb-pill");
    if (pill) pill.innerHTML = icono("chart") + ' Dirección <span class="bdg bdg-info" style="margin-left:4px">vista de gobierno</span>';
    const p2 = document.getElementById("tb-pill2");
    if (p2) p2.textContent = "Cuadro de mando ejecutivo";
    cur = id;
    document.querySelectorAll(".dirview").forEach((v) => { v.style.display = "none"; });
    const el = document.getElementById("dir-" + id);
    if (!el) return;
    if (!rendered[id]) { R[id](el); rendered[id] = true; }
    el.style.display = "block";
    document.querySelectorAll("[data-dirsec]").forEach((b) => b.classList.toggle("on", b.dataset.dirsec === id));
    window.scrollTo(0, 0);
  };
  UI.enterDireccion = function () { UI.goDir(SECCIONES[0].id); };
  UI.rerenderDir = function (id) { rendered[id] = false; if (cur === id) UI.goDir(id); };
  UI.informeDireccion = abrirInforme;

  // Mantener la tarjeta al re-renderizar el home.
  const X = window.__UI2;
  if (X && X.renderHome && !X._dirWrap) {
    const orig = X.renderHome;
    X.renderHome = function () { orig.apply(this, arguments); inyectarTarjeta(); };
    X._dirWrap = true;
  }

  inyectarTarjeta();
  const poll = setInterval(() => {
    const u = getCachedUser && getCachedUser();
    if (!u) return;
    inyectarTarjeta();
    // Redirección: el perfil directivo aterriza en su cuadro de mando.
    if (!redirigido && u.rol === "direccion_gobierno") { redirigido = true; UI.enterDireccion(); }
    clearInterval(poll);
  }, 1000);

  instalado = true;
}

(function init() {
  if (!window.UI || !window.__UI2 || !window.__UI2.renderHome) { setTimeout(init, 300); return; }
  instalar();
  if (!instalado) setTimeout(init, 300);
})();
