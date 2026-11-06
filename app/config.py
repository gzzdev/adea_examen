from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    ocr_lang: str = os.getenv("OCR_LANG", "en")
    oracle_enabled: bool = os.getenv("ORACLE_ENABLED", "false").lower() == "true"
    oracle_user: str = os.getenv("ORACLE_USER", "")
    oracle_password: str = os.getenv("ORACLE_PASSWORD", "")
    oracle_dsn: str = os.getenv("ORACLE_DSN", "")
    oracle_procedure: str = os.getenv("ORACLE_PROCEDURE", "SP_REGISTRAR_EXPEDIENTE")
    sqlserver_enabled: bool = os.getenv("SQLSERVER_ENABLED", "false").lower() == "true"
    sqlserver_connection_string: str = os.getenv("SQLSERVER_CONNECTION_STRING", "")
