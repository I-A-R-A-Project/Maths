"""Resolucion de sistemas de N ecuaciones con N variables, con pasos.

Separacion de responsabilidades:
- `parse_system` y `solve_system_step_by_step` son funciones de CALCULO
  puro: no imprimen nada, devuelven datos. Las usa tanto math_console.py
  como el main() de este mismo archivo.
- Solo `main()` (uso standalone `python equation.py "..."`) imprime.
"""
import sys

from sympy import Eq, simplify, solve
from sympy.parsing.sympy_parser import parse_expr


def parse_equation_chunk(chunk: str) -> Eq:
    chunk = chunk.strip()
    if not chunk:
        raise ValueError("Se encontro una ecuacion vacia.")
    normalized = chunk.replace("^", "**")
    if "=" in normalized:
        left, right = normalized.split("=", 1)
        return Eq(parse_expr(left), parse_expr(right))
    # Sin '=', se interpreta como "expresion = 0"
    return Eq(parse_expr(normalized), 0)


def parse_system(raw_text: str) -> list[Eq]:
    """Convierte 'x+y=10; x-y=2' (o N ecuaciones separadas por ';') en
    una lista de sympy.Eq. No esta limitado a 2 ecuaciones ni a x/y/z."""
    chunks = [part.strip() for part in raw_text.split(";") if part.strip()]
    if not chunks:
        raise ValueError("No se encontraron ecuaciones validas.")
    return [parse_equation_chunk(chunk) for chunk in chunks]


def solve_system_step_by_step(equations: list[Eq]):
    """Resuelve un sistema de N ecuaciones con N variables narrando el
    proceso de sustitucion (generaliza el metodo de sustitucion a
    cualquier cantidad de variables, no solo 2).

    Devuelve (steps: list[str], solutions: list[dict[Symbol, expr]]).
    No imprime nada.
    """
    if not equations:
        raise ValueError("No se proporcionaron ecuaciones.")

    steps = ["Sistema original:"]
    for i, eq in enumerate(equations, 1):
        steps.append(f"  {i}) {eq.lhs} = {eq.rhs}")

    all_symbols = sorted(
        {s for eq in equations for s in eq.free_symbols}, key=lambda s: s.name
    )
    if not all_symbols:
        raise ValueError("El sistema no tiene variables para resolver.")

    remaining_eqs = list(equations)
    remaining_symbols = list(all_symbols)
    substitutions = {}
    order = []
    step_counter = 1

    # Sustitucion iterativa: en cada vuelta, buscamos CUALQUIER ecuacion
    # de la que se pueda despejar CUALQUIER variable aun no resuelta.
    # Esto generaliza el metodo de sustitucion manual a N variables sin
    # asumir un orden fijo (x, y, z) ni una cantidad fija de ecuaciones.
    while remaining_eqs and remaining_symbols:
        chosen_symbol = None
        source_eq = None
        isolated_expr = None

        for eq in remaining_eqs:
            candidates = [s for s in remaining_symbols if eq.has(s)]
            for sym in candidates:
                try:
                    sols = solve(eq, sym)
                except Exception:
                    sols = []
                if sols:
                    chosen_symbol, source_eq, isolated_expr = sym, eq, sols[0]
                    break
            if chosen_symbol is not None:
                break

        if chosen_symbol is None:
            # No se pudo despejar ninguna variable restante por sustitucion
            # simple (sistema no lineal acoplado, redundante, etc.)
            break

        step_counter += 1
        steps.append(
            f"Paso {step_counter - 1}: despejar {chosen_symbol} de "
            f"{source_eq.lhs} = {source_eq.rhs}  ->  {chosen_symbol} = {isolated_expr}"
        )

        remaining_eqs.remove(source_eq)
        remaining_symbols.remove(chosen_symbol)
        substitutions[chosen_symbol] = isolated_expr
        order.append(chosen_symbol)

        updated_eqs = []
        for eq in remaining_eqs:
            new_lhs = eq.lhs.subs(chosen_symbol, isolated_expr)
            new_rhs = eq.rhs.subs(chosen_symbol, isolated_expr)
            difference = simplify(new_lhs - new_rhs)

            if difference == 0:
                # La ecuacion quedo trivialmente satisfecha (era redundante
                # dado lo ya sustituido); no aporta mas informacion, se
                # descarta en vez de intentar acceder a .lhs/.rhs de un
                # booleano (sympy colapsa Eq(x, x) a True).
                steps.append(
                    f"  Sustituir en {eq.lhs} = {eq.rhs}:  ->  ecuacion redundante (0 = 0), se descarta."
                )
                continue

            if not difference.free_symbols:
                # La diferencia es una constante distinta de 0 (p. ej. 3 = 0):
                # el sistema es inconsistente. sympy colapsaria esto a False,
                # asi que lo detectamos antes y lo reportamos como tal en vez
                # de dejar que un AttributeError opaco interrumpa el calculo.
                raise ValueError(
                    "El sistema no tiene solucion: es inconsistente "
                    f"(al sustituir en '{eq.lhs} = {eq.rhs}' se obtiene una contradiccion)."
                )

            # evaluate=False evita que sympy vuelva a intentar colapsar la
            # ecuacion a un booleano; ya sabemos que no es trivial ni
            # contradictoria, asi que es segura de mostrar y reutilizar.
            new_eq = Eq(new_lhs, new_rhs, evaluate=False)
            if difference != simplify(eq.lhs - eq.rhs):
                steps.append(
                    f"  Sustituir en {eq.lhs} = {eq.rhs}:  ->  {new_eq.lhs} = {new_eq.rhs}"
                )
            updated_eqs.append(new_eq)
        remaining_eqs = updated_eqs

    if remaining_eqs or remaining_symbols:
        # Sistema no lineal, redundante o subdeterminado: la narracion por
        # sustitucion no alcanza. En vez de fallar, resolvemos el resto
        # directamente con SymPy para no dar un resultado incorrecto.
        steps.append(
            "No se pudo continuar por sustitucion directa; "
            "resolviendo el resto del sistema con SymPy."
        )
        solutions = solve(equations, all_symbols, dict=True)
        return steps, solutions

    # Sustitucion hacia atras: reemplazamos en orden inverso para que cada
    # variable quede expresada solo en numeros.
    final_values = {}
    for sym in reversed(order):
        expr = substitutions[sym].subs(final_values)
        final_values[sym] = simplify(expr)

    steps.append("Sustitucion hacia atras:")
    for sym in all_symbols:
        steps.append(f"  {sym} = {final_values[sym]}")

    return steps, [final_values]


def main() -> None:
    if len(sys.argv) < 2:
        print('Uso: python equation.py "x+y=10; x-y=2"')
        print('Tambien admite N ecuaciones: "x+y+z=6; x-y=1; 2*x+z=7"')
        sys.exit(1)

    raw = sys.argv[1]
    try:
        equations = parse_system(raw)
        steps, solutions = solve_system_step_by_step(equations)
    except ValueError as exc:
        print(f"Error: {exc}")
        return
    except Exception as exc:
        print(f"Error inesperado: {exc}")
        return

    for step in steps:
        print(step)

    if not solutions:
        print("No se encontro solucion.")
        return

    print("Solucion(es):")
    for index, sol in enumerate(solutions, 1):
        parts = [f"{sym} = {sol.get(sym)}" for sym in sorted(sol, key=lambda s: s.name)]
        print(f"  {index}) " + ", ".join(parts))


if __name__ == "__main__":
    main()
