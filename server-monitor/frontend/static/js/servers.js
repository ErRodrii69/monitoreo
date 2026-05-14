/**
 * servers.js - Logica de la vista "Servidores" (CRUD)
 *
 * Responsabilidades:
 *  - Renderizar la tabla de servidores.
 *  - Gestionar el modal de creacion/edicion.
 *  - Lanzar pings manuales.
 *  - Eliminar servidores.
 */

let _editingServerId = null;

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
    tbody.innerHTML = '<tr><td colspan="7" class="loading-cell">No hay servidores. A&ntilde;ade uno con el bot&oacute;n "+".</td></tr>';
    return;
  }

  tbody.innerHTML = servers.map((server) => buildServerRow(server)).join("");
}

/**
 * Construye el HTML de una fila de la tabla de servidores.
 *
 * @param {object} server - Objeto servidor.
 * @returns {string} HTML de la fila.
 */
function buildServerRow(server) {
  const badge = `<span class="status-badge ${server.last_status}">${statusLabel(server.last_status)}</span>`;
  const latency = server.last_response_ms != null ? `${server.last_response_ms.toFixed(1)} ms` : "--";
  const lastCheck = server.last_checked_at ? formatDateTime(server.last_checked_at) : "--";
  const deleteName = escapeHtml(JSON.stringify(server.name));
  const active = server.is_active
    ? '<span class="text-ok">&#9679; S&iacute;</span>'
    : '<span class="text-muted">&#9675; No</span>';

  return `
    <tr data-id="${server.id}">
      <td>${escapeHtml(server.name)}</td>
      <td class="mono">${escapeHtml(server.ip_address)}</td>
      <td>${badge}</td>
      <td class="mono">${latency}</td>
      <td>${lastCheck}</td>
      <td>${active}</td>
      <td>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="btn btn-sm btn-ok" onclick="handleManualPing(${server.id})">Ping</button>
          <button class="btn btn-sm btn-ghost" onclick="openEditModal(${server.id})">Editar</button>
          <button class="btn btn-sm btn-danger" onclick='handleDeleteServer(${server.id}, ${deleteName})'>Borrar</button>
        </div>
      </td>
    </tr>
  `;
}

/**
 * Devuelve la etiqueta legible de un estado.
 *
 * @param {string} status - Estado interno.
 * @returns {string} Estado legible.
 */
function statusLabel(status) {
  return { up: "Operativo", down: "Ca&iacute;do", unknown: "Desconocido" }[status] || status;
}

// ---------------------------------------------------------------------------
// Modal de creacion / edicion
// ---------------------------------------------------------------------------

function openCreateModal() {
  _editingServerId = null;
  document.getElementById("modal-title").textContent = "Anadir servidor";
  document.getElementById("modal-name").value = "";
  document.getElementById("modal-ip").value = "";
  document.getElementById("modal-desc").value = "";
  document.getElementById("modal-active").checked = true;
  openModal();
}

/**
 * Abre el modal en modo edicion cargando los datos del servidor.
 *
 * @param {number} id - ID del servidor a editar.
 */
async function openEditModal(id) {
  try {
    const servers = await API.getServers();
    const server = servers.find((item) => item.id === id);
    if (!server) throw new Error("Servidor no encontrado");

    _editingServerId = id;
    document.getElementById("modal-title").textContent = "Editar servidor";
    document.getElementById("modal-name").value = server.name;
    document.getElementById("modal-ip").value = server.ip_address;
    document.getElementById("modal-desc").value = server.description || "";
    document.getElementById("modal-active").checked = server.is_active;
    openModal();
  } catch (err) {
    showToast("Error al cargar el servidor: " + err.message, "error");
  }
}

function openModal() {
  document.getElementById("modal-overlay").classList.add("open");
  document.getElementById("modal-name").focus();
}

function closeModal() {
  document.getElementById("modal-overlay").classList.remove("open");
  _editingServerId = null;
}

/**
 * Guarda el servidor creado o editado.
 */
async function handleSaveServer() {
  const name = document.getElementById("modal-name").value.trim();
  const ip = document.getElementById("modal-ip").value.trim();
  const desc = document.getElementById("modal-desc").value.trim();
  const active = document.getElementById("modal-active").checked;

  if (!name || !ip) {
    showToast("Nombre e IP son obligatorios.", "error");
    return;
  }

  const payload = {
    name,
    ip_address: ip,
    description: desc || null,
    is_active: active,
  };

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
 * Lanza un ping manual al servidor y refresca la interfaz.
 *
 * @param {number} id - ID del servidor.
 */
async function handleManualPing(id) {
  showToast("Lanzando ping...", "success");

  try {
    const result = await API.pingServer(id);
    await Promise.all([
      refreshServersTable(),
      refreshDashboard(),
      refreshLogsTable(),
    ]);

    if (result.success) {
      const latency = result.response_ms != null
        ? `${result.response_ms.toFixed(1)} ms`
        : "sin latencia medida";
      showToast(`${result.server_name} actualizado: ${latency}`, "success");
      return;
    }

    showToast(`${result.server_name} sin respuesta: ${result.error}`, "error");
  } catch (err) {
    showToast("Error en ping: " + err.message, "error");
  }
}

/**
 * Pide confirmacion y elimina un servidor.
 *
 * @param {number} id - ID del servidor.
 * @param {string} name - Nombre del servidor.
 */
async function handleDeleteServer(id, name) {
  if (!confirm(`Eliminar el servidor "${name}"?\nSe borraran tambien todos sus registros de comprobacion.`)) {
    return;
  }

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
// ---------------------------------------------------------------------------

document.getElementById("btn-modal-save").addEventListener("click", handleSaveServer);
document.getElementById("btn-modal-cancel").addEventListener("click", closeModal);
document.getElementById("modal-close").addEventListener("click", closeModal);
document.getElementById("btn-add-server").addEventListener("click", openCreateModal);

document.getElementById("modal-overlay").addEventListener("click", (event) => {
  if (event.target === document.getElementById("modal-overlay")) closeModal();
});
