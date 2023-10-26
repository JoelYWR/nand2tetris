import argparse
import os
import re

from collections import deque
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, Tuple

XML_OUTPUT = {
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "&": "&amp;",
}


class CompilerMode(str, Enum):
    TOKENIZE = "t"
    PARSE = "p"
    GENERATE = "g"

    def __str__(self) -> str:
        return self.value


class TokenType(str, Enum):
    KEYWORD = "keyword"
    SYMBOL = "symbol"
    INT_CONST = "integerConstant"
    STRING_CONST = "stringConstant"
    IDENTIFIER = "identifier"

    def __str__(self) -> str:
        return self.value


class IdentifierKind(str, Enum):
    STATIC = "static"
    FIELD = "field"
    ARG = "argument"
    LCL = "local"
    CLASS = "class"
    SUBROUTINE = "subroutine"

    def __str__(self) -> str:
        return self.value


class SubroutineKind(str, Enum):
    CONSTRUCTOR = "constructor"
    FUNCTION = "function"
    METHOD = "method"

    def __str__(self) -> str:
        return self.value


class SegmentPointer(str, Enum):
    LCL = "local"
    ARG = "argument"
    THIS = "this"
    THAT = "that"
    CONST = "constant"
    STATIC = "static"
    POINTER = "pointer"
    TEMP = "temp"

    def __str__(self) -> str:
        return self.value


class ArithmeticCommand(str, Enum):
    ADD = "add"
    SUB = "sub"
    NEG = "neg"
    EQ = "eq"
    GT = "gt"
    LT = "lt"
    AND = "and"
    OR = "or"
    NOT = "not"

    def __str__(self) -> str:
        return self.value


class Compiler:
    def __init__(self, src_file: str, dst_file: str) -> None:
        self.__src_file = src_file
        self.__dst_file = dst_file

    def compile(self, mode: CompilerMode) -> None:
        if mode == CompilerMode.TOKENIZE:
            tokenizer = Tokenizer(self.__src_file)
            with open(self.__dst_file, "w") as t_file:
                t_file.write("<tokens>\n")
                while tokenizer.has_more_tokens():
                    tokenizer.advance()
                    token_type, token = tokenizer.get_current_token()
                    if token in XML_OUTPUT:
                        token = XML_OUTPUT[token]
                    t_file.write(f"<{token_type}> {token} </{token_type}>\n")
                t_file.write("</tokens>\n")
            del tokenizer
        elif mode == CompilerMode.PARSE or mode == CompilerMode.GENERATE:
            tokenizer = Tokenizer(self.__src_file)
            parser = Parser(self.__dst_file, tokenizer)
            parser.parse()
            del parser
            del tokenizer


