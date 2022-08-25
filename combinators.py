import functools
import re
from collections import namedtuple
from math import inf

Source = namedtuple("Source", "string index")
ParseResult = namedtuple("ParseResult", "value source")


class ParseError(Exception):
    @staticmethod
    def throw(message: str):
        raise ParseError(message)


def match(src: Source, pattern):
    s, i = src
    match pattern:
        case str(string):
            if s[i : i + len(string)] != string:
                return None
        case regex:
            if match := regex.match(s, i):
                string = match.group(0)
            else:
                return None
    return ParseResult(string, Source(s, i + len(string)))


class Parser:
    def __init__(self, parse=None):
        self.parse = parse

    @staticmethod
    def error(message):
        return Parser(ParseError.throw(message))

    def __or__(self, other):
        return Parser(lambda s: self.parse(s) or other.parse(s))

    def repeat(self, minimum=0, maximum=inf):
        def parse(source):
            results = []
            while len(results) < maximum and (item := self.parse(source)):
                value, source = item
                results.append(value)
            if len(results) >= minimum:
                return ParseResult(results, source)
            return None

        return Parser(parse)

    def bind(self, f):
        def parse(source):
            if result := self.parse(source):
                return f(result.value).parse(result.source)
            return None

        return Parser(parse)

    def __and__(self, other):
        return self.bind(lambda _: other)

    def map(self, f):
        return self.bind(lambda x: constant(f(x)))

    def maybe(self):
        return self.repeat(maximum=1)

    def parse_string(self, string: str):
        if result := self.parse(Source(string, 0)):
            excess_chars = len(string) - result.source.index
            if not excess_chars:
                return result.value
            raise ParseError(f"{excess_chars} chars left")
        raise ParseError(f"Failed to parse")


def constant(constant) -> Parser:
    return Parser(lambda s: ParseResult(constant, s))


def regex(pattern) -> Parser:
    regex = re.compile(pattern) if isinstance(pattern, str) else pattern
    return Parser(functools.partial(match, pattern=regex))
