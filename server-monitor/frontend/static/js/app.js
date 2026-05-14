/**
 * app.js — Orquestador principal de la SPA
 *
 * Responsabilidades:
 *  - Navegación entre vistas.
 *  - Ciclo de refresco automático con cuenta atrás.
 *  - Sistema de toasts.
 *  - Utilidades compartidas (formateo de fechas, escape HTML).
 *
 * Este fichero debe cargarse ÚLTIMO porque usa funciones de los
 * demás módulos JS.
 */

// ---------------------------------------------------------------------------
// Navegación entre vistas
// ---------------------------------------------------------------------------

/** Mapa de id-de-vista → función de carga de datos */
const VIEW_LOADERS = {
  dashboard: refreshDashboard,
  servers:   refreshServersTable,
  logs:      refreshLogsTable,
  settings:  loadSettings,
};

let _currentView = "dashboard";

/**
 * Muestra la vista indicada y oculta las demás.
 * Carga los datos de la vista activa.
 *
 * @param {string} viewName - Identificador de la vista.
 */
function navigateTo(viewName) {
  _currentView = viewName;

  // Ocultar todas las vistas
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  // Mostrar la seleccionada
  document.getElementById(`view-${viewName}`)?.classList.add("active");

  // Actualizar estado activo en la barra de navegación
  document.querySelectorAll(".nav-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.view === viewName);
  });

  // Cargar los datos de la vista
  const loader = VIEW_LOADERS[viewName];
  if (loader) loader();
}

// Registramos los clics de la barra de navegación
document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.addEventListener("click", () => navigateTo(btn.dataset.view));
});

// ---------------------------------------------------------------------------
// Ciclo de refresco automático
// ---------------------------------------------------------------------------

let _refreshIntervalId  = null;
let _countdownIntervalId = null;
let _secondsUntilRefresh = 60;

/**
 * Inicia el ciclo de refresco automático.
 * El intervalo se obtiene de la API de ajustes para mantenerse sincronizado.
 */
async function startAutoRefresh() {
  // Recuperamos el intervalo configurado en el backend
  let intervalSeconds = 60;
  try {
    const cfg = await API.getSettings();
    intervalSeconds = cfg.check_interval_seconds || 60;
  } catch (_) { /* usamos el valor por defecto */ }

  _secondsUntilRefresh = intervalSeconds;
  updateCountdownDisplay();

  // Limpiamos ciclos anteriores si los hay
  clearInterval(_refreshIntervalId);
  clearInterval(_countdownIntervalId);

  // Refresco de datos
  _refreshIntervalId = setInterval(async () => {
    // Siempre refrescamos el dashboard (datos en segundo plano)
    await refreshDashboard();
    // Si estamos en otra vista, también la refrescamos
    const loader = VIEW_LOADERS[_currentView];
    if (loader && _currentView !== "dashboard") loader();

    // Relanzamos para recoger posibles cambios de intervalo
    startAutoRefresh();
  }, intervalSeconds * 1000);

  // Cuenta atrás en la cabecera
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
  const m = String(Math.floor(_secondsUntilRefresh / 60)).padStart(2, "0");
  const s = String(_secondsUntilRefresh % 60).padStart(2, "0");
  el.textContent = `${m}:${s}`;
}

// ---------------------------------------------------------------------------
// Sistema de toasts
// ---------------------------------------------------------------------------

/**
 * Muestra un mensaje toast temporal en la esquina inferior derecha.
 *
 * @param {string} message - Texto del mensaje.
 * @param {"success"|"error"} type - Tipo de toast (color).
 * @param {number} duration - Milisegundos antes de desaparecer.
 */
function showToast(message, type = "success", duration = 4000) {
  const container = document.getElementById("toast-container");
  const icon = type === "success" ? "✓" : "✗";

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icon}</span><span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);

  // Auto-eliminar tras la duración indicada
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
    .replace(/"/g, "&quot;");
}

/**
 * Formatea una cadena ISO 8601 como fecha y hora local legible.
 *
 * @param {string} isoString - Fecha en formato ISO 8601.
 * @returns {string} Fecha formateada.
 */
function formatDateTime(isoString) {
  if (!isoString) return "—";
  try {
    return new Intl.DateTimeFormat("es-ES", {
      dateStyle: "short",
      timeStyle: "medium",
    }).format(new Date(isoString));
  } catch (_) {
    return isoString;
  }
}

/**
 * Devuelve el tiempo transcurrido desde una fecha en formato relativo.
 * Ej: "hace 3 minutos", "hace 1 hora".
 *
 * @param {string} isoString - Fecha en formato ISO 8601.
 * @returns {string} Tiempo relativo.
 */
function formatRelativeTime(isoString) {
  if (!isoString) return "nunca";
  try {
    const diff = (Date.now() - new Date(isoString).getTime()) / 1000; // segundos
    if (diff < 60)   return "hace unos segundos";
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
  // Cargar la vista inicial
  navigateTo("dashboard");
  // Iniciar el refresco automático
  await startAutoRefresh();
});
