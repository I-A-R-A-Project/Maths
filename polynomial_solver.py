from sympy import Eq, Poly, diff, expand, factor, lambdify, simplify, solve, symbols
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)
import sys
from common import (
    analyze_notation,
    format_expression,
    format_symbol,
    normalize_algebraic_notation,
    reduce_numeric_subexpressions,
)

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


def parse_polynomial_input(poly_input: str, preferred_symbol: str = "x"):
    try:
        notation = analyze_notation(poly_input)
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

    return poly, x_symbol, notation


def polynomial_derivative(poly, x_symbol):
    return diff(poly, x_symbol)


def polynomial_factor(poly):
    return factor(poly)


def polynomial_expand(poly):
    return expand(poly)


def polynomial_evaluate(poly, x_symbol, value):
    return poly.subs(x_symbol, value)


def solve_roots_step_by_step(poly, x_symbol, notation):
    steps: list[str] = []
    expanded = expand(poly)
    steps.append(f"1) Polinomio: {format_expression(expanded, notation)}")
    extra_symbols = sorted(sym.name for sym in poly.free_symbols if sym != x_symbol)
    if extra_symbols:
        formatted_symbols = [format_symbol(name, notation) for name in extra_symbols]
        steps.append(
            "2) Variables tratadas como constantes: " + ", ".join(formatted_symbols)
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
        symbol_label = format_symbol(str(x_symbol), notation)
        steps.append(
            f"{step_index + 1}) Monomio: raiz {symbol_label}=0 con multiplicidad {degree}."
        )
        return steps, [0]

    if factored != expanded:
        steps.append(
            f"{step_index + 1}) Factorizar: {format_expression(factored, notation)}"
        )
    else:
        steps.append(f"{step_index + 1}) Factorizar: no se pudo factorizar en factores simples.")

    if degree == 0:
        roots = []
        steps.append(f"{step_index + 2}) Polinomio constante: no hay raices.")
        return steps, roots

    if degree == 1:
        a, b = poly_obj.all_coeffs()
        symbol_label = format_symbol(str(x_symbol), notation)
        linear_expr = a * x_symbol + b
        steps.append(
            f"{step_index + 2}) Forma lineal: "
            f"{format_expression(linear_expr, notation)} = 0"
        )
        root = -b / a
        steps.append(f"{step_index + 3}) {symbol_label} = -b/a = {-b}/{a} = {root}")
        return steps, [root]

    if degree == 2:
        a, b, c = poly_obj.all_coeffs()
        steps.append(f"{step_index + 2}) Coeficientes: a={a}, b={b}, c={c}")
        discriminant = b**2 - 4 * a * c
        steps.append(f"{step_index + 3}) Discriminante: Δ = b^2 - 4ac = {discriminant}")
        symbol_label = format_symbol(str(x_symbol), notation)
        steps.append(f"{step_index + 4}) Formula: {symbol_label} = (-b ± sqrt(Δ)) / (2a)")
        roots = solve(Eq(expanded, 0), x_symbol)
        return steps, roots

    if factored != expanded:
        steps.append(f"{step_index + 2}) Resolver cada factor = 0.")
    else:
        steps.append(f"{step_index + 2}) Sin factorizacion util; resolviendo con SymPy.")

    roots = solve(Eq(expanded, 0), x_symbol)
    return steps, roots


def format_roots(roots, notation) -> str:
    formatted = [format_expression(root, notation) for root in roots]
    return f"[{', '.join(formatted)}]"


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
        poly, x_symbol, notation = parse_polynomial_input(
            poly_input, preferred_symbol=preferred_symbol
        )
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
        steps, roots = solve_roots_step_by_step(poly, x_symbol, notation)
        for step in steps:
            print(step)
        print(f"Roots: {format_roots(roots, notation)}")

    elif option == "steps":
        steps, roots = solve_roots_step_by_step(poly, x_symbol, notation)
        for step in steps:
            print(step)
        print(f"Roots: {format_roots(roots, notation)}")

    elif option == "derivative":
        deriv = polynomial_derivative(poly, x_symbol)
        print(f"Derivative: {format_expression(deriv, notation)}")

    elif option == "factor":
        factored = polynomial_factor(poly)
        print(f"Factored form: {format_expression(factored, notation)}")

    elif option == "expand":
        expanded = polynomial_expand(poly)
        print(f"Expanded form: {format_expression(expanded, notation)}")

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
