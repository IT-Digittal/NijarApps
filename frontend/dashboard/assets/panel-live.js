/**
 * Puente de datos reales del panel DTI definitivo.
 *
 * Convierte el panel (index.html) de demo a producción:
 *  1. Exige login JWT (sesión compartida con gestion.html vía api-client.js).
 *  2. Carga los KPIs reales de la API y los inyecta en window.__DTI.T.
 *  3. Fuerza el re-render de las secciones y refresca cada 60 s.
 *  4. Marca las secciones que aún muestran datos de demostración.
 *
 * Regla de honestidad: si un dato tiene endpoint pero la llamada falla,
 * se muestra "—" (nunca el número ficticio del demo). Las secciones sin
 * fuente real llevan un aviso visible de demostración.
 */

import { api, tokens } from "./api-client.js?v=18";

const REFRESH_MS = 60_000;
const NO_DATA = "—";

/* Secciones informativas: documentan el expediente/contrato, no telemetría */
const SECCIONES_INFO = ["opendata", "plan", "proyecto"];

const COLOR_IDIOMA = { es: "#1F6FE5", en: "#17BEBB", de: "#F0B429", fr: "#7C6BF0" };
const NOMBRE_IDIOMA = { es: "Español", en: "Inglés", de: "Alemán", fr: "Francés" };
const SLA_POR_SEVERIDAD = { critica: "≤ 8 h", alta: "≤ 12 h", media: "≤ 48 h", baja: "—" };

/* ---------------- utilidades ---------------- */

function el(tag, attrs, html) {
  const e = document.createElement(tag);
  Object.assign(e, attrs || {});
  if (html != null) e.innerHTML = html;
  return e;
}

function num(v, dec) {
  if (v == null || Number.isNaN(v)) return null;
  return Math.round(v * Math.pow(10, dec || 0)) / Math.pow(10, dec || 0);
}

function horasDesde(iso) {
  if (!iso) return NO_DATA;
  const h = (Date.now() - new Date(iso).getTime()) / 36e5;
  if (h < 1) return Math.round(h * 60) + " min";
  if (h < 48) return num(h, 1) + " h";
  return Math.round(h / 24) + " d";
}

function fechaCorta(iso) {
  if (!iso) return NO_DATA;
  const d = new Date(iso);
  return String(d.getDate()).padStart(2, "0") + "/" + String(d.getMonth() + 1).padStart(2, "0");
}

function items(pag) {
  if (!pag) return [];
  return pag.items || pag.resultados || (Array.isArray(pag) ? pag : []);
}

function totalDe(pag) {
  if (!pag) return null;
  return pag.total ?? pag.total_items ?? items(pag).length;
}

/* ---------------- login ---------------- */

function montarLogin() {
  const css = `
  .live-gate{position:fixed;inset:0;z-index:9000;display:grid;place-items:center;
    background:linear-gradient(160deg,#003B7A 0%,#0A4C93 55%,#00A6C0 130%)}
  .live-gate__card{background:#fff;border-radius:18px;box-shadow:0 24px 60px rgba(0,20,60,.35);
    padding:34px 36px;width:min(94vw,400px);font-family:var(--ff)}
  .live-gate__card h1{font-size:19px;margin:0 0 4px;color:#16233D}
  .live-gate__card p{font-size:13px;color:#67769A;margin:0 0 20px}
  .live-gate__card label{display:block;font-size:11.5px;font-weight:800;letter-spacing:.04em;
    color:#67769A;text-transform:uppercase;margin:14px 0 5px}
  .live-gate__card input{width:100%;box-sizing:border-box;border:1.5px solid #E9EFF8;border-radius:11px;
    padding:11px 13px;font-size:14px;font-family:inherit}
  .live-gate__card input:focus{outline:none;border-color:#1F6FE5}
  .live-gate__err{display:none;background:#FDEBEC;color:#E5484D;border-radius:10px;
    padding:9px 12px;font-size:12.5px;margin-top:14px}
  .live-gate__btn{width:100%;margin-top:20px;background:#003B7A;color:#fff;border:0;border-radius:11px;
    padding:12px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit}
  .live-gate__btn:disabled{opacity:.6}
  .demo-note{background:#FFF7E0;border:1px solid #F0B429;color:#7a5c00;border-radius:12px;
    padding:10px 14px;font-size:12.5px;margin-bottom:14px}
  .live-dot{display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:800;color:#12A150}
  .live-dot i{width:8px;height:8px;border-radius:50%;background:#12A150;animation:liveblink 1.6s infinite}
  @keyframes liveblink{50%{opacity:.25}}`;
  document.head.appendChild(el("style", null, css));

  const gate = el("div", { className: "live-gate", id: "live-gate" }, `
    <div class="live-gate__card">
      <h1>Plataforma DTI Níjar</h1>
      <p>Panel de operación del destino turístico inteligente.<br>Acceso restringido al personal autorizado.</p>
      <form id="live-login-form">
        <label for="lg-email">Email corporativo</label>
        <input id="lg-email" type="email" autocomplete="username" required>
        <label for="lg-pwd">Contraseña</label>
        <input id="lg-pwd" type="password" autocomplete="current-password" required>
        <div class="live-gate__err" id="lg-err"></div>
        <button class="live-gate__btn" id="lg-btn" type="submit">Entrar</button>
      </form>
    </div>`);
  document.body.appendChild(gate);

  gate.querySelector("#live-login-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const btn = gate.querySelector("#lg-btn");
    const err = gate.querySelector("#lg-err");
    btn.disabled = true;
    err.style.display = "none";
    try {
      await api.login(gate.querySelector("#lg-email").value.trim(), gate.querySelector("#lg-pwd").value);
      gate.remove();
      arrancar();
    } catch (e) {
      err.textContent = e && e.code === "UNAUTHORIZED"
        ? "Credenciales incorrectas."
        : "No se pudo iniciar sesión. Inténtalo de nuevo.";
      err.style.display = "block";
    } finally {
      btn.disabled = false;
    }
  });
}

