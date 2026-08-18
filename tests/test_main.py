import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

SRC_MAIN = Path(__file__).resolve().parent.parent / "src" / "main.py"


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
