async function refreshDashboard() {
  try {
    const [servers, incidents] = await Promise.all([
      API.getServers(),
      API.getIncidents("open", 20),
    ]);

    renderGlobalStatus(servers, incidents);
    renderServerGrid(servers);
    renderIncidentsFeed(incidents);
  } catch (err) {
    showToast(`Error al cargar dashboard: ${err.message}`, "error");
  }
}

function renderGlobalStatus(servers, incidents) {
  const active = servers.filter((server) => server.is_active);
  const up = active.filter((server) => server.last_status === "up").length;
  const down = active.filter((server) => server.last_status === "down").length;
  const unknown = active.filter((server) => server.last_status === "unknown").length;

  setText("stat-active", active.length);
  setText("stat-up", up);
  setText("stat-down", down);
  setText("stat-unknown", unknown);

  const bar = document.getElementById("global-status-bar");
  const label = document.getElementById("global-label");
  const sub = document.getElementById("global-sub");

  bar.classList.remove("ok", "error");

  if (active.length === 0) {
    label.textContent = "Sin servidores activos";
    sub.textContent = "0 comprobaciones programadas";
    return;
  }

  if (down > 0 || incidents.length > 0) {
    bar.classList.add("error");
    label.textContent = `${down} servidor${down === 1 ? "" : "es"} con fallo`;
    sub.textContent = `${incidents.length} incidencia${incidents.length === 1 ? "" : "s"} abierta${incidents.length === 1 ? "" : "s"}`;
    return;
  }

  if (unknown > 0) {
    label.textContent = "Comprobaciones pendientes";
    sub.textContent = `${unknown} servidor${unknown === 1 ? "" : "es"} sin resultado reciente`;
    return;
  }

  bar.classList.add("ok");
  label.textContent = "Todo operativo";
  sub.textContent = `${up} servidor${up === 1 ? "" : "es"} respondiendo`;
}

function renderServerGrid(servers) {
  const grid = document.getElementById("dashboard-grid");

  if (servers.length === 0) {
    grid.innerHTML = '<div class="empty-state">No hay servidores registrados.</div>';
    return;
  }

  const sorted = [...servers].sort((a, b) => {
    const order = { down: 0, unknown: 1, up: 2 };
    return (order[a.last_status] ?? 1) - (order[b.last_status] ?? 1);
  });

  grid.innerHTML = sorted.map(buildServerCard).join("");
}

function buildServerCard(server) {
  const status = server.last_status || "unknown";
  const latency = server.last_response_ms != null ? `${server.last_response_ms.toFixed(1)} ms` : "--";
  const checked = server.last_checked_at ? formatRelativeTime(server.last_checked_at) : "nunca";
  const services = buildServiceChips(server);
  const inactive = server.is_active ? "" : '<span class="text-muted">Inactivo</span>';
  const error = server.last_error ? `<div class="card-error">${escapeHtml(server.last_error)}</div>` : '<div class="card-error"></div>';

  return `
    <article class="server-card status-${status}">
      <div class="card-top">
        <div>
          <div class="card-name">${escapeHtml(server.name)}</div>
          <div class="card-host">${escapeHtml(server.ip_address)}</div>
        </div>
        ${statusBadge(status)}
      </div>
      <div class="service-list">${services || '<span class="service-chip">Sin checks</span>'}</div>
      ${error}
      <div class="card-meta">
        <span>Latencia<strong>${latency}</strong></span>
        <span>Ultima<strong>${checked}</strong></span>
      </div>
      ${inactive}
    </article>
  `;
}

function renderIncidentsFeed(incidents) {
  const feed = document.getElementById("incidents-feed");

  if (incidents.length === 0) {
    feed.innerHTML = '<div class="empty-state">No hay incidencias abiertas.</div>';
    return;
  }

  feed.innerHTML = incidents.map((incident) => `
    <div class="incident-item">
      <span class="incident-time">${formatDateTime(incident.started_at)}</span>
      <span class="incident-server">${escapeHtml(incident.server_name)}</span>
      <span class="incident-type">${escapeHtml(incident.check_type.toUpperCase())}</span>
      <span>
        <span class="incident-target">${escapeHtml(incident.target)}</span>
        <span class="incident-error">${escapeHtml(incident.error_message)}</span>
      </span>
    </div>
  `).join("");
}

function buildServiceChips(server) {
  const services = server.service_summary || [];
  return services.map((item) => `<span class="service-chip">${escapeHtml(item)}</span>`).join("");
}

function statusBadge(status) {
  const labels = { up: "Operativo", down: "Caido", unknown: "Pendiente" };
  return `<span class="status-badge ${status}">${labels[status] || status}</span>`;
}
