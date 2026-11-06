import re

import cv2
import numpy as np

CARD_WIDTH = 856
CARD_HEIGHT = 540


def detect_and_normalize_faces(image):
    """Devuelve las tarjetas encontradas, corregidas a formato horizontal."""
    faces = _card_candidates(image)
    if not faces:
        raise ValueError("No se localizaron caras de credencial en la imagen")
    
    return faces


def select_field_regions(front, lines):
    """Recorta CURP y clave usando las cajas de sus etiquetas."""
    regions = {"curp": None, "key": None}
    height, width = front.shape[:2]
    for text, (x, y, right, bottom) in lines:
        word = re.sub(r"[^A-Z0-9]", "", text.upper())
        kind = "curp" if "CURP" in word else "key" if "ELECTOR" in word else None
        if not kind or regions[kind] is not None:
            continue
        box_height = max(1, bottom - y)
        if kind == "curp":
            x0, x1 = max(0, x - box_height), min(width, x + int(width * .55))
            y0 = min(height, bottom)
            y1 = min(height, y0 + box_height * 3)
        else:
            x0, x1 = min(width, right), min(width, right + int(width * .48))
            y0, y1 = max(0, y - box_height), min(height, bottom + box_height)
        regions[kind] = front[y0:y1, x0:x1]

    return regions["curp"], regions["key"]


def _card_candidates(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    edges = cv2.Canny(gray, 35, 130)
    image_area = image.shape[0] * image.shape[1]
    short_side = min(image.shape[:2])
    long_kernel = max(9, int(short_side * .012)) | 1
    short_kernel = max(5, int(short_side * .005)) | 1
    contours = []
    for size in ((long_kernel, short_kernel), (short_kernel, long_kernel)):
        closed = cv2.morphologyEx(
            edges, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, size), iterations=2
        )
        found, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours.extend(found)

    pairs = []
    detected = []
    for contour in contours:
        rect = cv2.minAreaRect(contour)
        (_, _), (width, height), _ = rect
        if min(width, height) < 80:
            continue
        area = width * height
        ratio = max(width, height) / min(width, height)
        if cv2.contourArea(contour) / area < .18:
            continue
        box = cv2.boxPoints(rect).astype("float32")
        bounds = cv2.boundingRect(box.astype("int32"))
        if .03 <= area / image_area <= .75 and 2.45 <= ratio <= 3.85:
            if not any(_iou(bounds, previous[0]) > .70 for previous in pairs):
                strip = _warp_rectangle(image, box, CARD_WIDTH * 2, CARD_HEIGHT)
                pairs.append((bounds, [strip[:, :CARD_WIDTH], strip[:, CARD_WIDTH:]]))
            continue
        if not (.015 <= area / image_area <= .65 and 1.30 <= ratio <= 1.95):
            continue
        if any(_iou(bounds, previous[0]) > .55 for previous in detected):
            continue
        detected.append((bounds, _warp_card(image, box)))

    if pairs:
        # Una franja de dos credenciales conserva mejor el anverso cuando su
        # borde individual es tenue. Se toma la de mayor área.
        _, cards = max(pairs, key=lambda item: item[0][2] * item[0][3])
        return cards
    return [card for _, card in sorted(detected, key=lambda item: item[0][0])]


def _warp_card(image, points):
    return _warp_rectangle(image, points, CARD_WIDTH, CARD_HEIGHT)


def _warp_rectangle(image, points, target_width, target_height):
    ordered = _order_points(points)
    top_left, top_right, bottom_right, bottom_left = ordered
    horizontal = max(np.linalg.norm(top_right - top_left), np.linalg.norm(bottom_right - bottom_left))
    vertical = max(np.linalg.norm(bottom_left - top_left), np.linalg.norm(bottom_right - top_right))
    if vertical > horizontal:
        ordered = np.array([bottom_left, top_left, top_right, bottom_right], dtype="float32")
    destination = np.array(
        [[0, 0], [target_width - 1, 0],
         [target_width - 1, target_height - 1], [0, target_height - 1]],
        dtype="float32",
    )
    return cv2.warpPerspective(
        image, cv2.getPerspectiveTransform(ordered, destination), (target_width, target_height)
    )


def _order_points(points):
    ordered = np.zeros((4, 2), dtype="float32")
    sums = points.sum(axis=1)
    differences = np.diff(points, axis=1).reshape(-1)
    ordered[0], ordered[2] = points[np.argmin(sums)], points[np.argmax(sums)]
    ordered[1], ordered[3] = points[np.argmin(differences)], points[np.argmax(differences)]
    return ordered


def _iou(first, second):
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    left, top = max(ax, bx), max(ay, by)
    right, bottom = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    intersection = max(0, right - left) * max(0, bottom - top)
    union = aw * ah + bw * bh - intersection
    return intersection / union if union else 0
