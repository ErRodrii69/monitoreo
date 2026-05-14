/**
 * servers.js — Lógica de la vista "Servidores" (CRUD)
 *
 * Responsabilidades:
 *  - Renderizar la tabla de servidores.
 *  - Gestionar el modal de creación/edición.
 *  - Lanzar pings manuales.
 *  - Eliminar servidores.
 */

// Estado local de la vista de servidores
let _editingServerId = null;   // null → creación, número → edición

// ---------------------------------------------------------------------------
// Renderizado de la tabla
// ---------------------------------------------------------------------------

/**
 * Carga la lista de servidores desde la API y actualiza la tabla.
 */
async function refreshServersTable() {
  const tbody = document.getElementById("servers-tbody");
  try {
    const servers = await API.getServers();
    renderServersTable(servers);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="loading-cell text-err">Error: ${escapeHtml(err.message)}</td></tr>`;
  }
}

/**
 * Renderiza las filas de la tabla con los servidores recibidos.
 *
 * @param {Array} servers - Lista de objetos servidor.
 */
function renderServersTable(servers) {
  const tbody = document.getElementById("servers-tbody");

  if (servers.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="loading-cell">No hay servidores. Añade uno con el botón "+".</td></tr>';
    return;
  }

  tbody.innerHTML = servers.map(s => buildServerRow(s)).join("");
}

/**
 * Construye el HTML de una fila de la tabla de servidores.
 *
 * @param {object} s - Objeto servidor.
 * @returns {string} HTML de la fila <tr>.
 */
function buildServerRow(s) {
  const badge    = `<span class="status-badge ${s.last_status}">${statusLabel(s.last_status)}</span>`;
  const latency  = s.last_response_ms != null ? `${s.last_response_ms.toFixed(1)} ms` : "—";
  const lastChk  = s.last_checked_at ? formatDateTime(s.last_checked_at) : "—";
  const active   = s.is_active
    ? '<span class="text-ok">●  Sí</span>'
    : '<span class="text-muted">○  No</span>';

  return `
    <tr data-id="${s.id}">
      <td>${escapeHtml(s.name)}</td>
      <td class="mono">${escapeHtml(s.ip_address)}</td>
      <td>${badge}</td>
      <td class="mono">${latency}</td>
      <td>${lastChk}</td>
      <td>${active}</td>
      <td>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="btn btn-sm btn-ok"    onclick="handleManualPing(${s.id})">Ping</button>
          <button class="btn btn-sm btn-ghost"  onclick="openEditModal(${s.id})">Editar</button>
          <button class="btn btn-sm btn-danger" onclick="handleDeleteServer(${s.id}, '${escapeHtml(s.name)}')">Borrar</button>
        </div>
      </td>
    </tr>
  `;
}

/** Devuelve la etiqueta legible de un estado. */
function statusLabel(status) {
  return { up: "Operativo", down: "Caído", unknown: "Desconocido" }[status] || status;
}

// ---------------------------------------------------------------------------
// Modal de creación / edición
// ---------------------------------------------------------------------------

/** Abre el modal en modo creación (sin datos previos). */
function openCreateModal() {
  _editingServerId = null;
  document.getElementById("modal-title").textContent = "Añadir Servidor";
  document.getElementById("modal-name").value   = "";
  document.getElementById("modal-ip").value     = "";
  document.getElementById("modal-desc").value   = "";
  document.getElementById("modal-active").checked = true;
  openModal();
}

/**
 * Abre el modal en modo edición cargando los datos del servidor.
 *
 * @param {number} id - ID del servidor a editar.
 */
async function openEditModal(id) {
  try {
    const servers = await API.getServers();
    const s = servers.find(srv => srv.id === id);
    if (!s) throw new Error("Servidor no encontrado");

    _editingServerId = id;
    document.getElementById("modal-title").textContent = "Editar Servidor";
    document.getElementById("modal-name").value   = s.name;
    document.getElementById("modal-ip").value     = s.ip_address;
    document.getElementById("modal-desc").value   = s.description || "";
    document.getElementById("modal-active").checked = s.is_active;
    openModal();
  } catch (err) {
    showToast("Error al cargar el servidor: " + err.message, "error");
  }
}

/** Muestra el modal. */
function openModal() {
  document.getElementById("modal-overlay").classList.add("open");
  document.getElementById("modal-name").focus();
}

/** Cierra y resetea el modal. */
function closeModal() {
  document.getElementById("modal-overlay").classList.remove("open");
  _editingServerId = null;
}

/**
 * Guarda el servidor (crea o actualiza según _editingServerId).
 * Valida los campos obligatorios antes de enviar.
 */
async function handleSaveServer() {
  const name   = document.getElementById("modal-name").value.trim();
  const ip     = document.getElementById("modal-ip").value.trim();
  const desc   = document.getElementById("modal-desc").value.trim();
  const active = document.getElementById("modal-active").checked;

  if (!name || !ip) {
    showToast("Nombre e IP son obligatorios.", "error");
    return;
  }

  const payload = { name, ip_address: ip, description: desc || null, is_active: active };

  try {
    if (_editingServerId !== null) {
      await API.updateServer(_editingServerId, payload);
      showToast(`Servidor "${name}" actualizado.`, "success");
    } else {
      await API.createServer(payload);
      showToast(`Servidor "${name}" creado.`, "success");
    }
    closeModal();
    await refreshServersTable();
    await refreshDashboard();
  } catch (err) {
    showToast("Error al guardar: " + err.message, "error");
  }
}

// ---------------------------------------------------------------------------
// Acciones de fila
// ---------------------------------------------------------------------------

/**
 * Lanza un ping manual al servidor y muestra el resultado en un toast.
 *
 * @param {number} id - ID del servidor.
 */
async function handleManualPing(id) {
  showToast("Lanzando ping…", "success");
  try {
    const res = await API.pingServer(id);
    if (res.success) {
      showToast(`✓ ${res.ip_address} responde en ${res.response_ms?.toFixed(1)} ms`, "success");
    } else {
      showToast(`✗ ${res.ip_address} sin respuesta: ${res.error}`, "error");
    }
  } catch (err) {
    showToast("Error en ping: " + err.message, "error");
  }
}

/**
 * Pide confirmación y elimina un servidor.
 *
 * @param {number} id   - ID del servidor.
 * @param {string} name - Nombre del servidor (para el mensaje de confirmación).
 */
async function handleDeleteServer(id, name) {
  if (!confirm(`¿Eliminar el servidor "${name}"?\nSe borrarán también todos sus registros de comprobación.`)) return;

  try {
    await API.deleteServer(id);
    showToast(`Servidor "${name}" eliminado.`, "success");
    await refreshServersTable();
    await refreshDashboard();
  } catch (err) {
    showToast("Error al eliminar: " + err.message, "error");
  }
}

// ---------------------------------------------------------------------------
// Registro de eventos del modal
// Los eventos globales (botón Añadir, etc.) se registran en app.js
// ---------------------------------------------------------------------------
document.getElementById("btn-modal-save").addEventListener("click", handleSaveServer);
document.getElementById("btn-modal-cancel").addEventListener("click", closeModal);
document.getElementById("modal-close").addEventListener("click", closeModal);
document.getElementById("btn-add-server").addEventListener("click", openCreateModal);

// Cerrar modal al hacer clic fuera del cuadro
document.getElementById("modal-overlay").addEventListener("click", (e) => {
  if (e.target === document.getElementById("modal-overlay")) closeModal();
});
