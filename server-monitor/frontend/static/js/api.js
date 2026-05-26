const API_BASE = "/api";

async function apiFetch(path, opts = {}) {
  const res = await fetch(API_BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });

  if (!res.ok) {
    let message = `Error ${res.status}`;
    try {
      const body = await res.json();
      message = body.detail || JSON.stringify(body);
    } catch (_) {
      message = res.statusText || message;
    }
    throw new Error(message);
  }

  if (res.status === 204) return null;
  return res.json();
}

const getServers = () => apiFetch("/servers/");
const createServer = (data) => apiFetch("/servers/", { method: "POST", body: JSON.stringify(data) });
const updateServer = (id, data) => apiFetch(`/servers/${id}/`, { method: "PUT", body: JSON.stringify(data) });
const deleteServer = (id) => apiFetch(`/servers/${id}/`, { method: "DELETE" });
const checkServer = (id) => apiFetch(`/servers/${id}/check/`, { method: "POST" });
const pingServer = checkServer;

const getRecentChecks = (limit = 100) => apiFetch(`/checks/?limit=${limit}`);
const getServerChecks = (serverId, limit = 100) => apiFetch(`/checks/server/${serverId}/?limit=${limit}`);
const getIncidents = (status = "open", limit = 50) => apiFetch(`/incidents/?status=${status}&limit=${limit}`);
const getSummary = () => apiFetch("/summary/");

const getSettings = () => apiFetch("/settings/");
const updateSettings = (data) => apiFetch("/settings/", { method: "PATCH", body: JSON.stringify(data) });

window.API = {
  getServers,
  createServer,
  updateServer,
  deleteServer,
  checkServer,
  pingServer,
  getRecentChecks,
  getServerChecks,
  getIncidents,
  getSummary,
  getSettings,
  updateSettings,
};
