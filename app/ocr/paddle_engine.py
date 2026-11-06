"""Adaptador pequeño para los resultados de PaddleOCR 3.x."""

import re
import cv2
from paddleocr import PaddleOCR


def create_reader(language: str):
    language = {"eng": "en", "spa": "es"}.get(language.lower(), language.lower())
    return PaddleOCR(
        lang=language,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False,
    )


def read_lines(reader, image):
    """Devuelve (texto, caja xyxy) en orden de lectura."""
    if image is None or image.size == 0:
        return []
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    lines = []
    for result in reader.predict(image):
        data = result.json
        if callable(data):
            data = data()
        data = data.get("res", data)
        texts = data.get("rec_texts", [])
        boxes = data.get("rec_boxes", [])
        polygons = data.get("rec_polys", [])
        for index, text in enumerate(texts):
            if not text or not text.strip():
                continue
            if index < len(boxes):
                x0, y0, x1, y1 = (int(v) for v in boxes[index])
            elif index < len(polygons):
                points = polygons[index]
                x0, y0 = (int(min(p[0] for p in points)), int(min(p[1] for p in points)))
                x1, y1 = (int(max(p[0] for p in points)), int(max(p[1] for p in points)))
            else:
                continue
            lines.append((re.sub(r"\s+", " ", text.strip()), (x0, y0, x1, y1)))
    return sorted(lines, key=lambda item: (item[1][1], item[1][0]))
