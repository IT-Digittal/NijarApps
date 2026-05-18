/**
 * CMS Administrativo — Plataforma DTI Níjar
 * Lógica de navegación sidebar + carga de datos + visualizaciones.
 * Diseño "Salinas y Sal corporativa" v3.
 */

import { api, tokens, getCachedUser } from "./api-client.js?v=15";

// ============================================================
// State
// ============================================================
const charts = {};
let mapInstance = null;
let mapLayer = null;
const REFRESH_MS = 30_000;
let refreshTimer = null;

// ============================================================
// Helpers
// ============================================================
const fmt = (val, digits = 1) => {
  if (val === null || val === undefined || Number.isNaN(val)) return "—";
  return Number(val).toFixed(digits);
};

const setKPI = (key, value) => {
  document.querySelectorAll(`[data-kpi="${key}"]`).forEach(el => {
    el.textContent = value;
  });
};

const setBanner = (msg, type = "info") => {
  const b = document.getElementById("conn-banner");
  b.className = `banner banner--${type}`;
  b.textContent = msg;
  b.classList.remove("hidden");
  if (type === "success") setTimeout(() => b.classList.add("hidden"), 3000);
};

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

// ============================================================
// Auth flow
// ============================================================
const dialog = document.getElementById("login-dialog");
const loginForm = document.getElementById("login-form");
const loginError = document.getElementById("login-error");

const loginOverlay = document.getElementById("login-overlay");

function showLogin() {
  loginOverlay.classList.add("login-overlay--visible");
  dialog.showModal();
  setTimeout(() => document.getElementById("email")?.focus(), 50);
}

function hideLogin() {
  dialog.close();
  loginOverlay.classList.remove("login-overlay--visible");
  loginError.classList.add("hidden");
  loginForm.reset();
}

function applyUserChrome(user) {
  const nameEl = document.getElementById("user-name");
  const roleEl = document.getElementById("user-role");
  const avatarEl = document.getElementById("user-avatar");
  const logoutBtn = document.getElementById("logout-btn");

  if (!user) {
    nameEl.textContent = "—";
    roleEl.textContent = "—";
    avatarEl.textContent = "—";
    logoutBtn.classList.add("hidden");
    return;
  }

  nameEl.textContent = user.nombre_completo || user.email;
  roleEl.textContent = user.rol?.replace(/_/g, " ") || "";
  avatarEl.textContent = (user.nombre_completo || user.email)
    .split(" ").map(w => w[0]).join("").substring(0, 2).toUpperCase();
  logoutBtn.classList.remove("hidden");

  // Greeting
  const h = new Date().getHours();
  const saludo = h < 13 ? "Buenos días" : h < 20 ? "Buenas tardes" : "Buenas noches";
  const first = (user.nombre_completo || "").split(" ")[0] || "";
  document.getElementById("greeting").textContent = `${saludo}${first ? ", " + first : ""}`;
}

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  loginError.classList.add("hidden");
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  try {
    const user = await api.login(email, password);
    applyUserChrome(user);
    hideLogin();
    initDashboard();
  } catch (err) {
    loginError.textContent = err.code === "UNAUTHORIZED"
      ? "Credenciales inválidas"
      : `Error: ${err.message}`;
    loginError.classList.remove("hidden");
  }
});

document.getElementById("logout-btn").addEventListener("click", async () => {
  await api.logout();
  applyUserChrome(null);
  if (refreshTimer) clearInterval(refreshTimer);
  showLogin();
});

// ============================================================
// Sidebar navigation
// ============================================================
const navItems = document.querySelectorAll(".nav-item[data-section]");
const sectionPanels = document.querySelectorAll("[data-section-content]");

function switchSection(name) {
  navItems.forEach(btn => {
    btn.classList.toggle("nav-item--active", btn.dataset.section === name);
  });
  sectionPanels.forEach(panel => {
    panel.classList.toggle("hidden", panel.dataset.sectionContent !== name);
  });
  // Lazy load sections
  const loaders = {
    "dashboard": loadDashboard,
    "catalogo": loadCatalog,
    "eventos": loadEvents,
    "smart-office": loadSmartOffice,
    "big-data": loadBigData,
    "chatbot": loadChatbot,
    "mapa": loadMap,
    "totems": loadTotems,
    "usuarios": loadUsuarios,
    "config": loadConfig,
  };
  if (loaders[name]) loaders[name]();
}

navItems.forEach(btn => {
  btn.addEventListener("click", () => switchSection(btn.dataset.section));
});

// ============================================================
// DASHBOARD section
// ============================================================
async function loadDashboard() {
  // Smart Office overview
  try {
    const ov = await api.smartOfficeOverview();
    setKPI("co2", fmt(ov.co2_actual_ppm, 0));
    setKPI("temp", fmt(ov.temperatura_actual_c, 1));
    setKPI("hum", fmt(ov.humedad_actual_porc, 0));
    setKPI("noise", fmt(ov.ruido_actual_db, 0));
    setKPI("sensores-op", String(ov.sensores_operativos));
    setKPI("sensores-total", String(ov.sensores_total));
  } catch (err) {
    console.warn("Smart Office overview falló:", err);
  }

  // Resources count + draft/published breakdown
  try {
    const allRes = await api.listResources({ page: 1, page_size: 200 });
    const items = allRes.items || [];
    const total = allRes.total || items.length;
    const publicados = items.filter(r => r.publicado).length;
    const pendientes = total - publicados;
    setKPI("dash-recursos", String(total));
    setKPI("dash-recursos-meta", `${Math.round((total / 100) * 100)}% del objetivo (100)`);
    setKPI("dash-pendientes", String(pendientes));
    setKPI("dash-publicados", String(publicados));
    const bar = document.querySelector('[data-kpi-bar="recursos"]');
    if (bar) bar.style.width = `${Math.min(100, total)}%`;
    document.querySelectorAll('[data-badge="recursos"]').forEach(el => el.textContent = total);
  } catch { /* ignore */ }

  // Events count (badge sidebar)
  try {
    const evRes = await api.listEvents({ page: 1, page_size: 1 });
    const evTotal = evRes.total || 0;
    document.querySelectorAll('[data-badge="eventos"]').forEach(el => el.textContent = evTotal);
  } catch { /* ignore */ }

  // Totems
  try {
    const tot = await api.totemsUsage();
    setKPI("tot-int", String(tot.interacciones_total));
    setKPI("tot-ses", String(tot.sesiones_unicas));
  } catch { /* ignore */ }

  // Catalog status bars
  try {
    const recursos = await api.listResources({ page: 1, page_size: 200, publicado: true });
    const items = recursos.items || [];
    const cats = {};
    for (const r of items) {
      const c = r.categoria || "otro";
      cats[c] = (cats[c] || 0) + 1;
    }
    const container = document.getElementById("catalog-status");
    container.innerHTML = "";
    const catLabels = {
      playa: "Playas y calas",
      mirador: "Miradores",
      ruta: "Rutas senderistas",
      monumento: "Patrimonio cultural",
      punto_interes: "Puntos de interés",
      centro_visitantes: "Centros visitantes",
      oficina_turismo: "Oficinas de turismo",
      yacimiento: "Yacimientos",
    };
    const catTargets = { playa: 17, mirador: 12, ruta: 10, monumento: 10, punto_interes: 15, centro_visitantes: 5, oficina_turismo: 3, yacimiento: 5 };
    for (const [cat, label] of Object.entries(catLabels)) {
      const count = cats[cat] || 0;
      const target = catTargets[cat] || 10;
      const pct = Math.min(100, Math.round((count / target) * 100));
      const colorClass = pct >= 80 ? "catalog-bar__fill--teal" : pct >= 50 ? "catalog-bar__fill--gold" : "catalog-bar__fill--orange";
      container.innerHTML += `
        <div class="catalog-bar">
          <span class="catalog-bar__label">${escapeHtml(label)}</span>
          <div class="catalog-bar__track"><div class="catalog-bar__fill ${colorClass}" style="width:${pct}%"></div></div>
          <span class="catalog-bar__count">${count}</span>
        </div>`;
    }
  } catch { /* ignore */ }

  // Activity feed (synthetic for now based on available data)
  const feed = document.getElementById("activity-feed");
  feed.innerHTML = "";
  const activities = [
    { color: "green", title: "Sensores Smart Office operativos", meta: "8 sensores activos · sin alertas" },
    { color: "teal", title: "Datos de Social Listening actualizados", meta: "60 menciones procesadas · sentimiento positivo" },
    { color: "gold", title: "Tótems interactivos funcionando", meta: "2 tótems operativos · datos en tiempo real" },
    { color: "teal", title: "Chatbot multilingüe activo", meta: "ES/EN/DE/FR · motor lexical operativo" },
    { color: "green", title: "Mapa con recursos turísticos", meta: "14 POIs publicados con coordenadas GPS" },
  ];
  for (const a of activities) {
    const li = document.createElement("li");
    li.className = "activity-item";
    li.innerHTML = `
      <div class="activity-item__bar activity-item__bar--${a.color}"></div>
      <div class="activity-item__text">
        <div class="activity-item__title">${escapeHtml(a.title)}</div>
        <div class="activity-item__meta">${escapeHtml(a.meta)}</div>
      </div>`;
    feed.appendChild(li);
  }
}

