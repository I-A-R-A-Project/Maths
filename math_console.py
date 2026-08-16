import re
import unicodedata
from typing import Callable

import equation
import geometria
import physics
from calculator import format_steps, simplify_expression, solve_expression, write_history
from common import analyze_notation, format_expression
from polynomial_solver import (
    parse_polynomial_input,
    polynomial_derivative,
    polynomial_evaluate,
    polynomial_expand,
    polynomial_factor,
    solve_roots_step_by_step,
)

EXIT_WORDS = {"exit", "quit", "salir"}
HELP_WORDS = {"help", "ayuda", "?"}


def normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return normalized.lower().strip()


def extract_numbers(text: str) -> list[float]:
    matches = re.findall(r"-?\d+(?:\.\d+)?", text)
    return [float(value) for value in matches]


def print_help() -> None:
    print(
        """
Comandos aceptados (texto libre o formato directo):

1) Expresiones:
   - 2 + 3*5
   - sqrt(81) + sin(pi/2)

2) Ecuaciones / sistemas (N ecuaciones, N variables):
   - x + y = 10; x - y = 2
   - x + y + z = 6; x - y = 1; 2*x + z = 7
   - 2*x + 3 = 15

3) Geometria:
   - area circulo 5
   - perimetro rectangulo 10 4
   - volumen cilindro 2 8

4) Fisica:
   - fuerza 10 2
   - energia cinetica 5 3
   - velocidad 100 9.58

5) Polinomios:
   - raices de x^2 - 5*x + 6
   - pasos para x^2 - 5*x + 6
   - derivada de x^3 - 2*x
   - factorizar x^2 - 9
   - evaluar x^2 + 1 en 3

Escribe 'salir' para terminar.
"""
    )


def solve_system_or_equation(raw: str) -> None:
    equations = equation.parse_system(raw)
    steps, solutions = equation.solve_system_step_by_step(equations)

    for step in steps:
        print(step)

    if not solutions:
        print("No se encontro solucion.")
        return

    print("Solucion(es):")
    for index, sol in enumerate(solutions, 1):
        parts = [f"{sym} = {sol.get(sym)}" for sym in sorted(sol, key=lambda s: s.name)]
        print(f"  {index}) " + ", ".join(parts))


def detect_shape(text: str) -> str | None:
    shape_map = {
        "circulo": "circle",
        "circle": "circle",
        "rectangulo": "rectangle",
        "rectangle": "rectangle",
        "triangulo": "triangle",
        "triangle": "triangle",
        "poligono": "regular_polygon",
        "polygon": "regular_polygon",
        "cubo": "cube",
        "cube": "cube",
        "cilindro": "cylinder",
        "cylinder": "cylinder",
        "esfera": "sphere",
        "sphere": "sphere",
        "dodecaedro": "dodecahedron",
        "icosaedro": "icosahedron",
    }
    for keyword, shape in shape_map.items():
        if keyword in text:
            return shape
    return None


def solve_geometry(normalized_text: str, raw_text: str) -> bool:
    op_map: list[tuple[str, Callable[..., object]]] = [
        ("area", geometria.area),
        ("perimetro", geometria.perimeter),
        ("perimeter", geometria.perimeter),
        ("volumen", geometria.volume),
        ("volume", geometria.volume),
    ]

    selected = None
    for keyword, fn in op_map:
        if keyword in normalized_text:
            selected = fn
            break

    if selected is None:
        return False

    shape = detect_shape(normalized_text)
    if shape is None:
        print("No pude detectar la figura geometrica.")
        return True

    numbers = extract_numbers(raw_text)
    if not numbers:
        print("No encontre valores numericos para la operacion geometrica.")
        return True

    args = [str(number) for number in numbers]

    try:
        outcome = selected(shape, *args)
    except ValueError as exc:
        print(f"Error: {exc}")
        return True

    for step in outcome.steps:
        print(step)
    return True


