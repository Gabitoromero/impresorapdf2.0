"""Lectura de TXT y generación básica de PDF (Requisito: Formato salida PDF)."""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ANCHO_PAGINA, ALTO_PAGINA = A4
MARGEN_IZQUIERDO = 40
MARGEN_SUPERIOR = 40
ALTO_LINEA = 14


def convertir_txt_a_pdf(txt_path: Path, pdf_path: Path) -> None:
    """Lee un archivo TXT y genera un PDF con el mismo contenido, una línea del txt por línea del PDF."""
    lineas = txt_path.read_text().splitlines()

    pdf = canvas.Canvas(str(pdf_path), pagesize=A4)
    y = ALTO_PAGINA - MARGEN_SUPERIOR

    for linea in lineas:
        pdf.drawString(MARGEN_IZQUIERDO, y, linea)
        y -= ALTO_LINEA

    pdf.save()