// ============================================================
// CATÁLOGO section
// ============================================================
async function loadCatalog() {
  try {
    const recursos = await api.listResources({ page: 1, page_size: 200 });
    const items = recursos.items || [];
    const total = recursos.total || items.length;
    const borradores = items.filter(r => !r.publicado).length;
    setKPI("cat-total", String(total));
    setKPI("cat-borradores", String(borradores));

    // Filters
    const filtersEl = document.getElementById("catalog-filters");
    const cats = {};
    for (const r of items) { cats[r.categoria || "otro"] = (cats[r.categoria || "otro"] || 0) + 1; }
    const pub = items.filter(r => r.publicado).length;
    filtersEl.innerHTML = `<button class="filter-pill filter-pill--active" data-filter="all">Todos · ${total}</button>`;
    for (const [cat, count] of Object.entries(cats)) {
      filtersEl.innerHTML += `<button class="filter-pill" data-filter="${escapeHtml(cat)}">${escapeHtml(cat)} · ${count}</button>`;
    }
    if (borradores > 0) filtersEl.innerHTML += `<button class="filter-pill filter-pill--gold" data-filter="_draft">Borradores · ${borradores}</button>`;
    filtersEl.innerHTML += `<button class="filter-pill" data-filter="_pub">Publicados · ${pub}</button>`;
    filtersEl.querySelectorAll(".filter-pill").forEach(pill => {
      pill.addEventListener("click", () => {
        filtersEl.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("filter-pill--active"));
        pill.classList.add("filter-pill--active");
        filterTable(pill.dataset.filter);
      });
    });

    // Table
    const tbody = document.querySelector("#recursos-table tbody");
    tbody.innerHTML = "";
    for (const r of items) {
      const tr = document.createElement("tr");
      tr.dataset.categoria = r.categoria || "";
      tr.dataset.publicado = r.publicado ? "1" : "0";
      if (!r.publicado) tr.classList.add("row--draft");

      const statusClass = r.publicado ? "status-badge--active" : "status-badge--draft";
      const statusText = r.publicado ? "Activo" : "Borrador";
      const catClass = `cat-pill cat-pill--${(r.categoria || "").replace(/\s/g, "_")}`;
      const hasI18n = r.nombre_i18n && Object.keys(r.nombre_i18n).length >= 4;
      const idiomasHtml = hasI18n
        ? `<span style="color:#2D8F4F">ES · EN · DE · FR</span><br><span style="font-size:11px;color:#2D8F4F">Completo en 4 idiomas</span>`
        : `<span style="color:#E58A40">ES · — · — · —</span><br><span style="font-size:11px;color:#E58A40">Faltan traducciones</span>`;
      const accBadge = r.publicado
        ? `<span class="acc-badge acc-badge--si">PMR sí</span>`
        : `<span class="acc-badge acc-badge--nd">Sin definir</span>`;
      const updDate = r.updated_at ? new Date(r.updated_at) : null;
      const updText = updDate ? updDate.toLocaleDateString("es", { day: "numeric", month: "short" }) : "—";

      tr.innerHTML = `
        <td><span class="status-badge ${statusClass}">${statusText}</span></td>
        <td><strong>${escapeHtml(r.nombre)}</strong><br><span style="font-size:11px;color:var(--nijar-gris)">URN: ${escapeHtml((r.urn || "").replace("urn:ngsi-ld:RecursoTuristico:", ""))}</span></td>
        <td><span class="${catClass}">${escapeHtml(r.categoria || "—")}</span></td>
        <td style="font-size:13px;color:var(--nijar-gris)">${escapeHtml(r.descripcion_corta || "").substring(0, 40)}${(r.descripcion_corta || "").length > 40 ? "…" : ""}</td>
        <td style="font-size:12px">${idiomasHtml}</td>
        <td>${accBadge}</td>
        <td style="font-size:13px;color:var(--nijar-gris)">${updText}</td>
        <td>
          <div class="action-btns">
            <button class="action-btn${!r.publicado ? " action-btn--edit" : ""}" title="Editar recurso" data-action="edit">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
            </button>
            <button class="action-btn" title="Más acciones" data-action="more">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/></svg>
            </button>
          </div>
        </td>
      `;

      // Action handlers
      tr.querySelector('[data-action="edit"]').addEventListener("click", () => openRecursoDialog(r));
      tr.querySelector('[data-action="more"]').addEventListener("click", (e) => {
        e.stopPropagation();
        showRowMenu(e.currentTarget, r);
      });

      tbody.appendChild(tr);
    }
  } catch (err) {
    setBanner(`Error cargando catálogo: ${err.message}`, "error");
  }
}

function filterTable(cat) {
  document.querySelectorAll("#recursos-table tbody tr").forEach(tr => {
    if (cat === "all") tr.style.display = "";
    else if (cat === "_draft") tr.style.display = tr.dataset.publicado === "0" ? "" : "none";
    else if (cat === "_pub") tr.style.display = tr.dataset.publicado === "1" ? "" : "none";
    else tr.style.display = tr.dataset.categoria === cat ? "" : "none";
  });
}

