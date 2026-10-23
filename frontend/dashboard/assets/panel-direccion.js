/**
 * Vista de Gobierno 2.0 · Cuadro de Mando de Dirección (perfil ejecutivo / político).
 *
 * Módulo de nivel superior, al estilo del módulo de Administración: crea su
 * propia vista `view-direccion`, una tarjeta en el lanzador (visible para quien
 * tenga el permiso `ver_resumen_municipal`) y, si el usuario es del rol
 * `direccion_gobierno`, redirige aquí tras el login.
 *
 * Cada pantalla (Resumen municipal, las 7 verticales y Recomendaciones IA) se
 * pinta a partir de `GET /direccion/panel/{modulo}`: cabecera con el hallazgo
 * principal, KPIs con tendencia y bloques (gráficos, rankings, mapas de calor,
 * medidores, mapa por núcleo, eventos, recomendaciones…). El backend calcula
 * todos los datos; aquí solo se dibujan. Los gráficos usan Chart.js (cdnjs).
 */

import { api, getCachedUser } from "./api-client.js?v=19";

let UI, U2, UI2;

const CHART_JS = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js";

/* ---------------- utilidades ---------------- */

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function tienePermiso(p) {
  const u = getCachedUser && getCachedUser();
  if (!u) return false;
  if (!Array.isArray(u.permisos)) return true; // compat
  return u.permisos.includes(p);
}
const nf = (v, d = 0) => (v == null || v === "" || Number.isNaN(Number(v)) ? "—" :
  Number(v).toLocaleString("es-ES", { minimumFractionDigits: d, maximumFractionDigits: d }));

/* Paleta del panel (tokens de frontend/dashboard/index.html) */
const COL = {
  navy: "#003B7A", blue: "#1A5FD0", teal: "#17A394", cyan: "#00A6C0", gold: "#F0B429",
  coral: "#E05A4D", violet: "#7C6BF0", sky: "#5B8DEF", ok: "#2F9E5F", green: "#3DDC7F",
  muted: "#B4BFD3", brown: "#A0673A", grid: "#EDF1F7", text: "#515D77",
};
const col = (c) => COL[c] || c || COL.navy;

/* Iconos de trazo propios (24×24) para no depender de los nombres de window.icon */
const P = {
  home: "M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z",
  turismo: "M12 3a9 9 0 0 1 9 9H3a9 9 0 0 1 9-9zm0 9v8m-3 1h6",
  bulb: "M9 18h6m-5 3h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z",
  drop: "M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z",
  trash: "M4 7h16M10 11v6m4-6v6M6 7l1 13h10l1-13M9 7V4h6v3",
  car: "M5 16h14M6 16l1.5-5.5A2 2 0 0 1 9.4 9h5.2a2 2 0 0 1 1.9 1.5L18 16v3h-2v-2H8v2H6zM8 13.5h.01M16 13.5h.01",
  cam: "M3 8h10a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H3zm12 3l6-3v8l-6-3",
  bolt: "M13 2L4 14h7l-1 8 9-12h-7z",
  ai: "M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8zM19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9z",
  euro: "M17 6.5A6.5 6.5 0 1 0 17 17.5M4 10h9M4 14h9",
  leaf: "M5 19c0-8 6-14 15-14 0 9-6 15-14 15M5 19c3-4 6-6 9-7",
  users: "M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-6 10a6 6 0 0 1 12 0M17 11a3 3 0 1 0 0-6m2 16a5 5 0 0 0-3-4.6",
  alert: "M12 4l9 16H3zM12 10v4m0 3h.01",
  clock: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zm0-13v5l3 2",
  chart: "M4 20V10m6 10V4m6 16v-7m4 7H2",
  calendar: "M4 6h16v14H4zM4 10h16M8 3v4m8-4v4",
  route: "M6 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM18 9a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM8 17h7a3 3 0 0 0 0-6H9a3 3 0 0 1 0-6h7",
  wrench: "M14.7 6.3a4 4 0 0 0-5.4 5.1L3 17.7 6.3 21l6.3-6.3a4 4 0 0 0 5.1-5.4l-2.4 2.4-2.6-.6-.6-2.6z",
  sun: "M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm0-15v2m0 16v2M4.2 4.2l1.4 1.4m12.8 12.8l1.4 1.4M2 12h2m16 0h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4",
  shield: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z",
  recycle: "M7 19H4l3-5m10 5h3l-3-5M9 5l3-2 3 2m-9 9l-2-3.5M18 10.5L16 14M12 3v4m-5 12h10",
  present: "M3 4h18v12H3zm9 12v4m-4 0h8",
  refresh: "M20 11a8 8 0 0 0-14.3-4.9L4 8m0-4v4h4M4 13a8 8 0 0 0 14.3 4.9L20 16m0 4v-4h-4",
  bell: "M6 16V11a6 6 0 1 1 12 0v5l2 2H4zm4 4h4",
  doc: "M6 3h9l4 4v14H6zM14 3v5h5M9 13h6m-6 4h6",
  gauge: "M12 14l4-4M4 18a9 9 0 1 1 16 0",
  chat: "M4 5h16v11H8l-4 4z",
  check: "M5 12l5 5 9-10",
  flag: "M5 21V4m0 0h11l-2 4 2 4H5",
};
const ic = (n, c) => '<svg viewBox="0 0 24 24" fill="none" stroke="' + (c || "currentColor") +
  '" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' + (P[n] || P.chart) + '"/></svg>';

/* ---------------- estilos de la Vista de Gobierno ---------------- */

