import functools
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
    def regex(pattern):
        return Parser(functools.partial(match, pattern=pattern))

    @staticmethod
    def constant(constant):
        return Parser(lambda s: ParseResult(constant, s))

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
        return self.bind(lambda x: Parser.constant(f(x)))

    def maybe(self):
        return self.repeat(maximum=1)

    def parse_string(self, string: str):
        if result := self.parse(Source(string, 0)):
            if result.index == len(string):
                return result.value
            raise ParseError(f"{result.index - len(string)} chars left")
        raise ParseError(f"Failed to parse")
