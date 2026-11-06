import re
from pathlib import Path

import cv2

from app.models.results import ExtractionResult
from app.ocr.paddle_engine import read_lines
from app.parsing import clave_elector, curp
from app.parsing.ine_fields import parse_front
from app.vision.preprocessing import load_and_preprocess
from app.vision.qr_reader import read_reverse_qr


INE_KEYWORDS = (
    "INSTITUTO NACIONAL ELECTORAL",
    "CREDENCIAL PARA VOTAR",
    "CLAVE DE ELECTOR",
    "CURP",
)


def extract_image(path: Path, reader, debug_dir: Path | None = None) -> ExtractionResult:
    images = load_and_preprocess(path, reader)
    if debug_dir is not None:
        for name, image in (
            ("front_face", images["front_face"]),
            ("reverse_face", images["reverse_face"]),
            ("curp", images["curp"]["enhanced"] if images["curp"] else None),
            ("curp_binary", images["curp"]["binary"] if images["curp"] else None),
            ("key", images["key"]),
            ("front", images["front"]),
        ):
            if image is not None:
                cv2.imwrite(str(debug_dir / f"{path.stem}_{name}.png"), image)

    texts = [text for text, _ in images["front_lines"]]
    focused = []
    if images["curp"]:
        focused.extend((images["curp"]["enhanced"], images["curp"]["binary"]))
    if images["key"] is not None:
        focused.append(images["key"])
    for image in (images["front_face"], *focused):
        texts.extend(text for text, _ in read_lines(reader, image))

    compact = re.sub(r"[^A-Z0-9]", "", "".join(texts).upper())
    keyword_count = sum(re.sub(r"[^A-Z0-9]", "", word) in compact
                        for word in INE_KEYWORDS)
    curp_value = curp.extract(texts)
    clave_value = clave_elector.extract(texts)
    # Las pasadas enfocadas pueden recuperar líneas de nombre y domicilio que
    # no aparecieron en la primera detección usada para orientar la cara.
    front_fields = parse_front(texts)
    return ExtractionResult(
        is_ine=keyword_count >= 2 or bool(curp_value and clave_value),
        curp=curp_value,
        clave_elector=clave_value,
        qr_reverso=read_reverse_qr(images["qr_source"]),
        nombre_completo=front_fields["nombre_completo"],
        domicilio=front_fields["domicilio"],
        datos_electorales=front_fields["datos_electorales"],
    )
