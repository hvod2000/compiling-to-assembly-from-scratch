import functools
from nodes import *
from typing import Iterator


def label_factory(seed: int = 0):
    def generate_label() -> str:
        nonlocal seed
        label = ".L" + hex(seed)[2:]
        seed += 1
        return label
    return generate_label


new_label = label_factory(1)


@functools.singledispatch
def emit(ast: AST) -> Iterator[str]:
    raise NotImplementedError(f"{ast}:{type(ast)}")


@emit.register
def _(block: Block) -> Iterator[str]:
    for statement in block.statements:
        yield from emit(statement)


@emit.register
def _(f: Function) -> Iterator[str]:
    if f.name == "main":
        yield ".global main"
    yield f.name + ":"
    yield "  push {fp, lr}"
    for line in emit(f.body):
        yield "  " + line
    yield "  mov r0, #0"
    yield "  pop {fp, pc}"


@emit.register
def _(checker: Assert) -> Iterator[str]:
    yield from emit(checker.condition)
    yield "cmp r0, #1"
    yield "moveq r0, #'.'"
    yield "movne r0, #'F'"
    yield "bl putchar"


@emit.register
def _(number: Number) -> Iterator[str]:
    yield f"ldr r0, ={number.value}"


@emit.register
def _(node: Not) -> Iterator[str]:
    yield from emit(node.term)
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
def _(binary: BinaryOperation) -> Iterator[str]:
    yield from emit(binary.left)
    yield "push {r0, ip}"
    yield from emit(binary.right)
    yield "pop {r1, ip}"
    yield from BINARY_OPERATIONS[binary.operation].split("\n")


@emit.register
def _(call: Call) -> Iterator[str]:
    count = len(call.args)
    if count == 1:
        yield from emit(call.args[0])
    elif count > 1:
        # TODO: what about 8-byte stack alignment?
        yield f"sub sp, sp, #{4 * count - 4}"
        for i, arg in enumerate(call.args[1:], 1):
            yield from emit(arg)
            yield f"str r0, [sp, #{4*i}]"
        yield from emit(call.args[0])
        yield "pop {" + ", ".join(f"r{i+1}" for i in range(count)) + "}"
    yield f"bl {call.calle}"


@emit.register
def _(if_node: If) -> Iterator[str]:
    alt_label = new_label()
    end_label = new_label() if if_node.alternative != Block([]) else alt_label
    yield from emit(if_node.conditional)
    yield "cmp r0, #0"
    yield f"beq {alt_label}"
    yield from emit(if_node.consequence)
    if alt_label != end_label:
        yield f"b {end_label}"
        yield f"{alt_label}:"
        yield from emit(if_node.alternative)
    yield f"{end_label}:"