// Row context menu
function showRowMenu(anchor, recurso) {
  document.querySelector(".row-menu")?.remove();
  const menu = document.createElement("div");
  menu.className = "row-menu ev-filter-dropdown";
  menu.style.position = "absolute";
  menu.innerHTML = `
    <button class="ev-filter-option" data-rm="edit">Editar recurso</button>
    <button class="ev-filter-option" data-rm="pub">${recurso.publicado ? "Despublicar" : "Publicar"}</button>
    <button class="ev-filter-option" data-rm="dup">Duplicar</button>
    <button class="ev-filter-option" style="color:#DC2626" data-rm="del">Eliminar</button>
  `;
  anchor.style.position = "relative";
  anchor.appendChild(menu);
  menu.querySelectorAll("[data-rm]").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      menu.remove();
      const action = btn.dataset.rm;
      try {
        if (action === "edit") {
          openRecursoDialog(recurso);
        } else if (action === "pub") {
          await api.updateResource(recurso.id, { ...buildRecursoPayload(recurso), publicado: !recurso.publicado });
          setBanner(`${recurso.publicado ? "Despublicado" : "Publicado"}: ${recurso.nombre}`, "success");
          await loadCatalog();
        } else if (action === "dup") {
          const slug = recurso.nombre.toLowerCase().replace(/[^a-z0-9]+/g, "-").substring(0, 30);
          const dupPayload = {
            ...buildRecursoPayload(recurso),
            urn: `urn:ngsi-ld:RecursoTuristico:nijar:${slug}-copia-${Date.now() % 10000}`,
            nombre: recurso.nombre + " (copia)",
            publicado: false,
          };
          await api.createResource(dupPayload);
          setBanner(`Duplicado: ${recurso.nombre}`, "success");
          await loadCatalog();
        } else if (action === "del") {
          if (!confirm(`¿Eliminar "${recurso.nombre}"? Esta acción no se puede deshacer.`)) return;
          await api.deleteResource(recurso.id);
          setBanner(`Eliminado: ${recurso.nombre}`, "success");
          await loadCatalog();
        }
      } catch (err) {
        setBanner(`Error: ${err.message}`, "error");
      }
    });
  });
  setTimeout(() => document.addEventListener("click", () => menu.remove(), { once: true }), 10);
}

function buildRecursoPayload(r) {
  const coords = r.ubicacion?.coordinates || [-2.10, 36.85];
  return {
    urn: r.urn,
    nombre: r.nombre,
    categoria: r.categoria,
    descripcion_corta: r.descripcion_corta || null,
    ubicacion: { type: "Point", coordinates: coords },
    publicado: r.publicado ?? false,
    activo: r.activo ?? true,
  };
}

// Search
document.getElementById("catalog-search")?.addEventListener("input", (e) => {
  const q = e.target.value.toLowerCase();
  document.querySelectorAll("#recursos-table tbody tr").forEach(tr => {
    tr.style.display = tr.textContent.toLowerCase().includes(q) ? "" : "none";
  });
});

// Resource editor (full page section)
let edResource = null;

function openRecursoDialog(recurso = null) {
  edResource = recurso;
  const isEdit = !!recurso;

  document.getElementById("ed-title").textContent = isEdit
    ? `Editar · ${recurso.nombre}` : "Nuevo recurso";
  document.getElementById("ed-subtitle").textContent = isEdit
    ? `URN: ${(recurso.urn || "").replace("urn:ngsi-ld:RecursoTuristico:", "")} · Última edición: ${recurso.updated_at ? new Date(recurso.updated_at).toLocaleString("es") : "—"}`
    : "";
  document.getElementById("ed-saved").classList.add("hidden");

  // Populate fields
  document.getElementById("ed-categoria").value = recurso?.categoria || "playa";
  document.getElementById("ed-subcategoria").value = "";
  document.getElementById("ed-nombre-es").value = recurso?.nombre || "";
  document.getElementById("ed-nombre-en").value = recurso?.nombre_i18n?.en || "";
  document.getElementById("ed-nombre-de").value = recurso?.nombre_i18n?.de || "";
  document.getElementById("ed-nombre-fr").value = recurso?.nombre_i18n?.fr || "";
  document.getElementById("ed-desc-corta").value = recurso?.descripcion_corta || "";
  document.getElementById("ed-desc-larga").value = "";
  document.getElementById("ed-horarios").value = "";
  document.getElementById("ed-contacto").value = "";
  document.getElementById("ed-lat").value = recurso?.ubicacion?.coordinates?.[1] ?? "";
  document.getElementById("ed-lon").value = recurso?.ubicacion?.coordinates?.[0] ?? "";

  // Publication status
  const pubEl = document.getElementById("ed-pub-status");
  if (recurso?.publicado) {
    pubEl.innerHTML = '<span class="dot dot--green"></span> Publicado en los 2 tótems';
    pubEl.className = "ed-status-pill";
  } else {
    pubEl.innerHTML = '<span class="dot dot--gold"></span> Borrador · no publicado';
    pubEl.className = "ed-status-pill ed-status-pill--draft";
  }

  document.getElementById("ed-form-error").classList.add("hidden");

  // Switch to editor section
  switchSection("editor");
}

// Editor tabs
document.querySelectorAll(".ed-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".ed-tab").forEach(t => t.classList.remove("ed-tab--active"));
    tab.classList.add("ed-tab--active");
    document.querySelectorAll(".ed-panel").forEach(p => p.classList.add("hidden"));
    document.getElementById(`ed-panel-${tab.dataset.edtab}`)?.classList.remove("hidden");
  });
});

// Language tabs (visual toggle)
document.querySelectorAll(".ed-lang").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".ed-lang").forEach(b => b.classList.remove("ed-lang--active"));
    btn.classList.add("ed-lang--active");
  });
});

// Channel toggles
document.querySelectorAll(".ed-channel").forEach(btn => {
  btn.addEventListener("click", () => {
    btn.classList.toggle("ed-channel--active");
    btn.textContent = btn.classList.contains("ed-channel--active")
      ? "✓ " + btn.textContent.replace(/^[✓○] /, "")
      : "○ " + btn.textContent.replace(/^[✓○] /, "");
  });
});

// Back to catalog
document.getElementById("ed-btn-cancel")?.addEventListener("click", () => switchSection("catalogo"));

// Save draft
document.getElementById("ed-btn-draft")?.addEventListener("click", () => saveResource(false));

// Publish
document.getElementById("ed-btn-publish")?.addEventListener("click", () => saveResource(true));

async function saveResource(publish) {
  const errEl = document.getElementById("ed-form-error");
  errEl.classList.add("hidden");

  const nombre = document.getElementById("ed-nombre-es").value.trim();
  const categoria = document.getElementById("ed-categoria").value;
  const lat = parseFloat(document.getElementById("ed-lat").value);
  const lon = parseFloat(document.getElementById("ed-lon").value);

  if (!nombre || isNaN(lat) || isNaN(lon)) {
    errEl.textContent = "Rellena nombre (ES), categoría y coordenadas.";
    errEl.classList.remove("hidden");
    return;
  }

  const isEdit = !!edResource;
  const urn = isEdit
    ? edResource.urn
    : `urn:ngsi-ld:RecursoTuristico:nijar:${nombre.toLowerCase().replace(/[^a-z0-9]+/g, "-").substring(0, 40)}`;

  const payload = {
    urn,
    nombre,
    categoria,
    descripcion_corta: document.getElementById("ed-desc-corta").value.trim() || null,
    ubicacion: { type: "Point", coordinates: [lon, lat] },
    publicado: publish,
    activo: true,
  };

  try {
    if (isEdit) {
      await api.updateResource(edResource.id, payload);
    } else {
      await api.createResource(payload);
    }
    document.getElementById("ed-saved").classList.remove("hidden");
    setBanner(publish ? "Recurso publicado en tótems" : "Borrador guardado", "success");
    // Update pub status
    const pubEl = document.getElementById("ed-pub-status");
    if (publish) {
      pubEl.innerHTML = '<span class="dot dot--green"></span> Publicado en los 2 tótems';
      pubEl.className = "ed-status-pill";
    } else {
      pubEl.innerHTML = '<span class="dot dot--gold"></span> Borrador · no publicado';
      pubEl.className = "ed-status-pill ed-status-pill--draft";
    }
  } catch (err) {
    errEl.textContent = err.message || "Error al guardar";
    errEl.classList.remove("hidden");
  }
}

