"""Procesamiento paralelo de imágenes con actores Ray."""

from dataclasses import asdict
from pathlib import Path

import ray

from app.ocr.paddle_engine import create_reader
from app.services.extraction_service import extract_image


def process_batch(paths: list[Path], *, workers: int, debug_dir: Path | None, ocr_lang: str) -> list[dict]:
    ray.init(ignore_reinit_error=True, include_dashboard=False)
    actors = [OCRWorker.remote(ocr_lang) for _ in range(max(1, workers))]
    futures = [
        actors[index % len(actors)].process.remote(
            str(path), str(debug_dir) if debug_dir is not None else None
        )
        for index, path in enumerate(paths)
    ]
    results = ray.get(futures)
    ray.shutdown()
    return results

@ray.remote(num_cpus=1)
class OCRWorker:
    def __init__(self, ocr_lang: str):
        self.reader = create_reader(ocr_lang)

    def process(self, path: str, debug_dir: str | None) -> dict:
        image_path = Path(path)
        try:
            result = extract_image(
                image_path,
                self.reader,
                Path(debug_dir) if debug_dir else None,
            )
            return {"ruta": path, "archivo": image_path.name, "ok": True, **asdict(result)}
        except Exception as exc:
            return {"ruta": path, "archivo": image_path.name, "ok": False, "error": str(exc)}
