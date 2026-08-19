# Formato de marcas de tipografía en el TXT

Reemplaza a los códigos de control de impresora (PCL / ESC-P). En vez de que
Progress mande códigos de impresora, marca directamente en el texto qué parte
va con qué estilo, usando una sintaxis simple que el conversor Python
interpreta.

## Sintaxis

```
{{flags:texto}}
```

- `{{` y `}}`: delimitan la marca.
- `flags`: uno o más de los siguientes, separados por coma (sin espacios).
  Se pueden combinar.
  - `b` → negrita
  - `i` → cursiva
  - un número → tamaño de fuente en puntos (ej. `14`)
  - `helvetica`, `times` o `courier` → familia de fuente (si no se indica
    ninguna, se usa `helvetica` por defecto)
- `texto`: el contenido al que se le aplica el estilo.

Solo se soportan estas 3 familias de fuente (son las únicas que vienen
incluidas en el generador de PDF sin agregar archivos extra). No se admiten
otras fuentes (Calibri, Arial, etc.) por ahora.

Si un texto no está dentro de `{{...}}`, se imprime con el estilo por
defecto (tamaño y fuente normales, sin negrita ni cursiva).

Las marcas **no se anidan** — todo el estilo de un tramo de texto va junto
en una sola marca.

## Ejemplos

| Marca | Resultado |
|---|---|
| `{{b:FACTURA A}}` | **FACTURA A** en negrita |
| `{{i:Original}}` | *Original* en cursiva |
| `{{16:Total}}` | "Total" en tamaño 16 |
| `{{b,16:TOTAL}}` | **TOTAL** en negrita y tamaño 16 |
| `{{b,i,14:Aviso importante}}` | **_Aviso importante_** en negrita, cursiva y tamaño 14 |
| `{{times,14:Total}}` | "Total" en fuente Times, tamaño 14 |
| `{{b,courier:Codigo}}` | **Codigo** en negrita, fuente Courier |

## Ejemplo de línea de factura

```
{{b,16:FACTURA A}}  {{i:Original}}
{{b:TOTAL}}      : {{b,14:2446976.13}}
```

## Ver también

`archivos/A.txt` tiene un ejemplo real de una factura completa marcada con
esta sintaxis — sirve como referencia tanto para programar el lado
Progress como para testear el conversor.