class Tokenizer:
    __LEXICONS = {
        TokenType.KEYWORD: {
            "class",
            "constructor",
            "function",
            "method",
            "field",
            "static",
            "var",
            "int",
            "char",
            "boolean",
            "void",
            "true",
            "false",
            "null",
            "this",
            "let",
            "do",
            "if",
            "else",
            "while",
            "return",
        },
        TokenType.SYMBOL: {
            "{",
            "}",
            "(",
            ")",
            "[",
            "]",
            ".",
            ",",
            ";",
            "+",
            "-",
            "*",
            "/",
            "&",
            "|",
            "<",
            ">",
            "=",
            "~",
        },
    }

    __DIGIT_PATTERN = r"[\d]+"

    __IDENTIFIER_PATTERN = r"[a-zA-Z_][\w]*"
    __IDENTIFIER_REGEX = re.compile(rf"{__IDENTIFIER_PATTERN}")

    __SYMBOLS_PATTERN = "|".join(f"\{s}" for s in __LEXICONS[TokenType.SYMBOL])

    __COMPOSITE_REGEX = re.compile(
        rf"{__SYMBOLS_PATTERN}|{__IDENTIFIER_PATTERN}|{__DIGIT_PATTERN}"
    )

    __QUOTE_PATTERN = r'"'
    __QUOTE_REGEX = re.compile(rf"{__QUOTE_PATTERN}")

    __TOKENS_QUEUE: Deque[Tuple[TokenType, str]] = deque()

    __CURRENT_TOKEN: Tuple[Optional[TokenType], str] = (None, "")

    def __init__(self, file: str) -> None:
        self.__file = open(file, "r")

    def __del__(self) -> None:
        self.__file.close()

    def __is_token_a_keyword(self, token: str) -> bool:
        return token in self.__LEXICONS[TokenType.KEYWORD]

    def __is_token_a_symbol(self, token: str) -> bool:
        return token in self.__LEXICONS[TokenType.SYMBOL]

    def __is_token_an_integer_constant(self, token: str) -> bool:
        if len(token) > 1 and token.startswith("0"):
            return False

        return token.isdigit() and int(token) >= 0 and int(token) <= 32767

    def __is_token_a_string_constant(self, token: str) -> bool:
        return token.startswith('"') and token.endswith('"')

    def __is_token_an_identifier(self, token: str) -> bool:
        return self.__IDENTIFIER_REGEX.fullmatch(token) is not None

    def __check_token_type(self, token: str) -> Optional[TokenType]:
        if self.__is_token_a_keyword(token):
            return TokenType.KEYWORD
        elif self.__is_token_a_symbol(token):
            return TokenType.SYMBOL
        elif self.__is_token_an_integer_constant(token):
            return TokenType.INT_CONST
        elif self.__is_token_a_string_constant(token):
            return TokenType.STRING_CONST
        elif self.__is_token_an_identifier(token):
            return TokenType.IDENTIFIER
        else:
            return None

    def __update_tokens_queue(self) -> None:
        if self.__file.closed:
            raise Exception(f"${self.__file.name} is closed.")
        if self.__TOKENS_QUEUE:
            raise Exception(f"Tokens queue is not empty.")

        is_read_next = True
        line = ""
        while is_read_next:
            line = self.__file.readline()
            # EOF returns an empty string
            if not line:
                return

            line = line.strip()
            if not line or line.startswith("//"):
                continue
            elif line.startswith("/*") or line.startswith("/**"):
                s_line = line
                while not line.endswith("*/"):
                    line = self.__file.readline()
                    # EOF returns an empty string
                    if not line:
                        raise Exception(f"Unclosed comment (line: {s_line})")
                    line = line.strip()
                continue

            is_read_next = False

            if "//" in line:
                line = line.split("//")[0].strip()

        tokens: List[str] = []
        # Handle string constants
        # Preserve everything inside each non-overlapping pair of double quotes
        # Number of double quotes must be even
        # Split the rest of the line by whitespace
        # e.g. greeting = "Hello, World!"; => [greeting, =, "Hello, World!", ;]
        if '"' in line:
            quote_indexes = [m.start() for m in self.__QUOTE_REGEX.finditer(line)]
            if len(quote_indexes) % 2 != 0:
                raise Exception(f"Unclosed quote (line: {line})")
            if quote_indexes[0] != 0:
                tokens = tokens + line[: quote_indexes[0]].split()
            for i in range(0, len(quote_indexes), 2):
                start = quote_indexes[i]
                end = quote_indexes[i + 1] + 1
                tokens.append(line[start:end])
                if i + 2 < len(quote_indexes):
                    tokens = tokens + line[end : quote_indexes[i + 2]].split()
            if quote_indexes[-1] != len(line) - 1:
                tokens = tokens + line[quote_indexes[-1] + 1 :].split()
        else:
            tokens = line.split()

        for token in tokens:
            token_type = self.__check_token_type(token)
            if token_type:
                if token_type == TokenType.STRING_CONST:
                    token = token.strip('"')
                self.__TOKENS_QUEUE.append((token_type, token))
            # Handle composite tokens (i.e. combinations of multiple token types)
            # Break down composite tokens into sub-tokens
            # Will not contain string constants
            # e.g. (foo.bar() => ( foo . bar ( )
            else:
                invalid_tokens = self.__COMPOSITE_REGEX.sub("", token)
                if invalid_tokens:
                    raise Exception(
                        f"Invalid token: {token} (invalid tokens: {invalid_tokens})"
                    )

                sub_tokens = (m.span() for m in self.__COMPOSITE_REGEX.finditer(token))
                for start, end in sub_tokens:
                    sub_token = token[start:end]
                    token_type = self.__check_token_type(sub_token)
                    if token_type:
                        self.__TOKENS_QUEUE.append((token_type, sub_token))
                    else:
                        raise Exception(f"Invalid token: {sub_token}")

    def advance(self) -> None:
        if self.__TOKENS_QUEUE:
            self.__CURRENT_TOKEN = self.__TOKENS_QUEUE.popleft()
        else:
            self.__CURRENT_TOKEN = (None, "")

    def get_current_token(self) -> Tuple[Optional[TokenType], str]:
        return self.__CURRENT_TOKEN

    def peek_next_token(self) -> Tuple[Optional[TokenType], str]:
        if self.__TOKENS_QUEUE:
            return self.__TOKENS_QUEUE[0]
        else:
            return (None, "")

    def has_more_tokens(self) -> bool:
        if self.__TOKENS_QUEUE:
            return True
        else:
            self.__update_tokens_queue()
            return bool(self.__TOKENS_QUEUE)


