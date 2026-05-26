import os
import re
import socket
import subprocess
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from monitoring.models import CheckType, Server


@dataclass(slots=True)
class ServiceCheckResult:
    check_type: str
    target: str
    success: bool
    response_ms: float | None
    error: str


def run_configured_checks(
    server: Server,
    ping_count: int,
    ping_timeout: float,
    http_timeout: float,
) -> list[ServiceCheckResult]:
    results: list[ServiceCheckResult] = []

    if server.check_ping:
        results.append(ping_host(server.ip_address, ping_count, ping_timeout))

    if server.check_ssh:
        results.append(
            check_tcp_port(
                server.ip_address,
                server.ssh_port,
                timeout=ping_timeout,
                check_type=CheckType.SSH,
            )
        )

    if server.check_http:
        url = server.http_url or f"http://{server.ip_address}"
        results.append(check_http_endpoint(url, timeout=http_timeout, check_type=CheckType.HTTP))

    if server.check_https:
        url = server.https_url or f"https://{server.ip_address}"
        results.append(check_http_endpoint(url, timeout=http_timeout, check_type=CheckType.HTTPS))

    for port in server.custom_port_list():
        results.append(
            check_tcp_port(
                server.ip_address,
                port,
                timeout=ping_timeout,
                check_type=CheckType.PORT,
            )
        )

    return results


def ping_host(host: str, count: int = 1, timeout: float = 3.0) -> ServiceCheckResult:
    command = _build_ping_command(host, count, timeout)
    started = time.perf_counter()

    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout + 2,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ServiceCheckResult(CheckType.PING, host, False, None, "Tiempo agotado")
    except FileNotFoundError:
        return ServiceCheckResult(CheckType.PING, host, False, None, "No existe el binario ping")
    except OSError as exc:
        return ServiceCheckResult(CheckType.PING, host, False, None, str(exc))

    output = f"{proc.stdout}\n{proc.stderr}".strip()
    elapsed_ms = (time.perf_counter() - started) * 1000

    if proc.returncode == 0:
        return ServiceCheckResult(
            CheckType.PING,
            host,
            True,
            _parse_ping_ms(output) or elapsed_ms,
            "",
        )

    return ServiceCheckResult(
        CheckType.PING,
        host,
        False,
        None,
        _compact_error(output) or f"Ping fallo con codigo {proc.returncode}",
    )


def check_tcp_port(
    host: str,
    port: int,
    timeout: float,
    check_type: str = CheckType.PORT,
) -> ServiceCheckResult:
    target = f"{host}:{port}"
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            elapsed_ms = (time.perf_counter() - started) * 1000
            return ServiceCheckResult(check_type, target, True, elapsed_ms, "")
    except OSError as exc:
        return ServiceCheckResult(check_type, target, False, None, str(exc))


def check_http_endpoint(
    url: str,
    timeout: float,
    check_type: str,
) -> ServiceCheckResult:
    started = time.perf_counter()
    try:
        status_code = _request_status(url, timeout, method="HEAD")
    except HTTPError as exc:
        if exc.code == 405:
            try:
                status_code = _request_status(url, timeout, method="GET")
            except (HTTPError, URLError, TimeoutError, OSError) as inner_exc:
                return ServiceCheckResult(check_type, url, False, None, str(inner_exc))
        else:
            status_code = exc.code
    except (URLError, TimeoutError, OSError) as exc:
        return ServiceCheckResult(check_type, url, False, None, str(exc))

    elapsed_ms = (time.perf_counter() - started) * 1000
    if 200 <= int(status_code) < 400:
        return ServiceCheckResult(check_type, url, True, elapsed_ms, "")

    return ServiceCheckResult(
        check_type,
        url,
        False,
        elapsed_ms,
        f"HTTP {status_code}",
    )


def _request_status(url: str, timeout: float, method: str) -> int:
    request = Request(url, method=method, headers={"User-Agent": "ServerWatch/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return int(response.status)


def _build_ping_command(host: str, count: int, timeout: float) -> list[str]:
    if os.name == "nt":
        return ["ping", "-n", str(count), "-w", str(max(int(timeout * 1000), 1000)), host]
    return ["ping", "-c", str(count), "-W", str(max(int(timeout), 1)), host]


def _parse_ping_ms(output: str) -> float | None:
    patterns = [
        r"min/avg/max(?:/mdev)?\s*=\s*[\d.]+/([\d.]+)/",
        r"Average\s*=\s*([\d.]+)\s*ms",
        r"Media\s*=\s*([\d.]+)\s*ms",
        r"time[=<]\s*([\d.]+)\s*ms",
        r"tiempo[=<]\s*([\d.]+)\s*ms",
    ]
    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if not match:
            continue
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def _compact_error(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return ""
    return lines[-1][:500]