/* ---------------- carga de datos ---------------- */

async function cargar() {
  const hoy = new Date();
  const rutas = {
    tele: "/chatbot/telemetry",
    teleSeries: "/chatbot/telemetry/series",
    bigdata: "/dashboards/big-data/overview",
    sentimiento: "/data/social/kpis/sentiment?granularidad=dia",
    topics: "/data/social/topics?limit=12",
    menciones: "/data/social/mentions?page=1&page_size=8",
    nps: "/data/social/kpis/nps",
    sov: "/data/social/kpis/share-of-voice",
    smartoffice: "/dashboards/smart-office/overview",
    ambiente: "/dashboards/smart-office/environment?granularidad=hora",
    sensores: "/data/iot/sensors?page=1&page_size=100",
    totemsUso: "/dashboards/totems/usage",
    totemsSalud: "/dashboards/totems/health",
    incidencias: "/incidencias",
    ans: "/incidencias/ans",
    contenidos: "/cms/content?page=1&page_size=8",
    recursos: "/tourism/resources?page=1&page_size=1",
    eventos: "/tourism/events?page=1&page_size=1",
    informeMes: `/dashboards/reports/monthly?year=${hoy.getFullYear()}&month=${hoy.getMonth() + 1}`,
  };
  const claves = Object.keys(rutas);
  const res = await Promise.allSettled(claves.map((k) => api.get(rutas[k])));
  const d = {};
  claves.forEach((k, i) => { d[k] = res[i].status === "fulfilled" ? res[i].value : null; });
  return d;
}

/* ---------------- volcado en el modelo del panel ---------------- */

