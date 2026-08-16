"""Calculos de area, perimetro y volumen.

Separacion de responsabilidades: `area`, `perimeter` y `volume` son
funciones de CALCULO puro. No imprimen nada y no devuelven None en
silencio ante un error: si algo no se puede calcular, levantan
ValueError con un mensaje claro. Devuelven un ComputationResult con los
pasos y el resultado. Solo `parse_args`/`main` (uso standalone) y
math_console.py deciden como mostrarlo.
"""
import sys
import math
from datetime import datetime

from calculator import simplify_expression
from common import ComputationResult, to_floats

HISTORY_PATH = "history.txt"


# --------------------- Auxiliar: expresiones internas ---------------------

def _evaluate_expression(expression: str) -> float:
    """Evalua una expresion auxiliar (p. ej. el apotema de un poligono)
    usando el motor seguro de calculator.py. No imprime nada. Si la
    expresion no se puede resolver, levanta ValueError en vez de devolver
    un valor por defecto silencioso (antes esto devolvia 0 y contaminaba
    el resultado final sin avisar)."""
    steps = simplify_expression(expression)
    try:
        value = float(steps[-1])
    except (ValueError, IndexError) as exc:
        raise ValueError(
            f"No se pudo evaluar la expresion auxiliar '{expression}'."
        ) from exc
    _write_history(steps)
    return value


def _write_history(steps) -> None:
    from calculator import write_history
    write_history(steps)


def _ensure_positive(values, names) -> None:
    for value, name in zip(values, names):
        if value <= 0:
            raise ValueError(f"El valor de '{name}' debe ser mayor a 0 (se recibio {value}).")


def log_history(kind, shape, text) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = "\n".join(line.strip() for line in text.strip().splitlines())
    try:
        with open(HISTORY_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{now}] {kind}({shape})\n{entry}\n\n")
    except OSError:
        pass  # logging es best-effort, no debe interrumpir el calculo


# --------------------- Calculation functions ---------------------

def area(shape, *args) -> ComputationResult:
    steps = []

    if shape == "circle":
        (r,) = to_floats(args, ["radio"])
        _ensure_positive([r], ["radio"])
        result = math.pi * r ** 2
        steps.append(f"Area de circulo: pi x r^2 = pi x {r}^2 = {result:.5f}")

    elif shape == "rectangle":
        b, h = to_floats(args, ["base", "altura"])
        _ensure_positive([b, h], ["base", "altura"])
        result = b * h
        steps.append(f"Area de rectangulo: base x altura = {b} x {h} = {result:.5f}")

    elif shape == "triangle":
        a, h = to_floats(args, ["base", "altura"])
        _ensure_positive([a, h], ["base", "altura"])
        result = (a * h) / 2
        steps.append(f"Area de triangulo: (base x altura) / 2 = ({a} x {h}) / 2 = {result:.5f}")

    elif shape == "regular_polygon":
        n_raw, l_raw = to_floats(args, ["cantidad de lados (n)", "longitud de lado (l)"])
        n = int(n_raw)
        if n < 3:
            raise ValueError(f"Un poligono regular necesita al menos 3 lados (se recibio n={n}).")
        l = l_raw
        _ensure_positive([l], ["longitud de lado (l)"])
        perimeter_val = n * l
        apothem_expr = f"{l} / (2 * tan(pi / {n}))"
        apothem_val = _evaluate_expression(apothem_expr)
        result = (perimeter_val * apothem_val) / 2
        steps.append(f"Poligono regular (n={n}, l={l}):")
        steps.append(f"  Paso 1: perimetro = n x l = {n} x {l} = {perimeter_val:.5f}")
        steps.append(f"  Paso 2: apotema = {apothem_expr} = {apothem_val:.5f}")
        steps.append(
            f"  Paso 3: area = (perimetro x apotema) / 2 = "
            f"({perimeter_val:.5f} x {apothem_val:.5f}) / 2 = {result:.5f}"
        )

    else:
        raise ValueError(f"Figura no soportada para area: '{shape}'.")

    log_history("area", shape, "\n".join(steps))
    return ComputationResult(steps=steps, result=result)


