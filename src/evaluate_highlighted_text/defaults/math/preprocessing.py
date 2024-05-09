"""
Does the following:
- replaces `x` with `*` for multiplication
- replaces `^` with `**`
- replaces `log_n(x)` with `log(x, n)`
- replaces `logn(x)` with `log(x, n)`
"""

import pyparsing as pp

pp.ParserElement.enablePackrat()

number = pp.Combine(
    pp.Word(pp.nums)
    + pp.Optional("." + pp.Optional(pp.Word(pp.nums)))
    + pp.Optional(pp.one_of("e E") + pp.Word("+-" + pp.nums, pp.nums)),
)
variable = pp.Word(pp.alphas)
constant = number | variable

lpar = pp.Literal("(")
rpar = pp.Literal(")")

factorial_operator = pp.one_of("!")
unary_operator = pp.one_of("+ -")
exponentiation_operator = pp.one_of("^ **").add_parse_action(lambda: "**")
mult_div_operators = pp.one_of("* /")
add_sub_operators = pp.one_of("+ -")

expression = pp.Forward()

function_call = pp.Group(pp.Word(pp.alphas) + lpar + expression + rpar)
function_call |= pp.Group(
    pp.Literal("log_")
    + (pp.Group(lpar + expression + rpar) | constant)
    + lpar
    + expression
    + rpar,
    aslist=True,
).set_parse_action(lambda t: pp.ParseResults([["log(", t[0][3], ", ", t[0][1], ")"]]))
function_call |= pp.Group(
    pp.Literal("log") + number + lpar + expression + rpar,
    aslist=True,
).set_parse_action(lambda t: pp.ParseResults([["log(", t[0][3], ", ", t[0][1], ")"]]))

expression <<= pp.infix_notation(
    function_call | constant,
    [
        (
            factorial_operator,
            1,
            pp.OpAssoc.LEFT,
            lambda t: pp.ParseResults(["factorial(", t[0][0], ")"]),
        ),
        (unary_operator, 1, pp.OpAssoc.RIGHT),
        (exponentiation_operator, 2, pp.OpAssoc.LEFT),
        (mult_div_operators, 2, pp.OpAssoc.LEFT),
        (add_sub_operators, 2, pp.OpAssoc.LEFT),
    ],
    lpar=lpar,
    rpar=rpar,
)


def preprocess(text: str) -> str:
    return expression.transform_string(text)


if __name__ == "__main__":

    def test(expr: str, expected: str) -> None:
        actual = preprocess(expr)

        if actual != expected:
            msg = (
                f"FAILED: preprocess({expr!r})\n    {expected = !r}\n    {actual = !r}"
            )
            raise Exception(msg)

    # whitespace
    test("1 +  \t 2  + \n 3  + x  +\ny+  z", "1+2+3+x+y+z")

    # log_x(y)
    test("log_123(456)", "log(456, 123)")
    test("log_abc(xyz)", "log(xyz, abc)")
    test("log_(1+2+3)((x + y) * z)", "log((x+y)*z, (1+2+3))")

    # logN(x)
    test("log3(2 + 1)", "log(2+1, 3)")
    test("log1.5(9 ^ 5)", "log(9**5, 1.5)")

    # n!
    test("5!", "factorial(5)")
    test("x!", "factorial(x)")
    test("(1+2)!", "factorial((1+2))")
    test("-log(1+2)!", "-factorial(log(1+2))")

    print("All tests passed!")
