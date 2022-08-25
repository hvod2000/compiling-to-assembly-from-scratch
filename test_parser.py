from parser import parser
from nodes import *


assert parser.parse_string("1;") == Block([Number(1)])
assert parser.parse_string("1;") != Block([(1,)])

source = """
    function factorial(n) {
        var result = 1;
        while (n != 1) {
            result = result * n;
            n = n - 1;
        }
        return result;
    }
"""

expected = Block([
    Function("factorial", ["n"], [
        Var("result", Number(value=1)),
        While(BinaryOperation(Id("n"), "!=", Number(1)), [
            Assign("result", BinaryOperation(Id("result"), "*", Id("n"))),
            Assign("n", BinaryOperation(Id("n"),"-", Number(1)))
        ]),
        Return(Id("result")),
    ])
])

assert parser.parse_string(source) == expected