function aplicar(d) {
  const DTI = window.__DTI;
  if (!DTI) return;
  const T = DTI.T;
  const K = T.KPI;

  /* Chatbot */
  if (d.tele) {
    K.chatQ = d.tele.interacciones_totales;
    K.chatRes = num(d.tele.resolucion_autonoma_porc);
    K.chatSat = num(d.tele.satisfaccion_porc);
    K.chatSes = d.tele.sesiones_unicas;
    if (d.tele.top_intents && d.tele.top_intents.length) {
      T.CHATTOP = d.tele.top_intents.map((i) => [i.nombre, i.ocurrencias]);
    }
    const idiomas = Object.entries(d.tele.idiomas_distribucion || {})
      .sort((a, b) => b[1] - a[1])
      .map(([lang, pct]) => [NOMBRE_IDIOMA[lang] || lang.toUpperCase(), num(pct), COLOR_IDIOMA[lang] || "#9AA7BF"]);
    if (idiomas.length) T.CHATLANG = idiomas;
  } else {
    K.chatQ = null; K.chatRes = null; K.chatSat = null; K.chatSes = null;
  }
  if (d.teleSeries && d.teleSeries.puntos && d.teleSeries.puntos.length) {
    T.CHATSERIES = d.teleSeries.puntos.slice(-30).map((p) => p.total || 0);
    K.chatHoy = T.CHATSERIES[T.CHATSERIES.length - 1];
  } else { T.CHATSERIES = null; K.chatHoy = null; }
  T.CHATCH = null;       /* sin desglose por canal todavía */

  /* Social listening */
  if (d.bigdata) {
    K.ment = d.bigdata.menciones_ultimo_mes;
    K.mentTotal = d.bigdata.menciones_total;
    K.fuentes = d.bigdata.fuentes_activas;
  } else { K.ment = null; K.mentTotal = null; K.fuentes = null; }
  if (d.sentimiento && d.sentimiento.puntos && d.sentimiento.puntos.length) {
    const pts = d.sentimiento.puntos.slice(-30);
    T.MENTSERIES = pts.map((p) => (p.positivo || 0) + (p.neutro || 0) + (p.negativo || 0));
    const pos = pts.reduce((a, p) => a + (p.positivo || 0), 0);
    const tot = pts.reduce((a, p) => a + (p.positivo || 0) + (p.neutro || 0) + (p.negativo || 0), 0);
    K.sentPos = tot ? num((pos / tot) * 100) : null;
    K.mentHoy = T.MENTSERIES[T.MENTSERIES.length - 1];
  } else { T.MENTSERIES = null; K.sentPos = null; K.mentHoy = null; }
  if (d.topics && d.topics.length) T.WORDS = d.topics.map((t) => [t.tema, t.menciones, t.sentimiento_medio]);
  K.nps = d.nps ? num(d.nps.nps) : null;
  T.SOV = d.sov || null;
  K.sovTop = d.sov && d.sov.length ? d.sov[0] : null;
  const m = items(d.menciones);
  T.MENTIONS = m.length ? m.map((op) => ({
    src: op.fuente, user: op.autor_handle || "anónimo", txt: op.texto_original,
    sent: op.sentimiento, reach: (op.metricas && (op.metricas.alcance || op.metricas.reach)) || 0,
    date: fechaCorta(op.publicado_en),
  })) : [];

  /* Smart Office / IoT */
  if (d.smartoffice) {
    K.co2 = num(d.smartoffice.co2_actual_ppm);
    K.tempC = num(d.smartoffice.temperatura_actual_c, 1);
    K.hum = num(d.smartoffice.humedad_actual_porc);
    K.ruido = num(d.smartoffice.ruido_actual_db);
    K.sensTotal = d.smartoffice.sensores_total;
    K.sensOper = d.smartoffice.sensores_operativos;
    K.sensAlertas = d.smartoffice.alertas_activas;
    K.sensors = d.smartoffice.sensores_total;
  } else {
    K.co2 = null; K.tempC = null; K.hum = null; K.ruido = null;
    K.sensTotal = null; K.sensOper = null; K.sensAlertas = null; K.sensors = NO_DATA;
  }
  if (d.ambiente && d.ambiente.puntos && d.ambiente.puntos.some((p) => p.co2_ppm != null)) {
    T.CO2DAY = d.ambiente.puntos.slice(-24).map((p) => num(p.co2_ppm) || 0);
  } else T.CO2DAY = null;
  const sens = items(d.sensores);
  if (sens.length) {
    T.SOSENSORS = sens.map((s) => ({
      id: (s.urn || "").split(":").slice(-2).join(":") || s.id,
      n: s.nombre + (s.descripcion_ubicacion ? " · " + s.descripcion_ubicacion : ""),
      v: NO_DATA,
      st: (s.estado || "").startsWith("operat") ? "operativa" : (s.estado || "desconocido"),
      um: s.umbrales_alerta ? Object.entries(s.umbrales_alerta).map(([k2, v2]) => k2 + " " + v2).join(" · ") : NO_DATA,
      bat: s.nivel_bateria != null ? num(s.nivel_bateria) + "%" : NO_DATA,
      lat: s.frecuencia_muestreo_seg ? num(s.frecuencia_muestreo_seg / 60, 1) + " min" : NO_DATA,
    }));
    K.sensBatLow = sens.filter((s) => s.nivel_bateria != null && s.nivel_bateria < 20).length;
    if (K.sensTotal == null) { K.sensTotal = totalDe(d.sensores); K.sensors = K.sensTotal; }
  } else K.sensBatLow = null;

  /* Tótems */
  if (d.totemsUso) {
    K.totInter = d.totemsUso.interacciones_total;
    K.totSes = d.totemsUso.sesiones_unicas;
    K.totDur = num(d.totemsUso.duracion_media_seg);
    K.totSecs = d.totemsUso.secciones_top || [];
  } else { K.totInter = null; K.totSes = null; K.totDur = null; K.totSecs = []; }
  K.totDisp = d.totemsSalud ? num(d.totemsSalud.disponibilidad_media_pct, 2) : null;
  if (d.totemsSalud && d.totemsSalud.totems && d.totemsSalud.totems.length) {
    const posDemo = (T.TOTEMS || []).map((t) => [t.x, t.y]);
    T.TOTEMS = d.totemsSalud.totems.map((t, i) => ({
      id: (t.urn || "").split(":").pop().toUpperCase() || "T-" + (i + 1),
      name: t.nombre, loc: t.nombre,
      state: (t.estado || "").startsWith("operat") || t.estado === "online" ? "online" : "alerta",
      uptime: t.disponibilidad_pct != null ? num(t.disponibilidad_pct, 2) : NO_DATA,
      temp: t.temperatura_interna_media != null ? num(t.temperatura_interna_media, 1) : NO_DATA,
      tempMax: t.temperatura_interna_max != null ? num(t.temperatura_interna_max, 1) : NO_DATA,
      bright: NO_DATA, inter: NO_DATA, ctr: NO_DATA,
      lastComm: t.ultima_comunicacion ? "hace " + horasDesde(t.ultima_comunicacion) : NO_DATA,
      sai: NO_DATA, net: "conectividad " + (t.conectividad_media_pct != null ? num(t.conectividad_media_pct) + "%" : NO_DATA),
      ver: NO_DATA, langs: NO_DATA, top: [],
      x: (posDemo[i] || [640, 250])[0], y: (posDemo[i] || [640, 250])[1],
    }));
  }

  /* Incidencias y ANS */
  const incs = items(d.incidencias);
  const abiertas = incs.filter((i) => i.estado !== "resuelta" && i.estado !== "cerrada");
  T.DINC = abiertas.map((i) => ({
    id: (i.id || "").slice(0, 8), sev: i.severidad ? i.severidad[0].toUpperCase() + i.severidad.slice(1) : "—",
    t: i.titulo, asset: i.componente, open: horasDesde(i.detectada_en),
    sla: SLA_POR_SEVERIDAD[i.severidad] || "—",
    st: i.estado === "en_curso" ? "En curso" : (i.estado || "Pendiente"),
    resp: i.origen || "—",
  }));
  K.incAbiertas = d.incidencias ? abiertas.length : null;
  if (d.ans && d.ans.por_severidad && d.ans.por_severidad.length) {
    T.SLAROWS = d.ans.por_severidad.map((s) => [
      "Resolución incidencias " + s.severidad + "s",
      SLA_POR_SEVERIDAD[s.severidad] || "—",
      (s.porcentaje_cumplimiento != null ? num(s.porcentaje_cumplimiento) + "% cumplimiento" : "sin casos") +
        (s.tiempo_medio_resolucion_h != null ? " · MTTR " + num(s.tiempo_medio_resolucion_h, 1) + " h" : "") +
        " · " + s.total + " incidencias",
      s.porcentaje_cumplimiento == null || s.porcentaje_cumplimiento >= 100 ? "ok" : "warn",
    ]);
    if (K.totDisp != null) T.SLAROWS.unshift(["Disponibilidad tótems (media)", "≥ 99% mensual", K.totDisp + "%", K.totDisp >= 99 ? "ok" : "warn"]);
    if (K.chatQ != null) T.SLAROWS.push(["Uso del chatbot", "≥ 100 preguntas/mes · resolución ≥ 80%", K.chatQ + " preg. · " + (K.chatRes ?? "—") + "% autónoma", K.chatRes >= 80 ? "ok" : "warn"]);
    if (K.chatSat != null) T.SLAROWS.push(["Satisfacción de usuarios", "≥ 80% satisfechos", K.chatSat + "%", K.chatSat >= 80 ? "ok" : "warn"]);
  }

  /* CMS */
  const cont = items(d.contenidos);
  if (cont.length) {
    T.CONT = cont.map((c) => ({
      t: c.tipo ? c.tipo[0].toUpperCase() + c.tipo.slice(1) : "Contenido",
      n: c.titulo || c.nombre || "—",
      pub: NO_DATA,
      can: c.canal || "—",
      st: (c.estado || "").toLowerCase() === "publicado" ? "Publicado" : (c.estado || "—"),
      d: fechaCorta(c.actualizado_en || c.updated_at || c.creado_en || c.created_at),
    }));
  }
  K.contPub = totalDe(d.contenidos);

  /* Catálogo / informe mensual */
  K.recursos = totalDe(d.recursos);
  K.eventos = totalDe(d.eventos);
  if (d.informeMes) {
    const comp = d.informeMes.disponibilidad_por_componente || {};
    const vals = Object.values(comp).filter((v) => v != null);
    K.disp = vals.length ? num(vals.reduce((a, b) => a + b, 0) / vals.length, 2) : K.totDisp;
    K.web = d.informeMes.visitas_web_estimadas;
  } else {
    K.disp = K.totDisp;
    K.web = null;
  }

  /* Índice compuesto del gauge (media de lo disponible) */
  const componentes = [K.disp, K.totDisp, K.chatRes, K.chatSat, K.sentPos].filter((v) => v != null);
  K.indice = componentes.length ? num(componentes.reduce((a, b) => a + b, 0) / componentes.length) : null;
}

