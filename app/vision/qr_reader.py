import cv2
import zxingcpp


def read_reverse_qr(image) -> str | None:
    if image is None or image.size == 0:
        return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    enlarged = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    variants = (
        enlarged,
        cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(enlarged),
        cv2.threshold(enlarged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
    )
    for variant in variants:
        for barcode in zxingcpp.read_barcodes(variant):
            if "qr" in str(barcode.format).lower() and barcode.text:
                return barcode.text.strip() or None
    return None
