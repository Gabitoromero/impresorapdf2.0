# Impresor PDF 2.0

Convierte archivos TXT a PDF, con inserción opcional de código QR. Corre en el servidor del cliente, invocado desde Progress ABL vía `UNIX SILENT`.

Especificación completa (requisitos y tareas): Notion — proyecto "Impresor PDF 2.0".

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python src/main.py --txt entrada.txt --qr codigo.png --out salida.pdf
```

`--qr` es opcional: sin ese parámetro, se genera el PDF sin código QR.
