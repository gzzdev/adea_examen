from dataclasses import dataclass


@dataclass
class ExtractionResult:
    is_ine: bool
    curp: str | None
    clave_elector: str | None
    qr_reverso: str | None
