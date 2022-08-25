from functools import reduce

from combinators import Parser, constant, regex
from nodes import *

whitespace = regex(r"[\s]+")
comments = regex("[/][/].*") | regex("[/][*].[\s\S]*[*][/]")
ignored = (whitespace | comments).repeat()
token = lambda pattern: regex(pattern).bind(lambda x: ignored & constant(x))
infix = lambda operator_parser, term_parser: term_parser.bind(lambda head:
    operator_parser.bind(lambda op: term_parser.map(lambda term: (op, term)))
    .repeat().map(lambda tail:
        reduce(lambda x, op_y: op_y[0](x, op_y[1]), tail, head)))

FUNCTION = token(r"function\b")
IF = token(r"if\b")
ELSE = token(r"else\b")
RETURN = token(r"return\b")
VAR = token(r"var\b")
WHILE = token(r"while\b")
COMMA = token("[,]")
SEMICOLON = token("[;]")
LEFT_PAREN = token("[(]")
RIGHT_PAREN = token("[)]")
LEFT_BRACE = token("[{]")
RIGHT_BRACE = token("[}]")

NUMBER = token("[0-9]+").map(lambda digits: Number(int(digits)))
ID = token("[a-zA-Z_][a-zA-Z0-9_]*")

NOT = token("!").map(lambda _: Not)
EQUAL = token("==").map(lambda _: Equal)
ASSIGN = token("[=]").map(lambda _: Assign)
NOT_EQUAL = token("!=").map(lambda _: NotEqual)
PLUS = token("[+]").map(lambda _: Add)
MINUS = token("[-]").map(lambda _: Subtract)
STAR = token("[*]").map(lambda _: Multiply)
SLASH = token("[/]").map(lambda _: Divide)

# this is expression declaration, the definition will be later
expression = Parser()

# arguments <- (expression (COMMA expression)*)?
arguments = expression.bind(lambda head:
    (COMMA & expression).repeat().map(lambda tail: [head] + tail)
) | constant([])

# call <- ID LEFT_PAREN arguments RIGHT_PAREN
call = ID.bind(lambda callee:
    LEFT_PAREN & arguments.bind(lambda args:
    RIGHT_PAREN & constant(Call(callee, args))))

# atom <- call / ID / INTEGER / LEFT_PAREN expression RIGHT_PAREN
atom = (
    call | ID.map(lambda name: Id(name)) | NUMBER
    | (LEFT_PAREN & expression).bind(lambda expr: RIGHT_PAREN & constant(expr))
)

# unary <- NOT ? atom
unary = NOT.maybe().bind(lambda n: atom.map(lambda t: Not(t) if n else t))

# infix operators
product = infix(STAR | SLASH, unary)
sum_expr = infix(PLUS | MINUS, product)
comparison = infix(EQUAL | NOT_EQUAL, sum_expr)

# expression <- comparison
expression.parse = comparison.parse


# this is statement declaration, the definition will be later
statement = Parser()

# return_stmt <- RETURN expression SEMICOLON
return_stmt = RETURN & expression.bind(
    lambda expr: SEMICOLON & constant(Return(expr)))

# expression_stmt <- expression SEMICOLON
expression_stmt = expression.bind(lambda term: SEMICOLON & constant(term))

# if_stmt <- IF LEFT_PAREN expression RIGHT_PAREN statement ELSE statement
if_stmt = (IF & LEFT_PAREN & expression).bind(lambda condition:
    (RIGHT_PAREN & statement).bind(lambda consequence:
        (ELSE & statement).map(lambda alternative:
            If(condition, consequence, alternative))))

# while_stmt <- WHILE LEFT_PAREN expression RIGHT_PAREN statement
while_stmt = (WHILE & LEFT_PAREN & expression).bind(lambda condition:
    (RIGHT_PAREN & statement).map(lambda body:
        While(condition, body)))

# var_stmt <- VAR ID ASSIGN expression SEMICOLON
var_stmt = (VAR & ID).bind(lambda name:
    (ASSIGN & expression).bind(lambda value:
        SEMICOLON & constant(Var(name, value))))

# assignment_stmt <- ID ASSIGN expression SEMICOLON
assignment_stmt = ID.bind(lambda name:
    (ASSIGN & expression).bind(lambda value:
        SEMICOLON & constant(Assign(name, value))))

# block_stmt <- LEFT_BRACE statement* RIGHT_BRACE
block_stmt = (LEFT_BRACE & statement.repeat()).bind(lambda stmts:
    RIGHT_BRACE & constant(stmts))

# parameters <- (ID (COMMA ID)*)?
parameters = ID.bind(lambda head:
    (COMMA & ID).repeat().map(lambda tail: [head] + tail)
) | constant([])

# function_stmt <- FUNCTION ID LEFT_PAREN parameters RIGHT_PAREN block_stmt
function_stmt = (FUNCTION & ID).bind(lambda name:
    (LEFT_PAREN & parameters).bind(lambda params:
        (RIGHT_PAREN & block_stmt).map(lambda body:
            Function(name, params, body))))

# statement <- all the statements defined above
statement.parse = (
    return_stmt | function_stmt | if_stmt | while_stmt
    | var_stmt | assignment_stmt | block_stmt | expression_stmt
).parse

# the parser of the whole language
parser = ignored & statement.repeat().map(lambda stmts: Block(stmts))
