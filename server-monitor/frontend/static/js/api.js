/**
 * api.js — Cliente HTTP para la API REST del backend
 *
 * Centraliza todas las llamadas fetch a /api/*.
 * Responsabilidad única: comunicación con el backend.
 * Ninguna otra capa debe hacer fetch directamente.
 */

const API_BASE = "/api";

/**
 * Wrapper genérico de fetch.
 * Lanza un Error con el mensaje del servidor si la respuesta no es 2xx.
 *
 * @param {string} path   - Ruta relativa (ej: "/servers")
 * @param {object} opts   - Opciones de fetch (method, body, etc.)
 * @returns {Promise<any>} - JSON parseado de la respuesta
 */
async function apiFetch(path, opts = {}) {
  const url = API_BASE + path;
  const defaults = {
    headers: { "Content-Type": "application/json" },
  };

  const res = await fetch(url, { ...defaults, ...opts });

  if (!res.ok) {
    let message = `Error ${res.status}`;
    try {
      const body = await res.json();
      message = body.detail || JSON.stringify(body);
    } catch (_) { /* ignoramos errores de parseo */ }
    throw new Error(message);
  }

  // 204 No Content no tiene cuerpo
  if (res.status === 204) return null;
  return res.json();
}

// ---------------------------------------------------------------------------
// Servidores
// ---------------------------------------------------------------------------

/** Devuelve la lista completa de servidores. */
const getServers = () => apiFetch("/servers/");

/** Crea un nuevo servidor. */
const createServer = (data) =>
  apiFetch("/servers/", { method: "POST", body: JSON.stringify(data) });

/** Actualiza los campos del servidor con el ID dado. */
const updateServer = (id, data) =>
  apiFetch(`/servers/${id}`, { method: "PUT", body: JSON.stringify(data) });

/** Elimina un servidor por su ID. */
const deleteServer = (id) =>
  apiFetch(`/servers/${id}`, { method: "DELETE" });

/** Lanza un ping manual inmediato al servidor. */
const pingServer = (id) =>
  apiFetch(`/servers/${id}/ping`, { method: "POST" });

// ---------------------------------------------------------------------------
// Logs de comprobación
// ---------------------------------------------------------------------------

/** Devuelve los últimos *limit* registros globales de comprobación. */
const getRecentChecks = (limit = 50) =>
  apiFetch(`/checks/?limit=${limit}`);

/** Devuelve el historial de comprobaciones de un servidor concreto. */
const getServerChecks = (serverId, limit = 100) =>
  apiFetch(`/checks/server/${serverId}?limit=${limit}`);

// ---------------------------------------------------------------------------
// Ajustes
// ---------------------------------------------------------------------------

/** Devuelve los ajustes actuales de la aplicación. */
const getSettings = () => apiFetch("/settings/");

/** Actualiza los ajustes de la aplicación. */
const updateSettings = (data) =>
  apiFetch("/settings/", { method: "PATCH", body: JSON.stringify(data) });

// ---------------------------------------------------------------------------
// Exportamos como objeto global (sin módulos ES para compatibilidad simple)
// ---------------------------------------------------------------------------
window.API = {
  getServers, createServer, updateServer, deleteServer, pingServer,
  getRecentChecks, getServerChecks,
  getSettings, updateSettings,
};