const DIR_CSS = `
#view-direccion{--vg-ok:#3ddc7f;--vg-warn:#ffc247;--vg-err:#ff6a5c;--fd:"Nunito","Inter","Segoe UI",system-ui,sans-serif}
#view-direccion .vg{max-width:1360px;margin:0 auto;display:flex;flex-direction:column;gap:18px}
#view-direccion .vg-sub{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap}
#view-direccion .vg-crumb{font-size:11px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
#view-direccion .vg-crumb a{color:var(--muted);cursor:pointer;text-decoration:none}
#view-direccion .vg-crumb b{color:var(--navy)}
#view-direccion .vg-sub h1{font-family:var(--fd);font-weight:800;font-size:26px;margin:6px 0 4px;color:var(--ink);text-wrap:balance}
#view-direccion .vg-sub p{margin:0;color:var(--muted);max-width:76ch;font-size:13.5px}
#view-direccion .vg-act{display:flex;gap:8px;flex-wrap:wrap}
#view-direccion .vg-act .btn svg{width:15px;height:15px}
#view-direccion .vg-hero{position:relative;border-radius:20px;overflow:hidden;color:#fff;padding:24px 28px;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:24px;align-items:center;background-size:cover;background-position:center;box-shadow:0 18px 48px -18px rgba(21,40,80,.32);isolation:isolate}
#view-direccion .vg-hero::before{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(110deg,rgba(6,20,46,.92) 0%,rgba(8,28,64,.70) 50%,rgba(8,22,48,.35) 100%)}
#view-direccion .vg-hero-top{display:flex;align-items:center;gap:10px;font-size:11px;letter-spacing:.14em;text-transform:uppercase;font-weight:800;opacity:.95}
#view-direccion .vg-hero-top img{width:22px;height:28px}
#view-direccion .vg-estado{display:inline-flex;align-items:center;gap:8px;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
#view-direccion .vg-dot{width:11px;height:11px;border-radius:50%;flex:none}
#view-direccion .vg-dot--verde{background:var(--vg-ok);box-shadow:0 0 10px 2px rgba(61,220,127,.7)}
#view-direccion .vg-dot--ambar{background:var(--vg-warn);box-shadow:0 0 10px 2px rgba(255,194,71,.75)}
#view-direccion .vg-dot--rojo{background:var(--vg-err);box-shadow:0 0 10px 2px rgba(255,106,92,.8)}
#view-direccion .vg-hero h2{color:#fff;font-family:var(--fd);font-weight:900;font-size:clamp(22px,2.6vw,31px);line-height:1.15;margin:12px 0 6px;max-width:760px;text-wrap:balance;text-shadow:0 2px 14px rgba(0,0,0,.3)}
#view-direccion .vg-hero-sub{font-size:13.5px;opacity:.88;max-width:680px}
#view-direccion .vg-chips{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
#view-direccion .vg-chip{display:flex;flex-direction:column;gap:2px;padding:9px 14px;border-radius:14px;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.24);backdrop-filter:blur(8px);min-width:108px}
#view-direccion .vg-chip b{font-family:var(--fd);font-size:19px;font-weight:900;font-variant-numeric:tabular-nums}
#view-direccion .vg-chip span{font-size:10.5px;opacity:.86;letter-spacing:.03em;text-transform:uppercase}
#view-direccion .vg-ring{position:relative;width:128px;height:128px;border-radius:50%;display:grid;place-items:center}
#view-direccion .vg-ring::before{content:"";position:absolute;inset:11px;border-radius:50%;background:rgba(6,18,40,.86)}
#view-direccion .vg-ring div{position:relative;text-align:center;line-height:1.05}
#view-direccion .vg-ring b{display:block;font-family:var(--fd);font-size:30px;font-weight:900}
#view-direccion .vg-ring span{font-size:10.5px;opacity:.85;display:block;max-width:88px;margin:2px auto 0}
#view-direccion .vg-grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:16px}
#view-direccion .vg-s3{grid-column:span 3}#view-direccion .vg-s4{grid-column:span 4}#view-direccion .vg-s5{grid-column:span 5}#view-direccion .vg-s6{grid-column:span 6}#view-direccion .vg-s7{grid-column:span 7}#view-direccion .vg-s8{grid-column:span 8}#view-direccion .vg-s9{grid-column:span 9}#view-direccion .vg-s12{grid-column:span 12}
#view-direccion .vg-card{background:var(--surface,#fff);border:1px solid var(--line);border-radius:16px;box-shadow:var(--sh);padding:18px;min-width:0;display:flex;flex-direction:column;gap:12px}
#view-direccion .vg-card-h{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
#view-direccion .vg-card-t{font-weight:800;font-size:15px;color:var(--ink)}
#view-direccion .vg-card-s{font-size:12.5px;color:var(--muted);margin-top:2px}
#view-direccion .vg-card-f{font-size:11.5px;color:var(--subtle);border-top:1px dashed var(--line-2);padding-top:10px;margin-top:auto}
#view-direccion .vg-sec{display:flex;align-items:baseline;justify-content:space-between;gap:10px;flex-wrap:wrap;margin:4px 2px -6px}
#view-direccion .vg-sec h3{margin:0;font-family:var(--fd);font-size:18px;font-weight:800}
#view-direccion .vg-sec span{font-size:12.5px;color:var(--muted)}
#view-direccion .vg-tag{display:inline-flex;align-items:center;padding:2px 8px;border-radius:999px;font-size:9.5px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;white-space:nowrap;border:1px solid}
#view-direccion .vg-tag--real{color:#0A7A38;background:#e3f7ec;border-color:#bfe8cf}
#view-direccion .vg-tag--integrar{color:#9a5b00;background:#fff2dc;border-color:#f3d39b}
#view-direccion .vg-tag--estimado{color:#55617a;background:#eef1f6;border-color:#d7dde8}
#view-direccion .vg-tag--modelo{color:#1A5FD0;background:#eaf1fe;border-color:#c6d8f8}
#view-direccion .vg-ai{display:inline-flex;align-items:center;gap:4px;padding:2px 9px;border-radius:999px;font-size:11px;font-weight:800;color:#5a45c9;background:#f1ecff}
#view-direccion .vg-ai svg{width:12px;height:12px}
#view-direccion .vg-kpis{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:14px}
#view-direccion .vg-kpi{background:var(--surface,#fff);border:1px solid var(--line);border-radius:16px;box-shadow:var(--sh);padding:15px 16px 12px;display:flex;flex-direction:column;gap:4px;min-width:0;overflow:hidden}
#view-direccion .vg-kpi-l{display:flex;align-items:center;gap:8px;font-size:11.5px;font-weight:700;color:var(--muted)}
#view-direccion .vg-kpi-i{width:26px;height:26px;border-radius:8px;display:grid;place-items:center;flex:none}
#view-direccion .vg-kpi-i svg{width:15px;height:15px}
#view-direccion .vg-kpi-v{font-family:var(--fd);font-size:27px;font-weight:900;letter-spacing:-.01em;font-variant-numeric:tabular-nums;line-height:1.1;margin-top:4px;color:var(--ink);overflow-wrap:anywhere}
#view-direccion .vg-kpi-v--largo{font-size:21px}
#view-direccion .vg-kpi-v small{font-size:13px;font-weight:800;color:var(--muted);margin-left:3px}
#view-direccion .vg-kpi-d{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);flex-wrap:wrap}
#view-direccion .vg-delta{font-weight:800;font-variant-numeric:tabular-nums;padding:1px 7px;border-radius:6px}
#view-direccion .vg-delta--bueno{color:#0A7A38;background:#e3f7ec}#view-direccion .vg-delta--malo{color:#C42A30;background:#fbe4e5}#view-direccion .vg-delta--neutro{color:var(--muted);background:#eef1f6}
#view-direccion .vg-kpi-b{display:flex;align-items:flex-end;justify-content:space-between;gap:8px;margin-top:auto;padding-top:6px}
#view-direccion .vg-spark{width:96px;height:30px;flex:none}
#view-direccion .vg-chart{position:relative;width:100%;flex:1 1 auto;height:0}
#view-direccion .vg-legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--muted)}
#view-direccion .vg-legend i{display:inline-block;width:12px;height:4px;border-radius:2px;margin-right:6px;vertical-align:middle}
#view-direccion .vg-legend i.dash{background:repeating-linear-gradient(90deg,currentColor 0 4px,transparent 4px 7px)!important;height:3px}
#view-direccion .vg-rank{display:flex;flex-direction:column;gap:10px}
#view-direccion .vg-rk{display:grid;grid-template-columns:minmax(0,150px) minmax(0,1fr) auto;align-items:center;gap:10px;font-size:12.5px}
#view-direccion .vg-rk-n{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#view-direccion .vg-rk-bar{height:10px;border-radius:6px;background:#eef2f8;overflow:hidden}
#view-direccion .vg-rk-bar i{display:block;height:100%;border-radius:6px}
#view-direccion .vg-rk-v{font-weight:800;font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}
#view-direccion .vg-heat{display:grid;gap:3px;font-size:10.5px;color:var(--muted)}
#view-direccion .vg-heat .hc{height:24px;border-radius:4px}
#view-direccion .vg-heat .hl{display:flex;align-items:center;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#view-direccion .vg-heat .hh{text-align:center}
#view-direccion .vg-scale{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted);flex-wrap:wrap}
#view-direccion .vg-scale i{width:90px;height:8px;border-radius:4px;display:inline-block}
#view-direccion .vg-gauges{display:grid;grid-template-columns:repeat(auto-fit,minmax(86px,1fr));gap:10px}
#view-direccion .vg-gauge{display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center}
#view-direccion .vg-gring{width:84px;height:84px;border-radius:50%;display:grid;place-items:center;position:relative}
#view-direccion .vg-gring::before{content:"";position:absolute;inset:10px;border-radius:50%;background:#fff}
#view-direccion .vg-gring b{position:relative;font-family:var(--fd);font-weight:900;font-size:19px;font-variant-numeric:tabular-nums}
#view-direccion .vg-gauge span{font-size:12px;color:var(--muted);font-weight:600}
#view-direccion .vg-recs{display:flex;flex-direction:column;gap:12px}
#view-direccion .vg-rec{border:1px solid var(--line);border-radius:14px;padding:14px;display:flex;flex-direction:column;gap:8px;background:linear-gradient(180deg,#fff,#fbfcff)}
#view-direccion .vg-rec-h{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
#view-direccion .vg-prio{font-size:10px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;padding:3px 8px;border-radius:6px}
#view-direccion .vg-prio--critica{background:#fbe4e5;color:#C42A30}#view-direccion .vg-prio--alta{background:#fdf1d8;color:#8A5E00}#view-direccion .vg-prio--media{background:#eaf1fe;color:#1A5FD0}#view-direccion .vg-prio--informativa{background:#eef1f6;color:#55617a}
#view-direccion .vg-rec-t{font-weight:800;font-size:14px;color:var(--ink)}
#view-direccion .vg-rec p{margin:0;font-size:12.8px;color:var(--muted)}
#view-direccion .vg-rec-m{font-size:12.5px;color:var(--ink)}
#view-direccion .vg-rec-m b{color:#0A7A38}
#view-direccion .vg-rec-a{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
#view-direccion .vg-rec-st{font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;padding:3px 8px;border-radius:6px;background:#eef1f6;color:#55617a}
#view-direccion .vg-rec-st--aceptada,#view-direccion .vg-rec-st--ejecutada{background:#e3f7ec;color:#0A7A38}
#view-direccion .vg-rec-st--descartada{background:#fbe4e5;color:#C42A30}
#view-direccion .vg-rec-st--en_revision{background:#fdf1d8;color:#8A5E00}
#view-direccion .vg-rec input{flex:1;min-width:160px;border:1.5px solid var(--line);border-radius:8px;padding:6px 9px;font-size:12.5px;font-family:inherit}
#view-direccion .vg-evs{display:flex;flex-direction:column}
#view-direccion .vg-ev{display:flex;gap:12px;align-items:center;padding:9px 0;border-bottom:1px dashed var(--line-2)}
#view-direccion .vg-ev:last-child{border-bottom:0}
#view-direccion .vg-ev-f{min-width:48px;text-align:center;border-radius:10px;padding:5px 4px;background:#eaf1fe;color:var(--navy);font-weight:900;line-height:1.05;font-family:var(--fd);font-size:17px}
#view-direccion .vg-ev-f small{display:block;font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;font-family:var(--ff)}
#view-direccion .vg-ev-t{font-weight:700;font-size:13px}
#view-direccion .vg-ev-s{font-size:12px;color:var(--muted)}
#view-direccion .vg-ev-r{margin-left:auto;text-align:right;font-size:12px;color:var(--muted);white-space:nowrap}
#view-direccion .vg-tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px}
#view-direccion .vg-tile{position:relative;min-height:188px;border:0;border-radius:16px;overflow:hidden;color:#fff;padding:15px;display:flex;flex-direction:column;justify-content:flex-end;align-items:stretch;gap:2px;cursor:pointer;text-align:left;font-family:inherit;background-size:cover;background-position:center;transition:transform .18s ease,box-shadow .18s ease;isolation:isolate}
#view-direccion .vg-tile::before{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(180deg,rgba(9,24,52,.10) 20%,rgba(7,17,38,.88) 100%)}
#view-direccion .vg-tile:hover{transform:translateY(-3px);box-shadow:0 14px 30px rgba(10,25,50,.32)}
#view-direccion .vg-tile h4{margin:6px 0 2px;font-family:var(--fd);font-size:19px;font-weight:900;color:#fff;text-shadow:0 1px 8px rgba(0,0,0,.45)}
#view-direccion .vg-tile-f{font-size:12px;opacity:.92}
#view-direccion .vg-tile-b{display:flex;align-items:flex-end;justify-content:space-between;gap:8px;margin-top:8px}
#view-direccion .vg-tile-c{font-size:11px;opacity:.85}
#view-direccion .vg-tile-c b{display:block;font-family:var(--fd);font-size:16px;font-weight:900}
#view-direccion .vg-srcs{display:flex;flex-wrap:wrap;gap:8px}
#view-direccion .vg-src{display:flex;align-items:center;gap:8px;padding:7px 11px;border-radius:10px;border:1px solid var(--line);background:#fbfcfe;font-size:12px;font-weight:600}
#view-direccion .vg-pregs{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:6px;font-size:13px}
#view-direccion .vg-mini{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
#view-direccion .vg-mini div{background:var(--bg);border-radius:12px;padding:10px 12px;min-width:0}
#view-direccion .vg-mini b{display:block;font-family:var(--fd);font-weight:900;font-size:18px;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
#view-direccion .vg-mini span{font-size:11.5px;color:var(--muted)}
#view-direccion .vg-funnel{display:flex;flex-direction:column;gap:8px}
#view-direccion .vg-fn{display:flex;align-items:center;gap:12px}
#view-direccion .vg-fn-b{height:42px;border-radius:10px;display:flex;align-items:center;padding:0 14px;color:#fff;font-weight:800;font-family:var(--fd);font-size:18px;min-width:56px}
#view-direccion .vg-fn-l{font-size:12.5px;color:var(--muted)}
#view-direccion .vg-fn-l b{display:block;color:var(--ink);font-size:13px}
#view-direccion .vg-pend{display:flex;gap:12px;align-items:flex-start;background:repeating-linear-gradient(135deg,#fbfcfe 0 10px,#f4f7fc 10px 20px);border:1px dashed var(--line-2);border-radius:12px;padding:14px;color:var(--muted);font-size:13px}
#view-direccion .vg-pend svg{width:22px;height:22px;flex:none;color:#C77A12}
#view-direccion .vg-filtros{display:flex;gap:8px;flex-wrap:wrap}
#view-direccion .vg-fbtn{border:1px solid var(--line-2);background:#fff;border-radius:999px;padding:6px 12px;font-size:12px;font-weight:700;color:var(--muted);cursor:pointer;font-family:inherit}
#view-direccion .vg-fbtn.on{background:var(--navy);border-color:var(--navy);color:#fff}
#view-direccion .vg-mapa svg{width:100%;height:auto;max-height:360px;display:block}
#view-direccion .vg-vacio{color:var(--muted);text-align:center;padding:26px 0;font-size:13px}
#view-direccion .vg-txt{margin:0;font-size:13.5px;line-height:1.6;color:var(--ink)}
@media (max-width:1320px){#view-direccion .vg-kpis{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (max-width:1180px){#view-direccion .vg-s3{grid-column:span 6}#view-direccion .vg-s4,#view-direccion .vg-s5,#view-direccion .vg-s6,#view-direccion .vg-s7,#view-direccion .vg-s8,#view-direccion .vg-s9{grid-column:span 12}}
@media (max-width:640px){#view-direccion .vg-hero{grid-template-columns:1fr;padding:20px}#view-direccion .vg-s3{grid-column:span 12}#view-direccion .vg-ring{width:104px;height:104px}#view-direccion .vg-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}#view-direccion .vg-kpi-v{font-size:22px}#view-direccion .vg-spark{width:70px}#view-direccion .vg-rk{grid-template-columns:minmax(0,100px) minmax(0,1fr) auto}}
@media (prefers-reduced-motion:reduce){#view-direccion .vg-tile{transition:none}}
`;

