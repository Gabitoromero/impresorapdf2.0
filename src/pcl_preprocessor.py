"""Traduce códigos de control legacy (no-PCL) que Progress todavía inyecta en el TXT.

Marce usa CHR(15)/CHR(18) para alternar modo condensado. GhostPCL no reconoce esos
bytes sueltos (no forman parte del estándar PCL5: los únicos códigos de control de
un solo byte que reconoce PCL5 son BS/HT/LF/CR/FF), así que hay que traducirlos al
comando PCL real equivalente antes de pasarle el archivo a gpcl6.

Los comandos reales usados acá (`ESC&k2S` / `ESC&k0S`) son los que efectivamente
define el propio sistema de Marce en su include de Progress `setlaser.i`
(variables `wlcsi` / `wlcno`, ver archivos/setlaser.txt) — no son un valor inventado.
"""

CHR_CONDENSADO_ON = 0x0F
CHR_CONDENSADO_OFF = 0x12

PCL_PITCH_CONDENSADO = b"\x1b&k2S"  # wlcsi: "LETRA COMPRIMIDA 16.67"
PCL_PITCH_NORMAL = b"\x1b&k0S"  # wlcno: "DESCOMPRIMIR LETRA"


def traducir_toggle_condensado(datos: bytes) -> bytes:
    """Reemplaza CHR(15)/CHR(18) sueltos por los comandos PCL de pitch equivalentes."""
    datos = datos.replace(bytes([CHR_CONDENSADO_ON]), PCL_PITCH_CONDENSADO)
    datos = datos.replace(bytes([CHR_CONDENSADO_OFF]), PCL_PITCH_NORMAL)
    return datos
