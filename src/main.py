"""Punto de entrada: recibe TXT (+ QR opcional) y genera el PDF de salida."""

import argparse
import logging
from pathlib import Path

from codigo_barras import insertar_codigo_de_barras
from qr_overlay import insertar_qr
from txt_to_pdf import convertir_txt_a_pdf

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convierte un TXT a PDF, con QR opcional.")
    parser.add_argument("--txt", required=True, type=Path, help="Ruta del archivo TXT de entrada")
    parser.add_argument("--qr", type=Path, default=None, help="Ruta de la imagen QR (jpg/png), opcional")
    parser.add_argument("--out", required=True, type=Path, help="Ruta del PDF de salida")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    digitos_codigo_barras = convertir_txt_a_pdf(args.txt, args.out)
    if args.qr is not None:
        insertar_qr(args.out, args.qr)
    if digitos_codigo_barras is not None:
        insertar_codigo_de_barras(args.out, digitos_codigo_barras)


if __name__ == "__main__":
    main()
