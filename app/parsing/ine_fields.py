"""Extrae los campos visibles del anverso a partir de líneas OCR ordenadas."""

import re
import unicodedata


STATES = {
    "AGS": "AGUASCALIENTES", "BC": "BAJA CALIFORNIA", "BCS": "BAJA CALIFORNIA SUR",
    "CAMP": "CAMPECHE", "COAH": "COAHUILA", "COL": "COLIMA", "CHIS": "CHIAPAS",
    "CHIH": "CHIHUAHUA", "CDMX": "CIUDAD DE MEXICO", "DGO": "DURANGO",
    "GTO": "GUANAJUATO", "GRO": "GUERRERO", "HGO": "HIDALGO", "JAL": "JALISCO",
    "MEX": "MEXICO", "MICH": "MICHOACAN", "MOR": "MORELOS", "NAY": "NAYARIT",
    "NL": "NUEVO LEON", "OAX": "OAXACA", "PUE": "PUEBLA", "QRO": "QUERETARO",
    "Q RO": "QUERETARO", "QR": "QUINTANA ROO", "SLP": "SAN LUIS POTOSI",
    "SIN": "SINALOA", "SON": "SONORA", "TAB": "TABASCO", "TAMPS": "TAMAULIPAS",
    "TLAX": "TLAXCALA", "VER": "VERACRUZ", "YUC": "YUCATAN", "ZAC": "ZACATECAS",
}


def parse_front(lines: list[str]) -> dict:
    """Devuelve nombre, domicilio y datos electorales; ausentes quedan en None."""
    values = [_clean(line) for line in lines if _clean(line)]
    address = _parse_address(values)
    electoral = _parse_electoral(values)
    # El encabezado suele contener "MEXICO"; el estado del domicilio es una
    # señal más precisa cuando la credencial no imprime un campo electoral separado.
    if address["estado"]:
        electoral["estado"] = address["estado"]
    return {
        "nombre_completo": _parse_name(values),
        "domicilio": address,
        "datos_electorales": electoral,
    }


def _parse_name(values):
    index = _find(values, "NOMBRE")
    if index is None:
        return {"apellido_paterno": None, "apellido_materno": None, "nombres": None}
    stop_words = ("DOMICILIO", "CLAVE", "CURP", "FECHA")
    name_lines = []
    inline = values[index].split("NOMBRE", 1)[1].strip()
    if inline:
        name_lines.append(inline)
    for value in values[index + 1:]:
        if any(word in value for word in stop_words):
            break
        if value.startswith("SEXO"):
            continue
        if value not in {"NOMBRE", "MEXICO", "INSTITUTO NACIONAL ELECTORAL"}:
            name_lines.append(value)
        if len(name_lines) == 3:
            break
    paterno = name_lines[0] if len(name_lines) > 0 else None
    materno = name_lines[1] if len(name_lines) > 1 else None
    nombres = " ".join(name_lines[2:]) if len(name_lines) > 2 else None
    return {
        "valor": " ".join(part for part in (paterno, materno, nombres) if part) or None,
        "apellido_paterno": paterno,
        "apellido_materno": materno,
        "nombres": nombres,
    }


