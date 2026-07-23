/**
 * Módulos de gestión (CRUD) integrados en el panel DTI definitivo.
 *
 * Añade al sidebar de la consola DTI el grupo «Gestión» con los módulos
 * del pliego que antes vivían en gestion.html: catálogo de recursos
 * turísticos, eventos, campañas, FAQs del chatbot, ficha del cliente y
 * configuración. Todo contra la API real con control de roles.
 */

import { api, getCachedUser } from "./api-client.js?v=18";

const CATEGORIAS = ["playa", "monumento", "ruta", "mirador", "centro_visitantes", "parque_natural", "museo", "yacimiento", "punto_interes", "oficina_turismo"];
const TIPOS_EVENTO = ["cultural", "gastronomico", "deportivo", "musical", "festivo", "naturaleza", "educativo", "otro"];
const ROLES_ESCRITURA = ["administrador_tic", "gestor_contenidos"];

let U, UI, DTI;

/* ---------------- utilidades ---------------- */

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function slug(s) {
  return String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60) || "sin-nombre";
}

function fechaCorta(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es-ES", { day: "2-digit", month: "2-digit", year: "numeric" });
}

function puedeEscribir() {
  const u = getCachedUser && getCachedUser();
  return !!u && ROLES_ESCRITURA.includes(u.rol);
}

function gsub(crumb, h1, p, acts) {
  return '<div class="subhead"><div><div class="crumb"><a onclick="UI.go(\'home\')">Plataforma</a> · <a onclick="UI.goD(\'resumen\')">DTI Turismo</a> · <b>' + esc(crumb) + "</b></div>" +
    "<h1>" + esc(h1) + "</h1><p>" + esc(p) + '</p></div><div class="acts">' + (acts || "") + "</div></div>";
}

/* Subhead del módulo de Administración (migaja propia, no DTI). */
function asub(crumb, h1, p, acts) {
  return '<div class="subhead"><div><div class="crumb"><a onclick="UI.go(\'home\')">Plataforma</a> · <a onclick="UI.enterAdmin()">Administración</a> · <b>' + esc(crumb) + "</b></div>" +
    "<h1>" + esc(h1) + "</h1><p>" + esc(p) + '</p></div><div class="acts">' + (acts || "") + "</div></div>";
}

function cargando(el, titulo) {
  el.innerHTML = gsub(titulo, titulo, "Cargando datos de la plataforma…") +
    '<div class="card"><div class="mini" style="color:var(--muted);padding:26px 0;text-align:center">Cargando…</div></div>';
}

function errorCarga(el, titulo, e) {
  el.innerHTML = gsub(titulo, titulo, "No se pudieron cargar los datos.") +
    '<div class="card"><div class="mini" style="color:var(--err);padding:20px 0;text-align:center">Error: ' + esc(e && e.message || e) + "</div></div>";
}

function pubBadge(p) {
  return p ? '<span class="bdg bdg-ok">publicado</span>' : '<span class="bdg bdg-mut">borrador</span>';
}

/* Diálogo de formulario genérico */
function abrirForm(titulo, camposHtml, onSubmit) {
  let dlg = document.getElementById("g-form-dialog");
  if (dlg) dlg.remove();
  dlg = document.createElement("dialog");
  dlg.id = "g-form-dialog";
  dlg.style.cssText = "border:0;border-radius:16px;box-shadow:var(--sh-lg);padding:0;width:min(94vw,560px)";
  dlg.innerHTML = '<form method="dialog" style="padding:26px 28px;font-family:var(--ff)" id="g-form">' +
    '<h2 style="margin:0 0 16px;font-size:17px;color:var(--ink)">' + esc(titulo) + "</h2>" +
    camposHtml +
    '<div class="mini" id="g-form-err" style="display:none;color:var(--err);margin-top:12px"></div>' +
    '<div style="display:flex;gap:10px;justify-content:flex-end;margin-top:20px">' +
    '<button type="button" class="btn" id="g-form-cancel">Cancelar</button>' +
    '<button type="submit" class="btn btn--pri" id="g-form-ok">Guardar</button></div></form>';
  document.body.appendChild(dlg);
  dlg.querySelector("#g-form-cancel").onclick = () => dlg.close();
  dlg.querySelector("#g-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const btn = dlg.querySelector("#g-form-ok");
    const err = dlg.querySelector("#g-form-err");
    btn.disabled = true;
    err.style.display = "none";
    try {
      await onSubmit(new FormData(ev.target));
      dlg.close();
      dlg.remove();
    } catch (e) {
      err.textContent = (e && e.message) || "Error al guardar";
      err.style.display = "block";
    } finally {
      btn.disabled = false;
    }
  });
  dlg.showModal();
  return dlg;
}

function campo(label, inner) {
  return '<label style="display:block;font-size:11px;font-weight:800;letter-spacing:.04em;color:var(--muted);text-transform:uppercase;margin:12px 0 4px">' + esc(label) + "</label>" + inner;
}

const INPUT_CSS = 'style="width:100%;box-sizing:border-box;border:1.5px solid var(--line);border-radius:10px;padding:9px 11px;font-size:13.5px;font-family:inherit"';

/* Diálogo informativo de solo lectura (un botón «Cerrar»). */
function mostrarInfo(titulo, htmlContenido) {
  let dlg = document.getElementById("g-info-dialog");
  if (dlg) dlg.remove();
  dlg = document.createElement("dialog");
  dlg.id = "g-info-dialog";
  dlg.style.cssText = "border:0;border-radius:16px;box-shadow:var(--sh-lg);padding:0;width:min(94vw,520px)";
  dlg.innerHTML = '<div style="padding:26px 28px;font-family:var(--ff)">' +
    '<h2 style="margin:0 0 16px;font-size:17px;color:var(--ink)">' + esc(titulo) + "</h2>" +
    htmlContenido +
    '<div style="display:flex;justify-content:flex-end;margin-top:20px">' +
    '<button type="button" class="btn btn--pri" id="g-info-close">Cerrar</button></div></div>';
  document.body.appendChild(dlg);
  dlg.querySelector("#g-info-close").onclick = () => { dlg.close(); dlg.remove(); };
  dlg.showModal();
  return dlg;
}

/* ================= CATÁLOGO DE RECURSOS ================= */

async function renderCatalogo(el) {
  cargando(el, "Catálogo");
  let data;
  try { data = await api.get("/tourism/resources?page=1&page_size=200"); }
  catch (e) { return errorCarga(el, "Catálogo", e); }
  const recursos = data.items || [];
  const rw = puedeEscribir();

  const filas = recursos.map((r, i) =>
    '<tr><td style="white-space:normal;min-width:200px;font-weight:600">' + esc(r.nombre) + "</td>" +
    '<td class="mini">' + esc(r.categoria) + '</td><td class="mini">' + esc(r.municipio) + "</td>" +
    "<td>" + pubBadge(r.publicado) + '</td><td class="mini tnum">' + fechaCorta(r.updated_at) + "</td>" +
    "<td>" + (rw
      ? '<div class="chip-row">' +
        '<button class="btn btn--sm" data-g="edit-rec" data-i="' + i + '">Editar</button>' +
        '<button class="btn btn--sm" data-g="pub-rec" data-i="' + i + '">' + (r.publicado ? "Despublicar" : "Publicar") + "</button>" +
        '<button class="btn btn--sm btn--ghost" data-g="del-rec" data-i="' + i + '">Eliminar</button></div>'
      : "") + "</td></tr>").join("");

  el.innerHTML = gsub("Catálogo", "Catálogo de recursos turísticos",
    "Gestión del inventario de recursos del destino: playas, rutas, monumentos, miradores… Publicación multicanal hacia web, app y tótems.",
    rw ? '<button class="btn btn--pri" data-g="new-rec">＋ Nuevo recurso</button>' : "") +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Recursos", data.total ?? recursos.length, "En el catálogo", "ic-navy", "globe") +
    kpi("Publicados", recursos.filter((r) => r.publicado).length, "Visibles en web, app y tótems", "ic-ok", "chart") +
    kpi("Borradores", recursos.filter((r) => !r.publicado).length, "Pendientes de publicación", "ic-gold", "doc") +
    kpi("Categorías", new Set(recursos.map((r) => r.categoria)).size, "Tipologías en uso", "ic-teal", "box") + "</div>" +
    '<div class="card card--pad0"><div style="padding:16px 16px 4px" class="card__h"><div><div class="card__t">Recursos</div><div class="card__s">' +
    (rw ? "Edición, publicación y borrado sincronizados con todos los canales" : "Tu rol solo permite consulta") + "</div></div></div>" +
    '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Nombre</th><th>Categoría</th><th>Municipio</th><th>Estado</th><th>Actualizado</th><th></th></tr></thead><tbody>' +
    (filas || '<tr><td colspan="6" class="mini" style="text-align:center;padding:20px">Sin recursos</td></tr>') +
    "</tbody></table></div></div>";

  el.querySelectorAll("[data-g]").forEach((b) => {
    const r = recursos[Number(b.dataset.i)];
    if (b.dataset.g === "new-rec") b.onclick = () => formRecurso(null);
    if (b.dataset.g === "edit-rec") b.onclick = () => formRecurso(r);
    if (b.dataset.g === "pub-rec") b.onclick = async () => {
      await api.updateResource(r.id, { ...limpiarRecurso(r), publicado: !r.publicado });
      UI.toast(r.publicado ? "Recurso despublicado" : "Recurso publicado en todos los canales");
      UI.rerenderD("g-catalogo");
    };
    if (b.dataset.g === "del-rec") b.onclick = async () => {
      if (!confirm('¿Eliminar «' + r.nombre + '» del catálogo?')) return;
      await api.deleteResource(r.id);
      UI.toast("Recurso eliminado");
      UI.rerenderD("g-catalogo");
    };
  });
}

function limpiarRecurso(r) {
  const { id, created_at, updated_at, ...resto } = r;
  return resto;
}

