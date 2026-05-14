/**
 * settings.js — Lógica de la vista "Ajustes"
 * Responsabilidad única: leer y guardar la configuración de la aplicación.
 */

/**
 * Carga los ajustes actuales desde la API y rellena el formulario.
 */
async function loadSettings() {
  try {
    const cfg = await API.getSettings();

    document.getElementById("cfg-interval").value   = cfg.check_interval_seconds;
    document.getElementById("cfg-email-to").value   = cfg.alert_email_to;
    document.getElementById("cfg-smtp-host").value  = cfg.smtp_host;
    document.getElementById("cfg-smtp-port").value  = cfg.smtp_port;
    document.getElementById("cfg-smtp-user").value  = cfg.smtp_user;
    document.getElementById("cfg-smtp-from").value  = cfg.smtp_from;
  } catch (err) {
    showToast("Error al cargar ajustes: " + err.message, "error");
  }
}

/**
 * Recoge los valores del formulario y los envía a la API.
 * Muestra feedback visual en línea (sin toast) para confirmación inmediata.
 */
async function saveSettings() {
  const feedback = document.getElementById("save-feedback");
  feedback.textContent = "";

  const payload = {};

  const interval = parseInt(document.getElementById("cfg-interval").value, 10);
  if (!isNaN(interval)) payload.check_interval_seconds = interval;

  const emailTo = document.getElementById("cfg-email-to").value.trim();
  if (emailTo) payload.alert_email_to = emailTo;

  const smtpHost = document.getElementById("cfg-smtp-host").value.trim();
  if (smtpHost) payload.smtp_host = smtpHost;

  const smtpPort = parseInt(document.getElementById("cfg-smtp-port").value, 10);
  if (!isNaN(smtpPort)) payload.smtp_port = smtpPort;

  const smtpUser = document.getElementById("cfg-smtp-user").value.trim();
  if (smtpUser) payload.smtp_user = smtpUser;

  const smtpPass = document.getElementById("cfg-smtp-pass").value;
  if (smtpPass) payload.smtp_password = smtpPass;

  const smtpFrom = document.getElementById("cfg-smtp-from").value.trim();
  if (smtpFrom) payload.smtp_from = smtpFrom;

  try {
    await API.updateSettings(payload);
    feedback.textContent = "✓ Ajustes guardados";
    showToast("Ajustes actualizados correctamente.", "success");
    setTimeout(() => { feedback.textContent = ""; }, 4000);
  } catch (err) {
    showToast("Error al guardar ajustes: " + err.message, "error");
  }
}

document.getElementById("btn-save-settings").addEventListener("click", saveSettings);