function inyectarEstilos() {
  if (document.getElementById("dir-css")) return;
  if (!document.getElementById("dir-fuente")) {
    const l = document.createElement("link");
    l.id = "dir-fuente";
    l.rel = "stylesheet";
    l.href = "https://fonts.googleapis.com/css2?family=Nunito:wght@800;900&display=swap";
    document.head.appendChild(l);
  }
  const st = document.createElement("style");
  st.id = "dir-css";
  st.textContent = DIR_CSS;
  document.head.appendChild(st);
}

/* ---------------- Chart.js bajo demanda ---------------- */

let _chartPromise = null;
function cargarChart() {
  if (window.Chart) return Promise.resolve(window.Chart);
  if (!_chartPromise) {
    _chartPromise = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = CHART_JS;
      s.onload = () => resolve(window.Chart);
      s.onerror = () => { _chartPromise = null; reject(new Error("No se pudo cargar la librería de gráficos")); };
      document.head.appendChild(s);
    });
  }
  return _chartPromise;
}

/* ---------------- piezas ---------------- */

const TAG_TXT = { real: "Real hoy", integrar: "Al integrar", estimado: "Estimado", modelo: "Modelo predictivo" };
const tag = (t) => (t ? '<span class="vg-tag vg-tag--' + t + '">' + TAG_TXT[t] + "</span>" : "");
const FRASE = { verde: "Funciona con normalidad", ambar: "Necesita seguimiento", rojo: "Requiere una decisión" };
const ESTADO_REC = { pendiente: "Pendiente", en_revision: "En revisión", aceptada: "Aceptada", descartada: "Descartada", ejecutada: "Ejecutada" };

