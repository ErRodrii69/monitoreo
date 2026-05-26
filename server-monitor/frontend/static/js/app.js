const VIEW_LOADERS = {
  dashboard: refreshDashboard,
  servers: refreshServersTable,
  logs: refreshLogsTable,
  settings: loadSettings,
};

const DISPLAY_TIMEZONE = "Europe/Madrid";

let currentView = "dashboard";
let refreshTimer = null;
let countdownTimer = null;
let secondsUntilRefresh = 60;

function navigateTo(viewName) {
  currentView = viewName;

  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("active", view.id === `view-${viewName}`);
  });

  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === viewName);
  });

  const loader = VIEW_LOADERS[viewName];
  if (loader) loader();
}

async function startAutoRefresh() {
  clearInterval(refreshTimer);
  clearInterval(countdownTimer);

  let intervalSeconds = 60;
  try {
    const cfg = await API.getSettings();
    intervalSeconds = cfg.check_interval_seconds || 60;
  } catch (_) {
    intervalSeconds = 60;
  }

  secondsUntilRefresh = intervalSeconds;
  updateCountdownDisplay();

  refreshTimer = setInterval(async () => {
    await refreshDashboard();
    if (currentView !== "dashboard") {
      const loader = VIEW_LOADERS[currentView];
      if (loader) await loader();
    }
    await startAutoRefresh();
  }, intervalSeconds * 1000);

  countdownTimer = setInterval(() => {
    secondsUntilRefresh = Math.max(0, secondsUntilRefresh - 1);
    updateCountdownDisplay();
  }, 1000);
}

function updateCountdownDisplay() {
  const el = document.getElementById("next-check-countdown");
  if (!el) return;
  const minutes = String(Math.floor(secondsUntilRefresh / 60)).padStart(2, "0");
  const seconds = String(secondsUntilRefresh % 60).padStart(2, "0");
  el.textContent = `${minutes}:${seconds}`;
}

function showToast(message, type = "success", duration = 4000) {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  window.setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity .2s ease";
    window.setTimeout(() => toast.remove(), 220);
  }, duration);
}

function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function parseApiDate(rawValue) {
  if (!rawValue) return null;
  const text = String(rawValue).trim();
  const normalized = /(?:Z|[+-]\d{2}:\d{2})$/i.test(text) ? text : `${text}Z`;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatDateTime(rawValue) {
  const date = parseApiDate(rawValue);
  if (!date) return rawValue || "--";

  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "short",
    timeStyle: "medium",
    hour12: false,
    timeZone: DISPLAY_TIMEZONE,
  }).format(date);
}

function formatRelativeTime(rawValue) {
  const date = parseApiDate(rawValue);
  if (!date) return "nunca";

  const diff = Math.max(0, (Date.now() - date.getTime()) / 1000);
  if (diff < 60) return "ahora";
  if (diff < 3600) return `${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} h`;
  return `${Math.floor(diff / 86400)} d`;
}

document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => navigateTo(btn.dataset.view));
});

document.getElementById("btn-refresh-dashboard").addEventListener("click", refreshDashboard);

document.addEventListener("DOMContentLoaded", async () => {
  navigateTo("dashboard");
  await startAutoRefresh();
});
