import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from codigo_barras import (
    CODBARRAS_ALTO,
    CODBARRAS_MARGEN,
    calcular_dimensiones_codigo_barras,
    calcular_posicion_codigo_barras,
    extraer_codigo_de_barras,
    generar_imagen_codigo_de_barras,
    insertar_codigo_de_barras,
)

# Comando real ESC/P2 de Epson que arma Progress. El bloque de parámetros
# medido byte a byte contra los 13 TXT reales de archivos/TXT es siempre
# idéntico (5 bytes), no los 8 que sugiere el manual de Epson (n1,n2,k,m,s,
# v1,v2,c) — el sistema de Marce no emite v1/v2/c como bytes separados.
# chr(27)+chr(40)+chr(66) = ESC ( B (inicio del comando)
# chr(46)+chr(1)+chr(2)+chr(2)+chr(254) = 5 bytes de parámetros reales
# después de estos 5 bytes viene el dato (los dígitos a codificar)
PREFIJO = bytes([27, 40, 66])
PARAMETROS = bytes([46, 1, 2, 2, 254])
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


def test_avisa_si_el_codigo_no_tiene_40_digitos(caplog):
    digitos_incompletos = "30707191"  # CAE recortado, visto en TXT reales de Marce
    comando_completo = PREFIJO + PARAMETROS + digitos_incompletos.encode()
    datos = comando_completo + b"\x0c"

    with caplog.at_level("WARNING"):
        _, digitos = extraer_codigo_de_barras(datos)

    assert digitos == digitos_incompletos
    assert len(caplog.records) == 1
    assert "40" in caplog.text
    assert digitos_incompletos in caplog.text


def test_no_avisa_si_el_codigo_tiene_40_digitos(caplog):
    comando_completo = PREFIJO + PARAMETROS + DIGITOS_REALES.encode()
    datos = comando_completo + b"\x0c"

    with caplog.at_level("WARNING"):
        extraer_codigo_de_barras(datos)

    assert len(caplog.records) == 0


def test_genera_una_imagen_itf_valida(tmp_path):
    destino = tmp_path / "barras.png"

    generar_imagen_codigo_de_barras(DIGITOS_REALES, destino)

    assert destino.exists()
    assert destino.stat().st_size > 0


def test_calcula_dimensiones_proporcionales_al_ancho_real(tmp_path):
    destino = tmp_path / "barras.png"
    generar_imagen_codigo_de_barras(DIGITOS_REALES, destino)

    ancho, alto = calcular_dimensiones_codigo_barras(destino)

    assert alto == CODBARRAS_ALTO

    from PIL import Image

    proporcion_real = Image.open(destino).size[0] / Image.open(destino).size[1]
    assert abs(ancho / alto - proporcion_real) < 0.01


def test_codigo_mas_largo_da_un_ancho_mayor(tmp_path):
    corto = tmp_path / "corto.png"
    largo = tmp_path / "largo.png"
    generar_imagen_codigo_de_barras("1234", corto)
    generar_imagen_codigo_de_barras(DIGITOS_REALES, largo)

    ancho_corto, _ = calcular_dimensiones_codigo_barras(corto)
    ancho_largo, _ = calcular_dimensiones_codigo_barras(largo)

    assert ancho_largo > ancho_corto


def test_calcula_posicion_abajo_a_la_derecha():
    x, y = calcular_posicion_codigo_barras(ancho_pagina=595, ancho_codigo=250)
    assert x == 595 - CODBARRAS_MARGEN - 250
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