/* Fondos de cabecera y tiles: foto del territorio o degradado temático. */
const FONDO = {
  hero: "url('../shared/cabo-de-gata-hero.jpg')",
  turismo: "url('../shared/tiles/cabo.jpg')",
  agua: "url('../shared/tiles/playas.jpg')",
  movilidad: "url('../shared/tiles/rutas.jpg')",
  energia: "url('../shared/tiles/naturaleza.jpg')",
  alumbrado: "radial-gradient(circle at 82% 18%,rgba(255,199,90,.55),transparent 50%),linear-gradient(150deg,#0f2145,#2f4f8f)",
  residuos: "radial-gradient(circle at 85% 10%,rgba(120,220,170,.35),transparent 55%),linear-gradient(150deg,#0b3328,#2e7d5b)",
  seguridad: "radial-gradient(circle at 80% 20%,rgba(120,150,230,.35),transparent 55%),linear-gradient(150deg,#141c2e,#46587e)",
  recomendaciones: "radial-gradient(circle at 85% 15%,rgba(160,140,255,.45),transparent 55%),linear-gradient(150deg,#16163f,#3a3d8f)",
};
const COLOR_SPARK_TILE = { verde: "#7fe0b0", ambar: "#ffd27a", rojo: "#ff9d92" };

function spark(data, color, w = 96, h = 30) {
  const vals = (data || []).filter((v) => v != null);
  if (vals.length < 2) return "";
  const mn = Math.min(...vals), mx = Math.max(...vals), rg = mx - mn || 1, pad = 3;
  const X = (i) => pad + (i * (w - 2 * pad)) / (vals.length - 1);
  const Y = (v) => h - pad - ((v - mn) / rg) * (h - 2 * pad);
  const pts = vals.map((v, i) => [X(i), Y(v)]);
  const line = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
  const id = "sp" + Math.random().toString(36).slice(2, 8);
  const c = col(color), last = pts[pts.length - 1];
  return '<svg class="vg-spark" viewBox="0 0 ' + w + " " + h + '" aria-hidden="true"><defs><linearGradient id="' + id +
    '" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="' + c + '" stop-opacity=".28"/><stop offset="1" stop-color="' + c +
    '" stop-opacity="0"/></linearGradient></defs><path d="' + line + " L" + X(vals.length - 1) + " " + h + " L" + X(0) + " " + h +
    ' Z" fill="url(#' + id + ')"/><path d="' + line + '" fill="none" stroke="' + c +
    '" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/><circle cx="' + last[0] + '" cy="' + last[1] + '" r="2.8" fill="' + c + '"/></svg>';
}

function hero(h) {
  const ring = h.anillo
    ? '<div class="vg-ring" style="background:conic-gradient(' + col(h.anillo.color) + " " + h.anillo.pct +
      '%,rgba(255,255,255,.16) 0)"><div><b>' + esc(h.anillo.valor) + "</b><span>" + esc(h.anillo.etiqueta) + "</span></div></div>"
    : "";
  const top = h.superior
    ? '<img src="../shared/escudo-nijar.svg" alt="">' + esc(h.superior)
    : (h.estado ? '<span class="vg-estado"><span class="vg-dot vg-dot--' + h.estado + '"></span>' + esc(h.frase || FRASE[h.estado]) + "</span>" : "");
  return '<section class="vg-hero" style="background-image:' + (FONDO[h.fondo] || FONDO.hero) + '">' +
    "<div><div class=\"vg-hero-top\">" + top + "</div><h2>" + esc(h.titulo) + '</h2><div class="vg-hero-sub">' + esc(h.subtitulo) + "</div>" +
    '<div class="vg-chips" data-chips>' + (h.chips || []).map((c) => '<div class="vg-chip"><b>' + esc(c.valor) + "</b><span>" + esc(c.etiqueta) + "</span></div>").join("") +
    "</div></div>" + ring + "</section>";
}

function kpi(k) {
  const c = col(k.color);
  return '<div class="vg-kpi"><div class="vg-kpi-l"><span class="vg-kpi-i" style="background:' + c + "1a;color:" + c + '">' + ic(k.icono, c) + "</span>" + esc(k.etiqueta) + "</div>" +
    '<div class="vg-kpi-v' + (String(k.valor).length + String(k.unidad || "").length > 9 ? " vg-kpi-v--largo" : "") + '"' + (k.color_valor ? ' style="color:' + col(k.color_valor) + '"' : "") + ">" + esc(k.valor) + (k.unidad ? "<small>" + esc(k.unidad) + "</small>" : "") + "</div>" +
    '<div class="vg-kpi-d">' + (k.delta ? '<span class="vg-delta vg-delta--' + k.sentido + '">' + esc(k.delta) + "</span>" : "") + "<span>" + esc(k.detalle || "") + "</span></div>" +
    '<div class="vg-kpi-b">' + tag(k.origen) + spark(k.serie, k.color) + "</div></div>";
}

/* ---------------- gráficos ---------------- */

function configGrafico(b) {
  const fmt = (v) => nf(v, b.decimales || 0);
  const horizontal = b.tipo === "barras_h";
  const unidad = b.unidad ? " " + b.unidad : "";
  if (b.tipo === "donut") {
    const s = b.series[0] || { valores: [] };
    return {
      type: "doughnut",
      data: { labels: b.etiquetas, datasets: [{ data: s.valores, backgroundColor: (s.colores || []).map(col), borderWidth: 3, borderColor: "#fff", hoverOffset: 6 }] },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: "68%",
        plugins: { legend: { display: false }, tooltip: { backgroundColor: "#0f1d38", callbacks: { label: (c) => " " + c.label + ": " + fmt(c.parsed) + unidad } } },
      },
    };
  }
  const datasets = b.series.map((s) => {
    const c = col(s.color);
    if (b.tipo === "linea") {
      const d = {
        label: s.nombre, data: s.valores, borderColor: c, backgroundColor: c, borderWidth: s.rol === "dato" ? 2.5 : 2.2,
        borderDash: s.discontinua ? [6, 5] : [], tension: 0.35, spanGaps: false, fill: false,
        pointRadius: s.rol === "prevision" ? 3 : (s.valores.length <= 14 ? 3 : 0), pointHoverRadius: 5,
        pointBackgroundColor: s.rol === "prevision" ? "#fff" : c, pointBorderColor: c, pointBorderWidth: 2, _rol: s.rol,
      };
      if (s.relleno) {
        d.fill = "origin";
        d.backgroundColor = (ctx) => {
          const a = ctx.chart.chartArea;
          if (!a) return c + "33";
          const g = ctx.chart.ctx.createLinearGradient(0, a.top, 0, a.bottom);
          g.addColorStop(0, c + "40"); g.addColorStop(1, c + "02");
          return g;
        };
      }
      if (s.rol === "banda_inf") Object.assign(d, { borderColor: "transparent", pointRadius: 0, pointHoverRadius: 0 });
      if (s.rol === "banda_sup") Object.assign(d, { borderColor: "transparent", pointRadius: 0, pointHoverRadius: 0, fill: "-1", backgroundColor: c + "26" });
      return d;
    }
    return {
      label: s.nombre, data: s.valores, backgroundColor: s.colores ? s.colores.map(col) : c,
      borderRadius: b.apilado ? 3 : 6, borderSkipped: false, maxBarThickness: horizontal ? 22 : 30,
      categoryPercentage: 0.72, barPercentage: 0.9,
    };
  });
  const ticks = { color: COL.text, font: { family: "Inter, system-ui, sans-serif", size: 11 } };
  const tipoChart = b.tipo === "linea" ? "line" : "bar";
  return {
    type: tipoChart,
    data: { labels: b.etiquetas, datasets },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 600 },
      indexAxis: horizontal ? "y" : "x",
      interaction: { mode: horizontal ? "nearest" : "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0f1d38", padding: 10, cornerRadius: 8, boxPadding: 4,
          filter: (it) => it.raw != null && it.dataset._rol !== "banda_inf" && it.dataset._rol !== "banda_sup",
          callbacks: { label: (c) => " " + c.dataset.label + ": " + fmt(c.parsed[horizontal ? "x" : "y"]) + unidad },
        },
      },
      scales: {
        x: {
          stacked: !!b.apilado, border: { display: false }, grid: { display: horizontal, color: COL.grid },
          ticks: horizontal ? { ...ticks, callback: (v) => fmt(v), precision: b.decimales || 0 } : { ...ticks, maxRotation: 0, autoSkipPadding: 8 },
          min: horizontal ? b.minimo ?? undefined : undefined, max: horizontal ? b.maximo ?? undefined : undefined,
        },
        y: {
          stacked: !!b.apilado, border: { display: false }, grid: { display: !horizontal, color: COL.grid },
          ticks: horizontal ? ticks : { ...ticks, callback: (v) => fmt(v), maxTicksLimit: 6, precision: b.decimales || 0 },
          min: horizontal ? undefined : b.minimo ?? undefined, max: horizontal ? undefined : b.maximo ?? undefined,
          beginAtZero: b.minimo == null && b.tipo !== "linea",
        },
      },
    },
  };
}

