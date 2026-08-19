import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from marcas_tipografia import Tramo, nombre_fuente_reportlab, parsear_marcas


def test_linea_sin_marcas_da_un_solo_tramo_con_estilo_por_defecto():
    tramos = parsear_marcas("Hola Marce")

    assert tramos == [Tramo(texto="Hola Marce")]


def test_marca_de_negrita():
    tramos = parsear_marcas("{{b:FACTURA A}}")

    assert tramos == [Tramo(texto="FACTURA A", negrita=True)]


def test_marca_de_cursiva():
    tramos = parsear_marcas("{{i:Original}}")

    assert tramos == [Tramo(texto="Original", cursiva=True)]


def test_marca_de_tamanio():
    tramos = parsear_marcas("{{16:Total}}")

    assert tramos == [Tramo(texto="Total", tamanio=16)]


def test_marca_de_fuente():
    tramos = parsear_marcas("{{times:Total}}")

    assert tramos == [Tramo(texto="Total", fuente="times")]


def test_marca_combinada():
    tramos = parsear_marcas("{{b,i,14:Aviso}}")

    assert tramos == [Tramo(texto="Aviso", negrita=True, cursiva=True, tamanio=14)]


def test_texto_mezclado_con_y_sin_marca():
    tramos = parsear_marcas("{{b:TOTAL}}      : {{b,14:2446976.13}}")

    assert tramos == [
        Tramo(texto="TOTAL", negrita=True),
        Tramo(texto="      : "),
        Tramo(texto="2446976.13", negrita=True, tamanio=14),
    ]


def test_nombre_fuente_reportlab_por_combinacion():
    assert nombre_fuente_reportlab(Tramo(texto="x")) == "Helvetica"
    assert nombre_fuente_reportlab(Tramo(texto="x", negrita=True)) == "Helvetica-Bold"
    assert nombre_fuente_reportlab(Tramo(texto="x", cursiva=True)) == "Helvetica-Oblique"
    assert (
        nombre_fuente_reportlab(Tramo(texto="x", negrita=True, cursiva=True))
        == "Helvetica-BoldOblique"
    )
    assert nombre_fuente_reportlab(Tramo(texto="x", fuente="times")) == "Times-Roman"
    assert (
        nombre_fuente_reportlab(Tramo(texto="x", fuente="times", negrita=True))
        == "Times-Bold"
    )
    assert nombre_fuente_reportlab(Tramo(texto="x", fuente="courier")) == "Courier"
