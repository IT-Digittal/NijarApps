const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa6");
const path = require("path");
const { applyTheme } = require("/root/.claude/skills/synced/3691cd2c-d821-4cec-9be0-0bdcbc212751_97ab52f9-b865-4418-9756-a7b7a1e05e4e/pptx/scripts/apply_theme.js");

const REPO = "/home/user/NijarApps";
const OUT = process.argv[2] || "deck.pptx";
const IMG = (p) => path.join(REPO, "frontend/shared", p);

const THEME = {
  name: "Nijar DTI Gobierno",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "14213D", lt1: "FFFFFF", dk2: "0B2A55", lt2: "EEF3FA",
    accent1: "17A394", accent2: "F2A93B", accent3: "2F9E5F", accent4: "E05A4D",
    accent5: "2563B0", accent6: "8A97B1", hlink: "2563B0", folHlink: "6B4FBB",
  },
};
const H = THEME.colors;
const MUTED = "5B6B88";
const LINE = "D9E1EE";
const TAGS = {
  real: { t: "REAL HOY", c: H.accent3 },
  integrar: { t: "AL INTEGRAR", c: "C77A12" },
  estimado: { t: "ESTIMADO", c: "6B7A99" },
  modelo: { t: "MODELO PREDICTIVO", c: H.accent5 },
};

