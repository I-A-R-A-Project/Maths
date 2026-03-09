# Maths Repository

Repositorio de utilidades matematicas y fisicas por consola.

## Contenido

- `calculator.py`: evaluador de expresiones con pasos.
- `equation.py`: resolucion paso a paso de sistemas simples de ecuaciones.
- `geometria.py`: calculos de area, perimetro y volumen.
- `physics.py`: formulas de fisica basica.
- `polynomial_solver.py`: operaciones con polinomios (raices, derivada, factorizar, expandir, plot).
- `math_console.py`: consola unificada con input libre, analiza la consulta y enruta al modulo correcto.

## Requisitos

- Python 3.10+
- Dependencias:

```bash
pip install sympy matplotlib numpy
```

## Uso rapido

### Consola inteligente

```bash
python math_console.py
```

Ejemplos de entradas dentro de la consola:

- `2 + 3*5`
- `x + y = 10; x - y = 2`
- `area circulo 5`
- `volumen cilindro 2 8`
- `fuerza 10 2`
- `raices de x^2 - 5*x + 6`
- `derivada de x^3 - 2*x`

### Modulos individuales

```bash
python calculator.py "sqrt(81) + 3^2"
python equation.py "x+y=10; x-y=2"
python geometria.py area circle 5
python physics.py force 10 2
python polynomial_solver.py "x**2 - 5*x + 6" roots
```

## Notas

- Algunos modulos escriben historial en `history.txt`.
- `polynomial_solver.py plot` abre ventana grafica local.
- La consola `math_console.py` prioriza texto libre en espanol/ingles y usa heuristicas por palabras clave.
