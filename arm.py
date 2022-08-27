import functools
from itertools import chain
from dataclasses import dataclass
from typing import Iterator
from nodes import *


@dataclass
class Environment:
    locals: dict[str, int]
    next_local_offset: int

    def push(self, variables: list[str]) -> Iterator[str]:
        if len(variables) > 4:
            raise NotImplementedError(">4 params is not implemented yet")
        registers = [f"r{i}" for i in range(len(variables))]
        if len(registers) % 2 != 0:
            registers.append("ip")
        for i, v in enumerate(variables):
            self.locals[v] = (i - len(registers)) * 4
        yield "mov fp, sp"
        if registers:
            yield "push {" + ", ".join(registers) + "}"
        self.next_local_offset = -4 - 4 * len(registers)

    def push_var(self, variable) -> Iterator[str]:
        # TODO: waste less stack space by taking record of offsets
        if variable in self.locals:
            yield f"str r0, [fp, #{self.locals[variable]}]"
        else:
            self.locals[variable] = self.next_local_offset - 4
            yield "push {r0, ip}"
            self.next_local_offset -= 8

    def free(self) -> Iterator[str]:
        if self.locals:
            yield "mov sp, fp"
        self.locals = {}
        self.next_local_offset = 0


def label_factory(seed: int = 0):
    def generate_label() -> str:
        nonlocal seed
        label = ".L" + hex(seed)[2:]
        seed += 1
        return label
    return generate_label


new_label = label_factory(1)


@functools.singledispatch
def emit(ast: AST, env: Environment) -> Iterator[str]:
    raise NotImplementedError(f"{ast}:{type(ast)}")


@emit.register
def _(block: Block, env: Environment) -> Iterator[str]:
    for statement in block.statements:
        yield from emit(statement, env)


@emit.register
def _(f: Function, env: Environment) -> Iterator[str]:
    params = f.parameters
    if f.name == "main":
        yield ".global main"
    yield f.name + ":"
    yield "  push {fp, lr}"
    for line in chain(env.push(params), emit(f.body, env), env.free()):
        yield "  " + line
    yield "  mov r0, #0"
    yield "  pop {fp, pc}"


@emit.register
def _(number: Number, env: Environment) -> Iterator[str]:
    yield f"ldr r0, ={number.value}"


@emit.register
def _(node: Not, env: Environment) -> Iterator[str]:
    yield from emit(node.term, env)
    yield "cmp r0, #0"
    yield "moveq r0, #1"
    yield "movne r0, #0"


BINARY_OPERATIONS = {
    "+": "add r0, r1, r0",
    "-": "sub r0, r1, r0",
    "*": "mul r0, r1, r0",
    "/": "udiv r0, r1, r0",
    "==": "cmp r1, r0\nmoveq r0, #1\nmovne r0, #0",
    "!=": "cmp r1, r0\nmoveq r0, #0\nmovne r0, #1",
}


@emit.register
def _(binary: BinaryOperation, env: Environment) -> Iterator[str]:
    yield from emit(binary.left, env)
    yield "push {r0, ip}"
    yield from emit(binary.right, env)
    yield "pop {r1, ip}"
    yield from BINARY_OPERATIONS[binary.operation].split("\n")


@emit.register
def _(call: Call, env: Environment) -> Iterator[str]:
    if len(call.args) == 1:
        yield from emit(call.args[0], env)
    elif len(call.args) > 1:
        extra_args = len(call.args) - 1
        if extra_args % 2 == 1:
            extra_args += 1
        yield f"sub sp, sp, #{4 * extra_args}"
        for i, arg in enumerate(call.args[1:]):
            yield from emit(arg, env)
            yield f"str r0, [sp, #{4*i}]"
        yield from emit(call.args[0], env)
        registers = [f"r{i+1}" for i in range(extra_args - 1)]
        yield "pop {" + ", ".join(registers) + "}"
    yield f"bl {call.calle}"


@emit.register
def _(if_node: If, env: Environment) -> Iterator[str]:
    alt_label = new_label()
    end_label = new_label() if if_node.alternative != Block([]) else alt_label
    yield from emit(if_node.conditional, env)
    yield "cmp r0, #0"
    yield f"beq {alt_label}"
    yield from emit(if_node.consequence, env)
    if alt_label != end_label:
        yield f"b {end_label}"
        yield f"{alt_label}:"
        yield from emit(if_node.alternative, env)
    yield f"{end_label}:"


@emit.register
def _(variable: Id, env: Environment) -> Iterator[str]:
    # TODO add error message about undefined variable
    offset = env.locals[variable.name]
    yield f"ldr r0, [fp, #{offset}]"


@emit.register
def _(ret: Return, env: Environment) -> Iterator[str]:
    yield from emit(ret.term, env)
    yield "mov sp, fp"
    yield "pop {fp, pc}"


@emit.register
def _(var: Var, env: Environment) -> Iterator[str]:
    yield from emit(var.value, env)
    yield from env.push_var(var.name)


@emit.register
def _(assgin: Assign, env: Environment) -> Iterator[str]:
    # TODO add good error message about undefined variable
    if assgin.name not in env.locals:
        raise Exception(f'"{assgin.name}" is undefined')
    yield from emit(assgin.value, env)
    yield from env.push_var(assgin.name)


@emit.register
def _(whl: While, env: Environment):
    start_label = new_label()
    end_label = new_label()
    yield f"{start_label}:"
    yield from emit(whl.conditional, env)
    yield "cmp r0, #0"
    yield f"beq {end_label}"
    yield from emit(whl.body, env)
    yield f"b {start_label}"
    yield f"{end_label}:"
