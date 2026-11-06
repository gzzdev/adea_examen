import argparse
import json
from pathlib import Path

from app.config import Settings
from app.ocr.paddle_engine import create_reader
from app.services.extraction_service import extract_image
from app.services.repositories import (
    FileAuditRepository,
    MariaDbAuditRepository,
)
from app.vision.preprocessing import discover_images


def main() -> None:
    parser = argparse.ArgumentParser(description="Extracción batch de credenciales INE")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("resultados"))
    parser.add_argument("--save-debug-images", action="store_true")
    args = parser.parse_args()
    args.input = args.input.resolve()
    args.output = args.output.resolve()

    settings = Settings()
    args.output.mkdir(parents=True, exist_ok=True)
    audit = (MariaDbAuditRepository(
                 host=settings.db_host,
                 port=settings.db_port,
                 database=settings.db_database,
                 user=settings.db_user,
                 password=settings.db_password,
             ) if settings.db_enabled else FileAuditRepository(args.output / "audit.csv"))
    reader = create_reader(settings.ocr_lang)

    records = []
    for path in discover_images(args.input):
        try:
            result = extract_image(path, reader, args.output if args.save_debug_images else None)
            if not result.is_ine:
                audit.record(filename=path.name, status="INVALIDO",
                             message="No se detectaron suficientes elementos de INE")
                continue

            status = "PROCESADO" if result.curp and result.clave_elector else "PENDIENTE_VALIDACION"
            records.append({
                "archivo": path.name,
                "es_ine": True,
                "curp": result.curp,
                "clave_elector": result.clave_elector,
                "qr_reverso": result.qr_reverso,
                "nombre_completo": result.nombre_completo,
                "domicilio": result.domicilio,
                "datos_electorales": result.datos_electorales,
                "estado": status,
            })
            audit.record(filename=path.name, status=status,
                         message="QR reverso leído" if result.qr_reverso else "QR reverso no detectado")
        except Exception as exc:
            audit.record(filename=path.name, status="ERROR", message=str(exc))

    output_file = args.output / "registros.json"
    output_file.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Procesadas: {len(records)}. Resultado: {output_file}")


if __name__ == "__main__":
    main()
