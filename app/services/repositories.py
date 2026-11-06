import csv
import uuid
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


class MariaDbAuditRepository:
    """Auditoría de ejecución; la conexión se mantiene por proceso CLI."""

    def __init__(self, *, host: str, port: int, database: str, user: str, password: str):
        import pymysql
        self.connection = pymysql.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            charset="utf8mb4",
            autocommit=False,
        )
        self.batch_id = str(uuid.uuid4())

    def record(self, *, filename: str, status: str, message: str = "") -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
            """
            INSERT INTO log_auditoria (lote_id, archivo, estado, mensaje)
            VALUES (%s, %s, %s, %s)
            """,
                (self.batch_id, filename, status, message),
            )
        self.connection.commit()
