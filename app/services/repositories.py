import csv
from datetime import datetime, timezone


class FileAuditRepository:
    def __init__(self, output_file):
        self.output_file = output_file
        if not self.output_file.exists():
            self.output_file.write_text("timestamp,filename,status,message\n", encoding="utf-8")

    def record(self, *, filename: str, status: str, message: str = "") -> None:
        with self.output_file.open("a", newline="", encoding="utf-8") as stream:
            csv.writer(stream).writerow([
                datetime.now(timezone.utc).isoformat(), filename, status, message
            ])


class SqlServerAuditRepository:
    def __init__(self, connection_string: str):
        import pyodbc
        self.connection = pyodbc.connect(connection_string)

    def record(self, *, filename: str, status: str, message: str = "") -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO auditoria_expedientes
                (archivo, estado, mensaje, fecha_proceso)
            VALUES (?, ?, ?, SYSUTCDATETIME())
            """,
            filename, status, message,
        )
        self.connection.commit()


class OracleExpedienteRepository:
    def __init__(self, user: str, password: str, dsn: str, procedure: str):
        import oracledb
        self.connection = oracledb.connect(user=user, password=password, dsn=dsn)
        self.procedure = procedure

    def save(self, *, filename: str, curp: str, clave_elector: str) -> None:
        cursor = self.connection.cursor()
        cursor.callproc(self.procedure, [filename, curp, clave_elector])
        self.connection.commit()