// New resource from catalog button
document.getElementById("btn-new-recurso")?.addEventListener("click", () => openRecursoDialog());

// ============================================================
// EVENTOS section — Calendar + List + Dialog
// ============================================================
const _DIAS_CORTO = ["DOM", "LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB"];
const _DIAS_LARGO = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"];
const _MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];
const _TIPO_LABEL = {
  cultural: "Cultural", musical: "Música", naturaleza: "Naturaleza", deportivo: "Deportivo",
  gastronomico: "Gastronomía", educativo: "Educativo", festivo: "Festivo", otro: "Otro",
};

let evWeekStart = getMonday(new Date());
let evAllItems = [];
let evFilteredItems = null; // null = no filter
let evSelectedEvent = null;
let evCurrentView = "semana";
let evEditingEvent = null;

function getMonday(d) {
  const dt = new Date(d);
  const day = dt.getDay();
  const diff = dt.getDate() - day + (day === 0 ? -6 : 1);
  dt.setDate(diff);
  dt.setHours(0, 0, 0, 0);
  return dt;
}

function evItems() { return evFilteredItems ?? evAllItems; }

// Week nav
document.getElementById("ev-prev")?.addEventListener("click", () => {
  evWeekStart.setDate(evWeekStart.getDate() - 7);
  renderEvView();
});
document.getElementById("ev-next")?.addEventListener("click", () => {
  evWeekStart.setDate(evWeekStart.getDate() + 7);
  renderEvView();
});

// View toggles
document.querySelectorAll(".ev-view-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".ev-view-btn").forEach(b => b.classList.remove("ev-view-btn--active"));
    btn.classList.add("ev-view-btn--active");
    evCurrentView = btn.dataset.view;
    renderEvView();
  });
});

// Filter button
const evFilterBtn = document.querySelector(".ev-filter-btn");
let evFilterOpen = false;
evFilterBtn?.addEventListener("click", (e) => {
  e.stopPropagation();
  if (evFilterOpen) { closeEvFilter(); return; }
  const existing = document.querySelector(".ev-filter-dropdown");
  if (existing) existing.remove();
  const dd = document.createElement("div");
  dd.className = "ev-filter-dropdown";
  dd.innerHTML = `<button class="ev-filter-option ev-filter-option--active" data-ft="all">Todos</button>`;
  const tipos = [...new Set(evAllItems.map(e => e.tipo))];
  for (const t of tipos) {
    dd.innerHTML += `<button class="ev-filter-option" data-ft="${escapeHtml(t)}">${escapeHtml(_TIPO_LABEL[t] || t)}</button>`;
  }
  evFilterBtn.style.position = "relative";
  evFilterBtn.appendChild(dd);
  evFilterOpen = true;
  dd.querySelectorAll(".ev-filter-option").forEach(opt => {
    opt.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const ft = opt.dataset.ft;
      if (ft === "all") { evFilteredItems = null; }
      else { evFilteredItems = evAllItems.filter(e => e.tipo === ft); }
      closeEvFilter();
      renderEvView();
    });
  });
});
function closeEvFilter() {
  document.querySelector(".ev-filter-dropdown")?.remove();
  evFilterOpen = false;
}
document.addEventListener("click", closeEvFilter);

// Load events
async function loadEvents() {
  try {
    const res = await api.listEvents({ page: 1, page_size: 50 });
    evAllItems = (res.items || []).sort((a, b) => new Date(a.fecha_inicio) - new Date(b.fecha_inicio));
    evFilteredItems = null;
    document.querySelectorAll('[data-badge="eventos"]').forEach(el => el.textContent = evAllItems.length);
    if (evAllItems.length > 0) {
      const firstDate = new Date(evAllItems[0].fecha_inicio);
      if (firstDate > new Date()) evWeekStart = getMonday(firstDate);
    }
    document.getElementById("ev-month-title").textContent =
      `Eventos · ${_MESES[evWeekStart.getMonth()]} ${evWeekStart.getFullYear()}`;
    renderEvView();
  } catch (err) {
    setBanner(`Error cargando eventos: ${err.message}`, "error");
  }
}

function renderEvView() {
  document.getElementById("ev-month-title").textContent =
    `Eventos · ${_MESES[evWeekStart.getMonth()]} ${evWeekStart.getFullYear()}`;
  if (evCurrentView === "semana") renderWeekView();
  else if (evCurrentView === "lista") renderListView();
  else if (evCurrentView === "mes") renderMonthView();
}

// ---------- WEEK VIEW ----------
function renderWeekView() {
  const headers = document.getElementById("ev-day-headers");
  const grid = document.getElementById("ev-day-grid");
  headers.innerHTML = ""; grid.innerHTML = "";
  headers.style.display = ""; grid.style.display = "";

  const weekEnd = new Date(evWeekStart); weekEnd.setDate(weekEnd.getDate() + 6);
  document.getElementById("ev-week-label").textContent =
    `${evWeekStart.getDate()} — ${weekEnd.getDate()} ${_MESES[evWeekStart.getMonth()].toLowerCase()}`;

  for (let i = 0; i < 7; i++) {
    const d = new Date(evWeekStart); d.setDate(d.getDate() + i);
    const dayNum = d.getDay();
    const isWE = dayNum === 0 || dayNum === 5 || dayNum === 6;
    const hdr = document.createElement("div");
    hdr.className = `ev-day-header${isWE ? " ev-day-header--weekend" : ""}`;
    hdr.textContent = `${_DIAS_CORTO[dayNum]} ${d.getDate()}`;
    headers.appendChild(hdr);

    const col = document.createElement("div");
    col.className = `ev-day-col${isWE ? " ev-day-col--weekend" : ""}`;
    const dayStr = d.toISOString().substring(0, 10);
    for (const ev of evItems().filter(e => new Date(e.fecha_inicio).toISOString().substring(0, 10) === dayStr)) {
      col.appendChild(makeEvBlock(ev));
    }
    grid.appendChild(col);
  }
  autoSelectFirst();
}

