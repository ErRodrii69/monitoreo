/**
 * dashboard.js — Lógica de la vista Dashboard
 *
 * Responsabilidades:
 *  - Renderizar la barra de estado global.
 *  - Renderizar las tarjetas de servidor.
 *  - Renderizar el feed de incidencias recientes.
 *
 * No hace fetch directamente: delega en window.API.
 */

// ---------------------------------------------------------------------------
// Punto de entrada: renderiza el dashboard con los datos actuales
// ---------------------------------------------------------------------------

/**
 * Actualiza toda la vista Dashboard.
 * Se llama al cargar la página y en cada ciclo de refresco automático.
 */
async function refreshDashboard() {
  try {
    const [servers, checks] = await Promise.all([
      API.getServers(),
      API.getRecentChecks(30),
    ]);

    renderGlobalStatus(servers);
    renderServerGrid(servers);
    renderIncidentsFeed(checks, servers);
  } catch (err) {
    showToast("Error al cargar el dashboard: " + err.message, "error");
  }
}

// ---------------------------------------------------------------------------
// Barra de estado global
// ---------------------------------------------------------------------------

/**
 * Actualiza el banner superior con el estado agregado de todos los servidores.
 *
 * @param {Array} servers - Lista de objetos servidor devueltos por la API.
 */
function renderGlobalStatus(servers) {
  const bar     = document.getElementById("global-status-bar");
  const icon    = document.getElementById("global-icon");
  const label   = document.getElementById("global-label");
  const sub     = document.getElementById("global-sub");
  const statUp  = document.getElementById("stat-up");
  const statDown= document.getElementById("stat-down");
  const statUnk = document.getElementById("stat-unknown");

  const active  = servers.filter(s => s.is_active);
  const up      = active.filter(s => s.last_status === "up").length;
  const down    = active.filter(s => s.last_status === "down").length;
  const unknown = active.filter(s => s.last_status === "unknown").length;

  statUp.textContent   = up;
  statDown.textContent = down;
  statUnk.textContent  = unknown;

  // Limpiamos clases de estado previas
  bar.classList.remove("all-ok", "has-errors");

  if (active.length === 0) {
    icon.textContent  = "◈";
    label.textContent = "Sin servidores activos";
    sub.textContent   = "Añade un servidor para empezar a monitorizar";
  } else if (down > 0) {
    bar.classList.add("has-errors");
    icon.textContent  = "⚠";
    icon.style.color  = "var(--err)";
    label.textContent = `${down} servidor${down > 1 ? "es" : ""} caído${down > 1 ? "s" : ""}`;
    sub.textContent   = "Se ha enviado una notificación por correo";
  } else if (unknown > 0 && up === 0) {
    icon.textContent  = "◌";
    icon.style.color  = "var(--warn)";
    label.textContent = "Estado desconocido";
    sub.textContent   = "Los servidores aún no han sido comprobados";
  } else {
    bar.classList.add("all-ok");
    icon.textContent  = "✓";
    icon.style.color  = "var(--ok)";
    label.textContent = "Todos los sistemas operativos";
    sub.textContent   = `${up} servidor${up !== 1 ? "es" : ""} respondiendo correctamente`;
  }
}

// ---------------------------------------------------------------------------
// Grid de tarjetas
// ---------------------------------------------------------------------------

/**
 * Renderiza una tarjeta por cada servidor en el grid principal.
 *
 * @param {Array} servers - Lista de servidores.
 */
function renderServerGrid(servers) {
  const grid = document.getElementById("dashboard-grid");

  if (servers.length === 0) {
    grid.innerHTML = '<div class="loading-placeholder">No hay servidores. Añade uno desde la pestaña "Servidores".</div>';
    return;
  }

  // Ordenamos: primero los caídos, luego desconocidos, luego operativos
  const sorted = [...servers].sort((a, b) => {
    const order = { down: 0, unknown: 1, up: 2 };
    return (order[a.last_status] ?? 1) - (order[b.last_status] ?? 1);
  });

  grid.innerHTML = sorted.map(buildServerCard).join("");
}

/**
 * Construye el HTML de una tarjeta de servidor.
 *
 * @param {object} s - Objeto servidor.
 * @returns {string} HTML de la tarjeta.
 */
function buildServerCard(s) {
  const statusClass = s.last_status;  // "up" | "down" | "unknown"
  const statusLabel = { up: "Operativo", down: "Caído", unknown: "Desconocido" }[statusClass] || statusClass;
  const latency     = s.last_response_ms != null ? `${s.last_response_ms.toFixed(1)} ms` : "—";
  const lastCheck   = s.last_checked_at ? formatRelativeTime(s.last_checked_at) : "Nunca";
  const activeTag   = s.is_active ? "" : ' <span class="text-muted">(inactivo)</span>';

  return `
    <div class="server-card status-${statusClass}">
      <div class="card-name">${escapeHtml(s.name)}${activeTag}</div>
      <div class="card-ip">${escapeHtml(s.ip_address)}</div>
      <div class="card-status-row">
        <span class="status-badge ${statusClass}">
          <span class="status-dot"></span>
          ${statusLabel}
        </span>
        <span class="card-latency">ping <span>${latency}</span></span>
      </div>
      <div class="card-footer">Comprobado ${lastCheck}</div>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Feed de incidencias
// ---------------------------------------------------------------------------

/**
 * Renderiza el feed con los últimos registros de comprobación.
 * Solo muestra los que tienen estado "down" o los más recientes.
 *
 * @param {Array} checks  - Lista de CheckLog.
 * @param {Array} servers - Lista de servidores (para obtener el nombre).
 */
function renderIncidentsFeed(checks, servers) {
  const feed = document.getElementById("incidents-feed");

  // Creamos un mapa id → nombre para resolver sin búsqueda lineal
  const serverMap = Object.fromEntries(servers.map(s => [s.id, s.name]));

  // Filtramos solo los caídos para destacarlos; si no hay, mostramos los últimos
  const downs = checks.filter(c => c.status === "down");
  const items = downs.length > 0 ? downs : checks.slice(0, 10);

  if (items.length === 0) {
    feed.innerHTML = '<div class="loading-placeholder">Sin incidencias registradas ✓</div>';
    return;
  }

  feed.innerHTML = items.map(c => {
    const name = serverMap[c.server_id] || `Servidor #${c.server_id}`;
    const time = formatDateTime(c.checked_at);
    const err  = c.error_message ? `<span class="incident-error">${escapeHtml(c.error_message)}</span>` : "";

    return `
      <div class="incident-item ${c.status}">
        <span class="incident-time">${time}</span>
        <span class="incident-server">${escapeHtml(name)}</span>
        ${err}
      </div>
    `;
  }).join("");
}
