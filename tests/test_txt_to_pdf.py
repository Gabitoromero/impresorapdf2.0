import os
import re
import shutil
import sys
from pathlib import Path

import pytest
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from txt_to_pdf import convertir_txt_a_pdf

GPCL6_BIN = os.environ.get("GPCL6_BIN", "gpcl6")
_gpcl6_disponible = shutil.which(GPCL6_BIN) is not None or Path(GPCL6_BIN).is_file()

pytestmark = pytest.mark.skipif(
    not _gpcl6_disponible,
    reason="gpcl6 no disponible en este entorno (definir GPCL6_BIN o instalarlo en PATH)",
)


def test_genera_un_pdf_no_vacio_a_partir_de_un_txt_plano(tmp_path):
    txt_path = tmp_path / "entrada.txt"
    txt_path.write_text("Hola Marce\nSegunda linea del texto")

    pdf_path = tmp_path / "salida.pdf"
    convertir_txt_a_pdf(txt_path, pdf_path)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0


def test_interpreta_comandos_pcl_reales_y_deja_el_texto_legible(tmp_path):
    txt_path = tmp_path / "entrada.txt"
    # ESC E = reset de impresora HP PCL, comando real que inyecta Progress.
    txt_path.write_bytes(b"\x1bEFACTURA A\n")

    pdf_path = tmp_path / "salida.pdf"
    convertir_txt_a_pdf(txt_path, pdf_path)

    texto = PdfReader(pdf_path).pages[0].extract_text()
    assert "FACTURA A" in texto
    assert "\x1b" not in texto


def test_genera_pdf_en_tamanio_a4_por_defecto(tmp_path):
    txt_path = tmp_path / "entrada.txt"
    txt_path.write_text("Hola Marce")

    pdf_path = tmp_path / "salida.pdf"
    convertir_txt_a_pdf(txt_path, pdf_path)

    mediabox = PdfReader(pdf_path).pages[0].mediabox
    assert abs(float(mediabox.width) - 595) < 5
    assert abs(float(mediabox.height) - 842) < 5


def test_traduce_chr15_chr18_a_cambio_de_tamanio_real(tmp_path):
    txt_path = tmp_path / "entrada.txt"
    # CHR(15)/CHR(18): toggle de modo condensado que usa Marce (no es PCL válido).
    txt_path.write_bytes(b"\x1bEnormal\x0fcondensado\x12normal de nuevo\n")

    pdf_path = tmp_path / "salida.pdf"
    convertir_txt_a_pdf(txt_path, pdf_path)

    contenido = PdfReader(pdf_path).pages[0].get_contents().get_data()
    tamanios_usados = set(re.findall(rb"/R\d+ ([\d.]+) Tf", contenido))
    assert len(tamanios_usados) > 1

    texto = PdfReader(pdf_path).pages[0].extract_text()
    assert "normal" in texto
    assert "condensado" in texto


def test_lanza_error_si_el_txt_de_entrada_no_existe(tmp_path):
    pdf_path = tmp_path / "salida.pdf"

    with pytest.raises(FileNotFoundError):
        convertir_txt_a_pdf(Path("/ruta/que/no/existe.txt"), pdf_path)