/* ---------------- render ---------------- */

function fmtV(v, suf) {
  if (v == null) return NO_DATA;
  const U = window.__U;
  return (typeof v === "number" && U ? U.fmt(v) : v) + (suf || "");
}

function renderHomeKpis() {
  const X = window.__UI2;
  const T = window.__DTI.T;
  const K = T.KPI;
  const kpis = document.getElementById("home-kpis");
  if (!X || !X.kpiCard || !kpis) return;
  const dispositivos = (K.sensTotal != null ? K.sensTotal : 0) + (T.TOTEMS ? T.TOTEMS.length : 0);
  kpis.innerHTML =
    X.kpiCard("Contrato en ejecución", "DTI <small>Exp. 18962/2025</small>", "A.1 · A.2 · A.3 · B.2 + C.1 (4 años)", "ic-navy", "totem", "UI.enterDTI()") +
    X.kpiCard("Disponibilidad del servicio", K.disp != null ? K.disp + " <small>%</small>" : NO_DATA, "SLA ≥ 99% mensual", "ic-ok", "chart", "UI.goD('slas')") +
    X.kpiCard("Dispositivos conectados", K.sensTotal != null ? String(dispositivos) : NO_DATA, (T.TOTEMS ? T.TOTEMS.length : 0) + " tótems · " + fmtV(K.sensTotal) + " sensores IoT", "ic-teal", "bolt", "UI.goD('sensores')") +
    X.kpiCard("Incidencias abiertas", fmtV(K.incAbiertas), "Matriz ANS · mantenimiento C.1", "ic-coral", "bell", "UI.goD('slas')");
}

