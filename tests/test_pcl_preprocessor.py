import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pcl_preprocessor import (
    asegurar_ancho_de_pitch,
    forzar_retorno_automatico,
    traducir_toggle_condensado,
)

PCL_CONDENSADO = b"\x1b&k2S"  # wlcsi en setlaser.i: "LETRA COMPRIMIDA 16.67"
PCL_NORMAL = b"\x1b&k0S"  # wlcno en setlaser.i: "DESCOMPRIMIR LETRA"
PCL_LINE_TERMINATION_AUTO_CR = b"\x1b&k2G"  # wterlin en setlaser.i: LF hace CR+LF


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


def test_antepone_retorno_automatico_al_principio_del_documento():
    datos = b"linea 1\nlinea 2\n"

    resultado = forzar_retorno_automatico(datos)

    assert resultado == PCL_LINE_TERMINATION_AUTO_CR + datos


def test_no_toca_documento_sin_ningun_pitch_conocido():
    datos = b"factura corta, sin toggles de pitch\notra linea"

    assert asegurar_ancho_de_pitch(datos) == datos


def test_no_toca_documento_condensado_que_ya_entra():
    linea_130_columnas = ("0" * 130).encode()
    datos = PCL_CONDENSADO + linea_130_columnas

    assert asegurar_ancho_de_pitch(datos) == datos


def test_achica_pitch_condensado_si_la_linea_mas_ancha_no_entra():
    linea_137_columnas = ("0" * 137).encode()
    datos = PCL_CONDENSADO + linea_137_columnas + b"\notra corta"

    resultado = asegurar_ancho_de_pitch(datos)

    assert PCL_CONDENSADO not in resultado
    assert resultado.endswith(linea_137_columnas + b"\notra corta")
    # 137 / (7.8 - 0.2 de colchon) pulgadas utiles = 18.0263...cpi
    assert resultado.startswith(b"\x1b(s0p18.0263h0s0b0T")


def test_no_cuenta_espacios_de_relleno_al_final_de_linea():
    # 200 columnas, pero las ultimas 80 son relleno invisible (no fuerza compresion extra)
    linea_con_relleno = ("0" * 120) + (" " * 80)
    datos = PCL_CONDENSADO + linea_con_relleno.encode()

    resultado = asegurar_ancho_de_pitch(datos)

    assert resultado == datos  # 120 <= 130, no hace falta tocar nada


def test_no_toca_pitch_normal_que_ya_entra():
    linea_78_columnas = ("0" * 78).encode()
    datos = PCL_NORMAL + linea_78_columnas

    assert asegurar_ancho_de_pitch(datos) == datos


def test_achica_pitch_normal_si_la_linea_mas_ancha_no_entra():
    # caso real: pie de factura a pitch normal (10cpi, 78 columnas utiles) con
    # una linea de 102 columnas que se cortaba a mitad de palabra
    linea_102_columnas = ("0" * 102).encode()
    datos = PCL_NORMAL + linea_102_columnas

    resultado = asegurar_ancho_de_pitch(datos)

    assert PCL_NORMAL not in resultado
    assert resultado.endswith(linea_102_columnas)
    # 102 / (7.8 - 0.2 de colchon) pulgadas utiles = 13.4211...cpi
    assert resultado.startswith(b"\x1b(s0p13.4211h0s0b0T")


def test_achica_el_pitch_por_default_si_no_hay_ningun_toggle_explicito():
    # caso real: cabecera de listado sin NINGUN comando de pitch (usa el default
    # implicito de gpcl6, que mide igual que el pitch normal, 78 columnas)
    linea_80_columnas = ("0" * 80).encode()
    datos = linea_80_columnas

    resultado = asegurar_ancho_de_pitch(datos)

    assert resultado.endswith(linea_80_columnas)
    assert resultado != datos
    assert resultado.startswith(b"\x1b(s0p")


def test_cada_pitch_se_evalua_por_separado_no_mezclado():
    # el tramo condensado (132 col, no entra) no debe afectar la decision sobre
    # el tramo normal (78 col, si entra) ni viceversa
    linea_condensada = ("0" * 132).encode()
    linea_normal = ("0" * 78).encode()
    datos = PCL_CONDENSADO + linea_condensada + b"\n" + PCL_NORMAL + linea_normal

    resultado = asegurar_ancho_de_pitch(datos)

    assert PCL_CONDENSADO not in resultado  # se tuvo que achicar
    assert PCL_NORMAL in resultado  # este entraba bien, queda igual
