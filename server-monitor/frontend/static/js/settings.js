async function loadSettings() {
  try {
    const cfg = await API.getSettings();
    document.getElementById("cfg-interval").value = cfg.check_interval_seconds;
    document.getElementById("cfg-ping-timeout").value = cfg.ping_timeout_seconds;
    document.getElementById("cfg-ping-count").value = cfg.ping_count;
    document.getElementById("cfg-http-timeout").value = cfg.http_timeout_seconds;
    document.getElementById("cfg-email-to").value = cfg.alert_email_to || "";
    document.getElementById("cfg-smtp-host").value = cfg.smtp_host || "";
    document.getElementById("cfg-smtp-port").value = cfg.smtp_port || 587;
    document.getElementById("cfg-smtp-user").value = cfg.smtp_user || "";
    document.getElementById("cfg-smtp-pass").value = "";
    document.getElementById("cfg-smtp-from").value = cfg.smtp_from || "";
    document.getElementById("cfg-notify-recovery").checked = Boolean(cfg.notify_recovery);
  } catch (err) {
    showToast(`Error al cargar ajustes: ${err.message}`, "error");
  }
}

async function saveSettings() {
  const feedback = document.getElementById("save-feedback");
  feedback.textContent = "";

  const payload = {
    check_interval_seconds: numberValue("cfg-interval"),
    ping_timeout_seconds: numberValue("cfg-ping-timeout"),
    ping_count: numberValue("cfg-ping-count"),
    http_timeout_seconds: numberValue("cfg-http-timeout"),
    alert_email_to: document.getElementById("cfg-email-to").value.trim(),
    smtp_host: document.getElementById("cfg-smtp-host").value.trim(),
    smtp_port: numberValue("cfg-smtp-port"),
    smtp_user: document.getElementById("cfg-smtp-user").value.trim(),
    smtp_from: document.getElementById("cfg-smtp-from").value.trim(),
    notify_recovery: document.getElementById("cfg-notify-recovery").checked,
  };

  const smtpPassword = document.getElementById("cfg-smtp-pass").value;
  if (smtpPassword) payload.smtp_password = smtpPassword;

  try {
    await API.updateSettings(payload);
    feedback.textContent = "Guardado";
    showToast("Ajustes guardados.", "success");
    await startAutoRefresh();
    window.setTimeout(() => { feedback.textContent = ""; }, 3000);
  } catch (err) {
    showToast(`Error al guardar ajustes: ${err.message}`, "error");
  }
}

function numberValue(id) {
  const parsed = Number(document.getElementById(id).value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

document.getElementById("btn-save-settings").addEventListener("click", saveSettings);
