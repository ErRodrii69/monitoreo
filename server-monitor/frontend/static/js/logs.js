/**
 * logs.js — Lógica de la vista "Registros"
 * Responsabilidad única: renderizar el historial de comprobaciones.
 */

/**
 * Carga y renderiza los últimos 100 registros de comprobación.
 */
async function refreshLogsTable() {
  const tbody = document.getElementById("logs-tbody");
  try {
    const checks = await API.getRecentChecks(100);
    renderLogsTable(checks);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="loading-cell text-err">Error: ${escapeHtml(err.message)}</td></tr>`;
  }
}

/**
 * Renderiza las filas de la tabla de registros.
 *
 * @param {Array} checks - Lista de objetos CheckLog.
 */
function renderLogsTable(checks) {
  const tbody = document.getElementById("logs-tbody");

  if (checks.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="loading-cell">Sin registros aún.</td></tr>';
    return;
  }

  tbody.innerHTML = checks.map(c => {
    const badge = `<span class="status-badge ${c.status}">${c.status === "up" ? "Operativo" : "Caído"}</span>`;
    const lat   = c.response_ms != null ? `${c.response_ms.toFixed(1)}` : "—";
    const err   = c.error_message ? escapeHtml(c.error_message) : '<span class="text-muted">—</span>';
    return `
      <tr>
        <td>${formatDateTime(c.checked_at)}</td>
        <td class="mono">#${c.server_id}</td>
        <td>${badge}</td>
        <td class="mono">${lat}</td>
        <td>${err}</td>
      </tr>
    `;
  }).join("");
}
