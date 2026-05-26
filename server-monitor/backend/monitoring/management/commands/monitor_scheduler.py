import signal
import time

from django.core.management.base import BaseCommand

from monitoring.models import AppSetting
from monitoring.services.monitoring import run_monitoring_round


class Command(BaseCommand):
    help = "Ejecuta el scheduler continuo de monitorizacion."

    def handle(self, *args, **options):
        running = True

        def stop(*_):
            nonlocal running
            running = False

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)

        self.stdout.write(self.style.SUCCESS("Scheduler de monitorizacion iniciado"))

        while running:
            started = time.monotonic()
            checked = run_monitoring_round()
            cfg = AppSetting.load()
            elapsed = time.monotonic() - started
            wait_seconds = max(1, int(cfg.check_interval_seconds - elapsed))
            self.stdout.write(
                f"Ronda completada: {checked} servidores. Proxima en {wait_seconds}s"
            )

            for _ in range(wait_seconds):
                if not running:
                    break
                time.sleep(1)

        self.stdout.write(self.style.WARNING("Scheduler detenido"))
