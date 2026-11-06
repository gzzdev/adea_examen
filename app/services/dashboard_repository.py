from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator


ALLOWED_EXPEDIENTE_STATES = {
    "PROCESADO",
    "PENDIENTE_VALIDACION",
    "INVALIDO",
    "ERROR",
}


class DashboardRepository:
    """Consultas de solo lectura para el tablero web."""

    def __init__(self, *, host: str, port: int, database: str, user: str, password: str):
        self.connection_options = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
            "charset": "utf8mb4",
            "cursorclass": self._dict_cursor(),
            "autocommit": True,
            "connect_timeout": 5,
        }

    @staticmethod
    def _dict_cursor():
        import pymysql
        return pymysql.cursors.DictCursor

    @contextmanager
    def _connection(self) -> Iterator[Any]:
        import pymysql
        connection = pymysql.connect(**self.connection_options)
        try:
            yield connection
        finally:
            connection.close()

    def summary(self) -> dict[str, int]:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) AS total,
                       COALESCE(SUM(estado = 'PROCESADO'), 0) AS procesados,
                       COALESCE(SUM(estado = 'PENDIENTE_VALIDACION'), 0) AS pendientes,
                       COALESCE(SUM(estado IN ('ERROR', 'INVALIDO')), 0) AS incidencias
                FROM expediente
                """
            )
            return cursor.fetchone()

    def expedientes(self, *, page: int, page_size: int, search: str = "", status: str = "") -> dict[str, Any]:
        where, params = self._expediente_filters(search=search, status=status)
        offset = (page - 1) * page_size
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) AS total FROM expediente {where}", params)
            total = cursor.fetchone()["total"]
            cursor.execute(
                f"""
                SELECT id, lote_id, archivo, estado, curp, clave_elector,
                       qr_reverso, nombre_completo, domicilio, datos_electorales,
                       mensaje_error, intentos, creado_en, iniciado_en, terminado_en
                FROM expediente {where}
                ORDER BY creado_en DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                [*params, page_size, offset],
            )
            items = cursor.fetchall()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def audit_logs(self, *, page: int, page_size: int, search: str = "", status: str = "") -> dict[str, Any]:
        clauses: list[str] = []
        params: list[Any] = []
        if search:
            wildcard = f"%{search}%"
            clauses.append("(archivo LIKE %s OR mensaje LIKE %s OR expediente_id LIKE %s)")
            params.extend([wildcard, wildcard, wildcard])
        if status and status in ALLOWED_EXPEDIENTE_STATES | {"DUPLICADO"}:
            clauses.append("estado = %s")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        offset = (page - 1) * page_size
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) AS total FROM log_auditoria {where}", params)
            total = cursor.fetchone()["total"]
            cursor.execute(
                f"""
                SELECT id, expediente_id, lote_id, archivo, estado, mensaje, creado_en
                FROM log_auditoria {where}
                ORDER BY creado_en DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                [*params, page_size, offset],
            )
            items = cursor.fetchall()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    @staticmethod
    def _expediente_filters(*, search: str, status: str) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if search:
            wildcard = f"%{search}%"
            clauses.append("(archivo LIKE %s OR curp LIKE %s OR clave_elector LIKE %s OR id LIKE %s)")
            params.extend([wildcard, wildcard, wildcard, wildcard])
        if status and status in ALLOWED_EXPEDIENTE_STATES:
            clauses.append("estado = %s")
            params.append(status)
        return (f"WHERE {' AND '.join(clauses)}" if clauses else ""), params
