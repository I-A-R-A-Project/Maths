import re
from sympy import Eq, Poly, diff, expand, factor, lambdify, simplify, solve, symbols
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)
import sys
from calculator import safe_eval

x = symbols('x')
TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)

def show_help():
    print("""
Usage: python polynomial_solver.py "<polynomial>" [option] [value|var]

Options:
  eval [value]     - Evaluate the polynomial at a specific value of x.
  roots            - Solve for the roots of the polynomial (shows steps).
  steps            - Show the step-by-step solving process and roots.
  derivative       - Show the derivative of the polynomial.
  factor           - Factor the polynomial (if possible).
  expand           - Expand the polynomial.
  plot             - Plot the polynomial curve.
  help             - Show this help message.

Examples:
  python polynomial_solver.py "x**2 - 5*x + 6" roots
  python polynomial_solver.py "x**2 - 5*x + 6" steps
  python polynomial_solver.py "x**2 - 5*x + 6" eval 2
  python polynomial_solver.py "x*(x - 2)" expand
  python polynomial_solver.py "x**3 - 3*x" plot
""")


def reduce_numeric_subexpressions(expr: str) -> str:
    expr = expr.replace("^", "**").replace("X", "x")
    pattern = re.compile(r"\(([^()]+)\)")

    while True:
        changed = False

        def replacer(match: re.Match) -> str:
            nonlocal changed
            inner = match.group(1)
            if re.search(r"[a-zA-Z]", inner) or "x" in inner.lower():
                return f"({inner})"
            value = safe_eval(inner)
            if value is None:
                return f"({inner})"
            changed = True
            return str(value)

        updated = re.sub(pattern, replacer, expr)
        if not changed:
            return updated
        expr = updated


def normalize_algebraic_notation(expr: str) -> str:
    expr = expr.replace("·", "*").replace("−", "-").replace("–", "-")
    expr = expr.replace("^", "**").replace("X", "x")
    expr = re.sub(r"\s+", "", expr)

    def replace_power(match: re.Match) -> str:
        return f"{match.group(1)}**{match.group(2)}"

    expr = re.sub(r"([a-zA-Z])(\d+)", replace_power, expr)
    return expr


def parse_polynomial_input(poly_input: str, preferred_symbol: str = "x"):
    try:
        normalized = normalize_algebraic_notation(poly_input)
        normalized = reduce_numeric_subexpressions(normalized)
        expr = parse_expr(normalized, transformations=TRANSFORMATIONS)
        poly = simplify(expr)
    except Exception as exc:
        raise ValueError(
            "Polinomio invalido. Si usas PowerShell, pon la expresion entre "
            "comillas o usa --% para evitar expansion de '*'. "
            f"Detalle: {exc}"
        ) from exc

    symbols = list(poly.free_symbols)
    if not symbols:
        raise ValueError(f"No hay variable en el polinomio: {poly}")
    if len(symbols) > 1:
        chosen = next((sym for sym in symbols if sym.name == preferred_symbol), None)
        if chosen is None:
            names = ", ".join(sorted(sym.name for sym in symbols))
            raise ValueError(
                f"Variable '{preferred_symbol}' no encontrada. Variables: {names}."
            )
        x_symbol = chosen
    else:
        x_symbol = symbols[0]

    return poly, x_symbol


def polynomial_derivative(poly, x_symbol):
    return diff(poly, x_symbol)


def polynomial_factor(poly):
    return factor(poly)


def polynomial_expand(poly):
    return expand(poly)


def polynomial_evaluate(poly, x_symbol, value):
    return poly.subs(x_symbol, value)


