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
# Se confirmó por separado (misma técnica) que a pitch normal (10cpi) el límite real
# es 78 columnas, exactamente lo que da la misma fórmula — el ancho útil de A4 es el
# mismo para ambos pitches (7.8"), sólo cambia cuántas columnas entran a cada cpi.
ANCHO_UTIL_A4_PULGADAS = 7.8

# cpi estándar de cada pitch que Marce define en setlaser.i (variables wlcno / wlcsi).
_CPI_POR_COMANDO_PITCH = {
    PCL_PITCH_NORMAL: 10.0,
    PCL_PITCH_CONDENSADO: 100 / 6,  # 16.6667
}

# Colchón de seguridad SÓLO para calcular el pitch de reemplazo (no para decidir si
# hace falta reemplazar: ahí se usa el límite real de 7.8" tal cual). Se vio en un
# documento real completo (no en una línea de calibración aislada) que calcular el
# pitch justo al límite exacto —e incluso con un carácter de margen— igual perdía el
# último carácter: efecto acumulativo de redondeo/selección de fuente de gpcl6 al
# haber más contenido/páginas previas en el mismo documento. Se ajustó empíricamente
# contra ese documento real hasta que dejó de cortarse (0.1" no alcanzó, 0.2" sí).
MARGEN_SEGURIDAD_PULGADAS = 0.2

# Una secuencia PCL termina en la primera mayúscula (o @): ESC & k 2 S -> el
# terminador real es "S", no "k" (que es el caracter de grupo, minúscula, parte
# del medio de la secuencia). Cortar en la primera letra cualquiera (mayúscula
# o minúscula) rompía comandos parametrizados como este.
_PATRON_ESCAPE_PCL = re.compile(rb"\x1b[^\x1b]*?[A-Z@]")


def _ancho_maximo_de_linea(datos: bytes) -> int:
    texto_visible = _PATRON_ESCAPE_PCL.sub(b"", datos)
    # rstrip: espacios de relleno al final de línea (común en reportes de Progress,
    # columnas paddeadas a ancho fijo) no imprimen nada visible, así que no deberían
    # forzar una compresión que en los hechos no hace falta.
    return max((len(linea.rstrip()) for linea in texto_visible.split(b"\n")), default=0)


_PATRON_TOGGLE_PITCH = re.compile(
    b"(" + b"|".join(re.escape(c) for c in _CPI_POR_COMANDO_PITCH) + b")"
)


def _anchos_maximos_por_pitch(datos: bytes):
    """Recorre el documento y devuelve, para cada comando de pitch (normal o
    condensado), el ancho de la línea más ancha entre TODOS los tramos donde
    ese pitch estuvo activo. Cada pitch se evalúa por separado: una línea
    ancha bajo condensado no debe afectar la decisión sobre el pitch normal
    (y viceversa), porque cada uno tiene su propio límite de columnas.

    El contenido ANTES del primer toggle explícito (si lo hay) se cuenta como
    pitch normal: es el default implícito de gpcl6 sin ningún comando de pitch
    — medido empíricamente, entran exactamente las mismas 78 columnas que con
    `ESC&k0S` explícito.
    """
    anchos = {}
    pitch_activo = PCL_PITCH_NORMAL
    for parte in _PATRON_TOGGLE_PITCH.split(datos):
        if parte in _CPI_POR_COMANDO_PITCH:
            pitch_activo = parte
            continue
        ancho = _ancho_maximo_de_linea(parte)
        anchos[pitch_activo] = max(anchos.get(pitch_activo, 0), ancho)
    return anchos


def asegurar_ancho_de_pitch(datos: bytes) -> bytes:
    """Si alguno de los pitches estándar (normal o condensado) no alcanza para
    la línea más ancha de sus propios tramos, lo reemplaza por un pitch a
    medida calculado para que esa línea entre completa en el ancho útil de
    A4. Tramos que ya entran, o pitches que el documento no usa, quedan sin
    tocar.

    Usa el comando PCL de selección de fuente por pitch (`ESC(s0p#h0s0b0T`,
    grupo "(s" — HP PCL5 Technical Reference / IBM "Breakdown of HP PCL5 Font
    Strings"), no el HMI puro (`ESC&k#H`). El HMI sólo mueve el cursor sin
    reseleccionar la fuente ("HMI will not alter the point size of your
    fonts"), así que si el glifo real es más ancho que el nuevo espaciado los
    caracteres quedan superpuestos e ilegibles — se probó y pasaba exactamente
    eso. El comando de selección de fuente sí reescala el glifo, confirmado
    con una línea de calibración: sin superposición y sin cortes, exacto al
    límite calculado.
    """
    anchos_maximos = _anchos_maximos_por_pitch(datos)

    for comando, cpi_estandar in _CPI_POR_COMANDO_PITCH.items():
        ancho_maximo = anchos_maximos.get(comando, 0)
        columnas_max_estandar = math.floor(ANCHO_UTIL_A4_PULGADAS * cpi_estandar)
        if ancho_maximo <= columnas_max_estandar:
            continue

        ancho_util_con_colchon = ANCHO_UTIL_A4_PULGADAS - MARGEN_SEGURIDAD_PULGADAS
        pitch_necesario = ancho_maximo / ancho_util_con_colchon
        comando_a_medida = (
            b"\x1b(s0p" + f"{pitch_necesario:.4f}".encode("ascii") + b"h0s0b0T"
        )
        if comando in datos:
            datos = datos.replace(comando, comando_a_medida)
        elif comando == PCL_PITCH_NORMAL:
            # El documento nunca manda el toggle normal explícito (usa el
            # default implícito de gpcl6, que mide igual) pero igual necesita
            # achicarse: no hay nada que reemplazar, se antepone al principio.
            datos = comando_a_medida + datos

    return datos
