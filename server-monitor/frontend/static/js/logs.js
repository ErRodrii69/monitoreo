async function refreshLogsTable() {
  const tbody = document.getElementById("logs-tbody");
  try {
    const checks = await API.getRecentChecks(150);
    renderLogsTable(checks);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="loading-cell text-err">${escapeHtml(err.message)}</td></tr>`;
  }
}

function renderLogsTable(checks) {
  const tbody = document.getElementById("logs-tbody");

  if (checks.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="loading-cell">Sin registros.</td></tr>';
    return;
  }

  tbody.innerHTML = checks.map((check) => {
    const latency = check.response_ms != null ? `${check.response_ms.toFixed(1)} ms` : "--";
    const error = check.error_message ? escapeHtml(check.error_message) : '<span class="text-muted">--</span>';
    return `
      <tr>
        <td>${formatDateTime(check.checked_at)}</td>
        <td>${escapeHtml(check.server_name || `#${check.server_id}`)}</td>
        <td class="mono">${escapeHtml(check.check_type.toUpperCase())}</td>
        <td class="mono">${escapeHtml(check.target)}</td>
        <td>${statusBadge(check.status)}</td>
        <td class="mono">${latency}</td>
        <td>${error}</td>
      </tr>
    `;
  }).join("");
}

document.getElementById("btn-refresh-logs").addEventListener("click", refreshLogsTable);
