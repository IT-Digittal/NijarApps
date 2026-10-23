/* Vista de Gobierno 2.0 · componentes de las maquetas.
   Cada página llama a VG.render({...}) con su configuración; aquí se pinta la
   carcasa del panel, el hero, los KPIs y las tarjetas (gráficos Chart.js,
   rankings, mapas de calor, medidores, recomendaciones…). */
(function () {
  "use strict";

  const COL = {
    navy: "#003B7A", blue: "#1A5FD0", teal: "#17A394", cyan: "#00A6C0", gold: "#F0B429",
    coral: "#E05A4D", violet: "#7C6BF0", sky: "#5B8DEF", ok: "#2F9E5F", muted: "#B4BFD3",
    grid: "#EDF1F7", text: "#515D77", ink: "#16233D", brown: "#A0673A",
  };
  const col = (c) => COL[c] || c;

  const nf = (v, d = 0) => (v == null || v === "" ? "—" : Number(v).toLocaleString("es-ES", { minimumFractionDigits: d, maximumFractionDigits: d }));
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /* ---------- iconos (trazo, 24×24) ---------- */
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
    map: "M9 4L3 6v14l6-2 6 2 6-2V4l-6 2zM9 4v14m6-12v14",
    thermo: "M10 14V5a2 2 0 1 1 4 0v9a4 4 0 1 1-4 0z",
    flag: "M5 21V4m0 0h11l-2 4 2 4H5",
    gauge: "M12 14l4-4M4 18a9 9 0 1 1 16 0",
    calendar: "M4 6h16v14H4zM4 10h16M8 3v4m8-4v4",
    route: "M6 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM18 9a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM8 17h7a3 3 0 0 0 0-6H9a3 3 0 0 1 0-6h7",
    wrench: "M14.7 6.3a4 4 0 0 0-5.4 5.1L3 17.7 6.3 21l6.3-6.3a4 4 0 0 0 5.1-5.4l-2.4 2.4-2.6-.6-.6-2.6z",
    sun: "M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm0-15v2m0 16v2M4.2 4.2l1.4 1.4m12.8 12.8l1.4 1.4M2 12h2m16 0h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4",
    shield: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z",
    recycle: "M7 19H4l3-5m10 5h3l-3-5M9 5l3-2 3 2m-9 9l-2-3.5M18 10.5L16 14M12 3v4m-5 12h10",
    present: "M3 4h18v12H3zm9 12v4m-4 0h8",
    refresh: "M20 11a8 8 0 0 0-14.3-4.9L4 8m0-4v4h4M4 13a8 8 0 0 0 14.3 4.9L20 16m0 4v-4h-4",
    bell: "M6 16V11a6 6 0 1 1 12 0v5l2 2H4zm4 4h4",
    download: "M12 4v11m0 0l-4-4m4 4l4-4M5 20h14",
  };
  const ic = (n, c) => `<svg viewBox="0 0 24 24" fill="none" stroke="${c || "currentColor"}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${P[n] || P.chart}"/></svg>`;

  /* ---------- navegación ---------- */
  const NAV = [
    ["index.html", "resumen", "Resumen municipal", "home", null],
    ["turismo.html", "turismo", "Turismo inteligente", "turismo", "verde"],
    ["alumbrado.html", "alumbrado", "Alumbrado público", "bulb", "ambar"],
    ["agua.html", "agua", "Ciclo del agua", "drop", "ambar"],
    ["residuos.html", "residuos", "Residuos", "recycle", "ambar"],
    ["movilidad.html", "movilidad", "Movilidad", "car", "verde"],
    ["seguridad.html", "seguridad", "Seguridad", "shield", "ambar"],
    ["energia.html", "energia", "Energía municipal", "bolt", "verde"],
    ["recomendaciones.html", "recomendaciones", "Recomendaciones IA", "ai", null],
  ];

  function shell(active) {
    const tb = `<header class="tb">
      <img class="tb-logo" src="assets/img/logo.png" alt="Ayuntamiento de Níjar">
      <div class="tb-prod"><b>Plataforma DTI</b><span>Smart City · Níjar</span></div>
      <span class="pill pill--ctx">Dirección <small>· vista de gobierno</small></span>
      <span class="pill pill--ok"><i class="dotp"></i>Plataforma disponible 100 %</span>
      <span class="pill pill--draft">Maqueta · propuesta</span>
      <div class="tb-sp"></div>
      <span class="vivo"><i></i>EN VIVO</span>
      <button class="btn" type="button">${ic("refresh")}Actualizar</button>
      <button class="btn btn--pri" type="button">${ic("present")}<span>Modo presentación</span></button>
      <span class="avatar" aria-label="Usuario JT">JT</span>
    </header>`;
    const sb = `<nav class="sb" aria-label="Vista de Gobierno">
      <div class="sb-h"><b>Dirección</b><span>Cuadro de mando ejecutivo</span></div>
      <div class="sb-grp">Gobierno</div>
      ${NAV.map(([h, id, n, i, e]) => `<a href="${h}" class="${id === active ? "on" : ""}"${id === active ? ' aria-current="page"' : ""}>${ic(i)}${esc(n)}${e ? `<span class="sd sd--${e}" aria-label="estado ${e}"></span>` : ""}</a>`).join("")}
    </nav>`;
    return tb + `<div class="shell">${sb}<main><div class="wrap" id="vg-main"></div></main></div>`;
  }

  /* ---------- piezas ---------- */
  const TAG_TXT = { real: "Real hoy", integrar: "Al integrar", estimado: "Estimado", modelo: "Modelo predictivo" };
  const tag = (t) => (t ? `<span class="tag tag--${t}">${TAG_TXT[t]}</span>` : "");

  function spark(data, color, opts = {}) {
    const w = opts.w || 96, h = opts.h || 30, pad = 3;
    const vals = data.filter((v) => v != null);
    const mn = Math.min(...vals), mx = Math.max(...vals), rg = mx - mn || 1;
    const X = (i) => pad + (i * (w - 2 * pad)) / (data.length - 1);
    const Y = (v) => h - pad - ((v - mn) / rg) * (h - 2 * pad);
    const pts = data.map((v, i) => [X(i), Y(v)]);
    const line = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
    const area = `${line} L${X(data.length - 1)} ${h} L${X(0)} ${h} Z`;
    const id = "g" + Math.random().toString(36).slice(2, 8);
    const c = col(color);
    const last = pts[pts.length - 1];
    return `<svg class="spark" viewBox="0 0 ${w} ${h}" aria-hidden="true"><defs><linearGradient id="${id}" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${c}" stop-opacity=".28"/><stop offset="1" stop-color="${c}" stop-opacity="0"/></linearGradient></defs>
      <path d="${area}" fill="url(#${id})"/><path d="${line}" fill="none" stroke="${c}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>
      <circle cx="${last[0]}" cy="${last[1]}" r="2.8" fill="${c}"/></svg>`;
  }

  function hero(h) {
    const bg = h.img ? `background-image:url('${h.img}')` : `background:${h.bg}`;
    const ring = h.ring ? `<div class="ring" style="--v:${h.ring.pct};--c:${col(h.ring.c || "gold")}"><div><b>${esc(h.ring.v)}</b><span>${esc(h.ring.l)}</span></div></div>` : "";
    return `<section class="hero" style="${bg}">
      <div>
        <div class="hero-top">${h.top ? esc(h.top) : `<span class="estado"><span class="dot dot--${h.estado}"></span>${esc(h.frase)}</span>`}</div>
        <h2>${esc(h.titulo)}</h2>
        <div class="hero-sub">${esc(h.sub)}</div>
        <div class="chips">${(h.chips || []).map(([v, l]) => `<div class="chip"><b>${esc(v)}</b><span>${esc(l)}</span></div>`).join("")}</div>
      </div>${ring}</section>`;
  }

  function kpi(k) {
    const c = col(k.c || "navy");
    return `<div class="kpi">
      <div class="kpi-l"><span class="kpi-i" style="background:${c}1a;color:${c}">${ic(k.i || "chart", c)}</span>${esc(k.l)}</div>
      <div class="kpi-v" style="color:${k.vc ? col(k.vc) : "var(--ink)"}">${esc(k.v)}${k.u ? `<small>${esc(k.u)}</small>` : ""}</div>
      <div class="kpi-d">${k.d ? `<span class="delta delta--${k.dg || "neutro"}">${esc(k.d)}</span>` : ""}<span>${esc(k.s || "")}</span></div>
      <div class="kpi-b">${tag(k.tag)}${k.spark ? spark(k.spark, k.c || "navy") : ""}</div>
    </div>`;
  }

  /* ---------- gráficos (Chart.js) ---------- */
  const charts = [];
  function baseOpts(o = {}) {
    const fmt = o.fmt || ((v) => nf(v));
    const ticks = { color: COL.text, font: { family: "Inter, system-ui, sans-serif", size: 11 } };
    return {
      responsive: true, maintainAspectRatio: false, animation: { duration: 650 },
      interaction: { mode: o.horizontal ? "nearest" : "index", intersect: false },
      indexAxis: o.horizontal ? "y" : "x",
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0f1d38", titleFont: { family: "Inter", weight: "700" }, bodyFont: { family: "Inter" }, padding: 10, cornerRadius: 8, boxPadding: 4,
          filter: (it) => it.raw != null && !(it.dataset.noTip),
          callbacks: { label: (c) => ` ${c.dataset.label}: ${fmt(c.parsed[o.horizontal ? "x" : "y"])}${o.unit ? " " + o.unit : ""}` },
        },
      },
      scales: {
        x: { stacked: !!o.stacked, grid: { display: !!o.horizontal, color: COL.grid }, border: { display: false }, ticks: o.horizontal ? { ...ticks, callback: (v) => fmt(v) } : { ...ticks, maxRotation: 0, autoSkipPadding: 8 }, min: o.horizontal ? o.min : undefined, max: o.horizontal ? o.max : undefined },
        y: { stacked: !!o.stacked, grid: { display: !o.horizontal, color: COL.grid }, border: { display: false }, ticks: o.horizontal ? ticks : { ...ticks, callback: (v) => fmt(v), maxTicksLimit: 6 }, min: o.horizontal ? undefined : o.min, max: o.horizontal ? undefined : o.max, beginAtZero: o.min == null },
      },
    };
  }
  function line(labels, series, o = {}) {
    return {
      type: "line",
      data: {
        labels,
        datasets: series.map((s) => {
          const c = col(s.c);
          return {
            label: s.n, data: s.d, borderColor: c, backgroundColor: s.fill ? (ctx) => grad(ctx, c) : c,
            fill: s.fill ? "origin" : false, borderWidth: s.w || 2.5, borderDash: s.dash ? [6, 5] : [], tension: s.t ?? 0.35,
            pointRadius: s.pts ?? (s.dash ? 3 : 0), pointHoverRadius: 5, pointBackgroundColor: s.dash ? "#fff" : c, pointBorderColor: c, pointBorderWidth: 2,
            spanGaps: false, order: s.order ?? 1, noTip: s.noTip,
          };
        }),
      },
      options: baseOpts(o),
    };
  }
  function band(labels, lo, hi, c) {
    // banda de intervalo de confianza: dos series, la superior rellena hasta la inferior
    return [
      { n: "Intervalo inferior", d: lo, c: "transparent", w: 0, pts: 0, noTip: true, order: 3 },
      { n: "Intervalo", d: hi, c, w: 0, pts: 0, bandFill: true, noTip: true, order: 3 },
    ];
  }
  function bar(labels, series, o = {}) {
    return {
      type: "bar",
      data: {
        labels,
        datasets: series.map((s) => ({
          label: s.n, data: s.d, backgroundColor: Array.isArray(s.c) ? s.c.map(col) : col(s.c), borderRadius: o.stacked ? 3 : 6,
          borderSkipped: false, maxBarThickness: o.thick || 34, categoryPercentage: 0.72, barPercentage: 0.9, order: 2,
        })),
      },
      options: baseOpts(o),
    };
  }
  function grad(ctx, c) {
    const { chart } = ctx;
    const a = chart.chartArea;
    if (!a) return c + "33";
    const g = chart.ctx.createLinearGradient(0, a.top, 0, a.bottom);
    g.addColorStop(0, c + "40");
    g.addColorStop(1, c + "02");
    return g;
  }
  function donut(labels, data, colors, o = {}) {
    return {
      type: "doughnut",
      data: { labels, datasets: [{ data, backgroundColor: colors.map(col), borderWidth: 3, borderColor: "#fff", hoverOffset: 6 }] },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: o.cutout || "70%",
        plugins: { legend: { display: false }, tooltip: { backgroundColor: "#0f1d38", callbacks: { label: (c) => ` ${c.label}: ${nf(c.parsed, o.dec || 0)}${o.unit ? " " + o.unit : ""}` } } },
      },
    };
  }
  // plugin: rellena la banda entre "Intervalo inferior" y "Intervalo"
  function prepBand(cfg) {
    const ds = cfg.data.datasets;
    ds.forEach((d, i) => {
      if (d.label === "Intervalo" && ds[i - 1] && ds[i - 1].label === "Intervalo inferior") {
        const c = d.borderColor;
        d.fill = "-1"; d.backgroundColor = c + "26"; d.borderColor = "transparent";
      }
    });
    return cfg;
  }

  /* ---------- partes de tarjeta ---------- */
  const parts = {
    chart(p) {
      const id = "c" + charts.length;
      charts.push({ id, cfg: p.cfg });
      const lg = p.legend ? `<div class="legend">${p.legend.map(([n, c, d]) => `<span style="color:${col(c)}"><i class="${d ? "dash" : ""}" style="background:${col(c)}"></i><span style="color:var(--muted)">${esc(n)}</span></span>`).join("")}</div>` : "";
      return `${lg}<div class="chart" style="height:${p.h || 260}px"><canvas id="${id}" role="img" aria-label="${esc(p.alt || "")}"></canvas></div>`;
    },
    rank(p) {
      const mx = p.max || Math.max(...p.items.map((x) => x[1]));
      return `<div class="rank">${p.items.map(([n, v, c, txt]) => `<div class="rk"><span class="rk-n" title="${esc(n)}">${esc(n)}</span><span class="rk-bar"><i style="width:${Math.max(2, (v / mx) * 100)}%;background:${col(c || "navy")}"></i></span><span class="rk-v">${esc(txt ?? nf(v))}</span></div>`).join("")}</div>`;
    },
    heat(p) {
      const cols = p.cols.length;
      const mx = p.max || Math.max(...p.data.flat());
      const mn = p.min ?? 0;
      const c = (v) => {
        const t = Math.max(0, Math.min(1, (v - mn) / (mx - mn)));
        if (p.alert != null && v >= p.alert) return `rgba(224,90,77,${0.55 + 0.45 * t})`;
        return `rgba(0,59,122,${0.07 + 0.78 * t})`;
      };
      let h = `<div style="overflow-x:auto"><div class="heat" style="grid-template-columns:96px repeat(${cols},minmax(16px,1fr));min-width:${96 + cols * 18}px"><span></span>${p.cols.map((x) => `<span class="hh">${esc(x)}</span>`).join("")}`;
      p.rows.forEach((r, i) => {
        h += `<span class="hl">${esc(r)}</span>` + p.data[i].map((v, j) => `<span class="hc" style="background:${c(v)}" title="${esc(r)} ${esc(p.cols[j])}: ${nf(v)}${p.unit || ""}"></span>`).join("");
      });
      h += `</div></div>`;
      if (p.scale) h += `<div class="scale"><span>${esc(p.scale[0])}</span><i style="background:linear-gradient(90deg,rgba(0,59,122,.07),rgba(0,59,122,.85))"></i><span>${esc(p.scale[1])}</span>${p.alert != null ? `<i style="width:14px;background:var(--coral)"></i><span>${esc(p.scale[2] || "saturación")}</span>` : ""}</div>`;
      return h;
    },
    gauges(p) {
      return `<div class="gauges">${p.items.map(([v, l, c, txt]) => `<div class="gauge"><div class="gring" style="--v:${v};--c:${col(c || "teal")}"><b>${esc(txt ?? v + "%")}</b></div><span>${esc(l)}</span></div>`).join("")}</div>`;
    },
    recs(p) {
      return `<div class="recs">${p.items.map((r, i) => `<div class="rec" data-rec="${i}" data-mod="${esc(r.mod || "")}">
        <div class="rec-h"><span class="prio prio--${r.prio}">${esc(r.prio)}</span>${r.mod ? `<span class="tag tag--estimado">${esc(r.mod)}</span>` : ""}<span class="ai">${ic("ai")} IA</span></div>
        <div class="rec-t">${esc(r.t)}</div><p>${esc(r.p)}</p>
        <div class="rec-m">${r.imp ? `<span>Impacto <span class="rec-imp">${esc(r.imp)}</span></span>` : ""}${r.plazo ? `<span>Plazo <b>${esc(r.plazo)}</b></span>` : ""}${r.resp ? `<span>Responsable <b>${esc(r.resp)}</b></span>` : ""}</div>
        <div class="rec-a"><button class="btn btn--sm btn--pri" type="button" data-act="aceptada">Aceptar</button><button class="btn btn--sm" type="button" data-act="en revisión">En revisión</button><button class="btn btn--sm" type="button" data-act="descartada">Descartar</button><span class="rec-st" aria-live="polite"></span></div>
      </div>`).join("")}</div>`;
    },
    evs(p) {
      return `<div class="evs">${p.items.map(([d, m, t, s, r]) => `<div class="ev"><div class="ev-f">${esc(d)}<small>${esc(m)}</small></div><div><div class="ev-t">${esc(t)}</div><div class="ev-s">${esc(s)}</div></div><div class="ev-r">${r || ""}</div></div>`).join("")}</div>`;
    },
    mini(p) { return `<div class="mini">${p.items.map(([v, l]) => `<div><b>${esc(v)}</b><span>${esc(l)}</span></div>`).join("")}</div>`; },
    funnel(p) {
      const mx = p.items[0][1];
      return `<div class="funnel">${p.items.map(([n, v, c, s]) => `<div class="fn"><div class="fn-b" style="width:${Math.max(14, (v / mx) * 70)}%;background:${col(c)}">${nf(v)}</div><div class="fn-l"><b>${esc(n)}</b>${esc(s || "")}</div></div>`).join("")}</div>`;
    },
    map(p) {
      // Proyección esquemática del término municipal (lon/lat → svg)
      const X = (lon) => 20 + ((lon + 2.32) / 0.44) * 360, Y = (lat) => 14 + ((37.07 - lat) / 0.37) * 300;
      const contorno = [[-2.31, 37.0], [-2.2, 37.05], [-2.08, 37.06], [-1.97, 37.0], [-1.91, 36.95], [-1.96, 36.9], [-2.02, 36.84], [-2.07, 36.78], [-2.12, 36.72], [-2.19, 36.75], [-2.22, 36.82], [-2.27, 36.88], [-2.31, 36.94]];
      const d = contorno.map(([lo, la], i) => `${i ? "L" : "M"}${X(lo).toFixed(0)} ${Y(la).toFixed(0)}`).join(" ") + "Z";
      const colE = { verde: "#2F9E5F", ambar: "#E0A21F", rojo: "#E05A4D" };
      const pts = p.points.map((q) => {
        const x = X(q.lon), y = Y(q.lat), r = q.r || 7;
        const lx = q.left ? x - r - 5 : x + r + 5;
        return `<g><circle cx="${x}" cy="${y}" r="${r + 7}" fill="${colE[q.e]}" opacity=".16"/><circle cx="${x}" cy="${y}" r="${r}" fill="${colE[q.e]}" stroke="#fff" stroke-width="2"><title>${esc(q.n)}: ${esc(q.v || "")}</title></circle>
          <text x="${lx}" y="${y - 1}" text-anchor="${q.left ? "end" : "start"}" font-size="11.5" font-weight="700" fill="#16233D">${esc(q.n)}</text>${q.v ? `<text x="${lx}" y="${y + 12}" text-anchor="${q.left ? "end" : "start"}" font-size="10.5" fill="#515D77">${esc(q.v)}</text>` : ""}</g>`;
      }).join("");
      return `<div class="mapa"><svg viewBox="0 0 470 340" role="img" aria-label="${esc(p.alt || "Mapa esquemático del término municipal")}">
        <defs><linearGradient id="mar" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#e7f3fb"/><stop offset="1" stop-color="#cfe6f6"/></linearGradient></defs>
        <rect x="0" y="0" width="470" height="340" rx="14" fill="url(#mar)"/>
        <path d="${d}" fill="#f7f4ec" stroke="#c9bfa6" stroke-width="1.2"/>
        <text x="370" y="306" font-size="11" fill="#5b88b5" font-style="italic">Mar Mediterráneo</text>
        <text x="40" y="34" font-size="10.5" fill="#8a7d5e">Término municipal de Níjar · esquemático</text>${pts}</svg></div>`;
    },
    srcs(p) { return `<div class="srcs">${p.items.map(([n, t]) => `<span class="src">${esc(n)} ${tag(t)}</span>`).join("")}</div>`; },
    pregs(p) { return `<ul class="pregs">${p.items.map((q) => `<li>${esc(q)}</li>`).join("")}</ul>`; },
    html(p) { return p.html; },
  };

  function card(b) {
    const head = b.t ? `<div class="card-h"><div><div class="card-t">${esc(b.t)}${b.ai ? ` <span class="ai">${ic("ai")} IA</span>` : ""}</div>${b.s ? `<div class="card-s">${esc(b.s)}</div>` : ""}</div>${b.tag ? tag(b.tag) : ""}</div>` : "";
    const body = (b.parts || []).map((p) => parts[p.k](p)).join("");
    return `<section class="card s${b.span || 12}"${b.style ? ` style="${b.style}"` : ""}>${head}${body}${b.f ? `<div class="card-f">${esc(b.f)}</div>` : ""}</section>`;
  }

  /* ---------- página ---------- */
  function render(cfg) {
    document.body.insertAdjacentHTML("afterbegin", shell(cfg.active));
    const m = document.getElementById("vg-main");
    let h = `<div class="sub"><div><div class="crumb"><a href="index.html">Plataforma</a> · <b>Dirección</b>${cfg.crumb ? " · " + esc(cfg.crumb) : ""}</div><h1>${esc(cfg.title)}</h1><p>${esc(cfg.intro)}</p></div>
      <div class="sub-act"><div class="seg" role="group" aria-label="Periodo">${["7 días", "30 días", "12 meses"].map((x, i) => `<button type="button" class="${i === 1 ? "on" : ""}">${x}</button>`).join("")}</div><button class="btn" type="button">${ic("download")}Informe PDF</button></div></div>`;
    h += `<div class="nota">${ic("ai", "#5a45c9").replace("<svg", '<svg width="16" height="16"')}<span><b>Maqueta de propuesta.</b> Los valores de la portada actual son reales (23 oct 2026); el resto de cifras son ilustrativas para mostrar cómo se verá el módulo con los datos propuestos.</span></div>`;
    if (cfg.hero) h += hero(cfg.hero);
    if (cfg.kpis) h += `<div class="kpis">${cfg.kpis.map(kpi).join("")}</div>`;
    (cfg.rows || []).forEach((row) => {
      if (row.h) { h += `<div class="h-sec"><h3>${esc(row.h)}</h3>${row.hs ? `<span>${esc(row.hs)}</span>` : ""}</div>`; return; }
      if (row.raw) { h += row.raw; return; }
      h += `<div class="grid">${row.map(card).join("")}</div>`;
    });
    m.innerHTML = h;

    // interacciones: periodo (solo visual) y estados de recomendaciones
    m.querySelectorAll(".seg").forEach((s) => s.addEventListener("click", (e) => {
      const b = e.target.closest("button"); if (!b) return;
      s.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
    }));
    m.querySelectorAll(".rec").forEach((r) => r.addEventListener("click", (e) => {
      const b = e.target.closest("[data-act]"); if (!b) return;
      r.querySelector(".rec-st").textContent = "Marcada como " + b.dataset.act;
      r.style.opacity = b.dataset.act === "descartada" ? ".55" : "1";
    }));

    if (window.Chart) {
      Chart.defaults.font.family = "Inter, system-ui, sans-serif";
      charts.forEach(({ id, cfg: c }) => {
        const el = document.getElementById(id);
        if (el) new Chart(el, prepBand(typeof c === "function" ? c() : c));
      });
    }
    if (cfg.after) cfg.after(m);
  }

  window.VG = { render, line, bar, donut, band, spark, nf, ic, col, COL };
})();
