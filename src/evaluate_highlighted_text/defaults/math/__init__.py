import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from . import preprocessing


def math(text: str) -> int | float:
    result = (
        parse_expr(
            preprocessing.preprocess(text),
            transformations=(
                (
                    *standard_transformations,
                    implicit_multiplication_application,
                )
            ),
        )
        .subs({"e": sp.E})
        .doit()
    )

    if isinstance(result, sp.Integer):
        return int(result)

    return float(result)


def math_tests() -> None:
    def test(expr: str, expected: float) -> None:
        actual = math(expr)

        if actual != expected:
            msg = f"FAILED: math({expr!r})\n    {expected = !r}\n    {actual = !r}"
            raise Exception(msg)

    test("1+1", 2)

    print("All tests passed!")


def run_tests() -> None:
    print("Running preprocessing tests...")
    preprocessing.run_tests()

    print("Running math tests...")
    math_tests()
