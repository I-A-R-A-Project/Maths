"""Formulas de fisica basica.

Separacion de responsabilidades: force, work, kinetic_energy, etc. son
funciones de CALCULO puro. No imprimen nada; devuelven un ComputationResult.
Si algo no se puede calcular (division por cero, argumentos invalidos),
levantan ValueError con un mensaje claro en vez de fallar silenciosamente.
Solo main() (uso standalone) y math_console.py deciden como imprimir.
"""
import sys

from calculator import simplify_expression
from common import ComputationResult, to_floats


def _compute(expression: str, label: str) -> ComputationResult:
    steps = simplify_expression(expression)
    try:
        value = float(steps[-1])
    except (ValueError, IndexError) as exc:
        raise ValueError(f"No se pudo evaluar la formula de {label}: {expression}") from exc

    from calculator import write_history
    write_history(steps)

    return ComputationResult(steps=[f"{label}: {expression} = {value}"], result=value)


def force(mass, acceleration):
    m, a = to_floats((mass, acceleration), ["masa", "aceleracion"])
    return _compute(f"{m} * {a}", "Fuerza (F = m x a)")


def work(force_value, distance):
    f, d = to_floats((force_value, distance), ["fuerza", "distancia"])
    return _compute(f"{f} * {d}", "Trabajo (W = F x d)")


def kinetic_energy(mass, velocity_value):
    m, v = to_floats((mass, velocity_value), ["masa", "velocidad"])
    return _compute(f"0.5 * {m} * ({v} ** 2)", "Energia cinetica (KE = 1/2 x m x v^2)")


def potential_energy(mass, gravity, height):
    m, g, h = to_floats((mass, gravity, height), ["masa", "gravedad", "altura"])
    return _compute(f"{m} * {g} * {h}", "Energia potencial (PE = m x g x h)")


def velocity(distance, time):
    d, t = to_floats((distance, time), ["distancia", "tiempo"])
    if t == 0:
        raise ValueError("El tiempo no puede ser 0 (division por cero).")
    return _compute(f"{d} / {t}", "Velocidad (v = d / t)")


def acceleration(final_v, initial_v, time):
    vf, vi, t = to_floats((final_v, initial_v, time), ["v_final", "v_inicial", "tiempo"])
    if t == 0:
        raise ValueError("El tiempo no puede ser 0 (division por cero).")
    return _compute(f"({vf} - {vi}) / {t}", "Aceleracion (a = (vf - vi) / t)")


def show_help():
    print("""
Physics Calculator - Comandos soportados:

  force m a                  -> F = m x a
  work f d                   -> W = F x d
  kinetic_energy m v         -> KE = 1/2 x m x v^2
  potential_energy m g h     -> PE = m x g x h
  velocity d t                -> v = d / t
  acceleration vf vi t        -> a = (vf - vi) / t

Ejemplos:
  python physics.py force 10 2
  python physics.py kinetic_energy 5 3
""")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("help", "-h", "--help"):
        show_help()
        return

    command = sys.argv[1].lower()
    args = sys.argv[2:]

    functions = {
        "force": force,
        "work": work,
        "kinetic_energy": kinetic_energy,
        "potential_energy": potential_energy,
        "velocity": velocity,
        "acceleration": acceleration,
    }

    func = functions.get(command)
    if func is None:
        print(f"Comando desconocido: '{command}'.")
        show_help()
        return

    try:
        outcome = func(*args)
    except ValueError as exc:
        print(f"Error: {exc}")
        return
    except TypeError:
        print(f"Cantidad incorrecta de argumentos para '{command}'.")
        show_help()
        return

    for step in outcome.steps:
        print(step)


if __name__ == "__main__":
    main()
