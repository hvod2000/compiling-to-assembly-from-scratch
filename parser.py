from combinators import Parser, constant, regex
from nodes import *

whitespace = regex(r"[\s]+")
comments = regex("[/][/].*") | regex("[/][*].[\s\S]*[*][/]")
ignored = (whitespace | comments).repeat()
token = lambda pattern: regex(pattern).bind(lambda x: ignored & constant(x))

FUNCTION = token("function\b")
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
NOT_EQUAL = token("!=").map(lambda _: NotEqual)
PLUS = token("[+]").map(lambda _: Add)
MINUS = token("[-]").map(lambda _: Subtract)
STAR = token("[*]").map(lambda _: Multiply)
SLASH = token("[/]").map(lambda _: Divide)