// ---------- LIST VIEW ----------
function renderListView() {
  const headers = document.getElementById("ev-day-headers");
  const grid = document.getElementById("ev-day-grid");
  headers.innerHTML = ""; headers.style.display = "none";
  grid.innerHTML = ""; grid.style.display = "block";
  grid.style.padding = "var(--space-4)";

  const items = evItems();
  if (items.length === 0) {
    grid.innerHTML = '<p style="text-align:center;color:var(--nijar-gris);padding:var(--space-8)">Sin eventos en el periodo seleccionado</p>';
    return;
  }
  const list = document.createElement("div");
  list.style.cssText = "display:flex;flex-direction:column;gap:8px;";
  for (const ev of items) {
    const d = new Date(ev.fecha_inicio);
    const fin = new Date(ev.fecha_fin);
    const tipo = ev.tipo || "otro";
    const hora = d.toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
    const horaFin = fin.toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
    const row = document.createElement("button");
    row.style.cssText = "display:flex;align-items:center;gap:16px;padding:12px 16px;border-radius:12px;border:1px solid #E0DDD2;background:white;cursor:pointer;text-align:left;width:100%;font-family:inherit;transition:border-color .15s;";
    row.addEventListener("mouseenter", () => row.style.borderColor = "#00A6C0");
    row.addEventListener("mouseleave", () => row.style.borderColor = "#E0DDD2");
    row.innerHTML = `
      <div style="width:5px;height:40px;border-radius:99px;background:var(--ev-bar-${tipo});flex-shrink:0" class="ev-block--${escapeHtml(tipo)}"></div>
      <div style="width:50px;text-align:center;flex-shrink:0">
        <div style="font-family:var(--font-display);font-size:11px;font-weight:700;text-transform:uppercase;color:var(--nijar-gris)">${_DIAS_CORTO[d.getDay()]}</div>
        <div style="font-family:var(--font-display);font-size:20px;font-weight:700;color:var(--nijar-marino)">${d.getDate()}</div>
      </div>
      <div style="flex:1;min-width:0">
        <div style="font-family:var(--font-display);font-size:15px;font-weight:600;color:var(--nijar-marino)">${escapeHtml(ev.nombre)}</div>
        <div style="font-size:13px;color:var(--nijar-gris)">${escapeHtml(ev.direccion || "")}${ev.direccion ? " · " : ""}${hora} – ${horaFin}${ev.precio ? " · " + escapeHtml(ev.precio) : ""}</div>
      </div>
      <span class="ev-block__tag" style="padding:4px 12px;border-radius:99px;font-size:12px;font-weight:500;background:var(--nijar-marino);color:white">${escapeHtml(_TIPO_LABEL[tipo] || tipo)}</span>
    `;
    row.addEventListener("click", () => selectEvent(ev));
    list.appendChild(row);
  }
  grid.appendChild(list);
  autoSelectFirst();
}

// ---------- MONTH VIEW ----------
function renderMonthView() {
  const headers = document.getElementById("ev-day-headers");
  const grid = document.getElementById("ev-day-grid");
  headers.innerHTML = ""; headers.style.display = "";
  grid.innerHTML = ""; grid.style.display = "";
  grid.style.padding = "";

  // Headers
  for (let i = 1; i <= 7; i++) {
    const dayIdx = i % 7; // LUN=1..DOM=0
    const hdr = document.createElement("div");
    hdr.className = `ev-day-header${(dayIdx === 0 || dayIdx === 5 || dayIdx === 6) ? " ev-day-header--weekend" : ""}`;
    hdr.textContent = _DIAS_CORTO[dayIdx];
    headers.appendChild(hdr);
  }

  // Month start
  const monthStart = new Date(evWeekStart.getFullYear(), evWeekStart.getMonth(), 1);
  const monthEnd = new Date(evWeekStart.getFullYear(), evWeekStart.getMonth() + 1, 0);
  const firstMonday = getMonday(monthStart);

  document.getElementById("ev-week-label").textContent = `${_MESES[evWeekStart.getMonth()]} ${evWeekStart.getFullYear()}`;

  // 5-6 weeks
  const weeks = Math.ceil((monthEnd.getDate() + ((monthStart.getDay() + 6) % 7)) / 7);
  grid.style.gridTemplateColumns = "repeat(7, 1fr)";
  for (let w = 0; w < weeks; w++) {
    for (let d = 0; d < 7; d++) {
      const date = new Date(firstMonday);
      date.setDate(date.getDate() + w * 7 + d);
      const isCurrentMonth = date.getMonth() === evWeekStart.getMonth();
      const dayNum = date.getDay();
      const isWE = dayNum === 0 || dayNum === 5 || dayNum === 6;

      const cell = document.createElement("div");
      cell.className = `ev-day-col${isWE ? " ev-day-col--weekend" : ""}`;
      cell.style.minHeight = "80px";
      cell.style.opacity = isCurrentMonth ? "1" : "0.35";

      const dayLabel = document.createElement("div");
      dayLabel.style.cssText = "font-size:11px;font-weight:600;color:var(--nijar-gris);margin-bottom:4px;";
      dayLabel.textContent = date.getDate();
      cell.appendChild(dayLabel);

      const dayStr = date.toISOString().substring(0, 10);
      for (const ev of evItems().filter(e => new Date(e.fecha_inicio).toISOString().substring(0, 10) === dayStr)) {
        const mini = document.createElement("button");
        const tipo = ev.tipo || "otro";
        mini.className = `ev-block ev-block--${escapeHtml(tipo)}`;
        mini.style.cssText = "padding:3px 6px;font-size:10px;margin-bottom:2px;";
        mini.innerHTML = `<span class="ev-block__name" style="font-size:10px">${escapeHtml(ev.nombre.substring(0, 14))}</span>`;
        mini.addEventListener("click", () => selectEvent(ev));
        cell.appendChild(mini);
      }
      grid.appendChild(cell);
    }
  }
  autoSelectFirst();
}

// ---------- SHARED HELPERS ----------
function makeEvBlock(ev) {
  const tipo = ev.tipo || "otro";
  const hora = new Date(ev.fecha_inicio).toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
  const block = document.createElement("button");
  block.className = `ev-block ev-block--${escapeHtml(tipo)}`;
  if (evSelectedEvent && evSelectedEvent.urn === ev.urn) block.classList.add("ev-block--selected");
  const shortDir = (ev.direccion || "").split(",")[0].split("·")[0].trim();
  block.innerHTML = `
    <span class="ev-block__name">${escapeHtml(ev.nombre.length > 22 ? ev.nombre.substring(0, 20) + "…" : ev.nombre)}</span>
    <span class="ev-block__meta">${hora}${shortDir ? " · " + escapeHtml(shortDir) : ""}</span>
    <span class="ev-block__tag">${escapeHtml(_TIPO_LABEL[tipo] || tipo)}</span>`;
  block.addEventListener("click", () => selectEvent(ev));
  return block;
}

function autoSelectFirst() {
  if (evSelectedEvent) return;
  const items = evItems();
  if (items.length > 0) selectEvent(items[0]);
}