function formRecurso(r) {
  const coords = r && r.ubicacion && r.ubicacion.coordinates;
  const ni = (r && r.nombre_i18n) || {};
  const di = (r && r.descripcion_i18n) || {};
  const bloqueIdioma = (lang, etiqueta) =>
    '<details style="margin-top:10px;border:1.5px solid var(--line);border-radius:10px;padding:8px 12px"' + ((ni[lang] || di[lang]) ? " open" : "") + ">" +
    '<summary style="font-size:12px;font-weight:800;color:var(--muted);cursor:pointer">' + etiqueta + "</summary>" +
    campo("Nombre (" + lang.toUpperCase() + ")", '<input name="nombre_' + lang + '" maxlength="255" value="' + esc(ni[lang] || "") + '" ' + INPUT_CSS + ">") +
    campo("Descripción (" + lang.toUpperCase() + ")", '<textarea name="descripcion_' + lang + '" rows="2" ' + INPUT_CSS + ">" + esc(di[lang] || "") + "</textarea>") +
    "</details>";
  abrirForm(r ? "Editar recurso" : "Nuevo recurso turístico",
    campo("Nombre", '<input name="nombre" required maxlength="255" value="' + esc(r ? r.nombre : "") + '" ' + INPUT_CSS + ">") +
    campo("Categoría", '<select name="categoria" ' + INPUT_CSS + ">" + CATEGORIAS.map((c) =>
      '<option value="' + c + '"' + (r && r.categoria === c ? " selected" : "") + ">" + c.replace(/_/g, " ") + "</option>").join("") + "</select>") +
    campo("Descripción corta", '<textarea name="descripcion_corta" rows="3" ' + INPUT_CSS + ">" + esc(r ? r.descripcion_corta || "" : "") + "</textarea>") +
    bloqueIdioma("en", "Traducción · Inglés") +
    bloqueIdioma("de", "Traducción · Alemán") +
    bloqueIdioma("fr", "Traducción · Francés") +
    campo("Municipio", '<input name="municipio" value="' + esc(r ? r.municipio : "Níjar") + '" ' + INPUT_CSS + ">") +
    '<div style="display:flex;gap:10px">' +
    '<div style="flex:1">' + campo("Latitud", '<input name="lat" type="number" step="any" value="' + (coords ? coords[1] : "") + '" ' + INPUT_CSS + ">") + "</div>" +
    '<div style="flex:1">' + campo("Longitud", '<input name="lon" type="number" step="any" value="' + (coords ? coords[0] : "") + '" ' + INPUT_CSS + ">") + "</div></div>" +
    campo("Imágenes (una URL por línea; la primera es la miniatura del tótem)",
      '<textarea name="imagenes" rows="2" placeholder="https://…/playa.jpg" ' + INPUT_CSS + ">" + esc((r && r.imagenes || []).join("\n")) + "</textarea>") +
    '<label style="display:flex;gap:8px;align-items:center;margin-top:14px;font-size:13px"><input type="checkbox" name="publicado"' + (r && r.publicado ? " checked" : "") + "> Publicado (visible en web, app y tótems)</label>",
    async (fd) => {
      const nombre = fd.get("nombre").trim();
      const payload = {
        ...(r ? limpiarRecurso(r) : { urn: "urn:ngsi-ld:RecursoTuristico:nijar:" + slug(nombre), activo: true }),
        nombre,
        categoria: fd.get("categoria"),
        descripcion_corta: fd.get("descripcion_corta").trim() || null,
        municipio: fd.get("municipio").trim() || "Níjar",
        publicado: fd.get("publicado") === "on",
      };
      const lat = parseFloat(fd.get("lat")), lon = parseFloat(fd.get("lon"));
      if (!isNaN(lat) && !isNaN(lon)) payload.ubicacion = { type: "Point", coordinates: [lon, lat] };
      const urls = (fd.get("imagenes") || "").split("\n").map((u) => u.trim()).filter((u) => /^https?:\/\//.test(u));
      payload.imagenes = urls.length ? urls : null;
      const nI18n = { es: nombre }, dI18n = { es: payload.descripcion_corta };
      ["en", "de", "fr"].forEach((lang) => {
        nI18n[lang] = (fd.get("nombre_" + lang) || "").trim() || null;
        dI18n[lang] = (fd.get("descripcion_" + lang) || "").trim() || null;
      });
      payload.nombre_i18n = nI18n;
      payload.descripcion_i18n = dI18n;
      if (r) await api.updateResource(r.id, payload);
      else await api.createResource(payload);
      UI.toast(r ? "Recurso actualizado" : "Recurso creado");
      UI.rerenderD("g-catalogo");
    });
}

/* ================= EVENTOS ================= */

async function renderEventos(el) {
  cargando(el, "Eventos");
  let data;
  try { data = await api.get("/tourism/events?page=1&page_size=100"); }
  catch (e) { return errorCarga(el, "Eventos", e); }
  const eventos = (data.items || []).slice().sort((a, b) => new Date(a.fecha_inicio) - new Date(b.fecha_inicio));
  const rw = puedeEscribir();
  const ahora = new Date();

  el.innerHTML = gsub("Eventos", "Agenda de eventos del destino",
    "Eventos culturales, gastronómicos, deportivos y festivos publicados en la agenda multicanal.",
    rw ? '<button class="btn btn--pri" data-g="new-ev">＋ Nuevo evento</button>' : "") +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Eventos", data.total ?? eventos.length, "En la agenda", "ic-navy", "cal") +
    kpi("Próximos", eventos.filter((e) => new Date(e.fecha_inicio) > ahora).length, "A partir de hoy", "ic-teal", "clock") +
    kpi("Publicados", eventos.filter((e) => e.publicado).length, "Visibles al público", "ic-ok", "chart") +
    kpi("Tipos", new Set(eventos.map((e) => e.tipo)).size, "Categorías en uso", "ic-violet", "box") + "</div>" +
    '<div class="card card--pad0"><div style="padding:16px 16px 4px" class="card__h"><div><div class="card__t">Agenda</div><div class="card__s">Ordenada por fecha de inicio</div></div></div>' +
    '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Evento</th><th>Tipo</th><th>Inicio</th><th>Fin</th><th>Estado</th></tr></thead><tbody>' +
    (eventos.map((e) =>
      '<tr><td style="white-space:normal;min-width:220px;font-weight:600">' + esc(e.nombre) + "</td>" +
      '<td class="mini">' + esc(e.tipo) + '</td><td class="mini tnum">' + fechaCorta(e.fecha_inicio) + "</td>" +
      '<td class="mini tnum">' + fechaCorta(e.fecha_fin) + "</td><td>" + pubBadge(e.publicado) + "</td></tr>").join("") ||
      '<tr><td colspan="5" class="mini" style="text-align:center;padding:20px">Sin eventos</td></tr>') +
    "</tbody></table></div></div>";

  const btn = el.querySelector('[data-g="new-ev"]');
  if (btn) btn.onclick = () => abrirForm("Nuevo evento",
    campo("Nombre", '<input name="nombre" required maxlength="255" ' + INPUT_CSS + ">") +
    campo("Tipo", '<select name="tipo" ' + INPUT_CSS + ">" + TIPOS_EVENTO.map((t) => "<option>" + t + "</option>").join("") + "</select>") +
    campo("Descripción", '<textarea name="descripcion" rows="3" ' + INPUT_CSS + "></textarea>") +
    '<div style="display:flex;gap:10px">' +
    '<div style="flex:1">' + campo("Inicio", '<input name="fecha_inicio" type="datetime-local" required ' + INPUT_CSS + ">") + "</div>" +
    '<div style="flex:1">' + campo("Fin", '<input name="fecha_fin" type="datetime-local" required ' + INPUT_CSS + ">") + "</div></div>" +
    campo("Organizador", '<input name="organizador" ' + INPUT_CSS + ">") +
    campo("Imágenes (una URL por línea; la primera sale en «Destacado» del tótem)",
      '<textarea name="imagenes" rows="2" placeholder="https://…/evento.jpg" ' + INPUT_CSS + "></textarea>") +
    '<label style="display:flex;gap:8px;align-items:center;margin-top:14px;font-size:13px"><input type="checkbox" name="publicado" checked> Publicado</label>',
    async (fd) => {
      const nombre = fd.get("nombre").trim();
      const urls = (fd.get("imagenes") || "").split("\n").map((u) => u.trim()).filter((u) => /^https?:\/\//.test(u));
      await api.createEvent({
        urn: "urn:ngsi-ld:EventoTuristico:nijar:" + slug(nombre) + "-" + slug(fd.get("fecha_inicio")).slice(0, 10),
        nombre,
        tipo: fd.get("tipo"),
        descripcion: fd.get("descripcion").trim() || null,
        fecha_inicio: new Date(fd.get("fecha_inicio")).toISOString(),
        fecha_fin: new Date(fd.get("fecha_fin")).toISOString(),
        organizador: fd.get("organizador").trim() || null,
        imagenes: urls.length ? urls : null,
        activo: true,
        publicado: fd.get("publicado") === "on",
      });
      UI.toast("Evento creado y publicado en la agenda");
      UI.rerenderD("g-eventos");
    });
}

/* ================= CAMPAÑAS ================= */

async function renderCampanas(el) {
  cargando(el, "Campañas");
  let data;
  try { data = await api.get("/campanas"); }
  catch (e) { return errorCarga(el, "Campañas", e); }
  const campanas = data.items || (Array.isArray(data) ? data : []);
  const rw = puedeEscribir();

  el.innerHTML = gsub("Campañas", "Campañas de promoción",
    "Campañas del destino con medición de eficacia: menciones atribuidas, sentimiento, alcance e interacciones durante el periodo de campaña.",
    rw ? '<button class="btn btn--pri" data-g="new-cam">＋ Nueva campaña</button>' : "") +
    '<div class="grid g3">' +
    (campanas.map((c, i) =>
      '<div class="card"><div class="card__h" style="margin-bottom:6px"><div><div class="card__t" style="font-size:14px">' + esc(c.nombre) + '</div><div class="card__s">' +
      fechaCorta(c.fecha_inicio) + " → " + fechaCorta(c.fecha_fin) + "</div></div>" +
      '<span class="bdg ' + (c.estado === "activa" ? "bdg-ok" : c.estado === "finalizada" ? "bdg-mut" : "bdg-info") + '">' + esc(c.estado) + "</span></div>" +
      '<p class="mini" style="color:var(--muted);margin:0 0 10px">' + esc(c.descripcion || c.objetivo || "") + "</p>" +
      '<div class="chip-row"><button class="btn btn--sm btn--pri" data-g="kpi-cam" data-i="' + i + '">Ver KPIs</button></div></div>').join("") ||
      '<div class="card"><div class="mini" style="color:var(--muted);text-align:center;padding:18px">Sin campañas registradas</div></div>') + "</div>";

  el.querySelectorAll('[data-g="kpi-cam"]').forEach((b) => {
    const c = campanas[Number(b.dataset.i)];
    b.onclick = async () => {
      try {
        const k = await api.campanaKpis(c.id);
        UI.openDrawer("Campaña · " + c.nombre, fechaCorta(c.fecha_inicio) + " → " + fechaCorta(c.fecha_fin),
          '<div class="dsec"><div class="t">KPIs del periodo</div>' +
          Object.entries(k).filter(([, v]) => typeof v !== "object").map(([key, v]) =>
            '<div class="kv"><span class="k">' + esc(key.replace(/_/g, " ")) + '</span><span class="v tnum">' + esc(v ?? "—") + "</span></div>").join("") +
          "</div>");
      } catch (e) { UI.toast("No se pudieron cargar los KPIs: " + (e.message || e)); }
    };
  });

  const btn = el.querySelector('[data-g="new-cam"]');
  if (btn) btn.onclick = () => abrirForm("Nueva campaña",
    campo("Nombre", '<input name="nombre" required maxlength="255" ' + INPUT_CSS + ">") +
    campo("Descripción / objetivo", '<textarea name="descripcion" rows="2" ' + INPUT_CSS + "></textarea>") +
    '<div style="display:flex;gap:10px">' +
    '<div style="flex:1">' + campo("Inicio", '<input name="fecha_inicio" type="date" required ' + INPUT_CSS + ">") + "</div>" +
    '<div style="flex:1">' + campo("Fin", '<input name="fecha_fin" type="date" required ' + INPUT_CSS + ">") + "</div></div>",
    async (fd) => {
      await api.createCampana({
        nombre: fd.get("nombre").trim(),
        descripcion: fd.get("descripcion").trim() || null,
        fecha_inicio: new Date(fd.get("fecha_inicio")).toISOString(),
        fecha_fin: new Date(fd.get("fecha_fin")).toISOString(),
      });
      UI.toast("Campaña creada");
      UI.rerenderD("g-campanas");
    });
}

/* ================= FAQs DEL CHATBOT ================= */

async function renderFaqs(el) {
  cargando(el, "FAQs chatbot");
  let intents;
  try { intents = await api.get("/chatbot/intents"); }
  catch (e) { return errorCarga(el, "FAQs chatbot", e); }

  const porCat = {};
  intents.forEach((i) => { (porCat[i.categoria] = porCat[i.categoria] || []).push(i); });

  el.innerHTML = gsub("FAQs chatbot", "Base de conocimiento del asistente",
    "Intenciones y FAQs que alimentan al chatbot en 4 idiomas. La edición se hace en el seed de FAQs y se reentrena el modelo Rasa (ver documentación operativa).", "") +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Intenciones", intents.length, "Configuradas en el motor", "ic-navy", "chat") +
    kpi("Categorías", Object.keys(porCat).length, "Áreas temáticas", "ic-teal", "box") +
    kpi("Idiomas", "4", "ES · EN · DE · FR", "ic-ok", "globe") +
    kpi("Motor", "Rasa", "Con fallback léxico automático", "ic-violet", "gear") + "</div>" +
    Object.entries(porCat).map(([cat, lista]) =>
      '<div class="card card--pad0" style="margin-bottom:14px"><div style="padding:14px 16px 4px" class="card__h"><div><div class="card__t">' + esc(cat) +
      '</div><div class="card__s">' + lista.length + " intenciones</div></div></div>" +
      '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Intención</th><th>Pregunta canónica</th><th>Confianza</th><th>Idiomas</th></tr></thead><tbody>' +
      lista.map((i) =>
        '<tr><td class="mini lnk">' + esc(i.intent) + '</td><td style="white-space:normal;min-width:260px">' + esc(i.pregunta_es) + "</td>" +
        '<td class="mini">' + esc(i.nivel_confianza) + '</td><td class="mini">' + (i.cobertura_idiomas || []).join(" · ").toUpperCase() + "</td></tr>").join("") +
      "</tbody></table></div></div>").join("");
}

/* ================= FICHA DEL CLIENTE ================= */

async function renderCliente(el) {
  cargando(el, "Ficha del cliente");
  let c;
  try { c = await api.getCliente(); }
  catch (e) { return errorCarga(el, "Ficha del cliente", e); }
  const u = getCachedUser && getCachedUser();
  const admin = !!u && u.rol === "administrador_tic";

  el.innerHTML = gsub("Ficha del cliente", "Ficha del cliente · " + (c.nombre || ""),
    "Datos del organismo titular de la plataforma y del contrato en explotación.",
    admin ? '<button class="btn btn--pri" data-g="edit-cli">Editar ficha</button>' : "") +
    '<div class="grid g2">' +
    '<div class="card"><div class="card__h"><div><div class="card__t">Organismo</div></div></div>' +
    kv("Nombre", c.nombre) + kv("CIF", c.cif) + kv("Área responsable", c.area_responsable) +
    kv("Proyecto", c.proyecto) + kv("Dirección", c.direccion) + kv("Municipio · provincia", (c.municipio || "") + " · " + (c.provincia || "")) + "</div>" +
    '<div class="card"><div class="card__h"><div><div class="card__t">Explotación</div></div></div>' +
    kv("Inicio de explotación", fechaCorta(c.fecha_inicio_explotacion)) +
    kv("Fin de mantenimiento", fechaCorta(c.fecha_fin_mantenimiento)) +
    kv("Idiomas activos", (c.idiomas_activos || []).join(" · ").toUpperCase() || "—") +
    kv("Responsable municipal", c.responsable_municipal ? esc(c.responsable_municipal.nombre || JSON.stringify(c.responsable_municipal)) : "—") + "</div></div>";

  const btn = el.querySelector('[data-g="edit-cli"]');
  if (btn) btn.onclick = () => abrirForm("Editar ficha del cliente",
    campo("Nombre", '<input name="nombre" required value="' + esc(c.nombre || "") + '" ' + INPUT_CSS + ">") +
    campo("Área responsable", '<input name="area_responsable" value="' + esc(c.area_responsable || "") + '" ' + INPUT_CSS + ">") +
    campo("Proyecto", '<input name="proyecto" value="' + esc(c.proyecto || "") + '" ' + INPUT_CSS + ">") +
    campo("Dirección", '<input name="direccion" value="' + esc(c.direccion || "") + '" ' + INPUT_CSS + ">"),
    async (fd) => {
      await api.patchCliente({
        nombre: fd.get("nombre").trim(),
        area_responsable: fd.get("area_responsable").trim() || null,
        proyecto: fd.get("proyecto").trim() || null,
        direccion: fd.get("direccion").trim() || null,
      });
      UI.toast("Ficha del cliente actualizada");
      UI.rerenderD("g-cliente");
    });
}

/* ================= USUARIOS, ROLES Y PERMISOS ================= */

// Roles RBAC: nombres legibles de respaldo (los roles reales se cargan de la API).
const ROLES_FALLBACK = [
  { slug: "administrador_tic", display: "Superadministrador" },
  { slug: "gestor_contenidos", display: "Administrador municipal / Contenidos" },
  { slug: "analista_datos", display: "Analista de datos" },
  { slug: "operador_smart_office", display: "Operaciones" },
  { slug: "auditor", display: "Consulta / Visor" },
  { slug: "direccion_gobierno", display: "Dirección / Gobierno" },
];

// Cache de roles cargados de la API (se refresca al abrir el módulo admin).
let ROLES_CACHE = null;

async function cargarRoles() {
  try {
    const roles = await api.listRoles();
    ROLES_CACHE = roles.map((r) => ({ slug: r.slug, display: r.display }));
  } catch {
    /* si falla (p.ej. 403), se mantiene el respaldo */
  }
  return ROLES_CACHE || ROLES_FALLBACK;
}

function rolesDisponibles() {
  return ROLES_CACHE || ROLES_FALLBACK;
}

function rolLabel(r) {
  const found = rolesDisponibles().find((x) => x.slug === r);
  return found ? found.display : String(r || "").replace(/_/g, " ");
}

function opcionesRol(seleccionado) {
  return rolesDisponibles().map((r) =>
    '<option value="' + r.slug + '"' + (r.slug === seleccionado ? " selected" : "") + ">" + esc(r.display) + "</option>").join("");
}

async function renderUsuarios(el) {
  cargando(el, "Usuarios y permisos");
  await cargarRoles();
  let usuarios;
  try { usuarios = await api.listUsuarios(); }
  catch (e) {
    el.innerHTML = asub("Usuarios y permisos", "Usuarios y permisos", "Gestión de cuentas del panel.") +
      '<div class="card"><div class="mini" style="color:var(--muted);text-align:center;padding:26px 0">' +
      (e && e.status === 403 ? "Solo el administrador TIC puede gestionar usuarios." : "Error: " + esc(e && e.message || e)) + "</div></div>";
    return;
  }

  const yo = getCachedUser && getCachedUser();
  const miEmail = yo && yo.email;

  const filas = usuarios.map((u, i) => {
    const esYo = miEmail && u.email === miEmail;
    const acciones = '<div class="chip-row">' +
      '<button class="btn btn--sm" data-g="edit-usr" data-i="' + i + '">Editar</button>' +
      (u.activo
        ? '<button class="btn btn--sm" data-g="off-usr" data-i="' + i + '"' + (esYo ? " disabled title=\"No puedes desactivarte a ti mismo\"" : "") + ">Desactivar</button>"
        : '<button class="btn btn--sm" data-g="on-usr" data-i="' + i + '">Activar</button>') +
      '<button class="btn btn--sm" data-g="pwd-usr" data-i="' + i + '">Reset contraseña</button>' +
      '<button class="btn btn--sm btn--ghost" data-g="del-usr" data-i="' + i + '"' + (esYo ? " disabled title=\"No puedes eliminar tu propia cuenta\"" : "") + ">Eliminar</button></div>";
    return '<tr><td style="font-weight:600">' + esc(u.nombre_completo) + (esYo ? ' <span class="bdg bdg-mut">tú</span>' : "") + '</td><td class="mini">' + esc(u.email) + "</td>" +
      '<td><span class="bdg bdg-info">' + esc(rolLabel(u.rol)) + "</span></td>" +
      "<td>" + (u.activo ? '<span class="bdg bdg-ok">activo</span>' : '<span class="bdg bdg-mut">inactivo</span>') + "</td>" +
      '<td class="mini">' + (u.requiere_2fa ? "Sí" : "No") + '</td><td class="mini tnum">' + fechaCorta(u.created_at) + "</td>" +
      "<td>" + acciones + "</td></tr>";
  }).join("");

  el.innerHTML = asub("Usuarios y permisos", "Usuarios, roles y permisos",
    "Cuentas con acceso al panel y su rol RBAC. Las invitaciones y los reset generan una contraseña temporal que el usuario debe cambiar en el primer acceso.",
    '<button class="btn btn--pri" data-g="inv-usr">＋ Invitar usuario</button>') +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Usuarios", usuarios.length, "Con acceso al panel", "ic-navy", "gear") +
    kpi("Activos", usuarios.filter((u) => u.activo).length, "Pueden iniciar sesión", "ic-ok", "chart") +
    kpi("Superadministradores", usuarios.filter((u) => u.rol === "administrador_tic").length, "Control total de la plataforma", "ic-coral", "gear") +
    kpi("Con 2FA", usuarios.filter((u) => u.requiere_2fa).length, "Doble factor requerido", "ic-teal", "gear") + "</div>" +
    '<div class="card card--pad0"><div style="padding:16px 16px 4px" class="card__h"><div><div class="card__t">Cuentas</div><div class="card__s">Roles según la matriz RBAC (ENS medio). Consulta la matriz completa en «Matriz de permisos».</div></div></div>' +
    '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Nombre</th><th>Email</th><th>Rol</th><th>Estado</th><th>2FA</th><th>Alta</th><th></th></tr></thead><tbody>' +
    (filas || '<tr><td colspan="7" class="mini" style="text-align:center;padding:20px">Sin usuarios</td></tr>') +
    "</tbody></table></div></div>";

  const invBtn = el.querySelector('[data-g="inv-usr"]');
  if (invBtn) invBtn.onclick = () => abrirForm("Invitar usuario",
    campo("Nombre completo", '<input name="nombre_completo" required minlength="2" maxlength="255" ' + INPUT_CSS + ">") +
    campo("Email", '<input name="email" type="email" required ' + INPUT_CSS + ">") +
    campo("Rol", '<select name="rol" ' + INPUT_CSS + ">" + opcionesRol("direccion_gobierno") + "</select>"),
    async (fd) => {
      let creado;
      try {
        creado = await api.invitarUsuario({
          email: fd.get("email").trim(),
          nombre_completo: fd.get("nombre_completo").trim(),
          rol: fd.get("rol"),
        });
      } catch (e) {
        if (e && e.status === 409) throw new Error("Ya existe un usuario con ese email.");
        throw e;
      }
      UI.toast("Usuario creado con contraseña temporal");
      UI.rerenderAdm("usuarios");
      return creado;
    });

  el.querySelectorAll("[data-g$='-usr']").forEach((b) => {
    if (b.dataset.i == null) return;
    const u = usuarios[Number(b.dataset.i)];
    if (!u) return;
    if (b.dataset.g === "edit-usr") b.onclick = () => formEditarUsuario(u);
    if (b.dataset.g === "on-usr") b.onclick = () => accionUsuario(() => api.activarUsuario(u.id), "Usuario activado");
    if (b.dataset.g === "off-usr") b.onclick = () => accionUsuario(() => api.desactivarUsuario(u.id), "Usuario desactivado");
    if (b.dataset.g === "pwd-usr") b.onclick = async () => {
      if (!confirm("¿Restablecer la contraseña de " + u.email + "?")) return;
      try {
        const r = await api.resetPasswordUsuario(u.id);
        mostrarInfo("Contraseña temporal", "<p style=\"margin:0 0 10px;font-size:13px;color:var(--muted)\">Entrégala al usuario por un canal seguro. Deberá cambiarla en el primer acceso.</p>" +
          '<div style="font-family:monospace;font-size:15px;background:var(--bg);border:1.5px solid var(--line);border-radius:10px;padding:12px;word-break:break-all">' + esc(r.password_temporal) + "</div>");
      } catch (e) { UI.toast("Error: " + (e && e.message || e)); }
    };
    if (b.dataset.g === "del-usr") b.onclick = async () => {
      if (!confirm("¿Eliminar la cuenta de " + u.email + "? (borrado lógico)")) return;
      await accionUsuario(() => api.eliminarUsuario(u.id), "Usuario eliminado");
    };
  });
}

async function accionUsuario(fn, mensajeOk) {
  try {
    await fn();
    UI.toast(mensajeOk);
    UI.rerenderAdm("usuarios");
  } catch (e) {
    UI.toast("Error: " + (e && e.status === 409 ? (e.message || "operación no permitida") : (e && e.message || e)));
  }
}

function formEditarUsuario(u) {
  abrirForm("Editar usuario",
    campo("Nombre completo", '<input name="nombre_completo" required minlength="2" maxlength="255" value="' + esc(u.nombre_completo) + '" ' + INPUT_CSS + ">") +
    campo("Rol", '<select name="rol" ' + INPUT_CSS + ">" + opcionesRol(u.rol) + "</select>") +
    '<label style="display:flex;gap:8px;align-items:center;margin-top:14px;font-size:13px"><input type="checkbox" name="activo"' + (u.activo ? " checked" : "") + "> Cuenta activa</label>",
    async (fd) => {
      await api.updateUsuario(u.id, {
        nombre_completo: fd.get("nombre_completo").trim(),
        rol: fd.get("rol"),
        activo: fd.get("activo") === "on",
      });
      UI.toast("Usuario actualizado");
      UI.rerenderAdm("usuarios");
    });
}

/* ================= MATRIZ DE PERMISOS ================= */

async function renderMatrizPermisos(el) {
  cargando(el, "Matriz de permisos");
  let m;
  try { m = await api.getMatrizPermisos(); }
  catch (e) {
    el.innerHTML = asub("Matriz de permisos", "Matriz de permisos", "Qué módulos ve cada rol.") +
      '<div class="card"><div class="mini" style="color:var(--muted);text-align:center;padding:26px 0">' +
      (e && e.status === 403 ? "Solo el administrador TIC puede consultar la matriz." : "Error: " + esc(e && e.message || e)) + "</div></div>";
    return;
  }
  const permisosPorRol = Object.fromEntries(m.roles.map((r) => [r.rol, new Set(r.permisos)]));
  const check = (on) => on
    ? '<span class="bdg bdg-ok" style="min-width:26px;justify-content:center">✓</span>'
    : '<span class="bdg bdg-mut" style="min-width:26px;justify-content:center">·</span>';

  // Agrupa los módulos por su grupo, manteniendo el orden de aparición.
  const grupos = [];
  m.modulos.forEach((mod) => {
    let g = grupos.find((x) => x.grupo === mod.grupo);
    if (!g) { g = { grupo: mod.grupo, mods: [] }; grupos.push(g); }
    g.mods.push(mod);
  });

  const cabecera = "<tr><th>Módulo</th>" + m.roles.map((r) => '<th class="mini" style="text-align:center">' + esc(r.display) + "</th>").join("") + "</tr>";
  const cuerpo = grupos.map((g) =>
    '<tr><td colspan="' + (m.roles.length + 1) + '" class="mini" style="font-weight:800;background:var(--bg);text-transform:uppercase;letter-spacing:.04em;color:var(--muted)">' + esc(g.grupo) + "</td></tr>" +
    g.mods.map((mod) =>
      "<tr><td style=\"font-weight:600\">" + esc(mod.nombre) + "</td>" +
      m.roles.map((r) => '<td style="text-align:center">' + check(permisosPorRol[r.rol].has(mod.id)) + "</td>").join("") +
      "</tr>").join("")
  ).join("");

  el.innerHTML = asub("Matriz de permisos", "Matriz de permisos",
    "Qué módulos ve cada rol RBAC. Vista de solo lectura; para crear roles o cambiar permisos usa la sección «Roles».", "") +
    '<div class="card card--pad0"><div class="tbl-wrap"><table class="tbl">' +
    "<thead>" + cabecera + "</thead><tbody>" + cuerpo + "</tbody></table></div></div>";
}

/* ================= ROLES (CRUD + permisos) ================= */

function camposPermisos(modulos, seleccionados) {
  const sel = new Set(seleccionados || []);
  const grupos = [];
  modulos.forEach((mod) => {
    let g = grupos.find((x) => x.grupo === mod.grupo);
    if (!g) { g = { grupo: mod.grupo, mods: [] }; grupos.push(g); }
    g.mods.push(mod);
  });
  return '<div style="max-height:46vh;overflow:auto;margin-top:6px;border:1.5px solid var(--line);border-radius:10px;padding:10px 12px">' +
    grupos.map((g) =>
      '<div class="mini" style="font-weight:800;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:8px 0 4px">' + esc(g.grupo) + "</div>" +
      g.mods.map((mod) =>
        '<label style="display:flex;gap:8px;align-items:center;padding:3px 0;font-size:13px">' +
        '<input type="checkbox" name="perm_' + mod.id + '"' + (sel.has(mod.id) ? " checked" : "") + "> " + esc(mod.nombre) + "</label>").join("")
    ).join("") + "</div>";
}

function permisosDeForm(fd, modulos) {
  return modulos.filter((m) => fd.get("perm_" + m.id) === "on").map((m) => m.id);
}

async function renderRoles(el) {
  cargando(el, "Roles");
  let roles, modulos;
  try {
    const [rs, m] = await Promise.all([api.listRoles(), api.getMatrizPermisos()]);
    roles = rs;
    modulos = m.modulos;
  } catch (e) {
    el.innerHTML = asub("Roles", "Roles", "Gestión de roles y permisos.") +
      '<div class="card"><div class="mini" style="color:var(--muted);text-align:center;padding:26px 0">' +
      (e && e.status === 403 ? "Solo el administrador TIC puede gestionar roles." : "Error: " + esc(e && e.message || e)) + "</div></div>";
    return;
  }
  ROLES_CACHE = roles.map((r) => ({ slug: r.slug, display: r.display }));

  const filas = roles.map((r, i) =>
    '<tr><td style="font-weight:600">' + esc(r.display) + ' <span class="mini" style="color:var(--muted)">' + esc(r.slug) + "</span></td>" +
    '<td class="mini">' + (r.permisos ? r.permisos.length : 0) + " / " + modulos.length + "</td>" +
    '<td class="mini">' + (r.n_usuarios || 0) + "</td>" +
    "<td>" + (r.es_sistema ? '<span class="bdg bdg-info">sistema</span>' : '<span class="bdg bdg-mut">personalizado</span>') + "</td>" +
    '<td><div class="chip-row"><button class="btn btn--sm" data-r="edit" data-i="' + i + '">Editar</button>' +
    (r.es_sistema ? "" : '<button class="btn btn--sm btn--ghost" data-r="del" data-i="' + i + '">Eliminar</button>') +
    "</div></td></tr>").join("");

  el.innerHTML = asub("Roles", "Roles y permisos",
    "Crea roles a medida y decide qué módulos ve cada uno (p.ej. un rol que solo ve DTI y Agua). Los roles de sistema se pueden editar pero no borrar.",
    '<button class="btn btn--pri" data-r="new">＋ Crear rol</button>') +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Roles", roles.length, "Definidos en la plataforma", "ic-navy", "gear") +
    kpi("De sistema", roles.filter((r) => r.es_sistema).length, "Integrados (no borrables)", "ic-teal", "gear") +
    kpi("Personalizados", roles.filter((r) => !r.es_sistema).length, "Creados por el administrador", "ic-violet", "gear") +
    kpi("Módulos", modulos.length, "Permisos asignables", "ic-gold", "box") + "</div>" +
    '<div class="card card--pad0"><div class="tbl-wrap"><table class="tbl"><thead><tr><th>Rol</th><th>Permisos</th><th>Usuarios</th><th>Tipo</th><th></th></tr></thead><tbody>' +
    (filas || '<tr><td colspan="5" class="mini" style="text-align:center;padding:20px">Sin roles</td></tr>') +
    "</tbody></table></div></div>";

  const nuevo = el.querySelector('[data-r="new"]');
  if (nuevo) nuevo.onclick = () => abrirForm("Crear rol",
    campo("Identificador (slug)", '<input name="slug" required pattern="[a-z][a-z0-9_]{1,49}" placeholder="visor_dti_agua" ' + INPUT_CSS + ">") +
    campo("Nombre visible", '<input name="display" required minlength="2" maxlength="120" ' + INPUT_CSS + ">") +
    campo("Descripción (opcional)", '<input name="descripcion" maxlength="255" ' + INPUT_CSS + ">") +
    campo("Permisos (módulos visibles)", camposPermisos(modulos, [])),
    async (fd) => {
      try {
        await api.crearRol({
          slug: fd.get("slug").trim(),
          display: fd.get("display").trim(),
          descripcion: (fd.get("descripcion") || "").trim() || null,
          permisos: permisosDeForm(fd, modulos),
        });
      } catch (e) {
        if (e && e.status === 409) throw new Error("Ya existe un rol con ese identificador.");
        if (e && e.status === 400) throw new Error("Identificador o permisos no válidos.");
        throw e;
      }
      UI.toast("Rol creado");
      UI.rerenderAdm("roles");
    });

  el.querySelectorAll("[data-r]").forEach((b) => {
    if (b.dataset.i == null) return;
    const r = roles[Number(b.dataset.i)];
    if (!r) return;
    if (b.dataset.r === "edit") b.onclick = () => abrirForm("Editar rol · " + r.display,
      campo("Nombre visible", '<input name="display" required minlength="2" maxlength="120" value="' + esc(r.display) + '" ' + INPUT_CSS + ">") +
      campo("Descripción (opcional)", '<input name="descripcion" maxlength="255" value="' + esc(r.descripcion || "") + '" ' + INPUT_CSS + ">") +
      (r.slug === "administrador_tic"
        ? '<div class="mini" style="color:var(--muted);margin-top:10px">El superadministrador conserva siempre todos los permisos.</div>'
        : campo("Permisos (módulos visibles)", camposPermisos(modulos, r.permisos))),
      async (fd) => {
        const body = {
          display: fd.get("display").trim(),
          descripcion: (fd.get("descripcion") || "").trim() || null,
        };
        if (r.slug !== "administrador_tic") body.permisos = permisosDeForm(fd, modulos);
        await api.actualizarRol(r.slug, body);
        UI.toast("Rol actualizado");
        UI.rerenderAdm("roles");
      });
    if (b.dataset.r === "del") b.onclick = async () => {
      if (!confirm('¿Eliminar el rol «' + r.display + '»?')) return;
      try {
        await api.eliminarRol(r.slug);
        UI.toast("Rol eliminado");
        UI.rerenderAdm("roles");
      } catch (e) {
        UI.toast("Error: " + (e && e.status === 409 ? "el rol tiene usuarios asignados" : (e && e.message || e)));
      }
    };
  });
}

/* ================= PREDICCIÓN DE AFLUENCIA ================= */

async function renderPrediccion(el) {
  cargando(el, "Predicción");
  const [afluencia, validacion] = await Promise.all([
    api.get("/prediccion/afluencia?metrica=totem&horizonte_dias=14").catch(() => null),
    api.get("/prediccion/validacion?metrica=totem").catch(() => null),
  ]);
  const U2 = window.__U;
  const puntos = (afluencia && afluencia.puntos) || [];
  const vals = puntos.map((p) => p.valor_estimado ?? p.prediccion ?? p.valor ?? 0);

  el.innerHTML = gsub("Predicción", "Predicción de afluencia",
    "Modelo estacional sobre el histórico de la plataforma: previsión de visitas a 14 días con validación MAPE (holdout temporal).", "") +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Modelo", afluencia ? "estacional" : "—", "Entrenado con el histórico propio", "ic-navy", "gear") +
    kpi("Horizonte", afluencia ? afluencia.horizonte_dias + " días" : "—", "Días de histórico: " + (afluencia ? afluencia.dias_historico : "—"), "ic-teal", "cal") +
    kpi("MAPE validación", validacion && validacion.mape != null ? validacion.mape.toFixed(1) + " %" : "—", "Umbral del pliego ≤ " + (validacion ? validacion.umbral : 20) + "%", validacion && validacion.cumple_umbral ? "ic-ok" : "ic-gold", "chart") +
    kpi("Cobertura", validacion ? validacion.n_evaluable + " de " + validacion.n_test : "—", "Días evaluables del holdout", "ic-violet", "box") + "</div>" +
    '<div class="card"><div class="card__h"><div><div class="card__t">Visitas previstas en tótems · próximos 14 días</div><div class="card__s">' +
    (afluencia ? "Generado " + fechaCorta(afluencia.generado_en) : "Sin datos suficientes para predecir todavía") + "</div></div></div>" +
    (vals.length && U2 ? U2.areaChart(vals, { color: "blue", hpx: 170, h: 185 }) :
      '<div class="mini" style="color:var(--muted);padding:30px 0;text-align:center">El modelo necesita más histórico de visitas para generar la predicción.</div>') + "</div>";
}

/* ================= CONSUMO DE IA ================= */

async function renderConsumoIA(el) {
  cargando(el, "Consumo de IA");
  let c;
  try { c = await api.get("/dashboards/ia/consumo"); }
  catch (e) {
    el.innerHTML = gsub("Consumo de IA", "Consumo de IA generativa", "Control de costes de los modelos de IA.") +
      '<div class="card"><div class="mini" style="color:var(--muted);text-align:center;padding:26px 0">' +
      (e && e.status === 403 ? "Tu rol no tiene acceso al consumo de IA (administrador TIC, analista o auditor)."
        : "Error: " + esc(e && e.message || e)) + "</div></div>";
    return;
  }
  const U2 = window.__U;
  const fmtT = (n) => (U2 && n != null ? U2.fmt(n) : n ?? "—");
  const usd = (n) => (n != null ? "$" + Number(n).toFixed(2) : "—");
  const barras = (lista, color) => {
    const max = lista.length ? Math.max(...lista.map((x) => x.coste_estimado_usd)) || 1 : 1;
    return lista.map((x) => U2.barRow(
      esc(x.clave) + " · " + fmtT(x.tokens_entrada + x.tokens_salida) + " tokens",
      usd(x.coste_estimado_usd), (x.coste_estimado_usd / max) * 100, color)).join("") ||
      '<div class="mini" style="color:var(--muted)">Sin consumo registrado</div>';
  };

  el.innerHTML = gsub("Consumo de IA", "Consumo de IA generativa",
    "Tokens y coste estimado de todos los puntos de la plataforma que usan modelos de IA (últimos 30 días). Cada llamada queda registrada con su servicio, canal y modelo.", "") +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Llamadas al modelo", fmtT(c.llamadas), "Últimos 30 días", "ic-navy", "chat") +
    kpi("Tokens de entrada", fmtT(c.tokens_entrada), "Contexto + preguntas enviadas", "ic-teal", "chart") +
    kpi("Tokens de salida", fmtT(c.tokens_salida), "Respuestas generadas", "ic-violet", "chart") +
    kpi("Coste estimado", usd(c.coste_estimado_usd), "Según tarifas por modelo · latencia media " + (c.latencia_media_ms != null ? Math.round(c.latencia_media_ms) + " ms" : "—"), "ic-gold", "chart") + "</div>" +
    '<div class="grid c7-5" style="margin-bottom:16px">' +
    '<div class="card"><div class="card__h"><div><div class="card__t">Tokens por día</div><div class="card__s">Entrada + salida · últimos 30 días</div></div></div>' +
    (c.serie_diaria.length && U2 ? U2.areaChart(c.serie_diaria.map((p) => p.tokens), { color: "violet", hpx: 150, h: 170 }) :
      '<div class="mini" style="color:var(--muted);padding:26px 0;text-align:center">Sin consumo registrado todavía</div>') + "</div>" +
    '<div class="card"><div class="card__h"><div><div class="card__t">Por canal</div><div class="card__s">Dónde se usa la IA (tótem, web, app…)</div></div></div><div class="bars">' +
    barras(c.por_canal, "var(--teal2)") + "</div></div></div>" +
    '<div class="grid g2">' +
    '<div class="card"><div class="card__h"><div><div class="card__t">Por servicio</div><div class="card__s">Funcionalidad que consume IA</div></div></div><div class="bars">' +
    barras(c.por_servicio, "var(--blue)") + "</div></div>" +
    '<div class="card"><div class="card__h"><div><div class="card__t">Por modelo</div><div class="card__s">Con su coste estimado en USD</div></div></div><div class="bars">' +
    barras(c.por_modelo, "var(--gold)") + "</div></div></div>";
}

/* ================= CONFIGURACIÓN ================= */

async function renderConfig(el) {
  cargando(el, "Configuración");
  const [version, health, ready] = await Promise.all([
    api.get("/version").catch(() => null),
    api.get("/health").catch(() => null),
    api.get("/ready").catch(() => null),
  ]);
  const u = getCachedUser && getCachedUser();

  el.innerHTML = gsub("Configuración", "Configuración y estado del sistema",
    "Versión desplegada, salud de los servicios y sesión activa.", "") +
    '<div class="grid g2">' +
    '<div class="card"><div class="card__h"><div><div class="card__t">Plataforma</div></div></div>' +
    kv("Aplicación", version ? version.name : "—") +
    kv("Versión", version ? version.version : "—") +
    kv("Entorno", version ? version.environment : "—") +
    kv("Motor del chatbot", version ? version.chatbot_engine : "—") +
    kv("Expediente", version ? version.expediente : "—") +
    kv("API", health && health.status === "ok" ? '<span class="bdg bdg-ok">operativa</span>' : '<span class="bdg bdg-err">error</span>') +
    kv("Base de datos", ready && ready.checks && ready.checks.database === "ok" ? '<span class="bdg bdg-ok">conectada</span>' : '<span class="bdg bdg-warn">sin verificar</span>') + "</div>" +
    '<div class="card"><div class="card__h"><div><div class="card__t">Sesión</div></div></div>' +
    kv("Usuario", u ? u.nombre_completo || u.email : "—") +
    kv("Email", u ? u.email : "—") +
    kv("Rol", u ? '<span class="bdg bdg-info">' + esc(u.rol) + "</span>" : "—") +
    '<div class="chip-row" style="margin-top:14px"><button class="btn btn--sm" onclick="(async()=>{const m=await import(\'./api-client.js?v=18\');await m.api.logout();location.reload()})()">Cerrar sesión</button></div></div></div>';
}

/* ---------------- helpers de tarjetas ---------------- */

function kpi(l, v, d, cls, ic, click) {
  const X = window.__UI2;
  return X && X.kpiCard ? X.kpiCard(l, esc(String(v ?? "—")), d, cls, ic, click || "") : "";
}

function kv(k, v) {
  return '<div class="kv"><span class="k">' + esc(k) + '</span><span class="v">' + (v == null || v === "" ? "—" : v) + "</span></div>";
}

/* ================= MÓDULO ADMINISTRACIÓN (nivel superior, solo admin) ================= */
/* "Usuarios y permisos" y "Matriz de permisos" viven aquí, como un módulo más
   del lanzador (junto a las verticales), no dentro de la consola DTI. La tarjeta
   del home y el módulo solo se muestran al rol administrador_tic. */

const ADMIN_SECCIONES = [
  { id: "usuarios", n: "Usuarios y permisos", i: "gear", r: renderUsuarios },
  { id: "roles", n: "Roles", i: "gear", r: renderRoles },
  { id: "matriz", n: "Matriz de permisos", i: "box", r: renderMatrizPermisos },
];

// Mapa entrada de módulo → permiso requerido (para visibilidad por rol).
const ENTER_PERMISO = {
  enterDTI: "ver_dti",
  enterLighting: "ver_alumbrado",
  enterAgua: "ver_agua",
  enterResiduos: "ver_residuos",
  enterMovilidad: "ver_movilidad",
  enterSeguridad: "ver_seguridad",
  enterEnergia: "ver_energia",
};

function tienePermiso(p) {
  const u = getCachedUser && getCachedUser();
  if (!u) return false;
  // Compatibilidad: si el backend no envía permisos, no se bloquea nada.
  if (!Array.isArray(u.permisos)) return true;
  return u.permisos.includes(p);
}

const ADM_R = {};
let admRendered = {};
let admCur = null;
let admInstalado = false;

function icono(nombre) {
  return window.icon ? window.icon(nombre) : "";
}

function construirVistaAdmin() {
  if (document.getElementById("view-admin")) return;
  const home = document.getElementById("view-home");
  if (!home) return;
  const div = document.createElement("div");
  div.className = "view";
  div.id = "view-admin";
  div.innerHTML = '<div class="app"><aside class="sidebar" id="adm-sidebar"></aside>' +
    '<main class="main" id="adm-main">' +
    ADMIN_SECCIONES.map((s) => '<section class="admview" id="adm-' + s.id + '"></section>').join("") +
    "</main></div>";
  home.insertAdjacentElement("afterend", div);
  ADMIN_SECCIONES.forEach((s) => { ADM_R[s.id] = s.r; });
}

function renderAdmSidebar() {
  const sb = document.getElementById("adm-sidebar");
  if (!sb) return;
  let h = '<div class="sb-head"><div class="sb-title">' + icono("gear") + " Administración</div>" +
    '<div class="sb-sub">Usuarios, roles y permisos</div></div><div class="sb-g">Gestión</div>';
  ADMIN_SECCIONES.forEach((s) => {
    h += '<button class="sb-it" data-admsec="' + s.id + '" onclick="UI.goAdm(\'' + s.id + '\')">' + icono(s.i) + s.n + "</button>";
  });
  sb.innerHTML = h;
}

function tarjetaAdminHTML() {
  return '<div class="vcard vcard--on" data-admcard onclick="UI.enterAdmin()">' +
    '<div class="vi ic-coral">' + icono("gear") + "</div>" +
    "<h3>Administración</h3><p>Gestión de usuarios, roles y permisos de acceso a la plataforma: alta y baja de cuentas, cambio de rol, reset de contraseña y matriz de permisos RBAC.</p>" +
    '<div class="vfoot"><span class="bdg bdg-info">Solo administrador</span>' +
    '<button class="btn btn--sm btn--pri">Gestionar usuarios</button></div></div>';
}

function inyectarTarjetaAdmin() {
  const u = getCachedUser && getCachedUser();
  const cont = document.getElementById("home-verticals");
  if (!cont) return;
  const ya = cont.querySelector("[data-admcard]");
  if (!u || u.rol !== "administrador_tic") { if (ya) ya.remove(); return; }
  if (!ya) cont.insertAdjacentHTML("beforeend", tarjetaAdminHTML());
}

// Quita del lanzador las tarjetas de módulos que el rol no puede ver.
function filtrarTarjetasPorPermiso() {
  const cont = document.getElementById("home-verticals");
  const u = getCachedUser && getCachedUser();
  if (!cont || !u || !Array.isArray(u.permisos)) return; // compat: no filtrar
  cont.querySelectorAll(".vcard").forEach((card) => {
    if (card.hasAttribute("data-admcard")) return;
    const onclick = card.getAttribute("onclick") || "";
    const entry = Object.keys(ENTER_PERMISO).find((name) => onclick.indexOf(name) !== -1);
    if (entry && !tienePermiso(ENTER_PERMISO[entry])) card.remove();
  });
}

function aplicarPermisosHome() {
  inyectarTarjetaAdmin();
  filtrarTarjetasPorPermiso();
}

// Bloquea la entrada a un módulo por URL/onclick si el rol no tiene el permiso.
function bloquearEntradasSinPermiso() {
  Object.keys(ENTER_PERMISO).forEach((name) => {
    const orig = UI[name];
    if (typeof orig !== "function" || orig._permWrap) return;
    const permiso = ENTER_PERMISO[name];
    const wrapped = function () {
      if (!tienePermiso(permiso)) { if (UI.toast) UI.toast("No tienes acceso a este módulo"); return undefined; }
      return orig.apply(this, arguments);
    };
    wrapped._permWrap = true;
    UI[name] = wrapped;
  });
}

function instalarAdmin() {
  if (admInstalado) return;
  construirVistaAdmin();
  renderAdmSidebar();
  if (UI._VIEWS && UI._VIEWS.indexOf("view-admin") === -1) UI._VIEWS.push("view-admin");

  UI.goAdm = function (id) {
    UI._showV("view-admin");
    const ctx = document.getElementById("tb-ctx");
    if (ctx) ctx.style.display = "flex";
    const pill = document.getElementById("tb-pill");
    if (pill) pill.innerHTML = icono("gear") + ' Administración <span class="bdg bdg-info" style="margin-left:4px">solo admin</span>';
    const p2 = document.getElementById("tb-pill2");
    if (p2) p2.textContent = "Usuarios, roles y permisos";
    admCur = id;
    document.querySelectorAll(".admview").forEach((v) => { v.style.display = "none"; });
    const el = document.getElementById("adm-" + id);
    if (!el) return;
    if (!admRendered[id]) { ADM_R[id](el); admRendered[id] = true; }
    el.style.display = "block";
    document.querySelectorAll("[data-admsec]").forEach((b) => b.classList.toggle("on", b.dataset.admsec === id));
    window.scrollTo(0, 0);
  };
  UI.enterAdmin = function () { UI.goAdm(ADMIN_SECCIONES[0].id); };
  UI.rerenderAdm = function (id) { admRendered[id] = false; if (admCur === id) UI.goAdm(id); };

  bloquearEntradasSinPermiso();

  // La tarjeta del home solo se rehace en el arranque; envolvemos renderHome para
  // que, si vuelve a renderizarse, mantenga la tarjeta admin y el filtrado por rol.
  const X = window.__UI2;
  if (X && X.renderHome && !X._admWrap) {
    const orig = X.renderHome;
    X.renderHome = function () { orig.apply(this, arguments); aplicarPermisosHome(); };
    X._admWrap = true;
  }

  // El home se pinta antes del login; sondeamos hasta conocer el rol de la sesión.
  aplicarPermisosHome();
  const poll = setInterval(() => {
    const u = getCachedUser && getCachedUser();
    if (!u) return;               // aún sin sesión iniciada
    aplicarPermisosHome();
    clearInterval(poll);          // ya conocemos el rol de esta sesión
  }, 1000);

  admInstalado = true;
}

/* ================= CMS DE CONTENIDOS (avisos multicanal) ================= */

function formContenido(c) {
  const ti = (c && c.titulo_i18n) || {};
  const ci = (c && c.cuerpo_i18n) || {};
  const canales = (c && c.canales) || ["totem"];
  const dtLocal = (v) => (v ? String(v).slice(0, 16) : "");
  const bloqueIdioma = (lang, etiqueta) =>
    '<details style="margin-top:10px;border:1.5px solid var(--line);border-radius:10px;padding:8px 12px"' + ((ti[lang] || ci[lang]) ? " open" : "") + ">" +
    '<summary style="font-size:12px;font-weight:800;color:var(--muted);cursor:pointer">' + etiqueta + "</summary>" +
    campo("Título (" + lang.toUpperCase() + ")", '<input name="titulo_' + lang + '" maxlength="255" value="' + esc(ti[lang] || "") + '" ' + INPUT_CSS + ">") +
    campo("Texto (" + lang.toUpperCase() + ")", '<textarea name="cuerpo_' + lang + '" rows="2" ' + INPUT_CSS + ">" + esc(ci[lang] || "") + "</textarea>") +
    "</details>";
  const checkCanal = (id, etiqueta) =>
    '<label style="display:flex;gap:6px;align-items:center;font-size:13px"><input type="checkbox" name="canal_' + id + '"' +
    (canales.includes(id) ? " checked" : "") + "> " + etiqueta + "</label>";

  abrirForm(c ? "Editar contenido" : "Nuevo aviso / contenido",
    campo("Título (aparece en el ticker del tótem)", '<input name="titulo" required maxlength="255" value="' + esc(c ? c.titulo : "") + '" ' + INPUT_CSS + ">") +
    campo("Texto completo", '<textarea name="cuerpo" required rows="3" ' + INPUT_CSS + ">" + esc(c ? c.cuerpo || "" : "") + "</textarea>") +
    bloqueIdioma("en", "Traducción · Inglés") +
    bloqueIdioma("de", "Traducción · Alemán") +
    bloqueIdioma("fr", "Traducción · Francés") +
    campo("Canales", '<div style="display:flex;gap:16px;margin-top:4px">' +
      checkCanal("totem", "Tótems") + checkCanal("web", "Web") + checkCanal("app", "App") + "</div>") +
    '<div style="display:flex;gap:10px">' +
    '<div style="flex:1">' + campo("Visible desde (opcional)", '<input name="desde" type="datetime-local" value="' + dtLocal(c && c.publicar_desde) + '" ' + INPUT_CSS + ">") + "</div>" +
    '<div style="flex:1">' + campo("Visible hasta (opcional)", '<input name="hasta" type="datetime-local" value="' + dtLocal(c && c.publicar_hasta) + '" ' + INPUT_CSS + ">") + "</div></div>" +
    '<label style="display:flex;gap:8px;align-items:center;margin-top:14px;font-size:13px"><input type="checkbox" name="publicar"' +
    (!c || c.estado === "publicado" || c.estado === "programado" ? " checked" : "") + "> Publicado (visible en los canales marcados)</label>",
    async (fd) => {
      const tI18n = {}, cI18n = {};
      ["en", "de", "fr"].forEach((lang) => {
        tI18n[lang] = (fd.get("titulo_" + lang) || "").trim() || null;
        cI18n[lang] = (fd.get("cuerpo_" + lang) || "").trim() || null;
      });
      const payload = {
        titulo: fd.get("titulo").trim(),
        cuerpo: fd.get("cuerpo").trim(),
        titulo_i18n: { es: fd.get("titulo").trim(), ...tI18n },
        cuerpo_i18n: { es: fd.get("cuerpo").trim(), ...cI18n },
        canales: ["totem", "web", "app"].filter((x) => fd.get("canal_" + x) === "on"),
        publicar_desde: fd.get("desde") ? new Date(fd.get("desde")).toISOString() : null,
        publicar_hasta: fd.get("hasta") ? new Date(fd.get("hasta")).toISOString() : null,
        publicar: fd.get("publicar") === "on",
      };
      if (c) await api.updateContenido(c.id, payload);
      else await api.createContenido(payload);
      UI.toast(c ? "Contenido actualizado" : "Contenido creado");
      UI.rerenderD("contenidos");
    });
}

async function renderContenidosCMS(el) {
  cargando(el, "CMS de contenidos");
  let data;
  try { data = await api.listContenidos({ page: 1, page_size: 100 }); }
  catch (e) { return errorCarga(el, "CMS de contenidos", e); }
  const filas = data.items || [];
  const rw = puedeEscribir();
  const badgeEstado = (s) =>
    '<span class="bdg ' + (s === "publicado" ? "bdg-ok" : s === "programado" ? "bdg-info" : s === "archivado" ? "bdg-mut" : "bdg-warn") + '">' + esc(s) + "</span>";

  el.innerHTML = gsub("CMS", "CMS de contenidos",
    "Avisos y publicaciones multicanal. Lo marcado para el canal «Tótems» aparece en el ticker de AVISOS de la pantalla de inicio del tótem (en el idioma del visitante); web y app lo consumen por API.",
    rw ? '<button class="btn btn--pri" data-g="new-cont">＋ Nuevo aviso / contenido</button>' : "") +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Contenidos", data.total ?? filas.length, "En el CMS", "ic-navy", "folder") +
    kpi("Publicados", filas.filter((c) => c.estado === "publicado").length, "Visibles ahora", "ic-ok", "chart") +
    kpi("Canal tótems", filas.filter((c) => (c.canales || []).includes("totem")).length, "En el ticker del tótem", "ic-teal", "chat") +
    kpi("Programados", filas.filter((c) => c.estado === "programado").length, "Con fecha de inicio futura", "ic-violet", "clock") + "</div>" +
    '<div class="card card--pad0"><div style="padding:16px 16px 4px" class="card__h"><div><div class="card__t">Contenidos</div><div class="card__s">Los más recientes primero</div></div></div>' +
    '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Título</th><th>Canales</th><th>Estado</th><th>Ventana</th>' + (rw ? "<th></th>" : "") + "</tr></thead><tbody>" +
    (filas.map((c, i) =>
      '<tr><td style="white-space:normal;min-width:240px;font-weight:600">' + esc(c.titulo) + "</td>" +
      '<td class="mini">' + esc((c.canales || []).join(", ") || "—") + "</td>" +
      "<td>" + badgeEstado(c.estado) + "</td>" +
      '<td class="mini tnum">' + (c.publicar_desde ? fechaCorta(c.publicar_desde) : "—") + " → " + (c.publicar_hasta ? fechaCorta(c.publicar_hasta) : "—") + "</td>" +
      (rw ? '<td style="white-space:nowrap"><button class="btn btn--sm" data-g="ed-cont" data-i="' + i + '">Editar</button> ' +
        '<button class="btn btn--sm" data-g="del-cont" data-i="' + i + '">Eliminar</button></td>' : "") + "</tr>").join("") ||
      '<tr><td colspan="5" class="mini" style="text-align:center;padding:20px">Sin contenidos — crea el primer aviso para el tótem</td></tr>') +
    "</tbody></table></div></div>";

  const btn = el.querySelector('[data-g="new-cont"]');
  if (btn) btn.onclick = () => formContenido(null);
  el.querySelectorAll('[data-g="ed-cont"]').forEach((b) => { b.onclick = () => formContenido(filas[Number(b.dataset.i)]); });
  el.querySelectorAll('[data-g="del-cont"]').forEach((b) => {
    b.onclick = async () => {
      const c = filas[Number(b.dataset.i)];
      if (!window.confirm('¿Eliminar "' + c.titulo + '"? Dejará de mostrarse en todos los canales.')) return;
      try { await api.deleteContenido(c.id); UI.toast("Contenido eliminado"); UI.rerenderD("contenidos"); }
      catch (e) { UI.toast("Error: " + (e.message || e)); }
    };
  });
}

/* ================= PUBLICIDAD · EMPRESAS ANUNCIANTES ================= */

const SECTORES_EMPRESA = ["gastronomia", "alojamiento", "ocio_activo", "comercio", "servicios", "otro"];

function formEmpresa(e) {
  const di = (e && e.descripcion_i18n) || {};
  const dtLocal = (v) => (v ? String(v).slice(0, 16) : "");
  const bloqueIdioma = (lang, etiqueta) =>
    '<details style="margin-top:10px;border:1.5px solid var(--line);border-radius:10px;padding:8px 12px"' + (di[lang] ? " open" : "") + ">" +
    '<summary style="font-size:12px;font-weight:800;color:var(--muted);cursor:pointer">' + etiqueta + "</summary>" +
    campo("Descripción (" + lang.toUpperCase() + ")", '<textarea name="desc_' + lang + '" rows="2" ' + INPUT_CSS + ">" + esc(di[lang] || "") + "</textarea>") +
    "</details>";

  abrirForm(e ? "Editar empresa" : "Alta de empresa anunciante",
    campo("Nombre", '<input name="nombre" required maxlength="255" value="' + esc(e ? e.nombre : "") + '" ' + INPUT_CSS + ">") +
    campo("Sector", '<select name="sector" ' + INPUT_CSS + ">" + SECTORES_EMPRESA.map((s) =>
      '<option value="' + s + '"' + (e && e.sector === s ? " selected" : "") + ">" + s.replace(/_/g, " ") + "</option>").join("") + "</select>") +
    campo("Descripción (aparece en el tótem)", '<textarea name="descripcion" rows="3" ' + INPUT_CSS + ">" + esc(e ? e.descripcion || "" : "") + "</textarea>") +
    bloqueIdioma("en", "Traducción · Inglés") +
    bloqueIdioma("de", "Traducción · Alemán") +
    bloqueIdioma("fr", "Traducción · Francés") +
    '<div style="display:flex;gap:10px">' +
    '<div style="flex:1">' + campo("Núcleo", '<input name="nucleo" placeholder="San José, Níjar…" value="' + esc(e ? e.nucleo || "" : "") + '" ' + INPUT_CSS + ">") + "</div>" +
    '<div style="flex:1">' + campo("Teléfono", '<input name="telefono" value="' + esc(e ? e.telefono || "" : "") + '" ' + INPUT_CSS + ">") + "</div></div>" +
    campo("Dirección", '<input name="direccion" value="' + esc(e ? e.direccion || "" : "") + '" ' + INPUT_CSS + ">") +
    campo("Web", '<input name="web" placeholder="https://…" value="' + esc(e ? e.web || "" : "") + '" ' + INPUT_CSS + ">") +
    campo("Imágenes (una URL por línea; la primera es la foto del tótem)",
      '<textarea name="imagenes" rows="2" placeholder="https://…/local.jpg" ' + INPUT_CSS + ">" + esc((e && e.imagenes || []).join("\n")) + "</textarea>") +
    '<div style="display:flex;gap:10px">' +
    '<div style="flex:1">' + campo("Campaña desde (opcional)", '<input name="desde" type="datetime-local" value="' + dtLocal(e && e.campana_desde) + '" ' + INPUT_CSS + ">") + "</div>" +
    '<div style="flex:1">' + campo("Campaña hasta (opcional)", '<input name="hasta" type="datetime-local" value="' + dtLocal(e && e.campana_hasta) + '" ' + INPUT_CSS + ">") + "</div></div>" +
    '<label style="display:flex;gap:8px;align-items:center;margin-top:12px;font-size:13px"><input type="checkbox" name="destacado"' + (e && e.destacado ? " checked" : "") + "> Destacada (aparece la primera, con distintivo)</label>" +
    '<label style="display:flex;gap:8px;align-items:center;margin-top:8px;font-size:13px"><input type="checkbox" name="publicado"' + (!e || e.publicado ? " checked" : "") + "> Publicada (visible en el tótem)</label>",
    async (fd) => {
      const dI18n = { es: fd.get("descripcion").trim() || null };
      ["en", "de", "fr"].forEach((lang) => { dI18n[lang] = (fd.get("desc_" + lang) || "").trim() || null; });
      const urls = (fd.get("imagenes") || "").split("\n").map((u) => u.trim()).filter((u) => /^https?:\/\//.test(u));
      const payload = {
        nombre: fd.get("nombre").trim(),
        sector: fd.get("sector"),
        descripcion: fd.get("descripcion").trim() || null,
        descripcion_i18n: dI18n,
        nucleo: fd.get("nucleo").trim() || null,
        direccion: fd.get("direccion").trim() || null,
        telefono: fd.get("telefono").trim() || null,
        web: fd.get("web").trim() || null,
        imagenes: urls.length ? urls : null,
        destacado: fd.get("destacado") === "on",
        prioridad: e ? e.prioridad || 0 : 0,
        publicado: fd.get("publicado") === "on",
        campana_desde: fd.get("desde") ? new Date(fd.get("desde")).toISOString() : null,
        campana_hasta: fd.get("hasta") ? new Date(fd.get("hasta")).toISOString() : null,
      };
      if (e) await api.updateEmpresa(e.id, payload);
      else await api.createEmpresa(payload);
      UI.toast(e ? "Empresa actualizada" : "Empresa dada de alta");
      UI.rerenderD("g-publicidad");
    });
}

async function renderPublicidad(el) {
  cargando(el, "Publicidad");
  let data, resumen;
  try {
    [data, resumen] = await Promise.all([
      api.listEmpresas(),
      api.get("/publicidad/metricas?dias=30").catch(() => null),
    ]);
  }
  catch (err) { return errorCarga(el, "Publicidad", err); }
  const filas = data.items || [];
  const met = {};
  ((resumen && resumen.metricas) || []).forEach((m) => { met[m.empresa_id] = m; });
  const totalImpresiones = Object.values(met).reduce((a, m) => a + m.impresiones, 0);
  const rw = puedeEscribir();
  const ahora = new Date();
  const activaAhora = (e) => e.publicado &&
    (!e.campana_desde || new Date(e.campana_desde) <= ahora) &&
    (!e.campana_hasta || new Date(e.campana_hasta) >= ahora);

  el.innerHTML = gsub("Publicidad", "Publicidad · Empresas anunciantes",
    "Negocios locales con presencia en el apartado «Empresas» del tótem. Las destacadas aparecen primero con distintivo; la ventana de campaña controla cuándo se muestran.",
    rw ? '<button class="btn btn--pri" data-g="new-emp">＋ Alta de empresa</button>' : "") +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Empresas", data.total ?? filas.length, "Dadas de alta", "ic-navy", "box") +
    kpi("Visibles ahora", filas.filter(activaAhora).length, "Publicadas y en campaña", "ic-ok", "chart") +
    kpi("Destacadas", filas.filter((e) => e.destacado).length, "Posición preferente", "ic-gold", "bolt") +
    kpi("Impresiones (30 d)", totalImpresiones, "Apariciones en el tótem — base de facturación", "ic-violet", "chart") + "</div>" +
    '<div class="card card--pad0"><div style="padding:16px 16px 4px" class="card__h"><div><div class="card__t">Anunciantes</div><div class="card__s">Destacadas primero, luego por prioridad</div></div></div>' +
    '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Empresa</th><th>Sector</th><th>Núcleo</th><th>Campaña</th><th>Impresiones · Toques (30 d)</th><th>Estado</th>' + (rw ? "<th></th>" : "") + "</tr></thead><tbody>" +
    (filas.map((e, i) =>
      '<tr><td style="white-space:normal;min-width:200px;font-weight:600">' + esc(e.nombre) +
      (e.destacado ? ' <span class="bdg bdg-warn">destacada</span>' : "") + "</td>" +
      '<td class="mini">' + esc(e.sector.replace(/_/g, " ")) + "</td>" +
      '<td class="mini">' + esc(e.nucleo || "—") + "</td>" +
      '<td class="mini tnum">' + (e.campana_desde ? fechaCorta(e.campana_desde) : "—") + " → " + (e.campana_hasta ? fechaCorta(e.campana_hasta) : "—") + "</td>" +
      '<td class="mini tnum">' + (met[e.id] ? met[e.id].impresiones + " · " + met[e.id].toques : "0 · 0") + "</td>" +
      "<td>" + (activaAhora(e) ? '<span class="bdg bdg-ok">visible</span>' : e.publicado ? '<span class="bdg bdg-info">fuera de campaña</span>' : '<span class="bdg bdg-mut">borrador</span>') + "</td>" +
      (rw ? '<td style="white-space:nowrap"><button class="btn btn--sm" data-g="ed-emp" data-i="' + i + '">Editar</button> ' +
        '<button class="btn btn--sm" data-g="del-emp" data-i="' + i + '">Eliminar</button></td>' : "") + "</tr>").join("") ||
      '<tr><td colspan="7" class="mini" style="text-align:center;padding:20px">Sin empresas — da de alta la primera</td></tr>') +
    "</tbody></table></div></div>";

  const btn = el.querySelector('[data-g="new-emp"]');
  if (btn) btn.onclick = () => formEmpresa(null);
  el.querySelectorAll('[data-g="ed-emp"]').forEach((b) => { b.onclick = () => formEmpresa(filas[Number(b.dataset.i)]); });
  el.querySelectorAll('[data-g="del-emp"]').forEach((b) => {
    b.onclick = async () => {
      const e = filas[Number(b.dataset.i)];
      if (!window.confirm('¿Eliminar "' + e.nombre + '"? Dejará de mostrarse en el tótem.')) return;
      try { await api.deleteEmpresa(e.id); UI.toast("Empresa eliminada"); UI.rerenderD("g-publicidad"); }
      catch (err) { UI.toast("Error: " + (err.message || err)); }
    };
  });
}

/* ---------------- registro de secciones ---------------- */

const SECCIONES = [
  { g: "Gestión de contenidos" },
  { id: "g-catalogo", n: "Catálogo de recursos", i: "box", r: renderCatalogo },
  { id: "g-eventos", n: "Agenda de eventos", i: "cal", r: renderEventos },
  { id: "g-campanas", n: "Campañas", i: "chart", r: renderCampanas },
  { id: "g-publicidad", n: "Publicidad · Empresas", i: "box", r: renderPublicidad },
  { id: "g-faqs", n: "FAQs del chatbot", i: "chat", r: renderFaqs },
  { id: "g-cliente", n: "Ficha del cliente", i: "folder", r: renderCliente },
  { id: "g-prediccion", n: "Predicción de afluencia", i: "chart", r: renderPrediccion },
  { id: "g-ia", n: "Consumo de IA", i: "chat", r: renderConsumoIA },
  { id: "g-config", n: "Configuración", i: "gear", r: renderConfig },
];

function registrar() {
  DTI = window.__DTI;
  UI = window.UI;
  U = window.__U;
  if (!DTI || !DTI.DSECTIONS || !DTI.renderDSidebar || !UI) return false;

  /* La sección «CMS de contenidos» del demo pasa a ser el CRUD real */
  DTI.DR.contenidos = renderContenidosCMS;

  const main = document.getElementById("dti-main");
  SECCIONES.forEach((s) => {
    if (s.g) { DTI.DSECTIONS.push({ g: s.g }); return; }
    DTI.DSECTIONS.push({ id: s.id, n: s.n, i: s.i });
    DTI.DR[s.id] = s.r;
    if (main && !document.getElementById("dv-" + s.id)) {
      const sec = document.createElement("section");
      sec.className = "dview";
      sec.id = "dv-" + s.id;
      main.insertBefore(sec, main.lastElementChild);
    }
  });
  DTI.renderDSidebar();
  instalarAdmin();
  return true;
}

/* Espera a que el panel esté inicializado (los bloques inline ya corrieron
   porque este módulo se carga después, pero comprobamos por robustez). */
(function init() {
  if (!registrar()) setTimeout(init, 300);
})();