function leyenda(b) {
  if (b.tipo === "donut" || b.tipo === "barras_h" && b.items && b.items.length) {
    const items = b.tipo === "donut"
      ? b.etiquetas.map((n, i) => [n, (b.series[0].colores || [])[i], false])
      : b.items.map((x) => [x.nombre, x.color, false]);
    return '<div class="vg-legend">' + items.map(([n, c, d]) => '<span style="color:' + col(c) + '"><i class="' + (d ? "dash" : "") + '" style="background:' + col(c) + '"></i><span style="color:var(--muted)">' + esc(n) + "</span></span>").join("") + "</div>";
  }
  const series = b.series.filter((s) => s.rol !== "banda_inf" && !s.colores);
  if (series.length < 2 && !series.some((s) => s.rol === "prevision")) return "";
  return '<div class="vg-legend">' + series.map((s) =>
    '<span style="color:' + col(s.color) + '"><i class="' + (s.discontinua ? "dash" : "") + '" style="background:' + col(s.color) + (s.rol === "banda_sup" ? ";opacity:.35;height:8px" : "") + '"></i><span style="color:var(--muted)">' + esc(s.nombre) + "</span></span>").join("") + "</div>";
}

/* ---------------- partes de tarjeta ---------------- */

let _graficos = [];

const PARTES = {
  grafico(b) {
    const id = "vgc" + Math.random().toString(36).slice(2, 9);
    _graficos.push({ id, b });
    return leyenda(b) + '<div class="vg-chart" style="min-height:' + (b.alto || 260) + 'px"><canvas id="' + id + '" role="img" aria-label="' + esc(b.titulo || "") + '"></canvas></div>';
  },
  ranking(b) {
    if (!b.items.length) return '<div class="vg-vacio">Sin datos.</div>';
    const mx = b.maximo || Math.max(...b.items.map((x) => x.valor), 1);
    return '<div class="vg-rank">' + b.items.map((x) =>
      '<div class="vg-rk"><span class="vg-rk-n" title="' + esc(x.nombre) + '">' + esc(x.nombre) + '</span><span class="vg-rk-bar"><i style="width:' +
      Math.max(2, (x.valor / mx) * 100) + "%;background:" + col(x.color) + '"></i></span><span class="vg-rk-v">' + esc(x.texto ?? nf(x.valor)) + "</span></div>").join("") + "</div>";
  },
  calor(b) {
    const flat = b.matriz.flat();
    const mx = b.maximo ?? Math.max(...flat, 1), mn = b.minimo ?? 0;
    const color = (v) => {
      const t = Math.max(0, Math.min(1, (v - mn) / ((mx - mn) || 1)));
      if (b.umbral != null && v >= b.umbral) return "rgba(224,90,77," + (0.55 + 0.45 * t).toFixed(2) + ")";
      return "rgba(0,59,122," + (0.07 + 0.78 * t).toFixed(2) + ")";
    };
    const n = b.columnas.length;
    let h = '<div style="overflow-x:auto"><div class="vg-heat" style="grid-template-columns:110px repeat(' + n + ",minmax(16px,1fr));min-width:" + (110 + n * 20) + 'px"><span></span>' +
      b.columnas.map((c) => '<span class="hh">' + esc(c) + "</span>").join("");
    b.filas.forEach((f, i) => {
      h += '<span class="hl" title="' + esc(f) + '">' + esc(f) + "</span>" + (b.matriz[i] || []).map((v, j) =>
        '<span class="hc" style="background:' + color(v) + '" title="' + esc(f) + " · " + esc(b.columnas[j]) + ": " + nf(v, 1) + (b.unidad ? " " + esc(b.unidad) : "") + '"></span>').join("");
    });
    h += "</div></div>";
    if (b.escala && b.escala.length) {
      h += '<div class="vg-scale"><span>' + esc(b.escala[0]) + '</span><i style="background:linear-gradient(90deg,rgba(0,59,122,.07),rgba(0,59,122,.85))"></i><span>' + esc(b.escala[1]) + "</span>" +
        (b.umbral != null && b.escala[2] ? '<i style="width:14px;background:#E05A4D"></i><span>' + esc(b.escala[2]) + "</span>" : "") + "</div>";
    }
    return h;
  },
  medidores(b) {
    return '<div class="vg-gauges">' + b.items.map((x) => '<div class="vg-gauge"><div class="vg-gring" style="background:conic-gradient(' + col(x.color) + " " + x.valor +
      '%,#edf1f7 0)"><b>' + esc(x.texto ?? nf(x.valor) + "%") + "</b></div><span>" + esc(x.nombre) + "</span></div>").join("") + "</div>";
  },
  eventos(b) {
    if (!b.items.length) return '<div class="vg-vacio">Sin eventos próximos publicados.</div>';
    return '<div class="vg-evs">' + b.items.map((e) =>
      '<div class="vg-ev"><div class="vg-ev-f">' + esc(e.dia) + "<small>" + esc(e.mes) + '</small></div><div><div class="vg-ev-t">' + esc(e.titulo) +
      '</div><div class="vg-ev-s">' + esc(e.detalle || "") + '</div></div><div class="vg-ev-r">' +
      (e.prioridad ? '<span class="vg-prio vg-prio--' + e.prioridad + '">' + esc(e.derecha_txt || "") + "</span>" : esc(e.derecha || "")) + "</div></div>").join("") + "</div>";
  },
  mini(b) {
    return '<div class="vg-mini">' + b.items.map((x) => "<div><b>" + esc(x.valor) + "</b><span>" + esc(x.texto) + "</span></div>").join("") + "</div>";
  },
  mapa(b) {
    // Proyección esquemática del término municipal (lon/lat → svg)
    const X = (lon) => 20 + ((lon + 2.32) / 0.44) * 360, Y = (lat) => 14 + ((37.07 - lat) / 0.37) * 300;
    const contorno = [[-2.31, 37.0], [-2.2, 37.05], [-2.08, 37.06], [-1.97, 37.0], [-1.91, 36.95], [-1.96, 36.9], [-2.02, 36.84], [-2.07, 36.78], [-2.12, 36.72], [-2.19, 36.75], [-2.22, 36.82], [-2.27, 36.88], [-2.31, 36.94]];
    const d = contorno.map(([lo, la], i) => (i ? "L" : "M") + X(lo).toFixed(0) + " " + Y(la).toFixed(0)).join(" ") + "Z";
    const colE = { verde: "#2F9E5F", ambar: "#E0A21F", rojo: "#E05A4D" };
    // Colocación de etiquetas sin solapes: se prueban posiciones alrededor del punto.
    const ocupadas = [];
    const choca = (r) => ocupadas.some((o) => r.x1 < o.x2 && r.x2 > o.x1 && r.y1 < o.y2 && r.y2 > o.y1);
    const validos = b.items.filter((q) => q.lat != null && q.lon != null && !Number.isNaN(parseFloat(q.lon)));
    validos.forEach((q) => { const x = X(parseFloat(q.lon)), y = Y(parseFloat(q.lat)); ocupadas.push({ x1: x - 9, x2: x + 9, y1: y - 9, y2: y + 9 }); });
    const pts = validos.map((q) => {
      const x = X(parseFloat(q.lon)), y = Y(parseFloat(q.lat)), r = q.estado === "rojo" ? 9 : 7;
      const ancho = Math.max(String(q.nombre).length * 6.6, String(q.texto || "").length * 5.6) + 4;
      const opciones = [[1, 0], [-1, 0], [1, 16], [-1, 16], [1, -16], [-1, -16], [1, 30], [-1, 30], [1, -30], [-1, -30]];
      let lx = x + r + 5, dy = 0, anchor = "start", libre = false;
      for (const [lado, desp] of opciones) {
        const cx = lado > 0 ? x + r + 5 : x - r - 5 - ancho;
        const caja = { x1: cx, x2: cx + ancho, y1: y + desp - 11, y2: y + desp + (q.texto ? 15 : 4) };
        if (caja.x1 < 4 || caja.x2 > 466 || caja.y1 < 36 || caja.y2 > 336) continue;
        if (!choca(caja)) { ocupadas.push(caja); lx = lado > 0 ? x + r + 5 : x - r - 5; anchor = lado > 0 ? "start" : "end"; dy = desp; libre = true; break; }
      }
      return '<g><circle cx="' + x + '" cy="' + y + '" r="' + (r + 7) + '" fill="' + colE[q.estado] + '" opacity=".16"/><circle cx="' + x + '" cy="' + y + '" r="' + r + '" fill="' + colE[q.estado] +
        '" stroke="#fff" stroke-width="2"><title>' + esc(q.nombre) + ": " + esc(q.texto || "") + '</title></circle>' + (!libre ? "</g>" : '<text x="' + lx + '" y="' + (y + dy - 1) + '" text-anchor="' + anchor +
        '" font-size="11.5" font-weight="700" fill="#16233D">' + esc(q.nombre) + "</text>" +
        (q.texto ? '<text x="' + lx + '" y="' + (y + dy + 12) + '" text-anchor="' + anchor + '" font-size="10.5" fill="#515D77">' + esc(q.texto) + "</text>" : "") + "</g>");
    }).join("");
    return '<div class="vg-mapa"><svg viewBox="0 0 470 340" role="img" aria-label="' + esc(b.titulo || "Mapa del término municipal") + '">' +
      '<defs><linearGradient id="vg-mar" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#e7f3fb"/><stop offset="1" stop-color="#cfe6f6"/></linearGradient></defs>' +
      '<rect x="0" y="0" width="470" height="340" rx="14" fill="url(#vg-mar)"/><path d="' + d + '" fill="#f7f4ec" stroke="#c9bfa6" stroke-width="1.2"/>' +
      '<text x="370" y="320" font-size="11" fill="#5b88b5" font-style="italic">Mar Mediterráneo</text>' +
      '<text x="40" y="30" font-size="10.5" fill="#8a7d5e">Término municipal de Níjar · esquemático</text>' + pts + "</svg></div>";
  },
  embudo(b) {
    const mx = Math.max(...b.items.map((x) => x.valor), 1);
    return '<div class="vg-funnel">' + b.items.map((x) => '<div class="vg-fn"><div class="vg-fn-b" style="width:' + Math.max(14, (x.valor / mx) * 70) + "%;background:" + col(x.color) + '">' +
      nf(x.valor) + '</div><div class="vg-fn-l"><b>' + esc(x.nombre) + "</b>" + esc(x.texto || "") + "</div></div>").join("") + "</div>";
  },
  fuentes(b) {
    return '<div class="vg-srcs">' + b.items.map((x) => '<span class="vg-src">' + esc(x.nombre) + " " + tag(x.origen) + "</span>").join("") + "</div>";
  },
  preguntas(b) { return '<ul class="vg-pregs">' + b.items.map((x) => "<li>" + esc(x.texto) + "</li>").join("") + "</ul>"; },
  pendiente(b) { return '<div class="vg-pend">' + ic("clock") + "<div>" + esc(b.texto) + "</div></div>"; },
};

