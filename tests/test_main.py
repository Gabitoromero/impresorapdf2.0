import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from pypdf import PdfReader

SRC_MAIN = Path(__file__).resolve().parent.parent / "src" / "main.py"

GPCL6_BIN = os.environ.get("GPCL6_BIN", "gpcl6")
_gpcl6_disponible = shutil.which(GPCL6_BIN) is not None or Path(GPCL6_BIN).is_file()

pytestmark = pytest.mark.skipif(
    not _gpcl6_disponible,
    reason="gpcl6 no disponible en este entorno (definir GPCL6_BIN o instalarlo en PATH)",
)


def test_convierte_sin_qr_no_falla_y_no_agrega_imagenes(tmp_path):
    txt_path = tmp_path / "entrada.txt"
    txt_path.write_text("Hola Marce\nSegunda linea del texto")

    pdf_path = tmp_path / "salida.pdf"

    resultado = subprocess.run(
        [sys.executable, str(SRC_MAIN), "--txt", str(txt_path), "--out", str(pdf_path)],
        capture_output=True,
        text=True,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert pdf_path.exists()

    pagina = PdfReader(pdf_path).pages[0]
    assert len(pagina.images) == 0


def test_avisa_por_stderr_si_codigo_de_barras_no_tiene_40_digitos(tmp_path):
    prefijo_codigo_barras = bytes([27, 40, 66, 46, 1, 2, 2, 254])  # ESC(B + 5 bytes de parametros
    txt_path = tmp_path / "entrada.txt"
    txt_path.write_bytes(b"Hola Marce\n" + prefijo_codigo_barras + b"30707191\x0c")

    pdf_path = tmp_path / "salida.pdf"

    resultado = subprocess.run(
        [sys.executable, str(SRC_MAIN), "--txt", str(txt_path), "--out", str(pdf_path)],
        capture_output=True,
        text=True,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert "8 dígitos" in resultado.stderr
    assert "40" in resultado.stderr
