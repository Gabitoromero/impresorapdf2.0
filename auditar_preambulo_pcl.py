"""Audita que comandos del preambulo canonico (definidos en setlaser.i) faltan
en TXT reales de Progress, para pedirle a Marce que los agregue puntualmente
en vez de seguir parcheando sintomas en pcl_preprocessor.py.

Uso:
    python auditar_preambulo_pcl.py reporte1.txt reporte2.txt ...

Los valores de bytes de COMANDOS_CANONICOS estan calculados directamente a
partir de las variables que ya define /archivos/setlaser.txt (setlaser.i) del
lado de Progress -- no son inventados aca. Si Marce cambia setlaser.i, hay que
actualizar este diccionario a mano (no hay parser automatico del .i: algunas
asignaciones mezclan chr() con literales de texto embebidos, ej. wPCLFnt01,
lo que hace un parser generico mas riesgoso que transcribir a mano los pocos
comandos que importan para el preambulo).

wlcno y wlcsi coinciden con PCL_PITCH_NORMAL / PCL_PITCH_CONDENSADO ya usados
en pcl_preprocessor.py; wterlin coincide con PCL_LINE_TERMINATION_AUTO_CR.
"""

import sys
from pathlib import Path

# nombre de variable en setlaser.i -> (bytes exactos que emite, para que sirve)
COMANDOS_CANONICOS = {
    "wrestau": (b"\x1bE", "Reset a defaults de fabrica (debe ir primero)"),
    "wtampap": (b"\x1b&l26D", "Tamano de papel A4 (codigo 26)"),
    "wtampap1": (b"\x1b&l6D", "Tamano de papel alternativo (codigo 6)"),
    "woripap": (b"\x1b&l0O", "Orientacion portrait"),
    "woripap1": (b"\x1b&l1O", "Orientacion landscape"),
    "wmarsup": (b"\x1b&l1E", "Margen superior"),
    "wlogtex": (b"\x1b&l132F", "Longitud de texto / lineas por pagina"),
    "wterlin": (b"\x1b&k2G", "Terminacion de linea (LF hace CR+LF)"),
    "wcarpc8": (b"\x1b(10U", "Symbol set PC-8"),
    "wletnor": (b"\x1b(s0S", "Estilo de fuente normal"),
    "wlcno": (b"\x1b&k0S", "Pitch normal (10cpi)"),
    "wlcsi": (b"\x1b&k2S", "Pitch condensado (16.67cpi)"),
}

# De estos, cuales son imprescindibles en CUALQUIER reporte (el resto son
# situacionales: orientacion/pitch dependen de que use cada reporte puntual).
IMPRESCINDIBLES = ["wrestau", "wterlin"]


def auditar(txt_path: Path) -> None:
    datos = txt_path.read_bytes()
    print(f"\n{txt_path.name}:")

    encontrados = []
    for nombre, (secuencia, descripcion) in COMANDOS_CANONICOS.items():
        if secuencia in datos:
            posicion = datos.index(secuencia)
            encontrados.append(nombre)
            print(f"  [OK]     {nombre:10s} (pos {posicion:6d})  {descripcion}")

    faltantes = [n for n in IMPRESCINDIBLES if n not in encontrados]
    if faltantes:
        print(f"  [FALTA]  {', '.join(faltantes)}  <- avisar a Marce")

    if "wrestau" in encontrados:
        pos_reset = datos.index(COMANDOS_CANONICOS["wrestau"][0])
        if pos_reset != 0:
            print(f"  [AVISO]  wrestau no esta al principio del archivo (pos {pos_reset})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python auditar_preambulo_pcl.py archivo1.txt [archivo2.txt ...]")
        sys.exit(1)
    for ruta in sys.argv[1:]:
        auditar(Path(ruta))
