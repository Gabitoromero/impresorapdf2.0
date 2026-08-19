"""Lectura de TXT y generación básica de PDF (Requisito: Formato salida PDF)."""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from control_codes import limpiar_codigos_control
from marcas_tipografia import TAMANIO_DEFECTO, nombre_fuente_reportlab, parsear_marcas

ANCHO_PAGINA, ALTO_PAGINA = A4
MARGEN_IZQUIERDO = 40
MARGEN_SUPERIOR = 40
MARGEN_INFERIOR = 40
ALTO_LINEA = 14
INTERLINEA = 1.3


def convertir_txt_a_pdf(txt_path: Path, pdf_path: Path) -> None:
    """Lee un archivo TXT y genera un PDF con el mismo contenido, una línea del txt por línea del PDF.

    Interpreta las marcas de tipografía del texto (ver docs/formato-marcas-tipografia.md)
    para aplicar negrita, cursiva, tamaño y fuente. Si el texto no entra en una
    sola hoja A4, sigue en páginas siguientes.
    """
    texto = limpiar_codigos_control(txt_path.read_text(encoding="latin-1"))
    lineas = texto.splitlines()

    pdf = canvas.Canvas(str(pdf_path), pagesize=A4)
    y = ALTO_PAGINA - MARGEN_SUPERIOR

    for linea in lineas:
        tramos = parsear_marcas(linea)
        tamanios = [tramo.tamanio or TAMANIO_DEFECTO for tramo in tramos]
        alto_linea = max(ALTO_LINEA, max(tamanios, default=TAMANIO_DEFECTO) * INTERLINEA)

        if y < MARGEN_INFERIOR:
            pdf.showPage()
            y = ALTO_PAGINA - MARGEN_SUPERIOR

        x = MARGEN_IZQUIERDO
        for tramo in tramos:
            fuente = nombre_fuente_reportlab(tramo)
            tamanio = tramo.tamanio or TAMANIO_DEFECTO
            pdf.setFont(fuente, tamanio)
            pdf.drawString(x, y, tramo.texto)
            x += pdf.stringWidth(tramo.texto, fuente, tamanio)

        y -= alto_linea

    pdf.save()
