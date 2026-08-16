import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

from calculator import safe_eval


@dataclass(frozen=True)
class ComputationResult:
    """Resultado estructurado de un calculo de dominio (geometria, fisica,
    ecuaciones, etc). Las funciones de calculo devuelven esto en vez de
    imprimir directamente; quien las llama (math_console.py, o el main()
    de cada script para uso standalone) decide como y cuando mostrarlo."""

    steps: List[str] = field(default_factory=list)
    result: Any = None

    @property
    def formatted(self) -> str:
        return "\n".join(self.steps)


def to_floats(args, names: List[str]) -> List[float]:
    """Valida que `args` tenga la cantidad esperada de valores numericos y
    los convierte a float. Levanta ValueError con un mensaje claro en vez
    de dejar que un IndexError/ValueError generico se propague sin contexto."""
    if len(args) != len(names):
        raise ValueError(
            f"Se esperaban {len(names)} valor(es) ({', '.join(names)}), "
            f"se recibieron {len(args)}."
        )
    try:
        return [float(value) for value in args]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Todos los valores deben ser numericos: {list(args)}") from exc


@dataclass(frozen=True)
class Notation:
    power_style: str
    mul_style: str
    symbol_case: Dict[str, str]


def analyze_notation(expr: str) -> Notation:
    power_style = "python"
    if "**" in expr:
        power_style = "python"
    elif "^" in expr:
        power_style = "caret"
    elif re.search(r"[A-Za-z]\d+", expr):
        power_style = "implicit"

    mul_style = "explicit" if "*" in expr or "·" in expr else "implicit"

    symbol_case: Dict[str, str] = {}
    for ch in expr:
        if ch.isalpha():
            lower = ch.lower()
            if lower not in symbol_case:
                symbol_case[lower] = ch

    return Notation(power_style=power_style, mul_style=mul_style, symbol_case=symbol_case)


def normalize_algebraic_notation(expr: str) -> str:
    expr = expr.replace("·", "*").replace("−", "-").replace("–", "-")
    expr = expr.replace("^", "**")
    expr = re.sub(r"\s+", "", expr)

    def replace_power(match: re.Match) -> str:
        return f"{match.group(1)}**{match.group(2)}"

    expr = re.sub(r"([a-zA-Z])(\d+)", replace_power, expr)
    expr = "".join(ch.lower() if ch.isalpha() else ch for ch in expr)
    return expr


def reduce_numeric_subexpressions(expr: str) -> str:
    pattern = re.compile(r"\(([^()]+)\)")

    while True:
        changed = False

        def replacer(match: re.Match) -> str:
            nonlocal changed
            inner = match.group(1)
            if re.search(r"[a-zA-Z]", inner):
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


def format_expression(expr, notation: Notation) -> str:
    text = str(expr)

    for lower, original in notation.symbol_case.items():
        if lower != original:
            text = re.sub(
                rf"(?<![A-Za-z]){re.escape(lower)}(?![A-Za-z])",
                original,
                text,
            )

    if notation.power_style != "python":
        text = text.replace("**", "^")

    if notation.power_style == "implicit":
        text = re.sub(r"([A-Za-z])\^(\d+)", r"\1\2", text)

    if notation.mul_style == "implicit":
        text = re.sub(r"(?<=\w)\*(?=\w)", "", text)
        text = re.sub(r"(?<=\))\*(?=\()", "", text)
        text = re.sub(r"(?<=\w)\*(?=\()", "", text)
        text = re.sub(r"(?<=\))\*(?=\w)", "", text)

    return text


def format_symbol(symbol: str, notation: Notation) -> str:
    lower = symbol.lower()
    return notation.symbol_case.get(lower, symbol)
