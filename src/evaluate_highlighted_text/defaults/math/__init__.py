import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from .preprocessing import preprocess


def math(text: str) -> int | float:
    result = parse_expr(
        preprocess(text),
        transformations=(
            (
                *standard_transformations,
                implicit_multiplication_application,
            )
        ),
    ).doit()

    if isinstance(result, sp.Integer):
        return int(result)

    return float(result)
