import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from txt_to_pdf import convertir_txt_a_pdf


def test_genera_un_pdf_no_vacio_a_partir_de_un_txt(tmp_path):
    txt_path = tmp_path / "entrada.txt"
    txt_path.write_text("Hola Marce\nSegunda linea del texto")

    pdf_path = tmp_path / "salida.pdf"

    convertir_txt_a_pdf(txt_path, pdf_path)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0


def test_txt_con_pocas_lineas_genera_una_sola_pagina(tmp_path):
    txt_path = tmp_path / "entrada.txt"
    txt_path.write_text("\n".join(f"linea {i}" for i in range(5)))

    pdf_path = tmp_path / "salida.pdf"
    convertir_txt_a_pdf(txt_path, pdf_path)

    assert len(PdfReader(pdf_path).pages) == 1


def test_txt_largo_hace_salto_de_pagina_automatico(tmp_path):
    txt_path = tmp_path / "entrada.txt"
    txt_path.write_text("\n".join(f"linea {i}" for i in range(100)))

    pdf_path = tmp_path / "salida.pdf"
    convertir_txt_a_pdf(txt_path, pdf_path)

    assert len(PdfReader(pdf_path).pages) > 1