class Parser:
    def __init__(self, file: str, tokenizer: Tokenizer) -> None:
        self.__file = open(file, "w")
        self.__tokenizer = tokenizer
        self.__generator = Generator(file)
        self.__current_class = ""
        self.__current_subroutine_kind = ""
        self.__current_subroutine_name = ""
        self.__class_symbol_table = SymbolTable()
        self.__subroutine_symbol_table = SymbolTable()
        self.__if_label_counter = 0
        self.__while_label_counter = 0

        if self.__tokenizer.has_more_tokens():
            self.__tokenizer.advance()

    def __del__(self) -> None:
        self.__file.close()

    def __process(self, expected_token: str) -> None:
        token_type, token = self.__tokenizer.get_current_token()
        if token != expected_token:
            raise Exception(
                f"Expected token: {expected_token}, but got: {token} (token type: {token_type})"
            )
        if self.__tokenizer.has_more_tokens():
            self.__tokenizer.advance()

    def __process_identifier(
        self,
        is_declaration: bool = False,
        kind: Optional[IdentifierKind] = None,
        type: Optional[str] = None,
    ) -> Tuple[Optional[IdentifierKind], Optional[str], Optional[int]]:
        token_type, token = self.__tokenizer.get_current_token()
        stored_kind, stored_type, stored_index = None, None, None
        if token_type != TokenType.IDENTIFIER:
            raise Exception(
                f"Expected token type: {TokenType.IDENTIFIER}, but got: {token_type} (token: {token})"
            )
        # Variable declaration
        if is_declaration:
            if kind in {
                IdentifierKind.STATIC,
                IdentifierKind.FIELD,
            }:
                if type is None:
                    raise Exception("Type must be specified.")
                self.__class_symbol_table.define(token, kind, type)
            elif kind in {
                IdentifierKind.ARG,
                IdentifierKind.LCL,
            }:
                if type is None:
                    raise Exception("Type must be specified.")
                self.__subroutine_symbol_table.define(token, kind, type)
            elif kind == IdentifierKind.CLASS:
                self.__current_class = token
            elif kind == IdentifierKind.SUBROUTINE:
                self.__current_subroutine_name = token
            else:
                raise Exception(f"Invalid identifier kind: {kind}")
        # Variable usage
        else:
            if token in self.__subroutine_symbol_table:
                stored_kind = self.__subroutine_symbol_table.kind_of(token)
                stored_type = self.__subroutine_symbol_table.type_of(token)
                stored_index = self.__subroutine_symbol_table.index_of(token)
            elif token in self.__class_symbol_table:
                stored_kind = self.__class_symbol_table.kind_of(token)
                stored_type = self.__class_symbol_table.type_of(token)
                stored_index = self.__class_symbol_table.index_of(token)
            # Safe to assume identifier is class name or subroutine name
            else:
                pass

        if self.__tokenizer.has_more_tokens():
            self.__tokenizer.advance()

        return stored_kind, stored_type, stored_index

    def __compile_class(self) -> None:
        self.__process("class")
        self.__process_identifier(True, IdentifierKind.CLASS)
        self.__process("{")
        while self.__tokenizer.get_current_token()[1] in {
            IdentifierKind.STATIC,
            IdentifierKind.FIELD,
        }:
            self.__compile_class_var_dec()
        while self.__tokenizer.get_current_token()[1] in {
            SubroutineKind.CONSTRUCTOR,
            SubroutineKind.FUNCTION,
            SubroutineKind.METHOD,
        }:
            self.__compile_subroutine_dec()
        self.__process("}")

    def __compile_class_var_dec(self) -> None:
        kind = self.__tokenizer.get_current_token()[1]
        self.__process(kind)
        type = self.__tokenizer.get_current_token()[1]
        self.__compile_type()
        self.__process_identifier(True, IdentifierKind(kind), type)
        while self.__tokenizer.get_current_token()[1] == ",":
            self.__process(",")
            self.__process_identifier(True, IdentifierKind(kind), type)
        self.__process(";")

    def __compile_subroutine_dec(self) -> None:
        self.__subroutine_symbol_table.reset()
        self.__current_subroutine_kind = self.__tokenizer.get_current_token()[1]
        self.__process(self.__current_subroutine_kind)
        if self.__current_subroutine_kind == SubroutineKind.METHOD:
            self.__subroutine_symbol_table.define(
                "this", IdentifierKind.ARG, self.__current_class
            )
        if self.__tokenizer.get_current_token()[1] == "void":
            self.__process("void")
        else:
            self.__compile_type()
        self.__process_identifier(True, IdentifierKind.SUBROUTINE)
        self.__process("(")
        self.__compile_parameter_list()
        self.__process(")")
        self.__process("{")
        self.__compile_subroutine_body()
        self.__process("}")

    def __compile_parameter_list(self) -> None:
        while self.__tokenizer.get_current_token()[1] != ")":
            type = self.__tokenizer.get_current_token()[1]
            self.__compile_type()
            self.__process_identifier(True, IdentifierKind.ARG, type)
            if self.__tokenizer.get_current_token()[1] == ",":
                self.__process(",")

    def __compile_subroutine_body(self) -> None:
        while self.__tokenizer.get_current_token()[1] == "var":
            self.__compile_var_dec()
        self.__generator.generate_function(
            f"{self.__current_class}.{self.__current_subroutine_name}",
            self.__subroutine_symbol_table.var_count(IdentifierKind.LCL),
        )
        if self.__current_subroutine_kind == SubroutineKind.CONSTRUCTOR:
            self.__generator.generate_push(
                SegmentPointer.CONST,
                self.__class_symbol_table.var_count(IdentifierKind.FIELD),
            )
            self.__generator.generate_call("Memory.alloc", 1)
            self.__generator.generate_pop(SegmentPointer.POINTER, 0)
        elif self.__current_subroutine_kind == SubroutineKind.METHOD:
            self.__generator.generate_push(SegmentPointer.ARG, 0)
            self.__generator.generate_pop(SegmentPointer.POINTER, 0)
        self.__compile_statements()

    def __compile_var_dec(self) -> None:
        self.__process("var")
        type = self.__tokenizer.get_current_token()[1]
        self.__compile_type()
        self.__process_identifier(True, IdentifierKind.LCL, type)
        while self.__tokenizer.get_current_token()[1] == ",":
            self.__process(",")
            self.__process_identifier(True, IdentifierKind.LCL, type)
        self.__process(";")

    def __compile_statements(self) -> None:
        while self.__tokenizer.get_current_token()[1] in {
            "let",
            "if",
            "while",
            "do",
            "return",
        }:
            if self.__tokenizer.get_current_token()[1] == "let":
                self.__compile_let()
            elif self.__tokenizer.get_current_token()[1] == "if":
                self.__compile_if()
            elif self.__tokenizer.get_current_token()[1] == "while":
                self.__compile_while()
            elif self.__tokenizer.get_current_token()[1] == "do":
                self.__compile_do()
            elif self.__tokenizer.get_current_token()[1] == "return":
                self.__compile_return()

    def __compile_let(self) -> None:
        is_array = False
        self.__process("let")
        token = self.__tokenizer.get_current_token()[1]
        k, _, i = self.__process_identifier()
        if k is None or i is None:
            raise Exception(f"Invalid identifier: {token} (kind: {k}, index: {i})")
        if self.__tokenizer.get_current_token()[1] == "[":
            is_array = True
            if k == IdentifierKind.STATIC:
                self.__generator.generate_push(SegmentPointer.STATIC, i)
            elif k == IdentifierKind.FIELD:
                self.__generator.generate_push(SegmentPointer.THIS, i)
            elif k == IdentifierKind.ARG:
                self.__generator.generate_push(SegmentPointer.ARG, i)
            elif k == IdentifierKind.LCL:
                self.__generator.generate_push(SegmentPointer.LCL, i)
            self.__process("[")
            self.__compile_expression()
            self.__process("]")
            self.__generator.generate_arithmetic(ArithmeticCommand.ADD)
        self.__process("=")
        self.__compile_expression()
        self.__process(";")
        if is_array:
            self.__generator.generate_pop(SegmentPointer.TEMP, 0)
            self.__generator.generate_pop(SegmentPointer.POINTER, 1)
            self.__generator.generate_push(SegmentPointer.TEMP, 0)
            self.__generator.generate_pop(SegmentPointer.THAT, 0)
        else:
            if k == IdentifierKind.STATIC:
                self.__generator.generate_pop(SegmentPointer.STATIC, i)
            elif k == IdentifierKind.FIELD:
                self.__generator.generate_pop(SegmentPointer.THIS, i)
            elif k == IdentifierKind.ARG:
                self.__generator.generate_pop(SegmentPointer.ARG, i)
            elif k == IdentifierKind.LCL:
                self.__generator.generate_pop(SegmentPointer.LCL, i)

    def __compile_if(self) -> None:
        label1 = f"IF_L1_{self.__if_label_counter}"
        self.__if_label_counter += 1
        label2 = f"IF_L2_{self.__if_label_counter}"
        self.__if_label_counter += 1
        self.__process("if")
        self.__process("(")
        self.__compile_expression()
        self.__process(")")
        self.__generator.generate_arithmetic(ArithmeticCommand.NOT)
        self.__generator.generate_if_goto(label1)
        self.__process("{")
        self.__compile_statements()
        self.__process("}")
        if self.__tokenizer.get_current_token()[1] == "else":
            self.__generator.generate_goto(label2)
            self.__generator.generate_label(label1)
            self.__process("else")
            self.__process("{")
            self.__compile_statements()
            self.__process("}")
            self.__generator.generate_label(label2)
        else:
            self.__generator.generate_label(label1)

    def __compile_while(self) -> None:
        label1 = f"WHILE_L1_{self.__while_label_counter}"
        self.__while_label_counter += 1
        label2 = f"WHILE_L2_{self.__while_label_counter}"
        self.__while_label_counter += 1
        self.__process("while")
        self.__generator.generate_label(label1)
        self.__process("(")
        self.__compile_expression()
        self.__process(")")
        self.__generator.generate_arithmetic(ArithmeticCommand.NOT)
        self.__generator.generate_if_goto(label2)
        self.__process("{")
        self.__compile_statements()
        self.__process("}")
        self.__generator.generate_goto(label1)
        self.__generator.generate_label(label2)

    def __compile_do(self) -> None:
        self.__process("do")
        self.__compile_expression()
        self.__process(";")
        self.__generator.generate_pop(SegmentPointer.TEMP, 0)

    def __compile_return(self) -> None:
        self.__process("return")
        if self.__tokenizer.get_current_token()[1] != ";":
            self.__compile_expression()
        else:
            self.__generator.generate_push(SegmentPointer.CONST, 0)
        self.__process(";")
        self.__generator.generate_return()

    def __compile_expression(self) -> None:
        self.__compile_term()
        while self.__tokenizer.get_current_token()[1] in {
            "+",
            "-",
            "*",
            "/",
            "&",
            "|",
            "<",
            ">",
            "=",
        }:
            op = self.__tokenizer.get_current_token()[1]
            self.__process(op)
            self.__compile_term()
            if op == "+":
                self.__generator.generate_arithmetic(ArithmeticCommand.ADD)
            elif op == "-":
                self.__generator.generate_arithmetic(ArithmeticCommand.SUB)
            elif op == "*":
                self.__generator.generate_call("Math.multiply", 2)
            elif op == "/":
                self.__generator.generate_call("Math.divide", 2)
            elif op == "&":
                self.__generator.generate_arithmetic(ArithmeticCommand.AND)
            elif op == "|":
                self.__generator.generate_arithmetic(ArithmeticCommand.OR)
            elif op == "<":
                self.__generator.generate_arithmetic(ArithmeticCommand.LT)
            elif op == ">":
                self.__generator.generate_arithmetic(ArithmeticCommand.GT)
            elif op == "=":
                self.__generator.generate_arithmetic(ArithmeticCommand.EQ)

    def __compile_term(self) -> None:
        token_type, token = self.__tokenizer.get_current_token()
        if token_type == TokenType.INT_CONST:
            self.__process(token)
            self.__generator.generate_push(SegmentPointer.CONST, int(token))
        elif token in {
            "true",
            "false",
            "null",
            "this",
        }:
            self.__process(token)
            if token == "true":
                self.__generator.generate_push(SegmentPointer.CONST, 1)
                self.__generator.generate_arithmetic(ArithmeticCommand.NEG)
            elif token in {"false", "null"}:
                self.__generator.generate_push(SegmentPointer.CONST, 0)
            elif token == "this":
                self.__generator.generate_push(SegmentPointer.POINTER, 0)
        elif token_type == TokenType.STRING_CONST:
            self.__process(token)
            self.__generator.generate_push(SegmentPointer.CONST, len(token))
            self.__generator.generate_call("String.new", 1)
            for c in token:
                self.__generator.generate_push(SegmentPointer.CONST, ord(c))
                self.__generator.generate_call("String.appendChar", 2)
        elif token in {
            "-",
            "~",
        }:
            self.__process(token)
            self.__compile_term()
            if token == "-":
                self.__generator.generate_arithmetic(ArithmeticCommand.NEG)
            elif token == "~":
                self.__generator.generate_arithmetic(ArithmeticCommand.NOT)
        elif token == "(":
            self.__process("(")
            self.__compile_expression()
            self.__process(")")
        else:
            if self.__tokenizer.has_more_tokens():
                next_token = self.__tokenizer.peek_next_token()[1]
            if next_token == ".":
                is_var_name = False
                obj_name = token
                k, t, i = self.__process_identifier()
                if k is not None and t is not None and i is not None:
                    is_var_name = True
                if is_var_name:
                    assert i is not None
                    if k == IdentifierKind.STATIC:
                        self.__generator.generate_push(SegmentPointer.STATIC, i)
                    elif k == IdentifierKind.FIELD:
                        self.__generator.generate_push(SegmentPointer.THIS, i)
                    elif k == IdentifierKind.ARG:
                        self.__generator.generate_push(SegmentPointer.ARG, i)
                    elif k == IdentifierKind.LCL:
                        self.__generator.generate_push(SegmentPointer.LCL, i)
                self.__process(".")
                subroutine_name = self.__tokenizer.get_current_token()[1]
                self.__process_identifier()
                self.__process("(")
                n_args = self.__compile_expression_list()
                self.__process(")")
                if is_var_name:
                    self.__generator.generate_call(f"{t}.{subroutine_name}", n_args + 1)
                else:
                    self.__generator.generate_call(
                        f"{obj_name}.{subroutine_name}", n_args
                    )
            elif next_token == "(":
                subroutine_name = token
                self.__process_identifier()
                self.__generator.generate_push(SegmentPointer.POINTER, 0)
                self.__process("(")
                n_args = self.__compile_expression_list()
                self.__process(")")
                self.__generator.generate_call(
                    f"{self.__current_class}.{subroutine_name}", n_args + 1
                )
            else:
                k, _, i = self.__process_identifier()
                if k is None or i is None:
                    raise Exception(
                        f"Invalid identifier: {token} (kind: {k}, index: {i})"
                    )
                if k == IdentifierKind.STATIC:
                    self.__generator.generate_push(SegmentPointer.STATIC, i)
                elif k == IdentifierKind.FIELD:
                    self.__generator.generate_push(SegmentPointer.THIS, i)
                elif k == IdentifierKind.ARG:
                    self.__generator.generate_push(SegmentPointer.ARG, i)
                elif k == IdentifierKind.LCL:
                    self.__generator.generate_push(SegmentPointer.LCL, i)
                if self.__tokenizer.get_current_token()[1] == "[":
                    self.__process("[")
                    self.__compile_expression()
                    self.__process("]")
                    self.__generator.generate_arithmetic(ArithmeticCommand.ADD)
                    self.__generator.generate_pop(SegmentPointer.POINTER, 1)
                    self.__generator.generate_push(SegmentPointer.THAT, 0)

    def __compile_expression_list(self) -> int:
        n_args = 0
        if self.__tokenizer.get_current_token()[1] != ")":
            self.__compile_expression()
            n_args += 1
            while self.__tokenizer.get_current_token()[1] == ",":
                self.__process(",")
                self.__compile_expression()
                n_args += 1

        return n_args

    def __compile_type(self) -> None:
        token_type, token = self.__tokenizer.get_current_token()
        if token_type == TokenType.KEYWORD and token in {
            "int",
            "char",
            "boolean",
        }:
            self.__process(token)
        else:
            self.__process_identifier()

    def parse(self) -> None:
        self.__compile_class()


