import ast
import math
import operator
import re
import sys
from datetime import datetime

functions = {
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'log': math.log10,
    'ln': math.log,
    'abs': abs
}

constants = {
    'pi': math.pi,
    'e': math.e
}

# Unicamente estos nodos de AST son validos en una expresion aritmetica.
# Cualquier otra cosa (atributos, subscripts, llamadas a nombres no
# whitelisteados, comprensiones, strings, etc.) se rechaza antes de evaluar
# una sola operacion. No hay eval() ni compile() de por medio en ningun punto.
_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class UnsafeExpressionError(ValueError):
    """La expresion contiene algo fuera de la gramatica aritmetica permitida."""


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    if isinstance(node, ast.Constant):
        # Solo numeros. Nada de strings, bytes, None, etc.
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise UnsafeExpressionError(f"Valor no permitido: {node.value!r}")
        return node.value

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BINOPS:
            raise UnsafeExpressionError(f"Operador no permitido: {op_type.__name__}")
        return _BINOPS[op_type](_eval_node(node.left), _eval_node(node.right))

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARYOPS:
            raise UnsafeExpressionError(f"Operador unario no permitido: {op_type.__name__}")
        return _UNARYOPS[op_type](_eval_node(node.operand))

    if isinstance(node, ast.Name):
        if node.id in constants:
            return constants[node.id]
        raise UnsafeExpressionError(f"Nombre no permitido: '{node.id}'")

    if isinstance(node, ast.Call):
        # func debe ser un nombre simple ya whitelisteado; nada de
        # atributos (obj.metodo), ni llamadas indirectas.
        if not isinstance(node.func, ast.Name) or node.func.id not in functions:
            raise UnsafeExpressionError("Solo se permiten llamadas a funciones matematicas conocidas.")
        if node.keywords:
            raise UnsafeExpressionError("No se permiten argumentos con nombre.")
        args = [_eval_node(arg) for arg in node.args]
        return functions[node.func.id](*args)

    # Cualquier otro tipo de nodo (Attribute, Subscript, Lambda, Compare,
    # BoolOp, comprensiones, Str, List, Dict, Import, etc.) se rechaza.
    raise UnsafeExpressionError(f"Elemento no permitido en la expresion: {type(node).__name__}")


def format_number(n):
    if isinstance(n, float):
        n = round(n, 5)
        if n.is_integer():
            return str(int(n))
        return str(n)
    return str(n)

def safe_eval(expr):
    """Evalua una expresion aritmetica sin usar eval()/compile() sobre el
    string. Se parsea a AST y se recorre validando cada nodo contra una
    whitelist estricta antes de ejecutar ninguna operacion."""
    expr = expr.replace('^', '**')
    try:
        tree = ast.parse(expr, mode='eval')
        return _eval_node(tree)
    except (UnsafeExpressionError, SyntaxError, ZeroDivisionError, TypeError, ValueError, OverflowError, RecursionError):
        return None

def simplify_expression(expr):
    expr = expr.replace(' ', '')
    steps = [expr]

    def resolve_simple(expr):
        func_pattern = re.compile(r'([a-z]+)\(([^()]+)\)')
        while re.search(func_pattern, expr):
            expr = re.sub(func_pattern, lambda m: format_number(safe_eval(f"{m.group(1)}({m.group(2)})")), expr)
            steps.append(expr)

        paren_pattern = re.compile(r'\(([^()]+)\)')
        while re.search(paren_pattern, expr):
            expr = re.sub(paren_pattern, lambda m: format_number(safe_eval(m.group(1))), expr)
            steps.append(expr)

        power_pattern = re.compile(r'(-?\d+(\.\d+)?)(\^)(-?\d+(\.\d+)?)')
        while re.search(power_pattern, expr):
            expr = re.sub(power_pattern, lambda m: format_number(safe_eval(f"{m.group(1)} ** {m.group(4)}")), expr, count=1)
            steps.append(expr)

        md_pattern = re.compile(r'(-?\d+(\.\d+)?)([*/])(-?\d+(\.\d+)?)')
        while re.search(md_pattern, expr):
            expr = re.sub(md_pattern, lambda m: format_number(safe_eval(f"{m.group(1)} {m.group(3)} {m.group(4)}")), expr, count=1)
            steps.append(expr)

        addsub_pattern = re.compile(r'(-?\d+(\.\d+)?)([+-])(-?\d+(\.\d+)?)')
        while re.search(addsub_pattern, expr):
            expr = re.sub(addsub_pattern, lambda m: format_number(safe_eval(f"{m.group(1)} {m.group(3)} {m.group(4)}")), expr, count=1)
            steps.append(expr)

        return expr

    resolve_simple(expr)
    return steps

def format_steps(steps):
    """Formatea la lista de pasos con flechas, sin imprimir ni escribir nada."""
    return '\n'.join(("↓ " if i != 0 else "") + step for i, step in enumerate(steps))


def write_history(steps):
    """Escribe los pasos en el historial en disco. No imprime nada.
    El logging es best-effort: si falla la escritura (permisos, disco, etc.)
    no debe interrumpir el calculo en curso."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = format_steps(steps)
    try:
        with open("history.txt", "a", encoding="utf-8") as f:
            f.write(timestamp + "\n")
            f.write(result + "\n\n")
    except OSError:
        pass


def log_steps(steps):
    """Uso pensado para el CLI standalone de este script (log=True en
    solve_expression). Loguea a archivo Y imprime. Los modulos que usan
    calculator.py como libreria (geometria, physics, math_console) deben
    llamar con log=False y decidir ellos mismos si imprimen."""
    write_history(steps)
    print(format_steps(steps))

def solve_expression(expression: str, log: bool = False):
    steps = simplify_expression(expression)
    if log:
        log_steps(steps)
    try:
        return float(steps[-1])
    except ValueError:
        return None

def main():
    if len(sys.argv) > 1:
        expression = ' '.join(sys.argv[1:])
        solve_expression(expression, log=True)
    else:
        while True:
            expression = input("\nEnter an expression (or 'exit'): ")
            if expression.lower() == 'exit':
                break
            solve_expression(expression, log=True)

if __name__ == "__main__":
    main()