function cuerpoBloque(b) {
  switch (b.tipo) {
    case "linea": case "barras": case "barras_h": return b.series.length ? PARTES.grafico(b) : '<div class="vg-vacio">Sin histórico suficiente.</div>';
    case "donut": {
      let h = PARTES.grafico(b);
      if (b.items && b.items.length && b.items[0].nombre) h += PARTES.ranking({ ...b, items: b.items, maximo: Math.max(...b.items.map((x) => x.valor), 1) });
      else if (b.items && b.items.length) h += PARTES.mini(b);
      return h;
    }
    case "linea_mini": return "";
    case "ranking": return PARTES.ranking(b);
    case "calor": return PARTES.calor(b);
    case "medidores": return PARTES.medidores(b);
    case "eventos": return PARTES.eventos(b);
    case "mini": return PARTES.mini(b);
    case "mapa": return PARTES.mapa(b);
    case "embudo": return PARTES.embudo(b);
    case "fuentes": return PARTES.fuentes(b);
    case "preguntas": return PARTES.preguntas(b);
    case "pendiente": return PARTES.pendiente(b);
    case "texto": {
      let h = '<p class="vg-txt">' + esc(b.texto) + "</p>";
      if (b.items && b.items.length) h += PARTES.mini(b);
      if (b.series && b.series.length && b.series[0].valores.length) h += PARTES.grafico({ ...b, tipo: "donut", alto: 150 });
      return h;
    }
    case "recomendaciones": return '<div class="vg-recs" data-recs="' + esc(b.area || "") + '" data-limite="' + (b.limite || "") + '"><div class="vg-vacio">Cargando…</div></div>';
    case "vivo": return '<div data-vivo>' + PARTES.medidores({ items: b.items.map((x) => ({ nombre: x.medidor === "parkings" ? "Parkings" : "Contenedores", valor: Math.round(x.valor), color: x.medidor === "parkings" ? "gold" : "navy" })) }) + "</div>";
    default: return "";
  }
}

function tarjeta(b) {
  if (b.tipo === "servicios") return "";
  // Las líneas con "items" llevan dos destacados debajo del gráfico.
  const extra = b.tipo === "linea" && b.items && b.items.length ? PARTES.mini({ items: b.items }) : "";
  const head = b.titulo ? '<div class="vg-card-h"><div><div class="vg-card-t">' + esc(b.titulo) +
    (b.tipo === "recomendaciones" ? ' <span class="vg-ai">' + ic("ai") + " IA</span>" : "") + "</div>" +
    (b.subtitulo ? '<div class="vg-card-s">' + esc(b.subtitulo) + "</div>" : "") + "</div>" + tag(b.origen) + "</div>" : "";
  return '<section class="vg-card vg-s' + (b.ancho || 12) + '">' + head + cuerpoBloque(b) + extra + (b.pie ? '<div class="vg-card-f">' + esc(b.pie) + "</div>" : "") + "</section>";
}

