/**
 * app.js - Orquestador principal de la SPA
 *
 * Responsabilidades:
 *  - Navegacion entre vistas.
 *  - Ciclo de refresco automatico con cuenta atras.
 *  - Sistema de toasts.
 *  - Utilidades compartidas (formateo de fechas, escape HTML).
 *
 * Este fichero debe cargarse ultimo porque usa funciones de los
 * demas modulos JS.
 */

// ---------------------------------------------------------------------------
// Navegacion entre vistas
// ---------------------------------------------------------------------------

/** Mapa de id-de-vista -> funcion de carga de datos */
const VIEW_LOADERS = {
  dashboard: refreshDashboard,
  servers: refreshServersTable,
  logs: refreshLogsTable,
  settings: loadSettings,
};

const DISPLAY_TIMEZONE = "Europe/Madrid";

let _currentView = "dashboard";

/**
 * Muestra la vista indicada y oculta las demas.
 * Carga los datos de la vista activa.
 *
 * @param {string} viewName - Identificador de la vista.
 */
function navigateTo(viewName) {
  _currentView = viewName;

  document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
  document.getElementById(`view-${viewName}`)?.classList.add("active");

  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === viewName);
  });

  const loader = VIEW_LOADERS[viewName];
  if (loader) loader();
}

document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => navigateTo(btn.dataset.view));
});

// ---------------------------------------------------------------------------
// Ciclo de refresco automatico
// ---------------------------------------------------------------------------

let _refreshIntervalId = null;
let _countdownIntervalId = null;
let _secondsUntilRefresh = 60;

/**
 * Inicia el ciclo de refresco automatico.
 * El intervalo se obtiene de la API de ajustes para mantenerse sincronizado.
 */
async function startAutoRefresh() {
  let intervalSeconds = 60;
  try {
    const cfg = await API.getSettings();
    intervalSeconds = cfg.check_interval_seconds || 60;
  } catch (_) {
    // Usamos el valor por defecto si la API falla.
  }

  _secondsUntilRefresh = intervalSeconds;
  updateCountdownDisplay();

  clearInterval(_refreshIntervalId);
  clearInterval(_countdownIntervalId);

  _refreshIntervalId = setInterval(async () => {
    await refreshDashboard();

    const loader = VIEW_LOADERS[_currentView];
    if (loader && _currentView !== "dashboard") loader();

    startAutoRefresh();
  }, intervalSeconds * 1000);

  _countdownIntervalId = setInterval(() => {
    _secondsUntilRefresh = Math.max(0, _secondsUntilRefresh - 1);
    updateCountdownDisplay();
  }, 1000);
}

/**
 * Actualiza el texto del contador de la cabecera.
 */
function updateCountdownDisplay() {
  const el = document.getElementById("next-check-countdown");
  if (!el) return;

  const minutes = String(Math.floor(_secondsUntilRefresh / 60)).padStart(2, "0");
  const seconds = String(_secondsUntilRefresh % 60).padStart(2, "0");
  el.textContent = `${minutes}:${seconds}`;
}

// ---------------------------------------------------------------------------
// Sistema de toasts
// ---------------------------------------------------------------------------

/**
 * Muestra un mensaje toast temporal en la esquina inferior derecha.
 *
 * @param {string} message - Texto del mensaje.
 * @param {"success"|"error"} type - Tipo de toast.
 * @param {number} duration - Milisegundos antes de desaparecer.
 */
function showToast(message, type = "success", duration = 4000) {
  const container = document.getElementById("toast-container");
  const icon = type === "success" ? "&#10003;" : "&#10005;";

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icon}</span><span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity .3s";
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ---------------------------------------------------------------------------
// Utilidades compartidas
// ---------------------------------------------------------------------------

/**
 * Escapa caracteres HTML especiales para evitar XSS en innerHTML.
 *
 * @param {string} str - Cadena a escapar.
 * @returns {string} Cadena escapada.
 */
function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * Convierte una fecha devuelta por la API en un objeto Date fiable.
 * Si la marca viene sin offset (caso habitual de SQLite), se interpreta como UTC.
 *
 * @param {string} rawValue - Fecha en formato ISO o similar.
 * @returns {Date|null} Fecha parseada o null si no es valida.
 */
function parseApiDate(rawValue) {
  if (!rawValue) return null;

  const baseValue = String(rawValue).trim();
  if (!baseValue) return null;

  const isoValue = baseValue.includes("T")
    ? baseValue
    : baseValue.replace(" ", "T");

  const hasOffset = /(?:Z|[+-]\d{2}:\d{2})$/i.test(isoValue);
  const normalizedValue = hasOffset ? isoValue : `${isoValue}Z`;
  const parsed = new Date(normalizedValue);

  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

/**
 * Formatea una cadena ISO 8601 como fecha y hora en la zona de Espana.
 *
 * @param {string} isoString - Fecha en formato ISO 8601.
 * @returns {string} Fecha formateada.
 */
function formatDateTime(isoString) {
  if (!isoString) return "--";

  try {
    const date = parseApiDate(isoString);
    if (!date) return isoString;

    return new Intl.DateTimeFormat("es-ES", {
      dateStyle: "short",
      timeStyle: "medium",
      hour12: false,
      timeZone: DISPLAY_TIMEZONE,
    }).format(date);
  } catch (_) {
    return isoString;
  }
}

/**
 * Devuelve el tiempo transcurrido desde una fecha en formato relativo.
 *
 * @param {string} isoString - Fecha en formato ISO 8601.
 * @returns {string} Tiempo relativo.
 */
function formatRelativeTime(isoString) {
  if (!isoString) return "nunca";

  try {
    const date = parseApiDate(isoString);
    if (!date) return isoString;

    const diff = (Date.now() - date.getTime()) / 1000;
    if (diff < 60) return "hace unos segundos";
    if (diff < 3600) return `hace ${Math.floor(diff / 60)} min`;
    if (diff < 86400) return `hace ${Math.floor(diff / 3600)} h`;
    return `hace ${Math.floor(diff / 86400)} d`;
  } catch (_) {
    return isoString;
  }
}

// ---------------------------------------------------------------------------
// Arranque
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", async () => {
  navigateTo("dashboard");
  await startAutoRefresh();
});