async function icon(Comp, color, px = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: px }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
  pres.title = "Vista de Gobierno 2.0 · Propuesta de mejora";
  pres.author = "Plataforma DTI Níjar";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;

  const escudo = "image/png;base64," + (await sharp(IMG("escudo-nijar.svg")).resize({ height: 400 }).png().toBuffer()).toString("base64");

  const I = {};
  const iconList = {
    euro: fa.FaEuroSign, chart: fa.FaChartLine, check: fa.FaListCheck, umbrella: fa.FaUmbrellaBeach,
    bulb: fa.FaLightbulb, drop: fa.FaDroplet, trash: fa.FaRecycle, car: fa.FaCarSide, cam: fa.FaVideo,
    bolt: fa.FaBolt, robot: fa.FaWandMagicSparkles, road: fa.FaRoute, city: fa.FaCity, key: fa.FaKey,
    plug: fa.FaPlug, leaf: fa.FaLeaf, users: fa.FaUsers, bell: fa.FaBell, calendar: fa.FaCalendarDays,
  };
  for (const [k, v] of Object.entries(iconList)) I[k] = await icon(v, "FFFFFF");

  // ---------------- layouts ----------------
  pres.defineSlideMaster({
    title: "PORTADA",
    background: { color: H.dk2 },
    objects: [
      { image: { path: IMG("cabo-de-gata-hero.jpg"), x: 6.2, y: 0, w: 7.13, h: 7.5, sizing: { type: "cover", w: 7.13, h: 7.5 } } },
      { rect: { x: 6.2, y: 0, w: 7.13, h: 7.5, fill: { color: H.dk2, transparency: 45 } } },
      { placeholder: { options: { name: "kicker", type: "body", x: 0.7, y: 1.55, w: 5.4, h: 0.4, fontSize: 13, bold: true, color: C.accent2, charSpacing: 3 }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.7, y: 2.0, w: 5.4, h: 2.2, fontSize: 44, bold: true, color: C.background1, valign: "top", align: "left" }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.7, y: 4.3, w: 5.2, h: 1.3, fontSize: 16, color: "C9D6EA", valign: "top" }, text: "" } },
    ],
  });
  const footer = [
    { text: { text: "Plataforma DTI Níjar · Propuesta de mejora · Vista de Gobierno", options: { x: 0.6, y: 7.02, w: 8, h: 0.3, fontSize: 10, color: MUTED } } },
  ];
  pres.defineSlideMaster({
    title: "CONTENIDO",
    background: { color: "FFFFFF" },
    objects: [
      ...footer,
      { placeholder: { options: { name: "kicker", type: "body", x: 0.6, y: 0.35, w: 9, h: 0.35, fontSize: 12, bold: true, color: C.accent1, charSpacing: 2, margin: 0 }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.7, w: 12.1, h: 0.85, fontSize: 30, bold: true, color: C.text2, margin: 0, valign: "top", align: "left" }, text: "" } },
    ],
    slideNumber: { x: 12.3, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: MUTED, align: "right" },
  });
  pres.defineSlideMaster({
    title: "OSCURO",
    background: { color: H.dk2 },
    objects: [
      { text: { text: "Plataforma DTI Níjar · Propuesta de mejora · Vista de Gobierno", options: { x: 0.6, y: 7.02, w: 8, h: 0.3, fontSize: 10, color: "8EA3C4" } } },
      { placeholder: { options: { name: "kicker", type: "body", x: 0.6, y: 0.35, w: 9, h: 0.35, fontSize: 12, bold: true, color: C.accent2, charSpacing: 2, margin: 0 }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.7, w: 12.1, h: 0.85, fontSize: 30, bold: true, color: C.background1, margin: 0, valign: "top", align: "left" }, text: "" } },
    ],
    slideNumber: { x: 12.3, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: "8EA3C4", align: "right" },
  });

  // ---------------- helpers ----------------
  const shadow = () => ({ type: "outer", color: "0B2A55", blur: 8, offset: 2, angle: 90, opacity: 0.12 });
  function card(s, x, y, w, h, opt = {}) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w, h, rectRadius: 0.12, fill: { color: opt.fill || "FFFFFF" },
      line: { color: opt.line || LINE, width: opt.lineW ?? 1 }, shadow: opt.noShadow ? undefined : shadow(),
      objectName: opt.name,
    });
  }
  function iconCircle(s, key, x, y, d, color) {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color }, line: { color, width: 0 } });
    const p = d * 0.26;
    s.addImage({ data: I[key], x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p });
  }
  function tag(s, kind, x, y) {
    const t = TAGS[kind];
    const w = 0.12 + t.t.length * 0.075;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.24, rectRadius: 0.12, fill: { color: t.c, transparency: 85 }, line: { color: t.c, width: 0.75 } });
    s.addText(t.t, { x, y, w, h: 0.24, fontSize: 8, bold: true, color: t.c, align: "center", valign: "middle", margin: 0, isTextBox: true, charSpacing: 1 });
  }
  function kpi(s, x, y, w, h, label, value, sub, kind, valColor) {
    card(s, x, y, w, h, { name: "kpi " + label });
    s.addText(label, { x: x + 0.2, y: y + 0.14, w: w - 0.4, h: 0.3, fontSize: 11, bold: true, color: MUTED, margin: 0, isTextBox: true });
    s.addText(value, { x: x + 0.2, y: y + 0.44, w: w - 0.4, h: 0.6, fontSize: 28, bold: true, color: valColor || H.dk2, margin: 0, isTextBox: true, valign: "middle" });
    s.addText(sub, { x: x + 0.2, y: y + 1.04, w: w - 0.4, h: 0.3, fontSize: 10.5, color: MUTED, margin: 0, isTextBox: true });
    if (kind) tag(s, kind, x + 0.2, y + h - 0.36);
  }
  function accion(s, text, y = 6.05) {
    card(s, 0.6, y, 12.1, 0.8, { fill: "E8F6F4", line: "BFE6E0", noShadow: true, name: "accion" });
    iconCircle(s, "robot", 0.78, y + 0.14, 0.52, H.accent1);
    s.addText([
      { text: "Acción recomendada  ", options: { bold: true, color: "0E6F66" } },
      { text, options: { color: H.dk1 } },
    ], { x: 1.45, y, w: 11.1, h: 0.8, fontSize: 14, valign: "middle", margin: 0, isTextBox: true });
  }
  const axis = {
    catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt", titleFontFace: "+mn-lt",
    valGridLine: { color: "E3E8F0", size: 0.75 }, catGridLine: { style: "none" },
    catAxisLineShow: false, valAxisLineShow: false,
    titleFontSize: 13, titleColor: H.dk2, showTitle: true,
    legendFontSize: 10, legendColor: MUTED, dataLabelFontSize: 10, dataLabelColor: H.dk1,
  };
  function chartCard(s, x, y, w, h) { card(s, x, y, w, h, { name: "grafico" }); }
  function source(s, text, x, y, w) {
    s.addText(text, { x, y, w, h: 0.25, fontSize: 9, italic: true, color: MUTED, margin: 0, isTextBox: true });
  }
  const sec = (title) => pres.addSection({ title });

  // =============== 1. Portada ===============
  sec("Introducción");
  let s = pres.addSlide({ masterName: "PORTADA", sectionTitle: "Introducción" });
  s.addImage({ data: escudo, x: 0.7, y: 0.55, w: 0.6, h: 0.8 });
  s.addText("Ayuntamiento de Níjar · Smart City", { x: 1.45, y: 0.7, w: 4.5, h: 0.5, fontSize: 14, bold: true, color: "FFFFFF", margin: 0, isTextBox: true });
  s.addText("PROPUESTA DE MEJORA", { placeholder: "kicker" });
  s.addText("Vista de Gobierno 2.0", { placeholder: "title" });
  s.addText("Del semáforo de estado al cuadro de mando de decisión: consumos, costes, previsiones y acciones en cada módulo.", { placeholder: "body" });
  s.addText("Octubre 2026", { x: 0.7, y: 6.4, w: 4, h: 0.4, fontSize: 13, color: "8EA3C4", margin: 0, isTextBox: true });
  // tarjetas flotantes sobre la foto
  const flo = [["84", "Índice de ciudad hoy"], ["7", "módulos con previsión"], ["70 %", "KPIs ya con datos reales"]];
  flo.forEach(([v, l], i) => {
    const y = 1.9 + i * 1.45;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.6, y, w: 3.6, h: 1.15, rectRadius: 0.15, fill: { color: "FFFFFF", transparency: 10 }, line: { color: "FFFFFF", width: 0 }, shadow: shadow() });
    s.addText(v, { x: 8.85, y: y + 0.1, w: 1.5, h: 0.95, fontSize: 34, bold: true, color: i === 2 ? H.accent3 : H.dk2, valign: "middle", margin: 0, isTextBox: true });
    s.addText(l, { x: 10.15, y: y + 0.1, w: 1.95, h: 0.95, fontSize: 13, color: H.dk1, valign: "middle", margin: 0, isTextBox: true });
  });
  s.addNotes("Propuesta para el apartado Vista de Gobierno de la Plataforma DTI. Las cifras de los gráficos son ilustrativas y parten de los valores actuales de la plataforma.");

  // =============== 2. Mensaje clave ===============
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Introducción" });
  s.addText("LA PROPUESTA EN UNA PÁGINA", { placeholder: "kicker" });
  s.addText("Tres preguntas nuevas que la Vista de Gobierno responderá", { placeholder: "title" });
  const preg = [
    ["euro", H.accent5, "¿Cuánto nos cuesta y cuánto ahorramos?", "Consumo en kWh, m³ y toneladas, coste en euros y ahorro interanual en cada módulo."],
    ["chart", H.accent1, "¿Qué va a pasar?", "Previsión a 7 y 30 días: visitantes, parkings, contenedores, energía y agua."],
    ["check", H.accent2, "¿Qué tenemos que decidir?", "Una acción priorizada por módulo, con su impacto en euros o servicio y su estado."],
  ];
  preg.forEach(([ic, col, t, d], i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.95, 3.8, 3.0, { name: "pregunta " + (i + 1) });
    iconCircle(s, ic, x + 0.3, 2.25, 0.8, col);
    s.addText(t, { x: x + 0.3, y: 3.2, w: 3.2, h: 0.75, fontSize: 18, bold: true, color: H.dk2, margin: 0, valign: "top", isTextBox: true });
    s.addText(d, { x: x + 0.3, y: 3.95, w: 3.2, h: 0.9, fontSize: 14, color: H.dk1, margin: 0, valign: "top", isTextBox: true });
  });
  card(s, 0.6, 5.25, 12.1, 1.45, { fill: H.dk2, line: H.dk2, name: "dato clave" });
  s.addText("70 %", { x: 0.9, y: 5.3, w: 2.2, h: 1.35, fontSize: 54, bold: true, color: H.accent2, valign: "middle", margin: 0, isTextBox: true });
  s.addText("de los indicadores propuestos se construye ya con datos reales de la plataforma. El resto se activa sin rediseño en cuanto lleguen siGEUS, Datadis privado, Bettair, GA4 y Meta/X.",
    { x: 3.2, y: 5.3, w: 9.2, h: 1.35, fontSize: 16, color: "FFFFFF", valign: "middle", margin: 0, isTextBox: true });

  // =============== 3. Hoy vs propuesta ===============
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Introducción" });
  s.addText("PUNTO DE PARTIDA", { placeholder: "kicker" });
  s.addText("De una foto del estado a una herramienta para decidir", { placeholder: "title" });
  const hoy = ["Semáforo y una frase por módulo", "4 KPIs puntuales, sin coste", "Comparativa interanual aislada", "Sin previsión ni desglose territorial", "Recomendaciones sin impacto cuantificado"];
  const prop = ["Franja económica: coste, ahorro y CO₂", "Tendencia de 12 a 24 meses en cada módulo", "Previsión a 7 y 30 días con intervalo", "Mapa por núcleo sobre el gemelo digital", "Acciones con € en juego y seguimiento"];
  card(s, 0.6, 1.9, 5.7, 4.75, { fill: "F4F6FA", name: "hoy" });
  s.addText("HOY", { x: 0.95, y: 2.1, w: 3, h: 0.4, fontSize: 14, bold: true, color: MUTED, margin: 0, isTextBox: true });
  s.addText(hoy.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < hoy.length - 1 } })), { x: 0.95, y: 2.6, w: 5.1, h: 3.8, fontSize: 18, color: H.dk1, paraSpaceAfter: 20, valign: "top", margin: 0, isTextBox: true });
  card(s, 7.0, 1.9, 5.7, 4.75, { fill: H.dk2, line: H.dk2, name: "propuesta" });
  s.addText("VISTA DE GOBIERNO 2.0", { x: 7.35, y: 2.1, w: 5, h: 0.4, fontSize: 14, bold: true, color: H.accent2, margin: 0, isTextBox: true });
  s.addText(prop.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < prop.length - 1 } })), { x: 7.35, y: 2.6, w: 5.1, h: 3.8, fontSize: 18, color: "FFFFFF", paraSpaceAfter: 20, valign: "top", margin: 0, isTextBox: true });
  s.addShape(pres.shapes.RIGHT_ARROW, { x: 6.4, y: 3.95, w: 0.5, h: 0.6, fill: { color: H.accent1 }, line: { color: H.accent1, width: 0 } });

  // =============== 4. Fuentes ===============
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Introducción" });
  s.addText("FUENTES DE DATOS", { placeholder: "kicker" });
  s.addText("Cada módulo arranca con datos reales y crece al integrar fuentes", { placeholder: "title" });
  const fuentes = [
    ["umbrella", "Turismo", "INE, Junta, EGATUR, FRONTUR, AENA, tótems, chatbot, ThingsBoard", "Meta, X, GA4, app Vive Níjar"],
    ["bulb", "Alumbrado", "Inventario LED/VSAP, cuadros, incidencias, histórico 2 años", "Telegestión y curvas por cuadro"],
    ["drop", "Agua", "Sectores, caudal, fugas, rendimiento, telelectura", "Telelectura y SCADA concesionaria"],
    ["trash", "Residuos", "Contenedores, sensores de llenado, rutas", "siGEUS: toneladas, lavados, flota"],
    ["car", "Movilidad", "Aforos, parkings, recarga EV, aforo del Parque", "WiFi público y contadores (DPIA)"],
    ["cam", "Seguridad", "Cámaras, analítica, incidencias y ANS", "Analítica de vídeo, avisos 112"],
    ["bolt", "Energía", "Datadis público, CUPS, autoconsumo FV, coste", "Datadis privado: curvas horarias"],
  ];
  s.addText("REAL HOY", { x: 3.0, y: 1.75, w: 5.5, h: 0.3, fontSize: 11, bold: true, color: H.accent3, margin: 0, isTextBox: true });
  s.addText("AL INTEGRAR", { x: 8.75, y: 1.75, w: 4, h: 0.3, fontSize: 11, bold: true, color: "C77A12", margin: 0, isTextBox: true });
  const cols = [H.accent4, H.accent2, H.accent5, H.accent3, "6B4FBB", "46587E", "E0912F"];
  fuentes.forEach(([ic, n, r, p], i) => {
    const y = 2.1 + i * 0.62;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 12.1, h: 0.54, rectRadius: 0.1, fill: { color: i % 2 ? "FFFFFF" : "F4F7FB" }, line: { color: LINE, width: 0.5 } });
    iconCircle(s, ic, 0.72, y + 0.07, 0.4, cols[i]);
    s.addText(n, { x: 1.25, y, w: 1.7, h: 0.54, fontSize: 14, bold: true, color: H.dk2, valign: "middle", margin: 0, isTextBox: true });
    s.addText(r, { x: 3.0, y, w: 5.6, h: 0.54, fontSize: 12, color: H.dk1, valign: "middle", margin: 0, isTextBox: true });
    s.addText(p, { x: 8.75, y, w: 3.85, h: 0.54, fontSize: 12, color: H.dk1, valign: "middle", margin: 0, isTextBox: true });
  });
  source(s, "Transversal: Open-Meteo, inventario de bienes y consumo de IA (real hoy) · Bettair, calidad del aire (al integrar). Sin credencial, el módulo muestra «fuente pendiente» y nunca inventa datos.", 0.6, 6.55, 12.1);

  // =============== 5. Resumen municipal (mock) ===============
  sec("Módulos");
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Módulos" });
  s.addText("RESUMEN MUNICIPAL", { placeholder: "kicker" });
  s.addText("La portada suma economía, tendencia y la semana que viene", { placeholder: "title" });
  // banda hero
  s.addImage({ path: IMG("cabo-de-gata-hero.jpg"), x: 0.6, y: 1.75, w: 12.1, h: 1.35, sizing: { type: "cover", w: 12.1, h: 1.35 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.75, w: 12.1, h: 1.35, fill: { color: H.dk2, transparency: 20 }, line: { color: H.dk2, width: 0 } });
  s.addText("Níjar funciona bien, con 4 áreas en seguimiento", { x: 0.9, y: 1.85, w: 8.5, h: 0.6, fontSize: 22, bold: true, color: "FFFFFF", margin: 0, isTextBox: true, valign: "middle" });
  s.addText("3 de 7 servicios en verde · disponibilidad media 91,3 % · 1 incidencia crítica", { x: 0.9, y: 2.45, w: 8.5, h: 0.4, fontSize: 13, color: "D5E0F0", margin: 0, isTextBox: true });
  s.addShape(pres.shapes.OVAL, { x: 11.25, y: 1.88, w: 1.1, h: 1.1, fill: { color: H.dk2 }, line: { color: H.accent2, width: 5 } });
  s.addText([{ text: "84", options: { fontSize: 26, bold: true, breakLine: true } }, { text: "de 100", options: { fontSize: 9 } }], { x: 11.25, y: 1.88, w: 1.1, h: 1.1, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
  const fr = [
    ["Gasto energético mes", "98,4 k€", "−6 % interanual", "real", H.dk2],
    ["Ahorro en el año", "212 k€", "LED + autoconsumo", "estimado", H.accent3],
    ["CO₂ evitado", "168 t", "al año", "estimado", H.accent3],
    ["Incidencias críticas", "1", "ANS cumplido 94 %", "real", H.accent4],
    ["Satisfacción", "77,2 %", "NPS chatbot y tótems", "real", H.dk2],
    ["Visitantes semana", "18.600", "+12 % previsto", "modelo", H.accent5],
  ];
  fr.forEach(([l, v, d, k, c], i) => kpi(s, 0.6 + i * 2.04, 3.3, 1.9, 1.75, l, v, d, k, c));
  chartCard(s, 0.6, 5.25, 7.3, 1.65);
  const meses12 = ["nov", "dic", "ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct"];
  s.addChart(pres.charts.LINE, [
    { name: "Índice de ciudad", labels: meses12, values: [78, 79, 81, 80, 82, 83, 81, 80, 83, 85, 84, 84] },
    { name: "Objetivo", labels: meses12, values: Array(12).fill(85) },
  ], { x: 0.7, y: 5.3, w: 7.1, h: 1.55, ...axis, title: "Índice de ciudad, 12 meses (objetivo 85)", titleFontSize: 11, chartColors: [H.dk2, H.accent2], lineSize: 2, lineDataSymbol: "none", valAxisMinVal: 70, valAxisMaxVal: 90, valAxisMajorUnit: 10, showLegend: false });
  card(s, 8.1, 5.25, 4.6, 1.65, { fill: "FFF6E8", line: "F6D9A8", name: "decisiones" });
  iconCircle(s, "bell", 8.3, 5.45, 0.5, H.accent2);
  s.addText([{ text: "3 decisiones pendientes", options: { bold: true, breakLine: true, color: H.dk2, fontSize: 15 } }, { text: "Con 74.000 €/año en juego. Aceptar o descartar desde la portada.", options: { color: H.dk1, fontSize: 12 } }],
    { x: 8.95, y: 5.35, w: 3.6, h: 1.45, valign: "middle", margin: 0, isTextBox: true });

  // =============== módulos genéricos ===============
  function modulo(kicker, title, kpis, chartFn, act, src, sect = "Módulos") {
    const sl = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: sect });
    sl.addText(kicker, { placeholder: "kicker" });
    sl.addText(title, { placeholder: "title" });
    kpis.forEach((k, i) => kpi(sl, 0.6 + (i % 2) * 2.55, 1.8 + Math.floor(i / 2) * 2.08, 2.4, 1.92, ...k));
    chartCard(sl, 5.85, 1.8, 6.85, 4.0);
    chartFn(sl, 6.0, 1.9, 6.55, 3.6);
    if (src) source(sl, src, 6.05, 5.5, 6.5);
    accion(sl, act);
    return sl;
  }

  // 6. Turismo
  const sem = ["31 ago", "7 sep", "14 sep", "21 sep", "28 sep", "5 oct", "12 oct", "19 oct", "26 oct", "2 nov", "9 nov", "16 nov"];
  const realT = [31200, 27400, 24100, 21800, 20300, 19600, 21400, 16600, null, null, null, null];
  const prevT = [null, null, null, null, null, null, null, 16600, 18600, 14100, 13200, 12800];
  modulo("TURISMO INTELIGENTE", "Pico de visitantes en Todos los Santos; después, un 31 % menos",
    [["Visitantes previstos", "18.600", "semana del 26 oct", "modelo", H.accent5],
     ["Pernoctaciones", "+4,2 %", "interanual · INE EOH", "real", H.accent3],
     ["Aforo del Parque", "72 %", "34 banderas en verde", "real", H.dk2],
     ["Sentimiento en redes", "+0,55", "31.764 menciones/mes", "integrar", H.dk2]],
    (sl, x, y, w, h) => sl.addChart(pres.charts.LINE, [
      { name: "Real", labels: sem, values: realT },
      { name: "Previsión", labels: sem, values: prevT },
    ], { x, y, w, h, ...axis, title: "Visitantes por semana · real y previsión a 4 semanas", chartColors: ["8A97B1", H.accent5], lineSize: 3, lineDataSymbolSize: 7, showLegend: true, legendPos: "b", valAxisMinVal: 0, valAxisLabelFormatCode: "#,##0", displayBlanksAs: "gap" }),
    "Semana de baja afluencia (−31 %): campaña de temporada baja en mercados alemán y francés, el 38 % de las consultas en idiomas.",
    "Ilustrativo · prediccion_afluencia + aforo ThingsBoard");

  // 7. Alumbrado
  const m13 = ["nov", "dic", "ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov*"];
  modulo("ALUMBRADO PÚBLICO", "El LED ya ahorra 6.800 € al mes; quedan 1.140 VSAP por renovar",
    [["Coste mensual", "9.800 €", "61.300 kWh", "real", H.dk2],
     ["Ahorro LED vs VSAP", "41 %", "6.800 €/mes", "estimado", H.accent3],
     ["Luminarias LED", "72 %", "1.140 VSAP pendientes", "real", H.dk2],
     ["Incidencias abiertas", "31", "reparación media 2,6 días", "real", H.accent4]],
    (sl, x, y, w, h) => sl.addChart(pres.charts.BAR, [
      { name: "Real", labels: m13, values: [74, 79, 80, 72, 66, 58, 54, 52, 55, 60, 64, 61.3, 0] },
      { name: "Previsión", labels: m13, values: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64.9] },
    ], { x, y, w, h, ...axis, barDir: "col", barGrouping: "stacked", barGapWidthPct: 45, title: "Consumo mensual (MWh) y previsión de noviembre", chartColors: ["F2A93B", H.dk2], showLegend: true, legendPos: "b", valAxisMinVal: 0 }),
    "Renovar las 310 VSAP de Campohermoso: ahorro estimado de 18.000 €/año, retorno en 3 años.",
    "Ilustrativo · /verticales/alumbrado/overview + histórico 24 meses · *previsión");

  // 8. Agua
  const sect = ["San José Norte", "San Isidro", "Campohermoso", "Pujaire", "Níjar centro", "Agua Amarga", "Las Negras"];
  const rend = [73, 79, 81, 82, 84, 86, 88];
  modulo("CICLO DEL AGUA", "Cinco de siete sectores no llegan al 85 % de rendimiento",
    [["Agua no registrada", "82.400 m³", "≈ 49.000 € al mes", "estimado", H.accent4],
     ["Rendimiento medio", "80 %", "objetivo 85 %", "real", H.dk2],
     ["Fugas activas", "3", "reparación media 36 h", "real", H.accent2],
     ["Demanda en agosto", "+38 %", "frente a octubre", "modelo", H.accent5]],
    (sl, x, y, w, h) => sl.addChart(pres.charts.BAR, [
      { name: "Bajo objetivo", labels: sect, values: rend.map((v) => (v < 85 ? v : 0)) },
      { name: "En objetivo", labels: sect, values: rend.map((v) => (v >= 85 ? v : 0)) },
    ], { x, y, w, h, ...axis, barDir: "bar", barGrouping: "stacked", barGapWidthPct: 40, title: "Rendimiento de red por sector (%) · objetivo 85 %", chartColors: [H.accent4, H.accent1], showLegend: true, legendPos: "b", valAxisMinVal: 0, valAxisMaxVal: 100, catAxisOrientation: "maxMin", showValue: true, dataLabelPosition: "inEnd", dataLabelColor: "FFFFFF", dataLabelFormatCode: "0;;" }),
    "San José Norte pierde el 27 %: campaña de búsqueda activa de fugas; recuperar 5 puntos ahorra unos 14.000 €/año.",
    "Ilustrativo · /verticales/agua/overview · facturado al integrar la concesionaria");

  // 9. Residuos
  const m6 = ["may", "jun", "jul", "ago", "sep", "oct"];
  modulo("RESIDUOS · siGEUS", "Agosto dispara la recogida; la selectiva se queda en el 21 %",
    [["Toneladas del mes", "1.480 t", "por fracción", "integrar", H.dk2],
     ["Recogida selectiva", "21 %", "objetivo UE 2035: 65 %", "integrar", H.accent4],
     ["Contenedores ≥ 80 %", "94", "27 en riesgo en 48 h", "real", H.accent2],
     ["Coste por tonelada", "96 €", "contrato + siGEUS", "integrar", H.dk2]],
    (sl, x, y, w, h) => sl.addChart(pres.charts.BAR, [
      { name: "Resto", labels: m6, values: [1050, 1250, 1550, 1700, 1300, 1170] },
      { name: "Envases", labels: m6, values: [120, 140, 175, 190, 150, 125] },
      { name: "Papel", labels: m6, values: [90, 100, 120, 125, 105, 85] },
      { name: "Vidrio", labels: m6, values: [80, 100, 135, 150, 110, 65] },
      { name: "Orgánica", labels: m6, values: [60, 70, 85, 95, 75, 35] },
    ], { x, y, w, h, ...axis, barDir: "col", barGrouping: "stacked", barGapWidthPct: 50, title: "Toneladas recogidas por fracción", chartColors: ["8A97B1", "F2C744", H.accent5, H.accent3, "A0522D"], showLegend: true, legendPos: "b", valAxisLabelFormatCode: "#,##0" }),
    "Adelantar la ruta de envases en San José el viernes: 12 contenedores superarán el 95 % antes del fin de semana.",
    "Ilustrativo · siGEUS (Distromel) al recibir el usuario de solo lectura");

  // 10. Movilidad
  const horas = ["8h", "9h", "10h", "11h", "12h", "13h", "14h", "15h", "16h", "17h", "18h", "19h", "20h"];
  modulo("MOVILIDAD", "El sábado los parkings de playa se saturan de 13:00 a 16:00",
    [["Ocupación parking", "86 %", "97 % previsto a las 13:00", "modelo", H.accent2],
     ["Horas saturado", "14 h", "en la última semana", "real", H.accent4],
     ["Tráfico en accesos", "540 veh/h", "+8 % interanual", "real", H.dk2],
     ["Visitantes por núcleo", "—", "WiFi y contadores", "integrar", MUTED]],
    (sl, x, y, w, h) => sl.addChart(pres.charts.LINE, [
      { name: "Real", labels: horas, values: [20, 32, 51, 70, 86, null, null, null, null, null, null, null, null] },
      { name: "Previsión", labels: horas, values: [null, null, null, null, 86, 95, 98, 97, 93, 85, 72, 55, 38] },
      { name: "Umbral de saturación", labels: horas, values: Array(13).fill(95) },
    ], { x, y, w, h, ...axis, title: "Ocupación de parkings de playa (%) · sábado", chartColors: ["8A97B1", H.accent5, H.accent4], lineSize: 3, lineDataSymbolSize: 6, showLegend: true, legendPos: "b", valAxisMinVal: 0, valAxisMaxVal: 100, displayBlanksAs: "gap" }),
    "Saturación prevista en Los Genoveses de 13:00 a 16:00: aviso en tótems y app, y lanzadera desde San José.",
    "Ilustrativo · /verticales/movilidad/overview + curva típica por día");

  // 11. Seguridad
  const nucleos = ["San José", "Níjar", "Campohermoso", "San Isidro", "Las Negras", "Agua Amarga", "Otros"];
  modulo("SEGURIDAD", "San José y Níjar concentran casi la mitad de las incidencias",
    [["Cámaras disponibles", "96 %", "22 h sin cobertura en 30 días", "real", H.accent3],
     ["Fuera de servicio", "1", "4 días sin reparar", "real", H.accent4],
     ["ANS de reparación", "92 %", "objetivo 95 %", "real", H.dk2],
     ["Eventos de analítica", "—", "aglomeración, intrusión", "integrar", MUTED]],
    (sl, x, y, w, h) => sl.addChart(pres.charts.BAR, [
      { name: "Incidencias", labels: nucleos, values: [14, 12, 11, 9, 5, 4, 3] },
    ], { x, y, w, h, ...axis, barDir: "bar", barGapWidthPct: 40, title: "Incidencias en vía pública por núcleo · último mes (58)", chartColors: [H.dk2], invertedColors: [H.dk2], showLegend: false, catAxisOrientation: "maxMin", showValue: true, dataLabelPosition: "outEnd", valAxisHidden: true, valGridLine: { style: "none" } }),
    "La cámara del paseo de San José lleva 4 días sin comunicación y hay mercadillo el sábado: priorizar su reparación.",
    "Ilustrativo · /verticales/seguridad/overview + incidencias");

  // 12. Energía
  const m12 = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  modulo("ENERGÍA MUNICIPAL", "Los edificios municipales consumen un 6 % menos que en 2025",
    [["Consumo del mes", "468 MWh", "88.600 € · −6 %", "real", H.dk2],
     ["Autoconsumo FV", "4 %", "3.500 €/mes de ahorro", "real", H.accent3],
     ["Potencia sobrante", "11 CUPS", "9.200 €/año en término fijo", "integrar", H.accent2],
     ["Previsión diciembre", "512 MWh", "noches largas y frío", "modelo", H.accent5]],
    (sl, x, y, w, h) => sl.addChart(pres.charts.LINE, [
      { name: "2025", labels: m12, values: [520, 505, 480, 455, 470, 520, 590, 610, 540, 500, 510, 545] },
      { name: "2026", labels: m12, values: [490, 470, 452, 428, 441, 488, 553, 571, 507, 468, null, null] },
      { name: "Previsión 2026", labels: m12, values: [null, null, null, null, null, null, null, null, null, 468, 478, 512] },
    ], { x, y, w, h, ...axis, title: "Consumo eléctrico mensual de edificios (MWh)", chartColors: ["B8C2D6", H.accent1, H.accent2], lineSize: 3, lineDataSymbolSize: 6, showLegend: true, legendPos: "b", valAxisMinVal: 400, valAxisMaxVal: 650, displayBlanksAs: "gap" }),
    "FV en las cubiertas de los 5 edificios de mayor consumo diurno: autoconsumo del 4 % al 15 %, unos 42.000 €/año.",
    "Ilustrativo · oct 2026 = valor actual (467.921 kWh) · Datadis + /verticales/energia/overview");

  // =============== 13. Recomendaciones IA ===============
  sec("Decisión y plan");
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Decisión y plan" });
  s.addText("RECOMENDACIONES IA Y CONSUMO DE IA", { placeholder: "kicker" });
  s.addText("Cada recomendación, con su impacto y seguimiento hasta el ahorro", { placeholder: "title" });
  chartCard(s, 0.6, 1.8, 6.2, 4.1);
  s.addChart(pres.charts.BAR, [{ name: "Recomendaciones", labels: ["Propuestas", "Aceptadas", "Ejecutadas"], values: [24, 15, 9] }],
    { x: 0.75, y: 1.9, w: 5.9, h: 3.4, ...axis, barDir: "bar", barGapWidthPct: 35, title: "Embudo de decisiones del trimestre", chartColors: [H.accent1], invertedColors: [H.accent1], catAxisOrientation: "maxMin", showValue: true, dataLabelPosition: "outEnd", valAxisHidden: true, valGridLine: { style: "none" }, showLegend: false, catAxisLabelFontSize: 12 });
  s.addText([{ text: "31.000 € ", options: { bold: true, color: H.accent3 } }, { text: "de ahorro ya realizado frente a 38.000 € estimados", options: { color: H.dk1 } }], { x: 0.85, y: 5.3, w: 5.8, h: 0.5, fontSize: 14, margin: 0, isTextBox: true });
  const recs = [
    ["users", H.accent5, "Ficha por recomendación", "Módulo, prioridad, € en juego, plazo, responsable y estado."],
    ["calendar", H.accent1, "Resumen semanal automático", "Un párrafo por IA cada lunes para Alcaldía y concejalías, en PDF."],
    ["robot", "6B4FBB", "Coste de la IA, real hoy", "14.300 conversaciones · 41 USD/mes · 0,003 USD por conversación."],
  ];
  recs.forEach(([ic, col, t, d], i) => {
    const y = 1.8 + i * 1.4;
    card(s, 7.1, y, 5.6, 1.25, { name: t });
    iconCircle(s, ic, 7.3, y + 0.3, 0.65, col);
    s.addText([{ text: t, options: { bold: true, fontSize: 16, color: H.dk2, breakLine: true } }, { text: d, options: { fontSize: 13, color: H.dk1 } }], { x: 8.15, y: y + 0.08, w: 4.4, h: 1.1, valign: "middle", margin: 0, isTextBox: true });
  });
  source(s, "Ilustrativo · estados ya disponibles en la plataforma; coste de IA en GET /dashboards/ia/consumo", 0.6, 6.1, 12);

  // =============== 14. Hoja de ruta ===============
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Decisión y plan" });
  s.addText("HOJA DE RUTA", { placeholder: "kicker" });
  s.addText("Arrancamos con datos reales; cada acceso pendiente suma su bloque", { placeholder: "title" });
  const fases = [
    ["1", "Datos de hoy", "4 semanas desde la aprobación", ["Franja económica y CO₂", "Tendencias de 12 a 24 meses", "Previsión de afluencia y energía", "Recomendaciones con impacto"], H.accent1],
    ["2", "Accesos pendientes", "1 a 2 semanas por credencial", ["siGEUS: toneladas y reciclaje", "Datadis privado: curvas por CUPS", "Meta, X y GA4: turismo digital", "Bettair: calidad del aire"], H.accent2],
    ["3", "Nuevas fuentes", "Según acuerdos con terceros", ["WiFi y contadores (con DPIA)", "Telelectura y SCADA del agua", "Analítica de vídeo y 112", "App Vive Níjar"], H.accent5],
  ];
  fases.forEach(([n, t, p, items, col], i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.85, 3.8, 4.2, { fill: i === 0 ? "E8F6F4" : "FFFFFF", line: i === 0 ? H.accent1 : LINE, lineW: i === 0 ? 2 : 1, name: "fase " + n });
    s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: 2.1, w: 0.7, h: 0.7, fill: { color: col }, line: { color: col, width: 0 } });
    s.addText(n, { x: x + 0.3, y: 2.1, w: 0.7, h: 0.7, fontSize: 24, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(t, { x: x + 1.15, y: 2.05, w: 2.55, h: 0.45, fontSize: 19, bold: true, color: H.dk2, margin: 0, isTextBox: true, valign: "middle" });
    s.addText(p, { x: x + 1.15, y: 2.5, w: 2.55, h: 0.35, fontSize: 12, color: MUTED, margin: 0, isTextBox: true });
    s.addText(items.map((it, j) => ({ text: it, options: { bullet: true, breakLine: j < items.length - 1 } })), { x: x + 0.3, y: 3.1, w: 3.3, h: 2.8, fontSize: 14, color: H.dk1, paraSpaceAfter: 10, valign: "top", margin: 0, isTextBox: true });
    if (i < 2) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 3.82, y: 3.7, w: 0.26, h: 0.4, fill: { color: "B8C2D6" }, line: { color: "B8C2D6", width: 0 } });
  });
  s.addText([{ text: "Puertas:  ", options: { bold: true, color: H.dk2 } }, { text: "fase 2 al recibir cada credencial · fase 3 con acuerdos firmados y DPIA", options: { color: MUTED } }], { x: 0.6, y: 6.25, w: 12.1, h: 0.4, fontSize: 13, margin: 0, isTextBox: true });

  // =============== 15. Cierre ===============
  s = pres.addSlide({ masterName: "OSCURO", sectionTitle: "Decisión y plan" });
  s.addText("PRÓXIMOS PASOS", { placeholder: "kicker" });
  s.addText("Lo que necesitamos para tener la Vista de Gobierno 2.0 completa", { placeholder: "title" });
  const pasos = [
    ["check", H.accent1, "Aprobar la fase 1", "Entrega en 4 semanas con los datos que ya tiene la plataforma."],
    ["trash", H.accent3, "Usuario de siGEUS", "Solo lectura y sin 2FA, facilitado por Distromel."],
    ["bolt", H.accent2, "Usuario de Datadis", "Con autorización sobre los CUPS municipales."],
    ["key", H.accent5, "Tokens Meta, X y GA4", "Para Social Listening y analítica web reales."],
    ["leaf", "6B4FBB", "Credenciales de Bettair", "Calidad del aire en la portada y en Movilidad."],
  ];
  pasos.forEach(([ic, col, t, d], i) => {
    const y = 1.9 + i * 0.95;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 7.6, h: 0.8, rectRadius: 0.12, fill: { color: "FFFFFF", transparency: 90 }, line: { color: "3A5A8C", width: 0.75 } });
    iconCircle(s, ic, 0.8, y + 0.13, 0.54, col);
    s.addText([{ text: t + "  ", options: { bold: true, color: "FFFFFF" } }, { text: d, options: { color: "C9D6EA" } }], { x: 1.55, y, w: 6.5, h: 0.8, fontSize: 14, valign: "middle", margin: 0, isTextBox: true });
  });
  s.addImage({ path: IMG("tiles/playas.jpg"), x: 8.6, y: 1.9, w: 4.1, h: 4.6, sizing: { type: "cover", w: 4.1, h: 4.6 }, rounding: false });
  s.addShape(pres.shapes.RECTANGLE, { x: 8.6, y: 5.3, w: 4.1, h: 1.2, fill: { color: H.dk2, transparency: 25 }, line: { color: H.dk2, width: 0 } });
  s.addText("Datos reales, previsiones y decisiones en una sola pantalla", { x: 8.8, y: 5.3, w: 3.7, h: 1.2, fontSize: 15, bold: true, color: "FFFFFF", valign: "middle", margin: 0, isTextBox: true });

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("ok", OUT);
})();