function servicios(b) {
  return '<div class="vg-sec"><h3>' + esc(b.titulo) + "</h3><span>" + esc(b.subtitulo || "") + '</span></div><div class="vg-tiles">' +
    b.items.map((t) => '<button class="vg-tile" type="button" style="background-image:' + (FONDO[t.id] || FONDO.hero) + '" onclick="UI.goDir(\'' + esc(t.id) + "')\">" +
      '<span class="vg-estado"><span class="vg-dot vg-dot--' + t.estado + '"></span>' + esc(t.frase) + "</span><h4>" + esc(t.nombre) +
      '</h4><span class="vg-tile-f">' + esc(t.indicador) + '</span><div class="vg-tile-b"><span class="vg-tile-c"><b>' + esc(t.valor) + "</b>" + esc(t.valor_etiqueta) +
      "</span>" + spark(t.serie, COLOR_SPARK_TILE[t.estado], 90, 28) + "</div></button>").join("") + "</div>";
}

/* ---------------- recomendaciones (datos de /direccion/recomendaciones) ---------------- */

let _recs = null;
async function datosRecs(force) {
  if (force || !_recs) _recs = await api.getRecomendacionesDireccion().catch(() => null);
  return _recs;
}
function invalidarRecs() { _recs = null; }

function tarjetaRec(r, completa) {
  return '<div class="vg-rec" data-clave="' + esc(r.clave) + '" data-area="' + esc(r.area) + '">' +
    '<div class="vg-rec-h"><span class="vg-prio vg-prio--' + r.prioridad + '">' + esc(r.prioridad) + '</span><span class="vg-tag vg-tag--estimado">' + esc(r.area) +
    '</span><span class="vg-ai">' + ic("ai") + ' IA</span><span class="vg-rec-st vg-rec-st--' + r.estado + '" data-badge>' + esc(ESTADO_REC[r.estado] || r.estado) + "</span></div>" +
    '<div class="vg-rec-t">' + esc(r.titulo) + "</div><p>" + esc(r.justificacion) + "</p>" +
    '<div class="vg-rec-m"><b>Acción:</b> ' + esc(r.accion) + "</div>" +
    '<div class="vg-rec-m" style="color:var(--muted)">Impacto: ' + esc(r.impacto) + "</div>" +
    '<div class="vg-rec-a">' +
    (tienePermiso("ver_recomendaciones_ia")
      ? '<button class="btn btn--sm btn--pri" type="button" data-estado="aceptada">Aceptar</button>' +
        '<button class="btn btn--sm" type="button" data-estado="en_revision">En revisión</button>' +
        '<button class="btn btn--sm" type="button" data-estado="descartada">Descartar</button>' +
        (completa ? '<button class="btn btn--sm" type="button" data-estado="ejecutada">Ejecutada</button>' +
          '<input data-coment placeholder="Comentario de dirección…" value="' + esc(r.comentario || "") + '" aria-label="Comentario de dirección">' : "")
      : "") + "</div></div>";
}

function enlazarRecs(cont) {
  cont.querySelectorAll(".vg-rec").forEach((card) => {
    card.querySelectorAll("[data-estado]").forEach((btn) => {
      btn.onclick = async () => {
        const estado = btn.getAttribute("data-estado");
        const ci = card.querySelector("[data-coment]");
        const payload = { estado };
        if (ci) payload.comentario = ci.value.trim() || null;
        try {
          await api.actualizarRecomendacion(card.getAttribute("data-clave"), payload);
          const bd = card.querySelector("[data-badge]");
          bd.textContent = ESTADO_REC[estado];
          bd.className = "vg-rec-st vg-rec-st--" + estado;
          invalidarRecs();
          rendered.recomendaciones = false;
          UI.toast("Recomendación marcada como " + ESTADO_REC[estado].toLowerCase());
        } catch (e) { UI.toast("Error: " + (e && e.message || e)); }
      };
    });
  });
}

async function pintarRecs(el, completa) {
  const conts = el.querySelectorAll("[data-recs]");
  if (!conts.length) return;
  const recs = await datosRecs();
  const orden = { critica: 0, alta: 1, media: 2, informativa: 3 };
  conts.forEach((c) => {
    if (!recs) { c.innerHTML = '<div class="vg-vacio">Tu rol no tiene acceso a las recomendaciones.</div>'; return; }
    const area = (c.getAttribute("data-recs") || "").toLowerCase();
    const lim = parseInt(c.getAttribute("data-limite"), 10);
    let lista = recs.filter((r) => !area || (r.area || "").toLowerCase().includes(area));
    if (!area) lista = lista.filter((r) => completa || r.estado === "pendiente" || r.estado === "en_revision");
    lista = lista.slice().sort((a, b) => (orden[a.prioridad] ?? 9) - (orden[b.prioridad] ?? 9));
    if (lim) lista = lista.slice(0, lim);
    c.innerHTML = lista.length ? lista.map((r) => tarjetaRec(r, completa)).join("")
      : '<div class="vg-pend">' + ic("check") + "<div>" + (area ? "Sin recomendaciones activas para esta área: sus indicadores están dentro de lo esperado." : "No hay decisiones pendientes.") + "</div></div>";
    enlazarRecs(c);
  });
}

/* ---------------- datos en vivo (meteo, Parque, banderas) ---------------- */

async function pintarVivo(el) {
  const caja = el.querySelector("[data-vivo]");
  const chips = el.querySelector("[data-chips]");
  const [meteo, aforo, banderas, aire] = await Promise.all([
    api.get("/gemelo/meteo").catch(() => null),
    api.get("/gemelo/parque/aforo").catch(() => null),
    api.get("/gemelo/playas/banderas").catch(() => null),
    api.get("/gemelo/aire/resumen").catch(() => null),
  ]);
  const chip = (v, l) => '<div class="vg-chip"><b>' + esc(v) + "</b><span>" + esc(l) + "</span></div>";
  if (chips) {
    let extra = "";
    if (aire && aire.temperatura_media_c != null) extra += chip(Math.round(aire.temperatura_media_c) + "°", "aire " + (aire.eaqi_peor_texto || ""));
    else if (meteo && meteo.temperatura_c != null) extra += chip(Math.round(meteo.temperatura_c) + "°", meteo.descripcion || "ahora");
    if (aforo && aforo.aforo_actual != null) extra += chip(nf(aforo.aforo_actual), "vehículos en el Parque");
    if (extra) chips.insertAdjacentHTML("beforeend", extra);
  }
  if (!caja) return;
  const mini = [];
  if (meteo) {
    const tmax = meteo.prevision && meteo.prevision[0] ? meteo.prevision[0].temp_max_c : null;
    const tmin = meteo.prevision && meteo.prevision[0] ? meteo.prevision[0].temp_min_c : null;
    mini.push({ valor: tmax != null ? Math.round(tmax) + "° / " + Math.round(tmin) + "°" : (meteo.temperatura_c != null ? Math.round(meteo.temperatura_c) + "°" : "—"), texto: "Hoy · " + (meteo.descripcion || "") });
    if (meteo.viento_kmh != null) mini.push({ valor: nf(meteo.viento_kmh) + " km/h", texto: "Viento" + (meteo.viento_cardinal ? " " + meteo.viento_cardinal : "") });
  }
  if (banderas && Array.isArray(banderas.banderas) && banderas.banderas.length) {
    const verdes = banderas.banderas.filter((b) => b.estado === "verde").length;
    mini.push({ valor: verdes + " / " + banderas.banderas.length, texto: "Playas con bandera verde" });
  }
  if (aforo && aforo.aforo_actual != null) mini.push({ valor: nf(aforo.aforo_actual), texto: "Vehículos en el Parque" });
  const medidores = caja.innerHTML;
  caja.innerHTML = (mini.length ? PARTES.mini({ items: mini.slice(0, 4) }) : '<div class="vg-pend">' + ic("clock") + "<div>Sin conexión con Open-Meteo ni ThingsBoard en este momento.</div></div>") +
    '<div style="margin-top:12px">' + medidores + "</div>";
}

/* ---------------- render genérico de un panel ---------------- */