def perimeter(shape, *args) -> ComputationResult:
    steps = []

    if shape == "circle":
        (r,) = to_floats(args, ["radio"])
        _ensure_positive([r], ["radio"])
        result = 2 * math.pi * r
        steps.append(f"Perimetro de circulo: 2 pi x r = 2 pi x {r} = {result:.5f}")

    elif shape == "rectangle":
        b, h = to_floats(args, ["base", "altura"])
        _ensure_positive([b, h], ["base", "altura"])
        result = 2 * (b + h)
        steps.append(f"Perimetro de rectangulo: 2 x (b + h) = 2 x ({b} + {h}) = {result:.5f}")

    elif shape == "triangle":
        a, b, c = to_floats(args, ["lado a", "lado b", "lado c"])
        _ensure_positive([a, b, c], ["lado a", "lado b", "lado c"])
        if a + b <= c or a + c <= b or b + c <= a:
            raise ValueError(
                f"Los lados {a}, {b}, {c} no forman un triangulo valido "
                "(la suma de dos lados debe superar al tercero)."
            )
        result = a + b + c
        steps.append(f"Perimetro de triangulo: a + b + c = {a} + {b} + {c} = {result:.5f}")

    elif shape == "regular_polygon":
        n_raw, l_raw = to_floats(args, ["cantidad de lados (n)", "longitud de lado (l)"])
        n = int(n_raw)
        if n < 3:
            raise ValueError(f"Un poligono regular necesita al menos 3 lados (se recibio n={n}).")
        _ensure_positive([l_raw], ["longitud de lado (l)"])
        result = n * l_raw
        steps.append(f"Perimetro de poligono regular: n x l = {n} x {l_raw} = {result:.5f}")

    else:
        raise ValueError(f"Figura no soportada para perimetro: '{shape}'.")

    log_history("perimeter", shape, "\n".join(steps))
    return ComputationResult(steps=steps, result=result)


def volume(shape, *args) -> ComputationResult:
    steps = []

    if shape == "cube":
        (l,) = to_floats(args, ["lado"])
        _ensure_positive([l], ["lado"])
        result = l ** 3
        steps.append(f"Volumen de cubo: l^3 = {l}^3 = {result:.5f}")

    elif shape == "cylinder":
        r, h = to_floats(args, ["radio", "altura"])
        _ensure_positive([r, h], ["radio", "altura"])
        result = math.pi * r ** 2 * h
        steps.append(f"Volumen de cilindro: pi x r^2 x h = pi x {r}^2 x {h} = {result:.5f}")

    elif shape == "sphere":
        (r,) = to_floats(args, ["radio"])
        _ensure_positive([r], ["radio"])
        result = (4 / 3) * math.pi * r ** 3
        steps.append(f"Volumen de esfera: (4/3) pi x r^3 = (4/3) pi x {r}^3 = {result:.5f}")

    elif shape == "dodecahedron":
        (l,) = to_floats(args, ["lado"])
        _ensure_positive([l], ["lado"])
        expr = f"((15 + 7 * sqrt(5)) / 4) * ({l} ** 3)"
        result = _evaluate_expression(expr)
        steps.append(f"Volumen de dodecaedro: {expr} = {result:.5f}")

    elif shape == "icosahedron":
        (l,) = to_floats(args, ["lado"])
        _ensure_positive([l], ["lado"])
        expr = f"(5 * (3 + sqrt(5)) / 12) * ({l} ** 3)"
        result = _evaluate_expression(expr)
        steps.append(f"Volumen de icosaedro: {expr} = {result:.5f}")

    else:
        raise ValueError(f"Figura no soportada para volumen: '{shape}'.")

    log_history("volume", shape, "\n".join(steps))
    return ComputationResult(steps=steps, result=result)


# --------------------- Console input handler (uso standalone) ---------------------

def show_help() -> None:
    print("""
Usage: python geometria.py [operacion] [figura] [valores...]

Operaciones:
  area         Calcula el area de una figura
  perimeter    Calcula el perimetro de una figura
  volume       Calcula el volumen de una figura 3D

Ejemplos:
  python geometria.py area circle 5
  python geometria.py perimeter triangle 3 4 5
  python geometria.py volume icosahedron 2
""")


def parse_args() -> None:
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()

    if command == "help":
        show_help()
        return

    if len(sys.argv) < 4:
        print("Argumentos insuficientes. Usa 'help' para ver el uso.")
        return

    shape = sys.argv[2].lower()
    values = sys.argv[3:]

    func = {"area": area, "perimeter": perimeter, "volume": volume}.get(command)
    if func is None:
        print(f"Operacion desconocida '{command}'. Usa 'help' para ver el uso.")
        return

    try:
        outcome = func(shape, *values)
    except ValueError as exc:
        print(f"Error: {exc}")
        return

    for step in outcome.steps:
        print(step)


if __name__ == "__main__":
    parse_args()
