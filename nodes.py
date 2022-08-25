from dataclasses import dataclass, fields, make_dataclass
from collections import namedtuple


class AST:
    def __init__(self):
        raise NotImplementedError

    def __iter__(self):
        return (getattr(self, field.name) for field in fields(self))

@dataclass
class Number(AST):
    value: int


@dataclass
class Id(AST):
    name: str


@dataclass
class Not(AST):
    term: AST


@dataclass
class BinaryOperation(AST):
    left: AST
    operation: str
    right: AST


@dataclass
class Call(AST):
    calle: str
    args: list[AST]


@dataclass
class Return(AST):
    term: AST


@dataclass
class Block(AST):
    statements: list[AST]


@dataclass
class If(AST):
    conditional: AST
    consequence: AST
    alternative: AST


@dataclass
class Function:
    name: str
    parameters: list[str]
    body: AST


@dataclass
class Var:
    name: str
    value: AST


@dataclass
class Assign:
    name: str
    value: AST


@dataclass
class While:
    conditional: AST
    body: AST