function cabecera(p, id) {
  return '<div class="vg-sub"><div><div class="vg-crumb"><a onclick="UI.goDir(\'resumen\')">Plataforma</a> · <b>Dirección</b>' +
    (id !== "resumen" ? " · " + esc(p ? p.titulo.split(" · ")[0] : "") : "") + "</div><h1>" + esc(p ? p.titulo : "Vista de Gobierno") + "</h1><p>" + esc(p ? p.intro : "") + "</p></div>" +
    '<div class="vg-act"><button class="btn" type="button" data-actualizar>' + ic("refresh") + "Actualizar</button>" +
    (tienePermiso("generar_informes") ? '<button class="btn" type="button" onclick="UI.informeDireccion()">' + ic("doc") + "Informe</button>" : "") + "</div></div>";
}

async function dibujarGraficos() {
  const pend = _graficos;
  _graficos = [];
  if (!pend.length) return;
  let Chart;
  try { Chart = await cargarChart(); } catch (e) {
    pend.forEach(({ id }) => { const c = document.getElementById(id); if (c) c.parentElement.innerHTML = '<div class="vg-vacio">No se pudo cargar la librería de gráficos.</div>'; });
    return;
  }
  Chart.defaults.font.family = "Inter, system-ui, sans-serif";
  pend.forEach(({ id, b }) => {
    const c = document.getElementById(id);
    if (c) new Chart(c, configGrafico(b));
  });
}

function renderPanel(id) {
  return async function (el, force) {
    inyectarEstilos();
    el.innerHTML = '<div class="vg">' + cabecera(null, id) + '<div class="vg-card"><div class="vg-vacio">Cargando…</div></div></div>';
    let p;
    try {
      if (force) api.invalidateCache("/direccion");
      p = await api.get("/direccion/panel/" + id);
      if (id === "recomendaciones" || p.bloques.some((b) => b.tipo === "recomendaciones")) await datosRecs(force);
    } catch (e) {
      el.innerHTML = '<div class="vg">' + cabecera(null, id) + '<div class="vg-card"><div class="vg-vacio">' +
        (e && e.status === 403 ? "Tu rol no tiene acceso a esta sección." : "No se pudo cargar el panel: " + esc(e && e.message || e)) + "</div></div></div>";
      return;
    }
    _graficos = [];
    let h = '<div class="vg">' + cabecera(p, id) + hero(p.hero) + '<div class="vg-kpis">' + p.kpis.map(kpi).join("") + "</div>";
    let fila = "";
    const cerrar = () => { if (fila) { h += '<div class="vg-grid">' + fila + "</div>"; fila = ""; } };
    p.bloques.forEach((b) => {
      if (b.tipo === "servicios") { cerrar(); h += servicios(b); return; }
      if (b.tipo === "recomendaciones" && id === "recomendaciones") {
        cerrar();
        const areas = [...new Set((_recs || []).map((r) => r.area))];
        h += '<div class="vg-sec"><h3>' + esc(b.titulo) + "</h3><span>" + esc(b.subtitulo || "") + "</span></div>" +
          '<div class="vg-filtros" data-filtros role="group" aria-label="Filtrar por área"><button class="vg-fbtn on" type="button" data-f="">Todas</button>' +
          areas.map((a) => '<button class="vg-fbtn" type="button" data-f="' + esc(a) + '">' + esc(a) + "</button>").join("") + "</div>";
        fila += '<section class="vg-card vg-s8" style="padding:14px">' + cuerpoBloque({ ...b, area: "" }) + "</section>";
        return;
      }
      fila += tarjeta(b);
    });
    cerrar();
    h += "</div>";
    el.innerHTML = h;
    el.querySelector("[data-actualizar]").onclick = () => { invalidarRecs(); renderPanel(id)(el, true); };
    dibujarGraficos();
    await pintarRecs(el, id === "recomendaciones");
    if (id === "recomendaciones") {
      el.querySelectorAll("[data-f]").forEach((btn) => {
        btn.onclick = () => {
          el.querySelectorAll("[data-f]").forEach((x) => x.classList.toggle("on", x === btn));
          const f = btn.getAttribute("data-f");
          el.querySelectorAll(".vg-rec").forEach((r) => { r.hidden = !!f && r.getAttribute("data-area") !== f; });
        };
      });
    }
    if (id === "resumen") pintarVivo(el);
  };
}

/* ---------------- Informe de Dirección (imprimible → PDF) ---------------- */

async function abrirInforme() {
  let r, recs;
  try { [r, recs] = await Promise.all([api.getResumenDireccion(), datosRecs(true)]); }
  catch (e) { UI.toast("No se pudo generar el informe: " + (e && e.message || e)); return; }
  recs = recs || [];
  const im = r.impacto;
  const eur = (n) => (n == null ? "—" : Number(n).toLocaleString("es-ES") + " €");
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

/* ---------------- secciones y navegación ---------------- */

const SECCIONES = [
  { id: "resumen", n: "Resumen municipal", i: "home" },
  { id: "turismo", n: "Turismo inteligente", i: "turismo" },
  { id: "alumbrado", n: "Alumbrado público", i: "bulb" },
  { id: "agua", n: "Ciclo del agua", i: "drop" },
  { id: "residuos", n: "Residuos", i: "recycle" },
  { id: "movilidad", n: "Movilidad", i: "car" },
  { id: "seguridad", n: "Seguridad", i: "shield" },
  { id: "energia", n: "Energía municipal", i: "bolt" },
  { id: "recomendaciones", n: "Recomendaciones IA", i: "ai", permiso: "ver_recomendaciones_ia" },
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
  SECCIONES.forEach((s) => { R[s.id] = renderPanel(s.id); });
}

function renderSidebar() {
  const sb = document.getElementById("dir-sidebar");
  if (!sb) return;
  let h = '<div class="sb-head"><div class="sb-title">' + ic("chart") + " Dirección</div>" +
    '<div class="sb-sub">Cuadro de mando ejecutivo</div></div><div class="sb-g">Gobierno</div>';
  SECCIONES.forEach((s) => {
    if (s.permiso && !tienePermiso(s.permiso)) return;
    h += '<button class="sb-it" data-dirsec="' + s.id + '" onclick="UI.goDir(\'' + s.id + '\')">' + ic(s.i) + s.n + "</button>";
  });
  if (tienePermiso("generar_informes")) {
    h += '<div class="sb-g">Informes</div>' +
      '<button class="sb-it" onclick="UI.informeDireccion()">' + ic("doc") + "Generar informe</button>";
  }
  sb.innerHTML = h;
}

function tarjetaHTML() {
  return '<div class="vcard vcard--on" data-dircard onclick="UI.enterDireccion()">' +
    '<div class="vi ic-navy">' + ic("chart") + "</div>" +
    "<h3>Vista de Gobierno</h3><p>Cuadro de mando de dirección: estado del municipio, coste, tendencias y previsiones por servicio, y las decisiones pendientes con su impacto.</p>" +
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
    if (pill) pill.innerHTML = ic("chart") + ' Dirección <span class="bdg bdg-info" style="margin-left:4px">vista de gobierno</span>';
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
  UI.enterDireccion = function () { renderSidebar(); UI.goDir(SECCIONES[0].id); };
  UI.rerenderDir = function (id) { rendered[id] = false; if (cur === id) UI.goDir(id); };
  UI.informeDireccion = abrirInforme;

  // El perfil directivo vive SOLO en la Vista de Gobierno: si intenta volver al
  // panel general (miga "Plataforma"), aterriza de nuevo en su portada. El
  // backend ya le deniega los endpoints técnicos; esto evita pantallas vacías.
  if (!UI._dirGoWrap) {
    const origGo = UI.go;
    UI.go = function (id) {
      const u = getCachedUser && getCachedUser();
      if (u && u.rol === "direccion_gobierno" && id === "home") { UI.enterDireccion(); return; }
      return origGo.apply(this, arguments);
    };
    UI._dirGoWrap = true;
  }

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
    renderSidebar();
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
