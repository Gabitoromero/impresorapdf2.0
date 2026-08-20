import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pcl_preprocessor import traducir_toggle_condensado

PCL_CONDENSADO = b"\x1b&k2S"  # wlcsi en setlaser.i: "LETRA COMPRIMIDA 16.67"
PCL_NORMAL = b"\x1b&k0S"  # wlcno en setlaser.i: "DESCOMPRIMIR LETRA"


def test_no_toca_datos_sin_chr15_ni_chr18():
    datos = b"\x1bEFACTURA A\ntexto normal"

    assert traducir_toggle_condensado(datos) == datos


def test_chr15_se_traduce_a_pitch_condensado_pcl():
    datos = b"antes\x0fdespues"

    resultado = traducir_toggle_condensado(datos)

    assert resultado == b"antes" + PCL_CONDENSADO + b"despues"
    assert b"\x0f" not in resultado


def test_chr18_se_traduce_a_pitch_normal_pcl():
    datos = b"antes\x12despues"

    resultado = traducir_toggle_condensado(datos)

    assert resultado == b"antes" + PCL_NORMAL + b"despues"
    assert b"\x12" not in resultado


def test_traduce_ambos_en_un_documento_real():
    datos = b"cabecera\x0ftabla condensada\x12pie normal"

    resultado = traducir_toggle_condensado(datos)

    assert resultado == (
        b"cabecera" + PCL_CONDENSADO + b"tabla condensada" + PCL_NORMAL + b"pie normal"
    )
