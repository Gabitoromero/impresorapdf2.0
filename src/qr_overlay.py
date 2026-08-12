"""Inserción de imagen QR en el PDF (Requisito: Parámetros de entrada)."""

import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ANCHO_PAGINA, ALTO_PAGINA = A4

QR_ANCHO = 100
QR_ALTO = 100
QR_MARGEN = 40


def insertar_qr(pdf_path: Path, qr_image_path: Path) -> None:
    """Inserta la imagen QR (jpg/png) en la última página del PDF, en la esquina inferior derecha."""
    x = ANCHO_PAGINA - QR_MARGEN - QR_ANCHO
    y = QR_MARGEN

    overlay_buffer = io.BytesIO()
    overlay_canvas = canvas.Canvas(overlay_buffer, pagesize=A4)
    overlay_canvas.drawImage(str(qr_image_path), x, y, width=QR_ANCHO, height=QR_ALTO, mask="auto")
    overlay_canvas.save()
    overlay_buffer.seek(0)
    overlay_page = PdfReader(overlay_buffer).pages[0]

    writer = PdfWriter(clone_from=str(pdf_path))
    writer.pages[-1].merge_page(overlay_page)

    with open(pdf_path, "wb") as archivo_salida:
        writer.write(archivo_salida)
