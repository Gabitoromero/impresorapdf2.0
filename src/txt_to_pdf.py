"""Conversión de TXT con comandos PCL reales a PDF, delegando en GhostPCL."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from codigo_barras import extraer_codigo_de_barras
from pcl_preprocessor import forzar_retorno_automatico, traducir_toggle_condensado

GPCL6_BIN = os.environ.get("GPCL6_BIN", "gpcl6")


def convertir_txt_a_pdf(txt_path: Path, pdf_path: Path) -> Optional[str]:
    """Convierte un TXT (con o sin comandos PCL) en un PDF usando GhostPCL (gpcl6).

    Devuelve los dígitos del código de barras del CAE si el TXT traía uno (ver
    codigo_barras.py), o `None` si no había. Quien llame a esta función es
    responsable de pegar el código de barras en el PDF con `insertar_codigo_de_barras`.

    Progress inyecta comandos PCL reales (HP) en el TXT para controlar tamaño de
    fuente, negrita y layout. GhostPCL los interpreta directamente y genera el PDF
    ya formateado, sin que este proyecto tenga que reimplementar un intérprete PCL.

    Los TXT reales del cliente no traen un comando PCL explícito de tamaño de papel,
    así que gpcl6 cae en su default (Letter, EEUU). La impresora física siempre
    imprime en A4, así que se fuerza vía PJL (`-sPAPERSIZE=a4` no funciona en gpcl6:
    bug conocido https://bugs.ghostscript.com/show_bug.cgi?id=706207).

    Antes de pasarle el archivo a gpcl6 se traducen los CHR(15)/CHR(18) sueltos
    (toggle de modo condensado, legado de impresoras de matriz de puntos que Marce
    sigue usando) a su comando PCL real equivalente (ver pcl_preprocessor.py) —
    gpcl6 no reconoce esos bytes sueltos como comando de tamaño de letra.

    También se antepone el comando PCL de retorno automático (`ESC&k2G`), porque no
    todos los TXT reales lo traen (dependen de que la impresora física lo tenga
    configurado por default) y sin él un LF suelto no vuelve al margen izquierdo,
    perdiendo contenido en documentos de líneas largas (ver pcl_preprocessor.py).
    """
    datos_sin_codigo_barras, digitos_codigo_barras = extraer_codigo_de_barras(
        txt_path.read_bytes()
    )
    datos_traducidos = traducir_toggle_condensado(datos_sin_codigo_barras)
    datos_traducidos = forzar_retorno_automatico(datos_traducidos)

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as txt_temporal:
        txt_temporal.write(datos_traducidos)
        txt_temporal_path = Path(txt_temporal.name)

    try:
        resultado = subprocess.run(
            [
                GPCL6_BIN,
                "-sDEVICE=pdfwrite",
                "-J@PJL SET PAPER=A4",
                "-o",
                str(pdf_path),
                str(txt_temporal_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
    finally:
        if txt_temporal_path.exists():
            txt_temporal_path.unlink()

    if resultado.returncode != 0:
        raise RuntimeError(f"gpcl6 falló (código {resultado.returncode}): {resultado.stderr}")

    return digitos_codigo_barras
