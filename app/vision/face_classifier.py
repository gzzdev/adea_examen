import re

import cv2

from app.ocr.paddle_engine import read_lines
from app.vision.qr_reader import read_reverse_qr


FRONT_MARKERS = (
    "INSTITUTONACIONALELECTORAL",
    "CREDENCIALPARAVOTAR",
    "CLAVEDEELECTOR",
    "CURP",
)


def classify_faces(candidates, ocr):
    """Orienta las tarjetas y devuelve anverso, reverso y líneas del anverso."""
    classified = []
    for candidate in candidates:
        # El QR se puede leer en cualquier giro, por lo que basta intentarlo una vez.
        has_qr = bool(read_reverse_qr(candidate))
        image, lines = _upright(candidate, ocr)
        compact = _compact(lines)
        classified.append({
            "image": image,
            "lines": lines,
            "front_markers": sum(marker in compact for marker in FRONT_MARKERS),
            "is_reverse": has_qr or "IDMEX" in compact or compact.count("<") >= 3,
        })

    front = max(classified, key=lambda face: face["front_markers"])
    if front["front_markers"] == 0:
        raise ValueError("Ninguna cara localizada contiene las etiquetas del anverso de una INE")

    # El reverso es opcional: una imagen puede contener únicamente el anverso.
    reverse = next((face for face in classified if face is not front and face["is_reverse"]), None)
    return front["image"], reverse["image"] if reverse else None, front["lines"]


def _upright(image, ocr):
    """Elige entre 0° y 180° según las señales legibles del documento."""
    options = []
    for candidate in (image, cv2.rotate(image, cv2.ROTATE_180)):
        lines = read_lines(ocr, candidate)
        compact = _compact(lines)
        marker_count = sum(marker in compact for marker in FRONT_MARKERS)
        marker_count += int("IDMEX" in compact) + int(compact.count("<") >= 3)
        # La cantidad de texto solo desempata cuando ambas orientaciones tienen
        # las mismas señales conocidas.
        options.append((marker_count, len(compact), candidate, lines))
    _, _, oriented, lines = max(options, key=lambda option: option[:2])
    return oriented, lines


def _compact(lines):
    return re.sub(r"[^A-Z0-9<]", "", "".join(text for text, _ in lines).upper())
