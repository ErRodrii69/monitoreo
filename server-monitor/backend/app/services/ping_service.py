"""
=============================================================
app/services/ping_service.py - Logica de ping ICMP

Responsabilidad unica: ejecutar un ping a una IP/hostname y
devolver el resultado. No toca la base de datos ni envia correos.
=============================================================
"""

import asyncio
import os
import re
from dataclasses import dataclass


@dataclass
class PingResult:
    """
    Resultado de una comprobacion de ping.
    """

    success: bool
    response_ms: float | None
    error: str | None


async def ping_host(host: str, count: int = 1, timeout: float = 3.0) -> PingResult:
    """
    Lanza un ping ICMP asincrono a *host* y devuelve un PingResult.
    """

    cmd = _build_ping_command(host=host, count=count, timeout=timeout)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=timeout + 2
        )

        stdout = stdout_bytes.decode(errors="replace")
        stderr = stderr_bytes.decode(errors="replace")

        if proc.returncode == 0:
            return PingResult(
                success=True,
                response_ms=_parse_avg_ms(stdout),
                error=None,
            )

        error_message = stderr.strip() or stdout.strip()
        if not error_message:
            error_message = f"Host unreachable (exit code {proc.returncode})"

        return PingResult(
            success=False,
            response_ms=None,
            error=error_message,
        )

    except asyncio.TimeoutError:
        return PingResult(success=False, response_ms=None, error="Ping timed out")

    except FileNotFoundError:
        return PingResult(
            success=False,
            response_ms=None,
            error="'ping' binary not found in PATH.",
        )

    except Exception as exc:
        return PingResult(success=False, response_ms=None, error=str(exc))


def _build_ping_command(host: str, count: int, timeout: float) -> list[str]:
    """
    Construye el comando ping adecuado para el sistema operativo actual.
    """

    if os.name == "nt":
        timeout_ms = max(int(timeout * 1000), 1000)
        return ["ping", "-n", str(count), "-w", str(timeout_ms), host]

    return ["ping", "-c", str(count), "-W", str(max(int(timeout), 1)), host]


def _parse_avg_ms(ping_output: str) -> float | None:
    """
    Extrae la latencia media del output del comando ping.
    """

    patterns = [
        r"min/avg/max(?:/mdev)?\s*=\s*[\d.]+/([\d.]+)/",
        r"Average\s*=\s*([\d.]+)\s*ms",
        r"Media\s*=\s*([\d.]+)\s*ms",
        r"time[=<]\s*([\d.]+)\s*ms",
        r"tiempo[=<]\s*([\d.]+)\s*ms",
    ]

    for pattern in patterns:
        match = re.search(pattern, ping_output, re.IGNORECASE)
        if not match:
            continue

        try:
            return float(match.group(1))
        except ValueError:
            continue

    return None