def solve_physics(normalized_text: str, raw_text: str) -> bool:
    command_map = {
        "fuerza": physics.force,
        "force": physics.force,
        "trabajo": physics.work,
        "work": physics.work,
        "energia cinetica": physics.kinetic_energy,
        "kinetic": physics.kinetic_energy,
        "energia potencial": physics.potential_energy,
        "potential": physics.potential_energy,
        "velocidad": physics.velocity,
        "velocity": physics.velocity,
        "aceleracion": physics.acceleration,
        "acceleration": physics.acceleration,
    }

    selected = None
    for keyword, fn in command_map.items():
        if keyword in normalized_text:
            selected = fn
            break

    if selected is None:
        return False

    numbers = extract_numbers(raw_text)
    if not numbers:
        print("No encontre valores numericos para la operacion de fisica.")
        return True

    args = [str(number) for number in numbers]

    try:
        outcome = selected(*args)
    except ValueError as exc:
        print(f"Error: {exc}")
        return True
    except TypeError:
        print("Cantidad incorrecta de valores para esa operacion de fisica.")
        return True

    for step in outcome.steps:
        print(step)
    return True


def extract_polynomial_expression(raw_text: str) -> str | None:
    candidates = re.findall(r"[0-9xX\+\-\*/\^\(\)\.\s]+", raw_text)
    candidates = [item.strip() for item in candidates if re.search(r"[a-zA-Z]", item)]
    if not candidates:
        return None
    return max(candidates, key=len)


def extract_polynomial_variable(normalized_text: str) -> str:
    match = re.search(r"\b(en|para|respecto a)\s+([a-z])\b", normalized_text)
    if match:
        return match.group(2)
    return "x"


def solve_polynomial(normalized_text: str, raw_text: str) -> bool:
    poly_keywords = [
        "polinom",
        "raiz",
        "raices",
        "roots",
        "paso",
        "pasos",
        "steps",
        "deriv",
        "factor",
        "expand",
        "evaluar",
        "eval",
    ]
    if not any(keyword in normalized_text for keyword in poly_keywords):
        return False

    expression = extract_polynomial_expression(raw_text)
    if expression is None:
        print("No pude detectar el polinomio. Ejemplo: raices de x^2 - 5*x + 6")
        return True

    preferred_symbol = extract_polynomial_variable(normalized_text)
    notation = analyze_notation(expression)
    try:
        poly, x_symbol, _notation = parse_polynomial_input(
            expression, preferred_symbol=preferred_symbol
        )
    except ValueError as exc:
        print(exc)
        return True

    if "deriv" in normalized_text:
        deriv = polynomial_derivative(poly, x_symbol)
        print(f"Derivada: {format_expression(deriv, notation)}")
        return True

    if "factor" in normalized_text:
        factored = polynomial_factor(poly)
        print(f"Factorizado: {format_expression(factored, notation)}")
        return True

    if "expand" in normalized_text:
        expanded = polynomial_expand(poly)
        print(f"Expandido: {format_expression(expanded, notation)}")
        return True

    if "evaluar" in normalized_text or "eval" in normalized_text:
        numbers = extract_numbers(raw_text)
        if not numbers:
            print("Indica un valor para evaluar. Ejemplo: evaluar x^2+1 en 3")
            return True
        value = numbers[-1]
        print(f"P({value}) = {polynomial_evaluate(poly, x_symbol, value)}")
        return True

    steps, roots = solve_roots_step_by_step(poly, x_symbol, notation)
    for step in steps:
        print(step)
    formatted_roots = [format_expression(root, notation) for root in roots]
    print(f"Raices: [{', '.join(formatted_roots)}]")
    return True


def solve_expression_fallback(raw: str) -> None:
    steps = simplify_expression(raw)
    write_history(steps)
    print(format_steps(steps))

    value = solve_expression(raw, log=False)
    if value is None:
        print("No pude interpretar la entrada. Escribe 'ayuda' para ver ejemplos.")
        return
    print(f"Resultado: {value}")


def route_query(raw: str) -> None:
    normalized = normalize(raw)

    if normalized in HELP_WORDS:
        print_help()
        return

    if ";" in raw or ("=" in raw and sum(1 for ch in raw if ch == "=") >= 1):
        solve_system_or_equation(raw)
        return

    if solve_geometry(normalized, raw):
        return

    if solve_physics(normalized, raw):
        return

    if solve_polynomial(normalized, raw):
        return

    solve_expression_fallback(raw)


def main() -> None:
    print("Math Console listo. Escribe 'ayuda' para ver comandos.")
    while True:
        user_input = input("\n> ").strip()
        if not user_input:
            continue
        if normalize(user_input) in EXIT_WORDS:
            print("Saliendo...")
            break

        try:
            route_query(user_input)
        except ValueError as error:
            print(f"Error: {error}")
        except Exception as error:
            print(f"Error al resolver: {error}")


if __name__ == "__main__":
    main()