function marcarDemo(id) {
  if (!SECCIONES_INFO.includes(id)) return;
  const cont = document.getElementById("dv-" + id);
  if (!cont || cont.querySelector(".demo-note")) return;
  cont.prepend(el("div", { className: "demo-note" },
    "ℹ Sección <b>informativa</b>: documenta el expediente y la planificación del contrato, no telemetría en tiempo real."));
}

function refrescarUI() {
  const DTI = window.__DTI;
  const UI = window.UI;
  if (!DTI || !UI || !UI.rerenderD) return;
  Object.keys(DTI.DR).forEach((id) => UI.rerenderD(id));
  renderHomeKpis();
}

/* ---------------- arranque ---------------- */

let iniciado = false;

async function arrancar() {
  if (iniciado) return;
  iniciado = true;

  /* Indicador "en vivo" + salir en la topbar (los botones cuelgan del header) */
  const ancla = document.querySelector("header .btn--dark");
  if (ancla && ancla.parentElement) {
    ancla.parentElement.insertBefore(
      el("span", { className: "live-dot", title: "Conectado a la plataforma DTI" }, "<i></i> EN VIVO"),
      ancla,
    );
    const salir = el("button", { className: "btn", type: "button", title: "Cerrar sesión" }, "Salir");
    salir.addEventListener("click", async () => { await api.logout(); location.reload(); });
    const avatar = document.querySelector("header .tbav");
    if (avatar) ancla.parentElement.insertBefore(salir, avatar);
    else ancla.parentElement.appendChild(salir);
  }

  /* Aviso de demo al entrar en secciones sin fuente real */
  const goD = window.UI && window.UI.goD;
  if (goD) {
    window.UI.goD = function (id) { goD(id); marcarDemo(id); };
  }

  const aplicarYRender = async () => {
    try {
      aplicar(await cargar());
      refrescarUI();
      const pill2 = document.getElementById("tb-pill2");
      const K = window.__DTI.T.KPI;
      if (pill2 && K.disp != null) pill2.textContent = "Plataforma disponible " + K.disp + "%";
    } catch (e) {
      console.error("panel-live: error cargando datos", e);
    }
  };
  await aplicarYRender();
  setInterval(aplicarYRender, REFRESH_MS);
}

(async function init() {
  if (tokens.access) {
    try {
      await api.me();
      arrancar();
      return;
    } catch { tokens.clear(); }
  }
  montarLogin();
})();