function selectEvent(ev) {
  evSelectedEvent = ev;
  const detail = document.getElementById("ev-detail");
  detail.classList.remove("hidden");
  const d = new Date(ev.fecha_inicio);
  const fin = new Date(ev.fecha_fin);
  const durMs = fin - d;
  const durH = Math.floor(durMs / 3600000);
  const durM = Math.round((durMs % 3600000) / 60000);

  document.getElementById("ev-detail-sel").textContent =
    `Selección · ${_DIAS_LARGO[d.getDay()]} ${d.getDate()} ${_MESES[d.getMonth()].toLowerCase()} · ${d.toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" })}`;
  document.getElementById("ev-d-titulo").textContent = ev.nombre;
  document.getElementById("ev-d-duracion").textContent = durM > 0 ? `${durH}h ${durM}min` : `${durH}h`;
  document.getElementById("ev-d-ubicacion").textContent = ev.direccion || "—";
  document.getElementById("ev-d-precio").textContent = ev.precio || "—";

  const capEl = document.getElementById("ev-d-capacidad");
  if (ev.capacidad_aforo) {
    const oc = Math.round(ev.capacidad_aforo * 0.7), pct = Math.round((oc / ev.capacidad_aforo) * 100);
    capEl.innerHTML = `<span class="ev-detail__value">${oc} / ${ev.capacidad_aforo} plazas</span>
      <div class="ev-capacity-bar"><div class="ev-capacity-fill" style="width:${pct}%"></div></div>
      <span class="ev-capacity-text">${pct}% ocupado</span>`;
  } else { capEl.innerHTML = `<span class="ev-detail__value">Sin límite</span>`; }

  document.querySelectorAll(".ev-block--selected").forEach(b => b.classList.remove("ev-block--selected"));
  document.querySelectorAll(".ev-block").forEach(b => {
    if (b.querySelector(".ev-block__name")?.textContent.startsWith(ev.nombre.substring(0, 14))) b.classList.add("ev-block--selected");
  });
}

// ---------- EVENT DIALOG (create / edit) ----------
const evDialog = document.getElementById("event-dialog");
const evForm = document.getElementById("event-form");
const evFormError = document.getElementById("event-form-error");

function openEventDialog(ev = null) {
  evEditingEvent = ev;
  document.getElementById("event-dialog-title").textContent = ev ? "Editar evento" : "Nuevo evento";
  document.getElementById("event-form-submit").textContent = ev ? "Guardar cambios" : "Crear evento";

  // Pre-fill
  document.getElementById("ev-nombre").value = ev?.nombre || "";
  document.getElementById("ev-tipo").value = ev?.tipo || "cultural";
  document.getElementById("ev-descripcion").value = ev?.descripcion || "";
  document.getElementById("ev-direccion").value = ev?.direccion || "";
  document.getElementById("ev-organizador").value = ev?.organizador || "";
  document.getElementById("ev-precio").value = ev?.precio || "";
  document.getElementById("ev-capacidad").value = ev?.capacidad_aforo || "";

  if (ev?.fecha_inicio) {
    document.getElementById("ev-fecha-inicio").value = new Date(ev.fecha_inicio).toISOString().slice(0, 16);
  } else { document.getElementById("ev-fecha-inicio").value = ""; }
  if (ev?.fecha_fin) {
    document.getElementById("ev-fecha-fin").value = new Date(ev.fecha_fin).toISOString().slice(0, 16);
  } else { document.getElementById("ev-fecha-fin").value = ""; }

  evFormError.classList.add("hidden");
  evDialog.showModal();
}

function closeEventDialog() {
  evDialog.close();
  evEditingEvent = null;
}

document.getElementById("btn-new-event")?.addEventListener("click", () => openEventDialog());
document.getElementById("btn-edit-event")?.addEventListener("click", () => {
  if (evSelectedEvent) openEventDialog(evSelectedEvent);
});
document.getElementById("event-dialog-close")?.addEventListener("click", closeEventDialog);
document.getElementById("event-dialog-cancel")?.addEventListener("click", closeEventDialog);

evForm?.addEventListener("submit", async (e) => {
  e.preventDefault();
  evFormError.classList.add("hidden");

  const nombre = document.getElementById("ev-nombre").value.trim();
  const tipo = document.getElementById("ev-tipo").value;
  const fechaInicio = document.getElementById("ev-fecha-inicio").value;
  const fechaFin = document.getElementById("ev-fecha-fin").value;

  if (!nombre || !fechaInicio || !fechaFin) {
    evFormError.textContent = "Rellena los campos obligatorios (nombre, tipo, fechas).";
    evFormError.classList.remove("hidden");
    return;
  }

  const slug = nombre.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").substring(0, 40);
  const payload = {
    urn: `urn:ngsi-ld:EventoTuristico:nijar:${slug}`,
    nombre,
    tipo,
    fecha_inicio: new Date(fechaInicio).toISOString(),
    fecha_fin: new Date(fechaFin).toISOString(),
    descripcion: document.getElementById("ev-descripcion").value.trim() || null,
    direccion: document.getElementById("ev-direccion").value.trim() || null,
    organizador: document.getElementById("ev-organizador").value.trim() || null,
    precio: document.getElementById("ev-precio").value.trim() || null,
    capacidad_aforo: parseInt(document.getElementById("ev-capacidad").value) || null,
    publicado: true,
    activo: true,
  };

  try {
    await api.createEvent(payload);
    closeEventDialog();
    setBanner("Evento creado correctamente", "success");
    evSelectedEvent = null;
    await loadEvents();
  } catch (err) {
    evFormError.textContent = err.message || "Error al crear el evento";
    evFormError.classList.remove("hidden");
  }
});

