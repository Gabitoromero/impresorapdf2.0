"""Limpieza heurística de códigos de control de impresora (PCL / ESC-P).

No es un intérprete completo de PCL ni de ESC/P (eso requeriría algo como
GhostPCL). Reconoce los patrones de secuencia de escape vistos en archivos
reales del cliente y los elimina, junto con bytes de control sueltos, para
que el texto quede legible aunque no se reproduzca la tipografía original.
"""

import re

_SECUENCIA_PCL = r"\x1b[\x21-\x2f][a-z]?[+-]?[0-9]*\.?[0-9]*[A-Za-z]"
_SECUENCIA_SIMPLE = r"\x1b[A-Za-z@]"
_SECUENCIAS_ESCAPE = re.compile(f"(?:{_SECUENCIA_PCL})|(?:{_SECUENCIA_SIMPLE})")
_CONTROL_SUELTO = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def limpiar_codigos_control(texto: str) -> str:
    """Quita secuencias de escape PCL/ESC-P y caracteres de control sueltos, preservando \\n, \\r y \\t."""
    sin_secuencias = _SECUENCIAS_ESCAPE.sub("", texto)
    return _CONTROL_SUELTO.sub("", sin_secuencias)
