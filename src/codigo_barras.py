"""Código de barras del CAE (estándar AFIP: Interleaved 2 of 5).

El comando que arma Progress (`ESC ( B n1 n2 k m s v1 v2 c data`) es de Epson
ESC/P2, no de PCL — confirmado contra el manual oficial de Epson (k=2 codifica
Interleaved 2 of 5, que coincide con el estándar que exige AFIP para el CAE).
gpcl6 solo interpreta PCL, así que este comando no forma parte de lo que puede
llegar a entender por más que se lo "configure": el símbolo/fuente de barras
vive en el firmware de la impresora física de Marce, nunca viaja en el TXT.
Por eso se extraen los dígitos acá y se genera el código de barras nosotros
mismos como imagen, para pegarlo encima del PDF (igual que el QR).

Formato de los dígitos (estándar AFIP): CUIT(11) + tipo comprobante(2) +
punto de venta(4) + CAE(14) + vencimiento CAE(8) + dígito verificador(1) = 40.
"""

import io
import re
from pathlib import Path
from typing import Optional, Tuple

import barcode
from barcode.writer import ImageWriter
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

PREFIJO_CODIGO_BARRAS = bytes([27, 40, 66])  # ESC ( B
_LARGO_PARAMETROS = 8  # n1, n2, k, m, s, v1, v2, c (formato fijo del comando Epson ESC/P2)
_PATRON = re.compile(re.escape(PREFIJO_CODIGO_BARRAS) + rb".{%d}([0-9]+)\x0c?" % _LARGO_PARAMETROS, re.DOTALL)

CODBARRAS_ALTO = 58
CODBARRAS_MARGEN = 15


def extraer_codigo_de_barras(datos: bytes) -> Tuple[bytes, Optional[str]]:
    """Saca el comando de código de barras del TXT y devuelve los dígitos que codificaba.

    Si no hay comando, devuelve los datos sin cambios y `None`.
    """
    coincidencia = _PATRON.search(datos)
    if coincidencia is None:
        return datos, None

    digitos = coincidencia.group(1).decode("ascii")
    datos_limpios = datos[: coincidencia.start()] + datos[coincidencia.end() :]
    return datos_limpios, digitos


def generar_imagen_codigo_de_barras(digitos: str, destino: Path) -> Path:
    """Genera una imagen PNG con el código de barras Interleaved 2 of 5 de `digitos`."""
    codigo = barcode.get("itf", digitos, writer=ImageWriter())
    ruta_generada = codigo.save(str(destino.with_suffix("")), options={"write_text": False})
    return Path(ruta_generada)


def calcular_dimensiones_codigo_barras(
    imagen_path: Path, alto_objetivo: float = CODBARRAS_ALTO
) -> Tuple[float, float]:
    """Ancho y alto para dibujar el código de barras manteniendo su proporción real.

    Con un ancho fijo, un código de más dígitos queda con las barras más
    apretadas (ilegible). Se fija el alto y se deriva el ancho de la proporción
    real de la imagen generada, así el ancho crece con la cantidad de dígitos.
    """
    with Image.open(imagen_path) as imagen:
        ancho_px, alto_px = imagen.size
    ancho_objetivo = alto_objetivo * (ancho_px / alto_px)
    return ancho_objetivo, alto_objetivo


def calcular_posicion_codigo_barras(ancho_pagina: float, ancho_codigo: float) -> Tuple[float, float]:
    """Esquina inferior izquierda del código de barras, fijo abajo a la derecha de la página."""
    x = ancho_pagina - CODBARRAS_MARGEN - ancho_codigo
    y = CODBARRAS_MARGEN
    return x, y


def insertar_codigo_de_barras(pdf_path: Path, digitos: str) -> None:
    """Inserta el código de barras generado a partir de `digitos` en todas las páginas del PDF."""
    imagen_path = pdf_path.with_name(pdf_path.stem + "_codbarras_tmp.png")
    generar_imagen_codigo_de_barras(digitos, imagen_path)

    try:
        ancho_codigo, alto_codigo = calcular_dimensiones_codigo_barras(imagen_path)

        reader = PdfReader(str(pdf_path))
        ancho_pagina = float(reader.pages[0].mediabox.width)
        alto_pagina = float(reader.pages[0].mediabox.height)
        x, y = calcular_posicion_codigo_barras(ancho_pagina, ancho_codigo)

        overlay_buffer = io.BytesIO()
        overlay_canvas = canvas.Canvas(overlay_buffer, pagesize=(ancho_pagina, alto_pagina))
        overlay_canvas.drawImage(
            str(imagen_path), x, y, width=ancho_codigo, height=alto_codigo, mask="auto"
        )
        overlay_canvas.save()
        overlay_buffer.seek(0)
        overlay_page = PdfReader(overlay_buffer).pages[0]

        writer = PdfWriter(clone_from=str(pdf_path))
        for pagina in writer.pages:
            pagina.merge_page(overlay_page)

        with open(pdf_path, "wb") as archivo_salida:
            writer.write(archivo_salida)
    finally:
        if imagen_path.exists():
            imagen_path.unlink()
