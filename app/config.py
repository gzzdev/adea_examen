from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    ocr_lang: str = os.getenv("OCR_LANG", "en")
    db_enabled: bool = os.getenv("DB_ENABLED", "false").lower() == "true"
    db_host: str = os.getenv("DB_HOST", "127.0.0.1")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_database: str = os.getenv("DB_DATABASE", "adea")
    db_user: str = os.getenv("DB_USER", "adea")
    db_password: str = os.getenv("DB_PASSWORD", "")
