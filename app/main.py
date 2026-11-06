import argparse
import hashlib
import json
import uuid
from pathlib import Path

from app.config import Settings
from app.services.ray_processor import process_batch
from app.services.repositories import FileAuditRepository, MariaDbRepository
from app.vision.preprocessing import discover_images


def main() -> None:
    parser = argparse.ArgumentParser(description="Extracción batch de credenciales INE")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("resultados"))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--save-debug-images", action="store_true")
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers debe ser mayor que cero")

    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    settings = Settings()
    repository = (MariaDbRepository(
        host=settings.db_host, port=settings.db_port, database=settings.db_database,
        user=settings.db_user, password=settings.db_password,
    ) if settings.db_enabled else FileAuditRepository(output_dir / "audit.csv"))

    pending = []
    for path in discover_images(args.input.resolve()):
        file_hash = _sha256(path)
        if isinstance(repository, MariaDbRepository):
            previous = repository.find_by_hash(file_hash)
            if previous:
                repository.record(
                    filename=path.name, status="DUPLICADO", expediente_id=previous["id"],
                    message=f"Imagen ya recibida como {previous['archivo']} ({previous['estado']})",
                )
                continue
        pending.append((path, file_hash))

    results = process_batch(
        [path for path, _ in pending], workers=args.workers,
        debug_dir=output_dir if args.save_debug_images else None,
        ocr_lang=settings.ocr_lang,
    ) if pending else []
    hashes = {str(path): file_hash for path, file_hash in pending}
    records = []
    for result in results:
        filename = result["archivo"]
        file_hash = hashes[result["ruta"]]
        if not result["ok"]:
            _save_error(repository, filename, file_hash, result["error"])
            continue

        status = ("INVALIDO" if not result["is_ine"] else
                  "PROCESADO" if result["curp"] and result["clave_elector"]
                  else "PENDIENTE_VALIDACION")
        message = ("No se detectaron suficientes elementos de INE" if status == "INVALIDO"
                   else "QR reverso leído" if result["qr_reverso"]
                   else "QR reverso no detectado")
        if status != "INVALIDO":
            records.append({
                "archivo": filename, "es_ine": True, "curp": result["curp"],
                "clave_elector": result["clave_elector"], "qr_reverso": result["qr_reverso"],
                "nombre_completo": result["nombre_completo"], "domicilio": result["domicilio"],
                "datos_electorales": result["datos_electorales"], "estado": status,
            })
        _save_result(repository, result, file_hash, status, message)

    output_file = output_dir / "registros.json"
    output_file.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Procesadas: {len(results)}. Pendientes enviadas a Ray: {len(pending)}. Resultado: {output_file}")


def _save_result(repository, result, file_hash, status, message):
    if isinstance(repository, MariaDbRepository):
        repository.save_expediente(
            expediente_id=str(uuid.uuid4()), filename=result["archivo"], file_hash=file_hash,
            status=status, curp=result["curp"], clave_elector=result["clave_elector"],
            qr_reverso=result["qr_reverso"], nombre_completo=result["nombre_completo"],
            domicilio=result["domicilio"], datos_electorales=result["datos_electorales"],
            message=message,
        )
    else:
        repository.record(filename=result["archivo"], status=status, message=message)


def _save_error(repository, filename, file_hash, message):
    if isinstance(repository, MariaDbRepository):
        repository.save_expediente(
            expediente_id=str(uuid.uuid4()), filename=filename, file_hash=file_hash,
            status="ERROR", error_message=message, message=message,
        )
    else:
        repository.record(filename=filename, status="ERROR", message=message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
