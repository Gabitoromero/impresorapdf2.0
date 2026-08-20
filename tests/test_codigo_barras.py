import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from codigo_barras import (
    CODBARRAS_ALTO,
    CODBARRAS_ANCHO,
    CODBARRAS_MARGEN,
    calcular_posicion_codigo_barras,
    extraer_codigo_de_barras,
    generar_imagen_codigo_de_barras,
    insertar_codigo_de_barras,
)

# Comando real ESC/P2 de Epson que arma Progress (confirmado por Marce y contra el manual
# oficial de Epson: ESC ( B n1 n2 k m s v1 v2 c data).
# chr(27)+chr(40)+chr(66) = ESC ( B (inicio del comando)
# chr(46)+chr(1) = n1, n2 (cantidad de bytes que siguen)
# chr(2) = k -> tipo de codigo: 2 = Interleaved 2 of 5 (el que exige AFIP)
# chr(2) = m -> ancho de modulo
# chr(254) = s -> ajuste de espaciado
# chr(54)+chr(0) = v1, v2 -> alto de barra
# chr(0) = c -> flags de control
# después de estos 8 bytes de parámetros viene el dato (los dígitos a codificar)
PREFIJO = bytes([27, 40, 66])
PARAMETROS = bytes([46, 1, 2, 2, 254, 54, 0, 0])
DIGITOS_REALES = "3071858073700100002863387828410622026082"


def test_extrae_digitos_y_los_saca_del_stream():
    comando_completo = PREFIJO + PARAMETROS + DIGITOS_REALES.encode()
    datos = b"texto antes" + comando_completo + b"\x0c" + b"resto"

    datos_limpios, digitos = extraer_codigo_de_barras(datos)

    assert digitos == DIGITOS_REALES
    assert comando_completo not in datos_limpios
    assert datos_limpios == b"texto antesresto"


def test_no_encuentra_nada_si_no_hay_comando():
    datos = b"factura sin codigo de barras"

    datos_limpios, digitos = extraer_codigo_de_barras(datos)

    assert digitos is None
    assert datos_limpios == datos


def test_genera_una_imagen_itf_valida(tmp_path):
    destino = tmp_path / "barras.png"

    generar_imagen_codigo_de_barras(DIGITOS_REALES, destino)

    assert destino.exists()
    assert destino.stat().st_size > 0


def test_calcula_posicion_abajo_a_la_derecha():
    x, y = calcular_posicion_codigo_barras(ancho_pagina=595)
    assert x == 595 - CODBARRAS_MARGEN - CODBARRAS_ANCHO
    assert y == CODBARRAS_MARGEN


def test_inserta_el_codigo_de_barras_en_el_pdf(tmp_path):
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "salida.pdf"
    pdf = canvas.Canvas(str(pdf_path), pagesize=(595, 842))
    pdf.drawString(50, 800, "contenido de prueba")
    pdf.save()

    insertar_codigo_de_barras(pdf_path, DIGITOS_REALES)

    pagina = PdfReader(pdf_path).pages[0]
    assert len(pagina.images) == 1
