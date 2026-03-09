import re
import unicodedata
from typing import Callable

from sympy import Eq, simplify, solve
from sympy.parsing.sympy_parser import parse_expr

import geometria
import physics
from calculator import solve_expression

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

2) Ecuaciones / sistemas:
   - x + y = 10; x - y = 2
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
   - derivada de x^3 - 2*x
   - factorizar x^2 - 9
   - evaluar x^2 + 1 en 3

Escribe 'salir' para terminar.
"""
    )


def solve_system_or_equation(raw: str) -> None:
    chunks = [part.strip() for part in raw.split(";") if part.strip()]
    equations = []

    for chunk in chunks:
        if "=" in chunk:
            left, right = chunk.split("=", 1)
            equations.append(Eq(parse_expr(left.replace("^", "**")), parse_expr(right.replace("^", "**"))))
        else:
            expr = parse_expr(chunk.replace("^", "**"))
            equations.append(Eq(expr, 0))

    if not equations:
        raise ValueError("No se encontraron ecuaciones validas.")

    symbols = sorted({symbol for eq in equations for symbol in eq.free_symbols}, key=lambda item: item.name)
    if not symbols:
        raise ValueError("No hay variables para resolver.")

    solutions = solve(equations, symbols, dict=True)

    if not solutions:
        print("No se encontro solucion.")
        return

    print("Solucion(es):")
    for index, item in enumerate(solutions, 1):
        parts = [f"{symbol} = {item.get(symbol)}" for symbol in symbols if symbol in item]
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
    selected(shape, *args)
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
    selected(*args)
    return True


def extract_polynomial_expression(raw_text: str) -> str | None:
    candidates = re.findall(r"[0-9xX\+\-\*/\^\(\)\.\s]+", raw_text)
    candidates = [item.strip() for item in candidates if "x" in item.lower()]
    if not candidates:
        return None
    return max(candidates, key=len).replace("^", "**")


def solve_polynomial(normalized_text: str, raw_text: str) -> bool:
    poly_keywords = ["polinom", "raiz", "raices", "roots", "deriv", "factor", "expand", "evaluar", "eval"]
    if not any(keyword in normalized_text for keyword in poly_keywords):
        return False

    expression = extract_polynomial_expression(raw_text)
    if expression is None:
        print("No pude detectar el polinomio. Ejemplo: raices de x^2 - 5*x + 6")
        return True

    poly = simplify(expression)
    x_symbol = next(iter(poly.free_symbols), None)
    if x_symbol is None:
        print(f"No hay variable en el polinomio: {poly}")
        return True

    if "deriv" in normalized_text:
        from sympy import diff

        print(f"Derivada: {diff(poly, x_symbol)}")
        return True

    if "factor" in normalized_text:
        from sympy import factor

        print(f"Factorizado: {factor(poly)}")
        return True

    if "expand" in normalized_text:
        from sympy import expand

        print(f"Expandido: {expand(poly)}")
        return True

    if "evaluar" in normalized_text or "eval" in normalized_text:
        numbers = extract_numbers(raw_text)
        if not numbers:
            print("Indica un valor para evaluar. Ejemplo: evaluar x^2+1 en 3")
            return True
        value = numbers[-1]
        print(f"P({value}) = {poly.subs(x_symbol, value)}")
        return True

    roots = solve(Eq(poly, 0), x_symbol)
    print(f"Raices: {roots}")
    return True


def solve_expression_fallback(raw: str) -> None:
    value = solve_expression(raw, log=True)
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
        except Exception as error:
            print(f"Error al resolver: {error}")


if __name__ == "__main__":
    main()
