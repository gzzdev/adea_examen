from pathlib import Path

import cv2

from app.vision.face_classifier import classify_faces
from app.vision.roi import detect_and_normalize_faces, select_field_regions


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def discover_images(input_dir: Path) -> list[Path]:
    if input_dir.is_file():
        return [input_dir] if input_dir.suffix.lower() in SUPPORTED_EXTENSIONS else []
    return sorted(path for path in input_dir.rglob("*")
                  if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS)


def load_and_preprocess(path: Path, ocr) -> dict:
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"No se pudo leer la imagen: {path}")
    candidates = detect_and_normalize_faces(image)
    front, reverse, front_lines = classify_faces(candidates, ocr)
    curp_region, key_region = select_field_regions(front, front_lines)
    return {
        "front_face": front,
        "reverse_face": reverse,
        "front_lines": front_lines,
        "front": enhance(front, scale=2)["enhanced"],
        "curp": enhance(curp_region, scale=3) if curp_region is not None else None,
        "key": enhance(key_region, scale=3)["enhanced"] if key_region is not None else None,
        "qr_source": reverse if reverse is not None else image,
    }


def enhance(image, scale=1) -> dict:
    if image.size == 0:
        raise ValueError("ROI vacío durante el preprocesamiento")
    if scale != 1:
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    denoised = cv2.fastNlMeansDenoising(gray, None, 5, 7, 21)
    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(denoised)
    block_size = min(91, max(31, 31 * scale))
    if block_size % 2 == 0:
        block_size -= 1
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, block_size, 11,
    )
    return {"enhanced": enhanced, "binary": binary}