class SymbolTable:
    def __init__(self) -> None:
        self.__table: Dict[str, Dict[str, Any]] = {}
        self.__indexCount = {
            IdentifierKind.STATIC: 0,
            IdentifierKind.FIELD: 0,
            IdentifierKind.ARG: 0,
            IdentifierKind.LCL: 0,
        }

    def __contains__(self, name: str) -> bool:
        return name in self.__table

    def define(self, name: str, kind: IdentifierKind, type: str) -> None:
        if name in self.__table:
            raise Exception(f"Symbol {name} already defined.")
        self.__table[name] = {
            "kind": kind,
            "type": type,
            "index": self.__indexCount[kind],
        }
        self.__indexCount[kind] += 1

    def reset(self) -> None:
        self.__table.clear()
        self.__indexCount = {
            IdentifierKind.STATIC: 0,
            IdentifierKind.FIELD: 0,
            IdentifierKind.ARG: 0,
            IdentifierKind.LCL: 0,
        }

    def var_count(self, kind: IdentifierKind) -> int:
        return self.__indexCount[kind]

    def kind_of(self, name: str) -> Optional[IdentifierKind]:
        if name in self.__table:
            assert isinstance(self.__table[name]["kind"], IdentifierKind)
            return self.__table[name]["kind"]

        return None

    def type_of(self, name: str) -> Optional[str]:
        if name in self.__table:
            assert isinstance(self.__table[name]["type"], str)
            return self.__table[name]["type"]

        return None

    def index_of(self, name: str) -> Optional[int]:
        if name in self.__table:
            assert isinstance(self.__table[name]["index"], int)
            return self.__table[name]["index"]

        return None


