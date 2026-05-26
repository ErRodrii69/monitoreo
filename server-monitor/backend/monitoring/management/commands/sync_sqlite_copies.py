import sqlite3
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection

from monitoring.models import CheckLog, Server


class Command(BaseCommand):
    help = "Copia servers y check_logs desde la base activa a los SQLite locales."

    def add_arguments(self, parser):
        parser.add_argument(
            "--target",
            action="append",
            dest="targets",
            help="Ruta SQLite destino. Se puede repetir.",
        )

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parents[3]
        targets = options["targets"] or [
            str(base_dir / "server_monitor.sqlite3"),
            str(base_dir / "server_monitor.db"),
        ]

        servers = list(Server.objects.order_by("id").values())
        checks = list(
            CheckLog.objects.order_by("id").values(
                "id",
                "server_id",
                "check_type",
                "target",
                "status",
                "response_ms",
                "error_message",
                "checked_at",
            )
        )

        self.stdout.write(
            f"Origen: {connection.settings_dict['ENGINE']} "
            f"{connection.settings_dict.get('HOST', '')} "
            f"{connection.settings_dict.get('NAME', '')}".strip()
        )

        for raw_target in targets:
            target = Path(raw_target).resolve()
            if not target.exists():
                self.stdout.write(self.style.WARNING(f"No existe: {target}"))
                continue

            copied_servers, copied_checks = sync_sqlite(target, servers, checks)
            self.stdout.write(
                self.style.SUCCESS(
                    f"{target.name}: servers={copied_servers}, check_logs={copied_checks}"
                )
            )


def sync_sqlite(
    path: Path,
    servers: list[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> tuple[int, int]:
    con = sqlite3.connect(path)
    try:
        con.execute("PRAGMA foreign_keys = OFF")
        con.execute("DELETE FROM check_logs")
        con.execute("DELETE FROM servers")

        copied_servers = insert_matching(con, "servers", servers)
        copied_checks = insert_matching(con, "check_logs", checks)

        if table_exists(con, "sqlite_sequence"):
            for table in ("servers", "check_logs"):
                con.execute(
                    "UPDATE sqlite_sequence SET seq = COALESCE((SELECT MAX(id) FROM "
                    f"{table}), 0) WHERE name = ?",
                    (table,),
                )

        con.commit()
        return copied_servers, copied_checks
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def insert_matching(
    con: sqlite3.Connection,
    table: str,
    rows: list[dict[str, Any]],
) -> int:
    columns = table_columns(con, table)
    if not columns:
        return 0

    writable_columns = [column for column in columns if any(column in row for row in rows)]
    if not writable_columns:
        return 0

    placeholders = ", ".join("?" for _ in writable_columns)
    column_sql = ", ".join(f'"{column}"' for column in writable_columns)
    sql = f'INSERT INTO "{table}" ({column_sql}) VALUES ({placeholders})'

    values = [
        tuple(sqlite_value(row.get(column)) for column in writable_columns)
        for row in rows
    ]
    con.executemany(sql, values)
    return len(values)


def table_columns(con: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in con.execute(f'PRAGMA table_info("{table}")')]


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def sqlite_value(value: Any) -> Any:
    if value is True:
        return 1
    if value is False:
        return 0
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
