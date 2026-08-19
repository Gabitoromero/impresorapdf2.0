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


def test_soporta_txt_no_utf8_con_caracteres_acentuados(tmp_path):
    txt_path = tmp_path / "entrada.txt"
    txt_path.write_bytes("Factura para LEÑADOR".encode("latin-1"))

    pdf_path = tmp_path / "salida.pdf"
    convertir_txt_a_pdf(txt_path, pdf_path)

    assert pdf_path.exists()


def test_limpia_codigos_de_control_antes_de_dibujar(tmp_path):
    txt_path = tmp_path / "entrada.txt"
    txt_path.write_bytes(
        "\x1bE\x1b&k2G\x1b&l0OFACTURA A\x1b(s3B".encode("latin-1")
    )

    pdf_path = tmp_path / "salida.pdf"
    convertir_txt_a_pdf(txt_path, pdf_path)

    assert pdf_path.exists()


def test_interpreta_marcas_de_tipografia_y_deja_el_texto_sin_marcas(tmp_path):
    txt_path = tmp_path / "entrada.txt"
    txt_path.write_text("{{b:FACTURA A}}  {{i:Original}}  {{b,14,times:TOTAL}}")

    pdf_path = tmp_path / "salida.pdf"
    convertir_txt_a_pdf(txt_path, pdf_path)

    texto_extraido = PdfReader(pdf_path).pages[0].extract_text()
    assert "{{" not in texto_extraido
    assert "FACTURA A" in texto_extraido
    assert "Original" in texto_extraido
    assert "TOTAL" in texto_extraido
