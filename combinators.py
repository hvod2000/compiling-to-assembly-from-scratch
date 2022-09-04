import functools
import re
from collections import namedtuple
from math import inf

Source = namedtuple("Source", "string index")
ParseResult = namedtuple("ParseResult", "value source")


class ParseFailure(namedtuple("ParseFailure", "message source")):
    def __bool__(self):
        return False


class ParseError(Exception):
    def __init__(self, message: str, line_number: int | None = None):
        self.message = message
        self.line_number = line_number
        super().__init__(self.message)

    @staticmethod
    def throw(message: str, line_number=None):
        raise ParseError(message, line_number)


def match(src: Source, pattern):
    s, i = src
    match pattern:
        case str(string):
            if s[i : i + len(string)] != string:
                return ParseFailure(f"Expected {string}", src)
        case regex:
            if match := regex.match(s, i):
                string = match.group(0)
            else:
                return ParseFailure(f"Expected {regex}", src)
    return ParseResult(string, Source(s, i + len(string)))


class Parser:
    def __init__(self, parse=None):
        self.parse = parse

    @staticmethod
    def error(message):
        return Parser(ParseError.throw(message))

    def __or__(self, other):
        def parse(source: Source):
            first = self.parse(source)
            if isinstance(first, ParseResult):
                return first
            second = other.parse(source)
            if isinstance(second, ParseResult):
                return second
            return max((first, second), key=lambda fail: fail.source.index)
        return Parser(parse)

    def repeat(self, minimum=0, maximum=inf):
        def parse(source):
            results = []
            while len(results) < maximum and (item := self.parse(source)):
                value, source = item
                results.append(value)
            if len(results) >= minimum:
                return ParseResult(results, source)
            return item

        return Parser(parse)

    def bind(self, f):
        def parse(source):
            if result := self.parse(source):
                return f(result.value).parse(result.source)
            return result
        return Parser(parse)

    def __and__(self, other):
        return CatParser([self, other])

    def map(self, f):
        return self.bind(lambda x: constant(f(x)))

    def maybe(self):
        return self.repeat(maximum=1)

    def parse_string(self, string: str):
        result = self.parse(Source(string, 0))
        if isinstance(result, ParseFailure):
            raise ParseError(result.message, result.source.index)
        if len(string) > result.source.index:
            message = "Unexpected characters after the end"
            raise ParseError(message, result.source.index)
        return result.value


class CatParser(Parser):
    def __init__(self, parsers: list[Parser]):
        self.parsers = parsers

    def parse(self, source: Source):
        results = []
        for parser in self.parsers:
            result = parser.parse(source)
            if isinstance(result, ParseFailure):
                return result
            value, source = result
            results.append(value)
        return ParseResult(results, source)

    def bind(self, f):
        def parse(source):
            result = self.parse(source)
            if isinstance(result, ParseFailure):
                return result
            return f(*result.value).parse(result.source)
        return Parser(parse)

    def map(self, f):
        return self.bind(lambda *args: constant(f(*args)))

    def __and__(self, other):
        return CatParser(
            self.parsers
            + (other.parsers if isinstance(other, CatParser) else [other])
        )


def constant(constant) -> Parser:
    return Parser(lambda s: ParseResult(constant, s))


def regex(pattern) -> Parser:
    regex = re.compile(pattern) if isinstance(pattern, str) else pattern
    return Parser(functools.partial(match, pattern=regex))