def solve_roots_step_by_step(poly, x_symbol):
    steps: list[str] = []
    expanded = expand(poly)
    steps.append(f"1) Polinomio: {expanded}")
    extra_symbols = sorted(sym.name for sym in poly.free_symbols if sym != x_symbol)
    if extra_symbols:
        steps.append(
            "2) Variables tratadas como constantes: " + ", ".join(extra_symbols)
        )

    try:
        poly_obj = Poly(expanded, x_symbol)
    except Exception:
        roots = solve(Eq(expanded, 0), x_symbol)
        step_index = 3 if extra_symbols else 2
        steps.append(f"{step_index}) No es un polinomio clasico; resolviendo con SymPy.")
        return steps, roots

    degree = poly_obj.degree()
    step_index = 3 if extra_symbols else 2
    steps.append(f"{step_index}) Grado: {degree}")

    factored = factor(expanded)
    if poly_obj.length() == 1 and degree > 0:
        steps.append(
            f"{step_index + 1}) Monomio: raiz {x_symbol}=0 con multiplicidad {degree}."
        )
        return steps, [0]

    if factored != expanded:
        steps.append(f"{step_index + 1}) Factorizar: {factored}")
    else:
        steps.append(f"{step_index + 1}) Factorizar: no se pudo factorizar en factores simples.")

    if degree == 0:
        roots = []
        steps.append(f"{step_index + 2}) Polinomio constante: no hay raices.")
        return steps, roots

    if degree == 1:
        a, b = poly_obj.all_coeffs()
        steps.append(f"{step_index + 2}) Forma lineal: {a}*{x_symbol} + {b} = 0")
        root = -b / a
        steps.append(f"{step_index + 3}) {x_symbol} = -b/a = {-b}/{a} = {root}")
        return steps, [root]

    if degree == 2:
        a, b, c = poly_obj.all_coeffs()
        steps.append(f"{step_index + 2}) Coeficientes: a={a}, b={b}, c={c}")
        discriminant = b**2 - 4 * a * c
        steps.append(f"{step_index + 3}) Discriminante: Δ = b^2 - 4ac = {discriminant}")
        steps.append(f"{step_index + 4}) Formula: {x_symbol} = (-b ± sqrt(Δ)) / (2a)")
        roots = solve(Eq(expanded, 0), x_symbol)
        return steps, roots

    if factored != expanded:
        steps.append(f"{step_index + 2}) Resolver cada factor = 0.")
    else:
        steps.append(f"{step_index + 2}) Sin factorizacion util; resolviendo con SymPy.")

    roots = solve(Eq(expanded, 0), x_symbol)
    return steps, roots


def plot_polynomial(poly):
    import matplotlib.pyplot as plt
    import numpy as np

    symbol = next(iter(poly.free_symbols), x)
    f = lambdify(symbol, poly, "numpy")
    x_vals = np.linspace(-10, 10, 400)
    y_vals = f(x_vals)

    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    plt.plot(x_vals, y_vals, label=f"P(x) = {poly}")
    plt.title("Polynomial Graph")
    plt.xlabel("x")
    plt.ylabel("P(x)")
    plt.legend()
    plt.grid(True)
    return plt


def main():
    if len(sys.argv) < 3:
        show_help()
        return

    poly_input = sys.argv[1]
    option = sys.argv[2]

    try:
        preferred_symbol = "x"
        if option in {"roots", "steps"} and len(sys.argv) >= 4:
            preferred_symbol = sys.argv[3]
        poly, x_symbol = parse_polynomial_input(poly_input, preferred_symbol=preferred_symbol)
    except ValueError as exc:
        print(exc)
        return

    if option == "eval":
        if len(sys.argv) != 4:
            print("Missing value for evaluation.")
            return
        try:
            val = float(sys.argv[3])
            f = lambdify(x_symbol, poly, "math")
            result = f(val)
            print(f"P({val}) = {result}")
        except Exception as e:
            print(f"Error evaluating: {e}")

    elif option == "roots":
        steps, roots = solve_roots_step_by_step(poly, x_symbol)
        for step in steps:
            print(step)
        print(f"Roots: {roots}")

    elif option == "steps":
        steps, roots = solve_roots_step_by_step(poly, x_symbol)
        for step in steps:
            print(step)
        print(f"Roots: {roots}")

    elif option == "derivative":
        deriv = polynomial_derivative(poly, x_symbol)
        print(f"Derivative: {deriv}")

    elif option == "factor":
        factored = polynomial_factor(poly)
        print(f"Factored form: {factored}")

    elif option == "expand":
        expanded = polynomial_expand(poly)
        print(f"Expanded form: {expanded}")

    elif option == "plot":
        plot = plot_polynomial(poly)
        plot.show()

    elif option == "help":
        show_help()

    else:
        print(f"Unknown option: {option}")
        show_help()


if __name__ == "__main__":
    main()
