"""Traduce códigos de control legacy (no-PCL) que Progress todavía inyecta en el TXT.

Marce usa CHR(15)/CHR(18) para alternar modo condensado. GhostPCL no reconoce esos
bytes sueltos (no forman parte del estándar PCL5: los únicos códigos de control de
un solo byte que reconoce PCL5 son BS/HT/LF/CR/FF), así que hay que traducirlos al
comando PCL real equivalente antes de pasarle el archivo a gpcl6.

Los comandos reales usados acá (`ESC&k2S` / `ESC&k0S`) son los que efectivamente
define el propio sistema de Marce en su include de Progress `setlaser.i`
(variables `wlcsi` / `wlcno`, ver archivos/setlaser.txt) — no son un valor inventado.
"""

import math
import re

CHR_CONDENSADO_ON = 0x0F
CHR_CONDENSADO_OFF = 0x12

PCL_PITCH_CONDENSADO = b"\x1b&k2S"  # wlcsi: "LETRA COMPRIMIDA 16.67"
PCL_PITCH_NORMAL = b"\x1b&k0S"  # wlcno: "DESCOMPRIMIR LETRA"

# wterlin en setlaser.i: Line Termination = 2 (un LF también hace CR). Algunos TXT
# reales (ej. listados como "Subdiario I.V.A. Ventas") no lo mandan porque dependen
# de que la impresora física ya lo tenga configurado por default en su firmware.
# gpcl6 no replica ese default: sin este comando, un LF suelto (sin \r) solo baja el
# cursor y NO vuelve al margen izquierdo, así que en líneas largas el texto siguiente
# termina cayendo fuera de la página. Se antepone siempre, sea cual sea el documento.
PCL_LINE_TERMINATION_AUTO_CR = b"\x1b&k2G"


def traducir_toggle_condensado(datos: bytes) -> bytes:
    """Reemplaza CHR(15)/CHR(18) sueltos por los comandos PCL de pitch equivalentes."""
    datos = datos.replace(bytes([CHR_CONDENSADO_ON]), PCL_PITCH_CONDENSADO)
    datos = datos.replace(bytes([CHR_CONDENSADO_OFF]), PCL_PITCH_NORMAL)
    return datos


def forzar_retorno_automatico(datos: bytes) -> bytes:
    """Antepone el comando PCL que hace que un LF también vuelva al margen izquierdo."""
    return PCL_LINE_TERMINATION_AUTO_CR + datos


# Medido empíricamente contra gpcl6 con una línea de prueba de caracteres repetidos:
# a pitch condensado (16.67cpi) el margen físico no-imprimible de A4 que emula gpcl6
# (~6mm por lado, estándar de la familia HP LaserJet) deja exactamente 130 columnas
# utilizables — no es negociable vía flags de gpcl6, se probó con -H0x0x0x0 sin efecto.
COLUMNAS_MAX_PITCH_CONDENSADO = 130
ANCHO_UTIL_A4_PULGADAS = COLUMNAS_MAX_PITCH_CONDENSADO / (100 / 6)  # = 7.8"

# Una secuencia PCL termina en la primera mayúscula (o @): ESC & k 2 S -> el
# terminador real es "S", no "k" (que es el caracter de grupo, minúscula, parte
# del medio de la secuencia). Cortar en la primera letra cualquiera (mayúscula
# o minúscula) rompía comandos parametrizados como este.
_PATRON_ESCAPE_PCL = re.compile(rb"\x1b[^\x1b]*?[A-Z@]")


def _ancho_maximo_de_linea(datos: bytes) -> int:
    texto_visible = _PATRON_ESCAPE_PCL.sub(b"", datos)
    return max((len(linea) for linea in texto_visible.split(b"\n")), default=0)


def asegurar_ancho_condensado(datos: bytes) -> bytes:
    """Si el pitch condensado estándar no alcanza para la línea más ancha del
    documento, lo reemplaza por un pitch a medida (comando PCL HMI, `ESC&k#H`,
    # = 120 / cpi deseado — HP PCL5 Technical Reference) calculado para que esa
    línea entre completa en el ancho útil de A4. Documentos que ya entran, o que
    no usan pitch condensado, quedan sin tocar.
    """
    if PCL_PITCH_CONDENSADO not in datos:
        return datos

    ancho_maximo = _ancho_maximo_de_linea(datos)
    if ancho_maximo <= COLUMNAS_MAX_PITCH_CONDENSADO:
        return datos

    pitch_necesario = ancho_maximo / ANCHO_UTIL_A4_PULGADAS
    # HMI y pitch son inversamente proporcionales: redondear el HMI "para arriba"
    # da un pitch MENOS denso (justo lo contrario de lo que necesitamos). Por eso
    # se redondea siempre hacia abajo, para garantizar un pitch al menos tan denso
    # como el necesario y que la línea entre completa.
    hmi = math.floor(120 / pitch_necesario)
    comando_pitch_a_medida = b"\x1b&k" + str(hmi).encode("ascii") + b"H"
    return datos.replace(PCL_PITCH_CONDENSADO, comando_pitch_a_medida)
