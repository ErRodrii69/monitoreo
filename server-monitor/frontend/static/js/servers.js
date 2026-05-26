let editingServerId = null;

async function refreshServersTable() {
  const tbody = document.getElementById("servers-tbody");
  try {
    const servers = await API.getServers();
    renderServersTable(servers);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="loading-cell text-err">${escapeHtml(err.message)}</td></tr>`;
  }
}

function renderServersTable(servers) {
  const tbody = document.getElementById("servers-tbody");

  if (servers.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="loading-cell">No hay servidores registrados.</td></tr>';
    return;
  }

  tbody.innerHTML = servers.map(buildServerRow).join("");
}

function buildServerRow(server) {
  const latency = server.last_response_ms != null ? `${server.last_response_ms.toFixed(1)} ms` : "--";
  const checked = server.last_checked_at ? formatDateTime(server.last_checked_at) : "--";
  const services = buildServiceChips(server);
  const safeName = escapeHtml(JSON.stringify(server.name));

  return `
    <tr>
      <td><strong>${escapeHtml(server.name)}</strong></td>
      <td class="mono">${escapeHtml(server.ip_address)}</td>
      <td><div class="service-list">${services || '<span class="service-chip">Sin checks</span>'}</div></td>
      <td>${statusBadge(server.last_status || "unknown")}</td>
      <td class="mono">${latency}</td>
      <td>${checked}</td>
      <td>${server.is_active ? '<span class="text-ok">Si</span>' : '<span class="text-muted">No</span>'}</td>
      <td>
        <div class="row-actions">
          <button class="btn btn-sm btn-ghost" onclick="handleManualCheck(${server.id})">Check</button>
          <button class="btn btn-sm btn-ghost" onclick="openEditModal(${server.id})">Editar</button>
          <button class="btn btn-sm btn-danger" onclick='handleDeleteServer(${server.id}, ${safeName})'>Borrar</button>
        </div>
      </td>
    </tr>
  `;
}

function openCreateModal() {
  editingServerId = null;
  setText("modal-title", "Anadir servidor");
  setModalForm({
    name: "",
    ip_address: "",
    description: "",
    is_active: true,
    check_ping: true,
    check_ssh: true,
    ssh_port: 22,
    check_http: false,
    http_url: "",
    check_https: false,
    https_url: "",
    custom_ports: "",
  });
  openModal();
}

async function openEditModal(id) {
  try {
    const servers = await API.getServers();
    const server = servers.find((item) => item.id === id);
    if (!server) throw new Error("Servidor no encontrado");

    editingServerId = id;
    setText("modal-title", "Editar servidor");
    setModalForm(server);
    openModal();
  } catch (err) {
    showToast(`Error al cargar servidor: ${err.message}`, "error");
  }
}

function setModalForm(server) {
  document.getElementById("modal-name").value = server.name || "";
  document.getElementById("modal-ip").value = server.ip_address || "";
  document.getElementById("modal-desc").value = server.description || "";
  document.getElementById("modal-active").checked = Boolean(server.is_active);
  document.getElementById("modal-check-ping").checked = Boolean(server.check_ping);
  document.getElementById("modal-check-ssh").checked = Boolean(server.check_ssh);
  document.getElementById("modal-ssh-port").value = server.ssh_port || 22;
  document.getElementById("modal-check-http").checked = Boolean(server.check_http);
  document.getElementById("modal-http-url").value = server.http_url || "";
  document.getElementById("modal-check-https").checked = Boolean(server.check_https);
  document.getElementById("modal-https-url").value = server.https_url || "";
  document.getElementById("modal-custom-ports").value = server.custom_ports || "";
}

function readModalPayload() {
  const payload = {
    name: document.getElementById("modal-name").value.trim(),
    ip_address: document.getElementById("modal-ip").value.trim(),
    description: document.getElementById("modal-desc").value.trim(),
    is_active: document.getElementById("modal-active").checked,
    check_ping: document.getElementById("modal-check-ping").checked,
    check_ssh: document.getElementById("modal-check-ssh").checked,
    ssh_port: parseInt(document.getElementById("modal-ssh-port").value, 10) || 22,
    check_http: document.getElementById("modal-check-http").checked,
    http_url: document.getElementById("modal-http-url").value.trim(),
    check_https: document.getElementById("modal-check-https").checked,
    https_url: document.getElementById("modal-https-url").value.trim(),
    custom_ports: document.getElementById("modal-custom-ports").value.trim(),
  };

  if (!payload.name || !payload.ip_address) {
    throw new Error("Nombre y host son obligatorios.");
  }

  if (payload.is_active && !payload.check_ping && !payload.check_ssh && !payload.check_http && !payload.check_https && !payload.custom_ports) {
    throw new Error("Activa al menos una comprobacion.");
  }

  return payload;
}

function openModal() {
  const overlay = document.getElementById("modal-overlay");
  overlay.classList.add("open");
  overlay.setAttribute("aria-hidden", "false");
  document.getElementById("modal-name").focus();
}

function closeModal() {
  const overlay = document.getElementById("modal-overlay");
  overlay.classList.remove("open");
  overlay.setAttribute("aria-hidden", "true");
  editingServerId = null;
}

async function handleSaveServer() {
  let payload;
  try {
    payload = readModalPayload();
  } catch (err) {
    showToast(err.message, "error");
    return;
  }

  try {
    if (editingServerId === null) {
      await API.createServer(payload);
      showToast("Servidor creado.", "success");
    } else {
      await API.updateServer(editingServerId, payload);
      showToast("Servidor actualizado.", "success");
    }

    closeModal();
    await Promise.all([refreshServersTable(), refreshDashboard()]);
  } catch (err) {
    showToast(`Error al guardar: ${err.message}`, "error");
  }
}

async function handleManualCheck(id) {
  showToast("Comprobando servidor...", "success", 1800);
  try {
    const result = await API.checkServer(id);
    await Promise.all([refreshServersTable(), refreshDashboard(), refreshLogsTable()]);
    if (result.success) {
      const latency = result.response_ms != null ? `${result.response_ms.toFixed(1)} ms` : "sin latencia";
      showToast(`${result.server_name}: ${latency}`, "success");
    } else {
      showToast(`${result.server_name}: ${result.error || "fallo detectado"}`, "error");
    }
  } catch (err) {
    showToast(`Error en check: ${err.message}`, "error");
  }
}

async function handleDeleteServer(id, name) {
  if (!confirm(`Eliminar "${name}" y sus registros?`)) return;

  try {
    await API.deleteServer(id);
    showToast("Servidor eliminado.", "success");
    await Promise.all([refreshServersTable(), refreshDashboard()]);
  } catch (err) {
    showToast(`Error al eliminar: ${err.message}`, "error");
  }
}

document.getElementById("btn-add-server").addEventListener("click", openCreateModal);
document.getElementById("btn-modal-save").addEventListener("click", handleSaveServer);
document.getElementById("btn-modal-cancel").addEventListener("click", closeModal);
document.getElementById("modal-close").addEventListener("click", closeModal);
document.getElementById("modal-overlay").addEventListener("click", (event) => {
  if (event.target.id === "modal-overlay") closeModal();
});
