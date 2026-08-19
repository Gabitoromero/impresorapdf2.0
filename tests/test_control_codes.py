import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from control_codes import limpiar_codigos_control


def test_no_toca_texto_sin_codigos_de_control():
    texto = "Hola Marce\nSegunda linea del texto"

    assert limpiar_codigos_control(texto) == texto


def test_elimina_secuencias_pcl_reales():
    crudo = (
        "\x1bE\x1b&k2G\x1b&l0O\x1b&l1E\x1b&l68F\x1b(10U\x1b&l26D\x1b(s0S "
        "\x1b&k0S \x1b(s1S \x1b(s3B\n\n   ROGELIO DIEZ S.R.L\n"
        "\x1b&k4S \x1b(s-1B                                                          FACTURA  A"
    )

    limpio = limpiar_codigos_control(crudo)

    assert "\x1b" not in limpio
    assert "ROGELIO DIEZ S.R.L" in limpio
    assert "FACTURA  A" in limpio


def test_elimina_secuencias_escp_reales():
    crudo = (
        "\x1b@\x1bC@\x12\x12\r\n                                                "
        "\x1bEF A C T U R A\x1bF\r\n\r\n  "
    )

    limpio = limpiar_codigos_control(crudo)

    assert "\x1b" not in limpio
    assert "F A C T U R A" in limpio


def test_conserva_saltos_de_linea_y_tabs():
    texto = "linea 1\nlinea 2\r\ncon\ttab"

    assert limpiar_codigos_control(texto) == texto