class Generator:
    def __init__(self, file: str) -> None:
        self.__file = open(file, "w")

    def __del__(self) -> None:
        self.__file.close()

    def generate_push(self, segment: SegmentPointer, index: int) -> None:
        self.__file.write(f"push {segment} {index}\n")

    def generate_pop(self, segment: SegmentPointer, index: int) -> None:
        if segment == SegmentPointer.CONST:
            raise Exception("Cannot pop to constant segment.")
        self.__file.write(f"pop {segment} {index}\n")

    def generate_arithmetic(self, command: ArithmeticCommand) -> None:
        self.__file.write(f"{command}\n")

    def generate_label(self, label: str) -> None:
        self.__file.write(f"label {label}\n")

    def generate_goto(self, label: str) -> None:
        self.__file.write(f"goto {label}\n")

    def generate_if_goto(self, label: str) -> None:
        self.__file.write(f"if-goto {label}\n")

    def generate_call(self, name: str, n_args: int) -> None:
        self.__file.write(f"call {name} {n_args}\n")

    def generate_function(self, name: str, n_locals: int) -> None:
        self.__file.write(f"function {name} {n_locals}\n")

    def generate_return(self) -> None:
        self.__file.write("return\n")


argparser = argparse.ArgumentParser(
    description="Compiler for Jack programming language",
    prog="JackCompiler",
)
argparser.add_argument(
    "target",
    help=".jack file or folder containing .jack files to be compiled. Each .jack file compiled will produce a corresponding .vm file with the same name. If `tokenize` or `parse` mode is selected, .xml file(s) will be produced instead. For `tokenize` mode, the file name will have a `T` suffix appended. For `parse` mode, the file name will have a `P` suffix appended.",
    type=str,
)
argparser.add_argument(
    "-m",
    "--mode",
    choices=[CompilerMode.TOKENIZE, CompilerMode.PARSE, CompilerMode.GENERATE],
    default=CompilerMode.GENERATE,
    help="action of the %(prog)s. t = tokenize, p = parse, g = generate. (default: %(default)s)",
)


def main() -> None:
    args = argparser.parse_args()

    is_dir = os.path.isdir(args.target)
    files_to_compile = []
    if is_dir:
        for file in os.listdir(args.target):
            if file.endswith(".jack"):
                file_name, _ = os.path.splitext(file)

                src_file = os.path.join(args.target, file)
                if args.mode == CompilerMode.TOKENIZE:
                    file_name = f"{file_name}T.xml"
                elif args.mode == CompilerMode.PARSE:
                    file_name = f"{file_name}P.xml"
                else:
                    file_name = f"{file_name}.vm"
                dst_file = os.path.join(
                    args.target,
                    file_name,
                )

                files_to_compile.append((src_file, dst_file))
    else:
        file_path, _ = os.path.splitext(args.target)

        src_file = args.target
        if args.mode == CompilerMode.TOKENIZE:
            dst_file = f"{file_path}T.xml"
        elif args.mode == CompilerMode.PARSE:
            dst_file = f"{file_path}P.xml"
        else:
            dst_file = f"{file_path}.vm"

        files_to_compile.append((src_file, dst_file))

    for src_file, dst_file in files_to_compile:
        compiler = Compiler(src_file, dst_file)
        compiler.compile(args.mode)


if __name__ == "__main__":
    main()
