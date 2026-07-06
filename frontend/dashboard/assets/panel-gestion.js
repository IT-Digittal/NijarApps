/**
 * Módulos de gestión (CRUD) integrados en el panel DTI definitivo.
 *
 * Añade al sidebar de la consola DTI el grupo «Gestión» con los módulos
 * del pliego que antes vivían en gestion.html: catálogo de recursos
 * turísticos, eventos, campañas, FAQs del chatbot, ficha del cliente y
 * configuración. Todo contra la API real con control de roles.
 */

import { api, getCachedUser } from "./api-client.js?v=17";

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
    '<label style="display:flex;gap:8px;align-items:center;margin-top:14px;font-size:13px"><input type="checkbox" name="publicado" checked> Publicado</label>',
    async (fd) => {
      const nombre = fd.get("nombre").trim();
      await api.createEvent({
        urn: "urn:ngsi-ld:EventoTuristico:nijar:" + slug(nombre) + "-" + slug(fd.get("fecha_inicio")).slice(0, 10),
        nombre,
        tipo: fd.get("tipo"),
        descripcion: fd.get("descripcion").trim() || null,
        fecha_inicio: new Date(fd.get("fecha_inicio")).toISOString(),
        fecha_fin: new Date(fd.get("fecha_fin")).toISOString(),
        organizador: fd.get("organizador").trim() || null,
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

/* ================= USUARIOS Y PERMISOS ================= */

const ROLES = ["administrador_tic", "gestor_contenidos", "analista_datos", "operador_smart_office", "auditor"];

async function renderUsuarios(el) {
  cargando(el, "Usuarios y permisos");
  let usuarios;
  try { usuarios = await api.listUsuarios(); }
  catch (e) {
    el.innerHTML = gsub("Usuarios y permisos", "Usuarios y permisos", "Gestión de cuentas del panel.") +
      '<div class="card"><div class="mini" style="color:var(--muted);text-align:center;padding:26px 0">' +
      (e && e.status === 403 ? "Solo el administrador TIC puede gestionar usuarios." : "Error: " + esc(e && e.message || e)) + "</div></div>";
    return;
  }

  el.innerHTML = gsub("Usuarios y permisos", "Usuarios y permisos",
    "Cuentas con acceso al panel y sus roles RBAC (5 perfiles del pliego). Las invitaciones crean la cuenta con contraseña temporal.",
    '<button class="btn btn--pri" data-g="inv-usr">＋ Invitar usuario</button>') +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Usuarios", usuarios.length, "Con acceso al panel", "ic-navy", "gear") +
    kpi("Activos", usuarios.filter((u) => u.activo).length, "Pueden iniciar sesión", "ic-ok", "chart") +
    kpi("Administradores TIC", usuarios.filter((u) => u.rol === "administrador_tic").length, "Control total de la plataforma", "ic-coral", "gear") +
    kpi("Con 2FA", usuarios.filter((u) => u.requiere_2fa).length, "Doble factor requerido", "ic-teal", "gear") + "</div>" +
    '<div class="card card--pad0"><div style="padding:16px 16px 4px" class="card__h"><div><div class="card__t">Cuentas</div><div class="card__s">Roles según la matriz RBAC del pliego (ENS medio)</div></div></div>' +
    '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Nombre</th><th>Email</th><th>Rol</th><th>Estado</th><th>2FA</th><th>Alta</th></tr></thead><tbody>' +
    usuarios.map((u) =>
      '<tr><td style="font-weight:600">' + esc(u.nombre_completo) + '</td><td class="mini">' + esc(u.email) + "</td>" +
      '<td><span class="bdg bdg-info">' + esc(u.rol) + "</span></td>" +
      "<td>" + (u.activo ? '<span class="bdg bdg-ok">activo</span>' : '<span class="bdg bdg-mut">inactivo</span>') + "</td>" +
      '<td class="mini">' + (u.requiere_2fa ? "Sí" : "No") + '</td><td class="mini tnum">' + fechaCorta(u.created_at) + "</td></tr>").join("") +
    "</tbody></table></div></div>";

  const btn = el.querySelector('[data-g="inv-usr"]');
  if (btn) btn.onclick = () => abrirForm("Invitar usuario",
    campo("Nombre completo", '<input name="nombre_completo" required minlength="2" maxlength="255" ' + INPUT_CSS + ">") +
    campo("Email", '<input name="email" type="email" required ' + INPUT_CSS + ">") +
    campo("Rol", '<select name="rol" ' + INPUT_CSS + ">" + ROLES.map((r) => '<option value="' + r + '">' + r.replace(/_/g, " ") + "</option>").join("") + "</select>"),
    async (fd) => {
      try {
        await api.inviteUsuario({
          email: fd.get("email").trim(),
          nombre_completo: fd.get("nombre_completo").trim(),
          rol: fd.get("rol"),
        });
      } catch (e) {
        if (e && e.status === 409) throw new Error("Ya existe un usuario con ese email.");
        throw e;
      }
      UI.toast("Invitación enviada: cuenta creada con contraseña temporal");
      UI.rerenderD("g-usuarios");
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
  const vals = puntos.map((p) => p.prediccion ?? p.valor ?? 0);

  el.innerHTML = gsub("Predicción", "Predicción de afluencia",
    "Modelo estacional sobre el histórico de la plataforma: previsión de visitas a 14 días con validación MAPE (holdout temporal).", "") +
    '<div class="grid g4" style="margin-bottom:16px">' +
    kpi("Modelo", afluencia ? afluencia.modelo.replace(/_/g, " ") : "—", "Entrenado con el histórico propio", "ic-navy", "gear") +
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
    '<div class="chip-row" style="margin-top:14px"><button class="btn btn--sm" onclick="(async()=>{const m=await import(\'./api-client.js?v=17\');await m.api.logout();location.reload()})()">Cerrar sesión</button></div></div></div>';
}

/* ---------------- helpers de tarjetas ---------------- */

function kpi(l, v, d, cls, ic, click) {
  const X = window.__UI2;
  return X && X.kpiCard ? X.kpiCard(l, esc(String(v ?? "—")), d, cls, ic, click || "") : "";
}

function kv(k, v) {
  return '<div class="kv"><span class="k">' + esc(k) + '</span><span class="v">' + (v == null || v === "" ? "—" : v) + "</span></div>";
}

/* ---------------- registro de secciones ---------------- */

const SECCIONES = [
  { g: "Gestión de contenidos" },
  { id: "g-catalogo", n: "Catálogo de recursos", i: "box", r: renderCatalogo },
  { id: "g-eventos", n: "Agenda de eventos", i: "cal", r: renderEventos },
  { id: "g-campanas", n: "Campañas", i: "chart", r: renderCampanas },
  { id: "g-faqs", n: "FAQs del chatbot", i: "chat", r: renderFaqs },
  { id: "g-cliente", n: "Ficha del cliente", i: "folder", r: renderCliente },
  { id: "g-usuarios", n: "Usuarios y permisos", i: "gear", r: renderUsuarios },
  { id: "g-prediccion", n: "Predicción de afluencia", i: "chart", r: renderPrediccion },
  { id: "g-ia", n: "Consumo de IA", i: "chat", r: renderConsumoIA },
  { id: "g-config", n: "Configuración", i: "gear", r: renderConfig },
];

function registrar() {
  DTI = window.__DTI;
  UI = window.UI;
  U = window.__U;
  if (!DTI || !DTI.DSECTIONS || !DTI.renderDSidebar || !UI) return false;

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
  return true;
}

/* Espera a que el panel esté inicializado (los bloques inline ya corrieron
   porque este módulo se carga después, pero comprobamos por robustez). */
(function init() {
  if (!registrar()) setTimeout(init, 300);
})();
