"""Inserción de imagen QR en el PDF (Requisito: Parámetros de entrada)."""

import io
from pathlib import Path
from typing import Tuple

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

QR_ANCHO = 80
QR_ALTO = 80
QR_MARGEN = 15


def calcular_posicion_qr() -> Tuple[float, float]:
    """Esquina inferior izquierda del QR, fijo en la esquina inferior izquierda de la página.

    Va a la izquierda (no a la derecha) porque Marce agrega el código de barras
    del lado derecho de la hoja.
    """
    return QR_MARGEN, QR_MARGEN


def insertar_qr(pdf_path: Path, qr_image_path: Path) -> None:
    """Inserta la imagen QR (jpg/png) en todas las páginas del PDF, en la esquina inferior izquierda.

    La posición se calcula a partir del tamaño real de página del PDF (GhostPCL puede
    generar Letter, A4, u otro tamaño según lo que defina el driver PCL), en vez de
    asumir un tamaño de página fijo.
    """
    reader = PdfReader(str(pdf_path))
    primera_pagina = reader.pages[0]
    ancho_pagina = float(primera_pagina.mediabox.width)
    alto_pagina = float(primera_pagina.mediabox.height)
    x, y = calcular_posicion_qr()

    overlay_buffer = io.BytesIO()
    overlay_canvas = canvas.Canvas(overlay_buffer, pagesize=(ancho_pagina, alto_pagina))
    overlay_canvas.drawImage(str(qr_image_path), x, y, width=QR_ANCHO, height=QR_ALTO, mask="auto")
    overlay_canvas.save()
    overlay_buffer.seek(0)
    overlay_page = PdfReader(overlay_buffer).pages[0]

    writer = PdfWriter(clone_from=str(pdf_path))
    for pagina in writer.pages:
        pagina.merge_page(overlay_page)

    with open(pdf_path, "wb") as archivo_salida:
        writer.write(archivo_salida)
