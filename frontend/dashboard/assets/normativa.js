/* Normativa municipal: ordenanzas de la sede electrónica en el panel DTI.
   Buscador de texto completo, ficha por artículos, PDF original, importación de
   PDF (con su manifest.csv) y prueba del asistente con preguntas sobre normas.
   API: /normativa (listado, /resumen, /pasajes, /importar, /{id}, /{id}/pdf). */

import { api, fetchAuth, getCachedUser } from "./api-client.js?v=19";

const TIPOS = { ordenanza: "Ordenanza", reglamento: "Reglamento", edicto: "Edicto", proyecto: "Proyecto", certificado: "Certificado", bando: "Bando", otro: "Otro" };
const LOTE = 4; // PDF por petición al importar
let filtro = { buscar: "", tipo: "" };

function esc(t) {
  return String(t == null ? "" : t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function num(n) { return Number(n || 0).toString().replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
function mb(b) {
  if (b < 1048576) return Math.max(1, Math.round(b / 1024)) + " KB";
  return (b / 1048576).toFixed(b > 10485760 ? 0 : 1).replace(".", ",") + " MB";
}
function fecha(f) { return f ? new Date(f + (f.length === 10 ? "T00:00:00" : "")).toLocaleDateString("es-ES", { day: "numeric", month: "short", year: "numeric" }) : "—"; }
/* el extracto llega con «» marcando las palabras encontradas */
function resaltar(t) { return esc(t).replace(/«/g, "<mark>").replace(/»/g, "</mark>").replace(/\n/g, " "); }
function puedeGestionar() {
  const u = getCachedUser();
  return !!u && ["administrador_tic", "gestor_contenidos"].includes(u.rol);
}
async function abrirPdf(id) {
  window.open("/api/v1/normativa/" + encodeURIComponent(id) + "/pdf", "_blank", "noopener");
}
window.__normativaPdf = abrirPdf;

function cabecera() {
  return '<div class="subhead"><div><div class="crumb"><a onclick="UI.go(\'home\')">Plataforma</a> · <a onclick="UI.goD(\'resumen\')">DTI Turismo</a> · <b>Normativa municipal</b></div>' +
    "<h1>Normativa municipal</h1><p>Ordenanzas y documentos descargados del portal de transparencia de la sede electrónica. " +
    "El asistente del tótem y del chatbot las usa para responder preguntas sobre normas municipales, citando la ordenanza y el artículo.</p></div>" +
    '<div class="acts"><a class="btn" href="https://nijar.sedelectronica.es/transparency/c9a3aaec-46f8-4a66-8a27-187955d569e6/" target="_blank" rel="noopener">Portal de transparencia ↗</a></div></div>';
}

async function render(el) {
  el.innerHTML = cabecera() +
    '<div class="grid g4" style="margin-bottom:16px" id="nm-kpis"><div class="stat"><div class="stat__l">Cargando…</div></div></div>' +
    '<div class="grid c7-5">' +
    '<div class="card card--pad0"><div style="padding:16px 16px 4px" class="card__h"><div><div class="card__t">Documentos</div><div class="card__s" id="nm-cuenta"></div></div>' +
    '<div class="filters"><div class="fld"><label>Buscar en el texto</label><input class="inp" id="nm-q" placeholder="p. ej. venta en la playa, terrazas, ruidos…" value="' + esc(filtro.buscar) + '" style="width:240px"></div>' +
    '<div class="fld"><label>Tipo</label><select class="sel" id="nm-tipo"><option value="">Todos</option>' +
    Object.entries(TIPOS).map(([k, t]) => '<option value="' + k + '"' + (filtro.tipo === k ? " selected" : "") + ">" + t + "</option>").join("") + "</select></div></div></div>" +
    '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Documento</th><th>Tipo</th><th>Publicación</th><th>Págs.</th><th></th></tr></thead><tbody id="nm-filas"><tr><td colspan="5" class="mini">Cargando…</td></tr></tbody></table></div></div>' +
    '<div style="display:flex;flex-direction:column;gap:16px">' +
    '<div class="card"><div class="card__h"><div><div class="card__t">Probar el asistente</div><div class="card__s">Haz una pregunta como la haría un vecino o un turista</div></div></div>' +
    '<div style="display:flex;gap:8px;flex-wrap:wrap"><input class="inp" id="nm-preg" placeholder="¿Se puede vender en la playa?" style="flex:1;min-width:180px"><button class="btn btn--pri" id="nm-preguntar">Preguntar</button></div>' +
    '<div id="nm-respuesta" style="margin-top:12px"></div></div>' +
    (puedeGestionar()
      ? '<div class="card"><div class="card__h"><div><div class="card__t">Importar ordenanzas</div><div class="card__s">Selecciona los PDF descargados y, si lo tienes, su manifest.csv. Un PDF ya importado se actualiza, no se duplica.</div></div></div>' +
        '<input type="file" id="nm-ficheros" accept=".pdf,.csv,application/pdf,text/csv" multiple>' +
        '<div style="margin-top:10px;display:flex;gap:10px;align-items:center;flex-wrap:wrap"><button class="btn btn--pri" id="nm-importar">Importar</button><span class="mini" id="nm-progreso" style="color:var(--muted)"></span></div>' +
        '<div class="mini" id="nm-errores" style="margin-top:8px;color:var(--err)"></div></div>'
      : "") +
    "</div></div>";

  const pintarKpis = async () => {
    try {
      const r = await api.get("/normativa/resumen");
      const kpi = (l, v, d) => '<div class="stat"><div class="stat__l">' + l + '</div><div class="stat__v tnum">' + v + '</div><div class="stat__d">' + d + "</div></div>";
      el.querySelector("#nm-kpis").innerHTML =
        kpi("Documentos", num(r.total), "en el buscador y en el asistente") +
        kpi("Ordenanzas", num(r.por_tipo.ordenanza || 0), "reguladoras y fiscales") +
        kpi("Otros documentos", num(r.total - (r.por_tipo.ordenanza || 0)), Object.entries(r.por_tipo).filter(([t]) => t !== "ordenanza").map(([t, n]) => n + " " + (TIPOS[t] || t).toLowerCase()).join(" · ") || "edictos, proyectos, certificados") +
        kpi("Sin texto buscable", num(r.sin_texto), r.sin_texto ? "PDF escaneados: se pueden descargar, no buscar" : "todos los PDF tienen texto");
    } catch (e) {
      el.querySelector("#nm-kpis").innerHTML = '<div class="stat"><div class="stat__l" style="color:var(--err)">' + esc(e.message || e) + "</div></div>";
    }
  };
  const pintarFilas = async () => {
    const tbody = el.querySelector("#nm-filas");
    const q = new URLSearchParams();
    if (filtro.buscar.trim()) q.set("buscar", filtro.buscar.trim());
    if (filtro.tipo) q.set("tipo", filtro.tipo);
    let filas;
    try { filas = await api.get("/normativa" + (q.toString() ? "?" + q : "")); } catch (e) {
      tbody.innerHTML = '<tr><td colspan="5" class="mini" style="color:var(--err)">' + esc(e.message || e) + "</td></tr>";
      return;
    }
    const docs = filas.length === 1 ? " documento" : " documentos";
    el.querySelector("#nm-cuenta").textContent = filas.length + docs + (filtro.buscar.trim() ? " con esas palabras, por relevancia" : "");
    tbody.innerHTML = filas.length ? filas.map((n) =>
      '<tr class="rowclick" data-id="' + esc(n.id) + '"><td style="white-space:normal;min-width:260px"><span class="lnk">' + esc(n.titulo) + "</span>" +
      (n.extracto ? '<div class="mini" style="margin-top:4px;color:var(--muted)">…' + resaltar(n.extracto) + "…</div>" : "") +
      (n.sin_texto ? ' <span class="bdg bdg-warn">sin texto</span>' : "") + "</td>" +
      '<td><span class="bdg bdg-info">' + esc(TIPOS[n.tipo] || n.tipo) + "</span></td>" +
      '<td class="mini">' + fecha(n.fecha_publicacion) + '</td><td class="tnum mini">' + num(n.paginas) + "</td>" +
      '<td><button class="btn btn--sm" data-pdf="' + esc(n.id) + '">PDF</button></td></tr>').join("")
      : '<tr><td colspan="5" class="mini">' + (filtro.buscar.trim() || filtro.tipo ? "Ningún documento coincide con la búsqueda." : "Aún no hay normativa importada.") + "</td></tr>";
    tbody.querySelectorAll("[data-pdf]").forEach((b) => { b.onclick = (ev) => { ev.stopPropagation(); abrirPdf(b.dataset.pdf); }; });
    tbody.querySelectorAll("tr[data-id]").forEach((tr) => { tr.onclick = () => ficha(tr.dataset.id); });
  };

  let t = null;
  el.querySelector("#nm-q").oninput = (e) => { filtro.buscar = e.target.value; clearTimeout(t); t = setTimeout(pintarFilas, 350); };
  el.querySelector("#nm-tipo").onchange = (e) => { filtro.tipo = e.target.value; pintarFilas(); };

  const preguntar = async () => {
    const pregunta = el.querySelector("#nm-preg").value.trim() || el.querySelector("#nm-preg").placeholder;
    const out = el.querySelector("#nm-respuesta");
    out.innerHTML = '<div class="mini" style="color:var(--muted)">Consultando al asistente…</div>';
    try {
      const [resp, pasajes] = await Promise.all([
        fetchAuth("/chatbot/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sesion_id: "panel-normativa-prueba", canal: "web", idioma: "es", pregunta }),
        }).then((r) => (r.ok ? r.json() : Promise.reject(new Error("error " + r.status)))),
        api.get("/normativa/pasajes?limite=3&pregunta=" + encodeURIComponent(pregunta)).catch(() => []),
      ]);
      out.innerHTML = '<div class="kv" style="align-items:flex-start"><span class="k" style="max-width:100%;white-space:pre-line">' + esc(resp.respuesta) + "</span></div>" +
        (pasajes.length
          ? '<div class="mini" style="margin-top:8px;color:var(--muted)">Artículos que ha encontrado:</div>' +
            pasajes.map((p) => '<div class="mini" style="margin-top:4px">· <a class="lnk" onclick="__normativaPdf(\'' + esc(p.normativa_id) + '\')">' + esc(p.titulo) + "</a>" + (p.articulo ? " — " + esc(p.articulo) : "") + "</div>").join("")
          : '<div class="mini" style="margin-top:8px;color:var(--muted)">Ninguna ordenanza trata ese tema.</div>');
    } catch (e) {
      out.innerHTML = '<div class="mini" style="color:var(--err)">No se pudo consultar: ' + esc(e.message || e) + "</div>";
    }
  };
  el.querySelector("#nm-preguntar").onclick = preguntar;
  el.querySelector("#nm-preg").onkeydown = (e) => { if (e.key === "Enter") preguntar(); };

  const btn = el.querySelector("#nm-importar");
  if (btn) btn.onclick = async () => {
    const todos = Array.from(el.querySelector("#nm-ficheros").files);
    const pdfs = todos.filter((f) => /\.pdf$/i.test(f.name));
    const manifest = todos.find((f) => /\.csv$/i.test(f.name));
    const prog = el.querySelector("#nm-progreso"), errs = el.querySelector("#nm-errores");
    if (!pdfs.length) { prog.textContent = "Selecciona los PDF (puedes seleccionar toda la carpeta con Ctrl+A)."; return; }
    btn.disabled = true; errs.innerHTML = "";
    let nuevas = 0, actualizadas = 0, hechos = 0;
    const errores = [];
    for (let i = 0; i < pdfs.length; i += LOTE) {
      const fd = new FormData();
      pdfs.slice(i, i + LOTE).forEach((f) => fd.append("archivos", f));
      if (manifest) fd.append("manifest", manifest);
      prog.textContent = "Importando " + Math.min(i + LOTE, pdfs.length) + " de " + pdfs.length + "…";
      try {
        const r = await fetchAuth("/normativa/importar", { method: "POST", body: fd });
        const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j.detail || "error " + r.status);
        nuevas += j.importadas; actualizadas += j.actualizadas; errores.push(...j.errores);
      } catch (e) { errores.push("Lote " + (i / LOTE + 1) + ": " + (e.message || e)); }
      hechos = Math.min(i + LOTE, pdfs.length);
    }
    btn.disabled = false;
    prog.textContent = "Hecho: " + hechos + " PDF procesados · " + nuevas + " nuevos · " + actualizadas + " actualizados" + (errores.length ? " · " + errores.length + " con error" : "");
    errs.innerHTML = errores.map(esc).join("<br>");
    pintarKpis(); pintarFilas();
  };

  pintarKpis();
  pintarFilas();
}

async function ficha(id) {
  UI.openDrawer("Normativa", "Cargando…", '<div class="mini" style="color:var(--muted)">Cargando…</div>');
  let n;
  try { n = await api.get("/normativa/" + encodeURIComponent(id)); } catch (e) {
    UI.openDrawer("Normativa", "", '<div class="mini" style="color:var(--err)">' + esc(e.message || e) + "</div>");
    return;
  }
  const kv = (k, v) => '<div class="kv"><span class="k">' + k + '</span><span class="v">' + v + "</span></div>";
  const articulos = n.fragmentos.filter((f) => f.articulo);
  let h = '<div class="dsec"><div class="t">Documento</div>' +
    kv("Tipo", esc(TIPOS[n.tipo] || n.tipo)) + kv("Publicación", fecha(n.fecha_publicacion)) +
    kv("Páginas", num(n.paginas)) + kv("Tamaño", mb(n.tamano_bytes)) + kv("Fichero", '<span class="mini">' + esc(n.nombre_archivo) + "</span>") +
    (n.url_origen ? kv("Origen", '<a class="lnk" href="' + esc(n.url_origen) + '" target="_blank" rel="noopener">sede electrónica ↗</a>') : "") +
    '<div style="margin-top:10px"><button class="btn btn--pri btn--sm" onclick="__normativaPdf(\'' + esc(n.id) + '\')">Abrir el PDF original</button></div></div>';
  if (n.sin_texto) {
    h += '<div class="dsec"><div class="mini" style="color:var(--warn)">Este PDF es una imagen escaneada sin texto: se puede descargar, pero el buscador y el asistente no pueden leerlo.</div></div>';
  } else {
    h += '<div class="dsec"><div class="t">' + (articulos.length ? articulos.length + " artículos" : "Texto") + "</div>" +
      n.fragmentos.map((f) => '<details style="border-bottom:1px solid var(--line);padding:6px 0"><summary style="cursor:pointer;font-weight:600;font-size:13px">' +
        esc(f.articulo || (f.orden === 0 ? "Inicio del documento" : "Pasaje " + (f.orden + 1))) + "</summary>" +
        '<div class="mini" style="white-space:pre-line;margin-top:6px;line-height:1.55">' + esc(f.texto) + "</div></details>").join("") + "</div>";
  }
  UI.openDrawer(esc(n.titulo), esc(TIPOS[n.tipo] || n.tipo) + " · " + num(n.paginas) + " páginas", h);
}

/* Sección en la consola DTI, junto al CMS de contenidos */
(function instalar() {
  const DTI = window.__DTI;
  if (!DTI || !DTI.DSECTIONS || !DTI.renderDSidebar || !window.UI) { setTimeout(instalar, 300); return; }
  if (DTI.DSECTIONS.some((s) => s.id === "normativa")) return;
  const pos = DTI.DSECTIONS.findIndex((s) => s.id === "contenidos");
  DTI.DSECTIONS.splice(pos < 0 ? DTI.DSECTIONS.length : pos + 1, 0, { id: "normativa", n: "Normativa municipal", i: "doc" });
  DTI.DR.normativa = render;
  const main = document.getElementById("dti-main");
  if (main && !document.getElementById("dv-normativa")) {
    const sec = document.createElement("section");
    sec.className = "dview";
    sec.id = "dv-normativa";
    main.insertBefore(sec, main.lastElementChild);
  }
  DTI.renderDSidebar();
})();