def _parse_address(values):
    index = _find(values, "DOMICILIO")
    address = {"calle": None, "numero_exterior": None, "numero_interior": None,
               "colonia": None, "codigo_postal": None, "alcaldia_municipio": None,
               "estado": None}
    if index is None:
        return address
    address_lines = []
    inline = re.sub(r"^.*?DOMICILIO\s*", "", values[index]).strip()
    if inline:
        address_lines.append(inline)
    for value in values[index + 1:]:
        if any(word in value for word in ("CLAVE", "CURP", "FECHA", "SECCION", "SECCION")):
            break
        address_lines.append(value)
    if not address_lines:
        return address

    street = re.sub(r"^(?:C|CALLE)\s*", "", address_lines[0]).strip()
    number_match = re.search(r"(?<!\d)(\d+[A-Z]?)(?:\s*[/\-]\s*([A-Z0-9]+))?\s*$", street)
    if number_match:
        address["numero_exterior"] = number_match.group(1)
        address["numero_interior"] = number_match.group(2)
        street = street[:number_match.start()].strip()
    address["calle"] = street or None

    for value in address_lines[1:]:
        postal = re.search(r"(?<!\d)\d{5}(?!\d)", value)
        if postal:
            address["codigo_postal"] = postal.group(0)
        if re.search(r"(?:^|\s)COL(?:ONIA)?(?:\s|$)", value) or value.startswith(("COL", "COLONIA")):
            colony = re.sub(r"^.*?COL(?:ONIA)?\s*", "", value).strip()
            address["colonia"] = re.sub(r"\s*\d{5}\s*$", "", colony).strip() or None
        municipality = re.search(r"(?:ALCALD[IÍ]A|MUNICIPIO)\s*[:\-]?\s*(.+)", value)
        if municipality:
            address["alcaldia_municipio"] = municipality.group(1).strip()

    address["estado"] = _find_state(address_lines)
    return address


def _parse_electoral(values):
    result = {"estado": None, "seccion": None, "municipio": None, "localidad": None,
              "anio_registro": None, "emision": None, "vigencia": None}
    for value in values:
        section = re.search(r"SECCI[ÓO]N\s*([0-9]{3,5})", value)
        if section:
            result["seccion"] = section.group(1)
        elif "SECCION" in value:
            following = _next_number(values, value, 3, 5)
            if following:
                result["seccion"] = following
        registration = re.search(r"A[NÑ]O\s*DE\s*REGISTR\w*\s*([0-9]{4})(?:\s*([0-9]{2}))?", value)
        if registration:
            result["anio_registro"] = registration.group(1)
            result["emision"] = registration.group(2)
        elif "ANODE" in value and "REGISTR" in value:
            following = _find_registration_number(values)
            if following:
                result["anio_registro"] = following[:4]
                result["emision"] = following[4:6] or None
        validity = re.search(r"(20[0-9]{2})\s*[-/]\s*(20[0-9]{2})", value)
        if validity:
            result["vigencia"] = f"{validity.group(1)}-{validity.group(2)}"
        municipality = re.search(r"(?:ALCALD[IÍ]A|MUNICIPIO)\s*[:\-]?\s*(.+)", value)
        if municipality:
            result["municipio"] = municipality.group(1).strip()
        locality = re.search(r"LOCALIDAD\s*[:\-]?\s*(.+)", value)
        if locality:
            result["localidad"] = locality.group(1).strip()
    result["estado"] = _find_state(values)
    return result


def _find_state(values):
    for value in values:
        compact = value.replace(" ", "")
        for abbreviation, state in STATES.items():
            if re.search(rf"\b{re.escape(abbreviation.replace(' ', ''))}\b", compact):
                return state
        for state in STATES.values():
            if state in value:
                return state
    return None


def _find(values, prefix):
    for index, value in enumerate(values):
        if prefix in value or (prefix == "NOMBRE" and value.startswith("NOM") and len(value) <= 7):
            return index
    return None


def _next_number(values, current, minimum, maximum):
    try:
        index = values.index(current)
    except ValueError:
        return None
    for value in values[index + 1:index + 9]:
        match = re.fullmatch(r"\d{%d,%d}" % (minimum, maximum), value)
        if match:
            return match.group(0)
    return None


def _find_registration_number(values):
    """Busca el token YY/EE aunque Paddle lo devuelva lejos de la etiqueta."""
    for value in values:
        if re.fullmatch(r"20\d{4}", value):
            return value
    return None


def _clean(value):
    normalized = unicodedata.normalize("NFKD", value.upper())
    return "".join(char for char in normalized if not unicodedata.combining(char)).strip()
