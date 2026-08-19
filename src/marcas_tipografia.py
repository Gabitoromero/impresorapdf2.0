"""Parseo de marcas de tipografía del TXT (ver docs/formato-marcas-tipografia.md).

Sintaxis: {{flags:texto}}, con flags separados por coma: `b` (negrita),
`i` (cursiva), un número (tamaño en puntos) o una fuente
(`helvetica`/`times`/`courier`).
"""

import re
from dataclasses import dataclass

TAMANIO_DEFECTO = 12

FUENTES_VALIDAS = {"helvetica", "times", "courier"}

_MARCA = re.compile(r"\{\{([^:{}]+):([^{}]*)\}\}")

_NOMBRES_FUENTE = {
    "helvetica": {
        (False, False): "Helvetica",
        (True, False): "Helvetica-Bold",
        (False, True): "Helvetica-Oblique",
        (True, True): "Helvetica-BoldOblique",
    },
    "times": {
        (False, False): "Times-Roman",
        (True, False): "Times-Bold",
        (False, True): "Times-Italic",
        (True, True): "Times-BoldItalic",
    },
    "courier": {
        (False, False): "Courier",
        (True, False): "Courier-Bold",
        (False, True): "Courier-Oblique",
        (True, True): "Courier-BoldOblique",
    },
}


@dataclass
class Tramo:
    texto: str
    negrita: bool = False
    cursiva: bool = False
    tamanio: int | None = None
    fuente: str = "helvetica"


def parsear_marcas(linea: str) -> list[Tramo]:
    """Separa una línea de texto en tramos según las marcas {{flags:texto}} que tenga."""
    tramos = []
    pos = 0

    for coincidencia in _MARCA.finditer(linea):
        if coincidencia.start() > pos:
            tramos.append(Tramo(texto=linea[pos : coincidencia.start()]))

        flags_crudos, texto = coincidencia.group(1), coincidencia.group(2)
        negrita = False
        cursiva = False
        tamanio = None
        fuente = "helvetica"

        for flag in flags_crudos.split(","):
            flag = flag.strip()
            if flag == "b":
                negrita = True
            elif flag == "i":
                cursiva = True
            elif flag in FUENTES_VALIDAS:
                fuente = flag
            elif flag.isdigit():
                tamanio = int(flag)

        tramos.append(
            Tramo(texto=texto, negrita=negrita, cursiva=cursiva, tamanio=tamanio, fuente=fuente)
        )
        pos = coincidencia.end()

    if pos < len(linea):
        tramos.append(Tramo(texto=linea[pos:]))

    return tramos


def nombre_fuente_reportlab(tramo: Tramo) -> str:
    """Traduce un Tramo a un nombre de fuente base de ReportLab (una de las 14 estándar)."""
    return _NOMBRES_FUENTE[tramo.fuente][(tramo.negrita, tramo.cursiva)]