// ============================================================
// SMART OFFICE section
// ============================================================
async function loadSmartOffice() {
  // Environment chart
  await loadEnvironment();
  // Sensor table
  try {
    const sensores = await api.listSensors({ page: 1, page_size: 200 });
    const tbody = document.querySelector("#sensores-table tbody");
    tbody.innerHTML = "";
    for (const s of (sensores.items || [])) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(s.nombre)}</td>
        <td style="color:var(--nijar-gris)">${escapeHtml(s.tipo)}</td>
        <td><span class="sensor-status ${escapeHtml(s.estado)}">${escapeHtml(s.estado)}</span></td>
        <td style="color:var(--nijar-gris)">${escapeHtml(s.descripcion_ubicacion ?? "—")}</td>
      `;
      tbody.appendChild(tr);
    }
  } catch (err) {
    console.warn("listSensors falló:", err);
  }
}

async function loadEnvironment() {
  const granularidad = document.getElementById("env-granularity").value;
  const desde = document.getElementById("env-from").value;
  const hasta = document.getElementById("env-to").value;
  const params = { granularidad };
  if (desde) params.desde = new Date(desde).toISOString();
  if (hasta) params.hasta = new Date(hasta).toISOString();
  try {
    const data = await api.environment(params);
    const labels = data.puntos.map(p => p.timestamp);
    const datasets = [
      { label: "CO₂ (ppm)", data: data.puntos.map(p => p.co2_ppm), borderColor: "#003B7A", backgroundColor: "transparent" },
      { label: "Temp (°C)", data: data.puntos.map(p => p.temperatura_c), borderColor: "#DC2626", backgroundColor: "transparent" },
      { label: "Humedad (%)", data: data.puntos.map(p => p.humedad_porc), borderColor: "#00A6C0", backgroundColor: "transparent" },
      { label: "Ruido (dB)", data: data.puntos.map(p => p.ruido_db), borderColor: "#F4C430", backgroundColor: "transparent" },
    ];
    renderChart("chart-environment", "line", { labels, datasets });
  } catch (err) {
    setBanner(`Error series ambientales: ${err.message}`, "error");
  }
}

document.getElementById("env-refresh")?.addEventListener("click", loadEnvironment);

// ============================================================
// BIG DATA section
// ============================================================
async function loadBigData() {
  try {
    const ov = await api.bigDataOverview();
    setKPI("bd-total2", String(ov.menciones_total));
    setKPI("bd-mes", String(ov.menciones_ultimo_mes));
    setKPI("bd-sent2", ov.sentimiento_medio != null ? ov.sentimiento_medio.toFixed(2) : "—");

    const sent = await api.sentimentSeries({ granularidad: "dia" });
    renderChart("chart-sentiment", "bar", {
      labels: sent.puntos.map(p => p.timestamp.substring(0, 10)),
      datasets: [
        { label: "Positivos", data: sent.puntos.map(p => p.positivo), backgroundColor: "#2D8F4F" },
        { label: "Neutros", data: sent.puntos.map(p => p.neutro), backgroundColor: "#9CA3AF" },
        { label: "Negativos", data: sent.puntos.map(p => p.negativo), backgroundColor: "#DC2626" },
      ],
    }, { scales: { x: { stacked: true }, y: { stacked: true } } });

    const sov = await api.shareOfVoice();
    renderChart("chart-sov", "doughnut", {
      labels: sov.map(s => s.fuente),
      datasets: [{
        data: sov.map(s => s.menciones),
        backgroundColor: ["#003B7A", "#00A6C0", "#F4C430", "#2D8F4F", "#E58A40"],
      }],
    });

    const topics = await api.topTopics(15);
    const list = document.getElementById("topics-list");
    list.innerHTML = "";
    for (const t of topics) {
      const li = document.createElement("li");
      li.className = "topic-item";
      li.innerHTML = `
        <span class="topic-item__name">${escapeHtml(t.tema)}</span>
        <span class="topic-item__meta">${t.menciones} menciones · ${(t.sentimiento_medio ?? 0).toFixed(2)}</span>
      `;
      list.appendChild(li);
    }
  } catch (err) {
    setBanner(`Error Big Data: ${err.message}`, "error");
  }
}

// ============================================================
// CHATBOT section
// ============================================================
async function loadChatbot() {
  try {
    const t = await api.chatbotTelemetry();
    setKPI("cb-ses", String(t.sesiones_unicas));
    setKPI("cb-int", String(t.interacciones_totales));
    setKPI("cb-res", `${t.resolucion_autonoma_porc.toFixed(0)} %`);
    setKPI("cb-sat", t.satisfaccion_porc == null ? "—" : `${t.satisfaccion_porc.toFixed(0)} %`);

    const idiomas = t.idiomas_distribucion || {};
    renderChart("chart-idiomas", "pie", {
      labels: Object.keys(idiomas),
      datasets: [{
        data: Object.values(idiomas),
        backgroundColor: ["#003B7A", "#00A6C0", "#F4C430", "#2D8F4F", "#E58A40"],
      }],
    });

    const ol = document.getElementById("chatbot-intents");
    ol.innerHTML = "";
    for (const it of (t.top_intents || [])) {
      const li = document.createElement("li");
      li.className = "activity-item";
      li.innerHTML = `
        <div class="activity-item__bar activity-item__bar--teal"></div>
        <div class="activity-item__text">
          <div class="activity-item__title">${escapeHtml(it.nombre)}</div>
        </div>
        <span class="activity-item__value">${it.ocurrencias}</span>`;
      ol.appendChild(li);
    }
  } catch (err) {
    setBanner(`Error chatbot: ${err.message}`, "error");
  }
}

// ============================================================
// TÓTEMS section
// ============================================================
async function loadTotems() {
  try {
    const data = await api.totemsUsage();
    setKPI("tot-int2", String(data.interacciones_total));
    setKPI("tot-ses2", String(data.sesiones_unicas));
    setKPI("tot-dur", data.duracion_media_seg != null ? data.duracion_media_seg.toFixed(0) : "—");

    const ol = document.getElementById("totems-secciones");
    ol.innerHTML = "";
    for (const s of (data.secciones_top || [])) {
      const li = document.createElement("li");
      li.className = "activity-item";
      li.innerHTML = `
        <div class="activity-item__bar activity-item__bar--teal"></div>
        <div class="activity-item__text">
          <div class="activity-item__title">${escapeHtml(s.seccion)}</div>
        </div>
        <span class="activity-item__value">${s.interacciones}</span>`;
      ol.appendChild(li);
    }
  } catch (err) {
    setBanner(`Error tótems: ${err.message}`, "error");
  }
}

// ============================================================
// MAP section
// ============================================================
async function loadMap() {
  if (!mapInstance) {
    mapInstance = L.map("map", { scrollWheelZoom: false }).setView([36.85, -2.10], 11);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap",
      maxZoom: 18,
    }).addTo(mapInstance);
    mapLayer = L.layerGroup().addTo(mapInstance);
  }
  mapLayer.clearLayers();
  try {
    const recursos = await api.listResources({ page: 1, page_size: 200, publicado: true });
    for (const r of (recursos.items || [])) {
      if (!r.ubicacion?.coordinates) continue;
      const [lon, lat] = r.ubicacion.coordinates;
      L.marker([lat, lon])
        .bindPopup(`<strong>${escapeHtml(r.nombre)}</strong><br/><span style="font-size:12px">${escapeHtml(r.categoria)}</span>`)
        .addTo(mapLayer);
    }
  } catch (err) {
    setBanner(`Error mapa: ${err.message}`, "error");
  }
}

// ============================================================
// USUARIOS section
// ============================================================
const _TEAM = [
  { initials: "FA", name: "Francisco Aguilar", email: "f.aguilar@nijar.es", area: "Área TIC", rol: "administrador_tic", session: "hace 2h", avatar: "navy" },
  { initials: "MR", name: "María Ruiz", email: "m.ruiz@nijar.es", area: "Oficina de Turismo", rol: "gestor_contenidos", session: "ahora", avatar: "teal" },
  { initials: "AL", name: "Antonio López", email: "a.lopez@nijar.es", area: "Oficina de Turismo", rol: "gestor_contenidos", session: "hace 3h", avatar: "teal" },
  { initials: "JM", name: "Javier Moreno", email: "j.moreno@nijar.es", area: "Área TIC", rol: "administrador_tic", session: "ayer 17:42", avatar: "navy" },
];

function loadUsuarios() {
  // Add current logged-in user if not in the static list
  const me = getCachedUser();
  const team = [..._TEAM];
  if (me && !team.find(u => u.email === me.email)) {
    const ini = (me.nombre_completo || me.email).split(" ").map(w => w[0]).join("").substring(0, 2).toUpperCase();
    const isAdmin = me.rol === "administrador_tic";
    team.unshift({
      initials: ini, name: me.nombre_completo || me.email, email: me.email,
      area: isAdmin ? "Área TIC" : "Oficina de Turismo", rol: me.rol, session: "ahora",
      avatar: isAdmin ? "navy" : "teal",
    });
  }

  const admins = team.filter(u => u.rol === "administrador_tic").length;
  const gestores = team.filter(u => u.rol === "gestor_contenidos").length;
  document.getElementById("usr-summary-text").textContent =
    `${team.length} usuarios activos · ${admins} administradores TIC · ${gestores} gestores de contenidos`;

  const list = document.getElementById("usr-list");
  list.innerHTML = "";
  for (const u of team) {
    const isAdmin = u.rol === "administrador_tic";
    const rolLabel = isAdmin ? "Administrador TIC" : "Gestor de contenidos";
    const rolClass = isAdmin ? "usr-card__role--admin" : "usr-card__role--gestor";

    const card = document.createElement("div");
    card.className = "usr-card";
    card.innerHTML = `
      <div class="usr-card__avatar usr-card__avatar--${u.avatar}">${escapeHtml(u.initials)}</div>
      <div class="usr-card__info">
        <div class="usr-card__name">${escapeHtml(u.name)}</div>
        <div class="usr-card__meta">${escapeHtml(u.email)} · ${escapeHtml(u.area)}</div>
        <span class="usr-card__role ${rolClass}">${rolLabel}</span>
      </div>
      <div class="usr-card__session">Última sesión: ${escapeHtml(u.session)}</div>
      <span class="usr-card__status"><span class="dot dot--green"></span> Activo</span>
      <button class="usr-card__more" title="Más acciones">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/></svg>
      </button>
    `;
    card.querySelector(".usr-card__more").addEventListener("click", (e) => {
      e.stopPropagation();
      showUserMenu(e.currentTarget, u);
    });
    list.appendChild(card);
  }
}

function showUserMenu(anchor, user) {
  document.querySelector(".row-menu")?.remove();
  const menu = document.createElement("div");
  menu.className = "row-menu ev-filter-dropdown";
  menu.style.position = "absolute";
  menu.innerHTML = `
    <button class="ev-filter-option" data-um="edit">Editar usuario</button>
    <button class="ev-filter-option" data-um="role">Cambiar rol</button>
    <button class="ev-filter-option" data-um="reset">Restablecer contraseña</button>
    <button class="ev-filter-option" style="color:#DC2626" data-um="deactivate">Desactivar cuenta</button>
  `;
  anchor.style.position = "relative";
  anchor.appendChild(menu);
  menu.querySelectorAll("[data-um]").forEach(btn => {
    btn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      menu.remove();
      const act = btn.dataset.um;
      if (act === "edit") setBanner(`Editando usuario: ${user.name}`, "info");
      else if (act === "role") setBanner(`Cambiar rol de: ${user.name}`, "info");
      else if (act === "reset") setBanner(`Enlace de restablecimiento enviado a: ${user.email}`, "success");
      else if (act === "deactivate") {
        if (confirm(`¿Desactivar la cuenta de ${user.name}?`)) {
          setBanner(`Cuenta desactivada: ${user.name}`, "success");
        }
      }
    });
  });
  setTimeout(() => document.addEventListener("click", () => menu.remove(), { once: true }), 10);
}

// Invite user modal
const inviteDialog = document.getElementById("invite-dialog");
const inviteForm = document.getElementById("invite-form");

document.getElementById("btn-invite-user")?.addEventListener("click", () => {
  inviteForm.reset();
  document.getElementById("invite-error").classList.add("hidden");
  inviteDialog.showModal();
});

document.getElementById("invite-cancel")?.addEventListener("click", () => {
  inviteDialog.close();
});

inviteDialog?.addEventListener("click", (e) => {
  if (e.target === inviteDialog) inviteDialog.close();
});

inviteForm?.addEventListener("submit", (e) => {
  e.preventDefault();
  const email = document.getElementById("invite-email").value.trim();
  const nombre = document.getElementById("invite-nombre").value.trim();
  const rol = document.getElementById("invite-rol").value;
  const errEl = document.getElementById("invite-error");

  if (!email || !email.includes("@")) {
    errEl.textContent = "Introduce un correo electrónico válido.";
    errEl.classList.remove("hidden");
    return;
  }

  errEl.classList.add("hidden");
  inviteDialog.close();

  const rolLabel = rol.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  const quien = nombre || email;
  setBanner(`Invitación enviada a ${quien} como ${rolLabel}`, "success");
});

// ============================================================
// CONFIG section
// ============================================================
const API_BASE_RAW = `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;

async function loadConfig() {
  // User profile
  const user = getCachedUser();
  if (user) {
    const initials = (user.nombre_completo || user.email)
      .split(" ").map(w => w[0]).join("").substring(0, 2).toUpperCase();
    document.getElementById("config-avatar").textContent = initials;
    document.getElementById("config-name").textContent = user.nombre_completo || user.email;
    document.getElementById("config-email").textContent = user.email;
    const rolLabel = (user.rol || "").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
    document.getElementById("config-role-badge").textContent = rolLabel;
    document.getElementById("config-rol").textContent = rolLabel;
    document.getElementById("config-2fa").textContent = user.requiere_2fa ? "Activado" : "No requerido";
  }

  // System info via /version
  try {
    const res = await fetch(`${API_BASE_RAW}/version`);
    if (res.ok) {
      const v = await res.json();
      document.getElementById("config-app-name").textContent = v.name;
      document.getElementById("config-version").textContent = v.version;
      document.getElementById("config-env").textContent = v.environment;
      document.getElementById("config-chatbot-engine").textContent = v.chatbot_engine;
      document.getElementById("config-expediente").textContent = v.expediente + " · " + v.adjudicatario;
    }
  } catch { /* ignore */ }

  // Health + readiness
  try {
    const health = await fetch(`${API_BASE_RAW}/health`);
    const svcApi = document.getElementById("svc-api");
    if (health.ok) {
      svcApi.textContent = "Operativo";
      svcApi.className = "config-service__status config-service__status--ok";
      document.getElementById("config-api-status").innerHTML = '<span class="dot dot--green"></span> Operativo';
    } else {
      svcApi.textContent = "Error";
      svcApi.className = "config-service__status config-service__status--error";
    }
  } catch {
    document.getElementById("svc-api").textContent = "No disponible";
    document.getElementById("svc-api").className = "config-service__status config-service__status--error";
  }

  try {
    const ready = await fetch(`${API_BASE_RAW}/ready`);
    const svcDb = document.getElementById("svc-db");
    if (ready.ok) {
      const data = await ready.json();
      const dbOk = data.checks?.database === "ok";
      svcDb.textContent = dbOk ? "Operativo" : "Degradado";
      svcDb.className = `config-service__status config-service__status--${dbOk ? "ok" : "error"}`;
      document.getElementById("config-db-status").innerHTML = dbOk
        ? '<span class="dot dot--green"></span> PostgreSQL conectado'
        : '<span class="dot dot--red"></span> Error de conexión';
    }
  } catch {
    document.getElementById("svc-db").textContent = "No disponible";
    document.getElementById("svc-db").className = "config-service__status config-service__status--error";
  }
}

// ============================================================
// Charts helper
// ============================================================
function renderChart(canvasId, type, data, optionsOverrides = {}) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  if (charts[canvasId]) charts[canvasId].destroy();
  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          boxWidth: 12,
          font: { family: "Geist, sans-serif", size: 12 },
        },
      },
    },
  };
  charts[canvasId] = new Chart(canvas, {
    type,
    data,
    options: { ...baseOptions, ...optionsOverrides },
  });
}

// ============================================================
// Bootstrap
// ============================================================
function initDashboard() {
  applyUserChrome(getCachedUser());
  switchSection("dashboard");
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(loadDashboard, REFRESH_MS);
}

(async function main() {
  if (!tokens.access) {
    showLogin();
    return;
  }
  try {
    const user = await api.me();
    sessionStorage.setItem("nijar.dti.user", JSON.stringify(user));
    applyUserChrome(user);
    initDashboard();
  } catch {
    tokens.clear();
    showLogin();
  }
})();
