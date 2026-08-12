import sys
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from qr_overlay import insertar_qr
from txt_to_pdf import convertir_txt_a_pdf


def crear_qr_de_prueba(qr_path: Path) -> None:
    Image.new("RGB", (100, 100), color="black").save(qr_path)


def test_inserta_el_qr_en_todas_las_paginas(tmp_path):
    txt_path = tmp_path / "entrada.txt"
    txt_path.write_text("\n".join(f"linea {i}" for i in range(100)))  # fuerza 2+ páginas

    pdf_path = tmp_path / "salida.pdf"
    convertir_txt_a_pdf(txt_path, pdf_path)

    qr_path = tmp_path / "qr.png"
    crear_qr_de_prueba(qr_path)

    insertar_qr(pdf_path, qr_path)

    paginas = PdfReader(pdf_path).pages
    assert len(paginas) > 1

    for pagina in paginas:
        assert len(pagina.images) == 1
