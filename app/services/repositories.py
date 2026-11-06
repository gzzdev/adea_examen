import csv
import json
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


class MariaDbRepository:
    """Persistencia de expedientes y auditoría para una ejecución local."""

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

    def find_by_hash(self, file_hash: str) -> dict | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, lote_id, archivo, estado, creado_en
                FROM expediente WHERE hash_archivo = %s LIMIT 1
                """,
                (file_hash,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return dict(zip(("id", "lote_id", "archivo", "estado", "creado_en"), row))

    def save_expediente(
        self, *, expediente_id: str, filename: str, file_hash: str, status: str,
        curp: str | None = None, clave_elector: str | None = None,
        qr_reverso: str | None = None, nombre_completo: dict | None = None,
        domicilio: dict | None = None, datos_electorales: dict | None = None,
        error_message: str | None = None, message: str = "",
    ) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO expediente (
                    id, lote_id, archivo, hash_archivo, estado, curp,
                    clave_elector, qr_reverso, nombre_completo, domicilio,
                    datos_electorales, mensaje_error, intentos,
                    iniciado_en, terminado_en
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    1, UTC_TIMESTAMP(6), UTC_TIMESTAMP(6)
                )
                """,
                (expediente_id, self.batch_id, filename, file_hash, status, curp,
                 clave_elector, qr_reverso, _json(nombre_completo), _json(domicilio),
                 _json(datos_electorales), error_message),
            )
            self._insert_log(cursor, expediente_id, filename, status, message)
        self.connection.commit()

    def record(self, *, filename: str, status: str, message: str = "", expediente_id: str | None = None) -> None:
        with self.connection.cursor() as cursor:
            self._insert_log(cursor, expediente_id, filename, status, message)
        self.connection.commit()

    def _insert_log(self, cursor, expediente_id, filename, status, message):
        cursor.execute(
            """
            INSERT INTO log_auditoria (expediente_id, lote_id, archivo, estado, mensaje)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (expediente_id, self.batch_id, filename, status, message),
        )


def _json(value: dict | None) -> str | None:
    return json.dumps(value, ensure_ascii=False) if value is not None else None
