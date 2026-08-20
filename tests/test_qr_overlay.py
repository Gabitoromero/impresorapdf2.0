import sys
from pathlib import Path

from PIL import Image
from pypdf import PdfReader
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from qr_overlay import QR_MARGEN, calcular_posicion_qr, insertar_qr


def crear_qr_de_prueba(qr_path: Path) -> None:
    Image.new("RGB", (100, 100), color="black").save(qr_path)


def crear_pdf_de_prueba(pdf_path: Path, paginas: int, ancho: float, alto: float) -> None:
    pdf = canvas.Canvas(str(pdf_path), pagesize=(ancho, alto))
    for _ in range(paginas):
        pdf.drawString(50, alto - 50, "contenido de prueba")
        pdf.showPage()
    pdf.save()


def test_inserta_el_qr_en_todas_las_paginas(tmp_path):
    pdf_path = tmp_path / "salida.pdf"
    crear_pdf_de_prueba(pdf_path, paginas=2, ancho=612, alto=792)

    qr_path = tmp_path / "qr.png"
    crear_qr_de_prueba(qr_path)

    insertar_qr(pdf_path, qr_path)

    paginas = PdfReader(pdf_path).pages
    assert len(paginas) == 2
    for pagina in paginas:
        assert len(pagina.images) == 1


def test_qr_queda_en_la_esquina_inferior_izquierda():
    x, y = calcular_posicion_qr()
    assert x == QR_MARGEN
    assert y == QR_MARGEN
