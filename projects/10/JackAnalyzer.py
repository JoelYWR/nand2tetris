import argparse
import os
import re

from collections import deque
from enum import Enum
from typing import Tuple

XML_OUTPUT = {
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "&": "&amp;",
}


class AnalyzerMode(str, Enum):
    TOKENIZE = "t"
    PARSE = "p"

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


class Analyzer:
    def __init__(self, src_file: str, dst_file: str) -> None:
        self.__src_file = src_file
        self.__dst_file = dst_file

    def analyze(self, mode: AnalyzerMode) -> None:
        if mode == AnalyzerMode.TOKENIZE:
            XML_OUTPUT = {
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "&": "&amp;",
            }

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
        elif mode == AnalyzerMode.PARSE:
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

    __TOKENS_QUEUE = deque()

    __CURRENT_TOKEN = None

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

    def __check_token_type(self, token: str) -> TokenType:
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
        line = None
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

        tokens = []
        if '"' in line:
            # Handle string constants
            # Preserve everything inside each non-overlapping pair of double quotes
            # Number of double quotes must be even
            # Split the rest of the line by whitespace
            # e.g. greeting = "Hello, World!"; => [greeting, =, "Hello, World!", ;]
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
            else:
                # Handle composite tokens (i.e. combinations of multiple token types)
                # Break down composite tokens into sub-tokens
                # Will not contain string constants
                # e.g. (foo.bar() => ( foo . bar ( )
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
            self.__CURRENT_TOKEN = None

    def get_current_token(self) -> Tuple[TokenType, str]:
        return self.__CURRENT_TOKEN

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
        if token in XML_OUTPUT:
            token = XML_OUTPUT[token]
        self.__file.write(f"<{token_type}> {token} </{token_type}>\n")
        if self.__tokenizer.has_more_tokens():
            self.__tokenizer.advance()

    def __process_identifier(self) -> None:
        token_type, token = self.__tokenizer.get_current_token()
        if token_type != TokenType.IDENTIFIER:
            raise Exception(
                f"Expected token type: {TokenType.IDENTIFIER}, but got: {token_type}"
            )
        self.__file.write(f"<{token_type}> {token} </{token_type}>\n")
        if self.__tokenizer.has_more_tokens():
            self.__tokenizer.advance()

    def __process_subroutine_call(self) -> None:
        self.__process_identifier()
        if self.__tokenizer.get_current_token()[1] == ".":
            self.__process(".")
            self.__process_identifier()
        self.__process("(")
        self.__compile_expression_list()
        self.__process(")")

    def __compile_class(self) -> None:
        self.__file.write("<class>\n")
        self.__process("class")
        self.__process_identifier()
        self.__process("{")
        while self.__tokenizer.get_current_token()[1] in {
            "static",
            "field",
        }:
            self.__compile_class_var_dec()
        while self.__tokenizer.get_current_token()[1] in {
            "constructor",
            "function",
            "method",
        }:
            self.__compile_subroutine_dec()
        self.__process("}")
        self.__file.write("</class>\n")

    def __compile_class_var_dec(self) -> None:
        self.__file.write("<classVarDec>\n")
        self.__process(self.__tokenizer.get_current_token()[1])
        self.__compile_type()
        self.__process_identifier()
        while self.__tokenizer.get_current_token()[1] == ",":
            self.__process(",")
            self.__process_identifier()
        self.__process(";")
        self.__file.write("</classVarDec>\n")

    def __compile_subroutine_dec(self) -> None:
        self.__file.write("<subroutineDec>\n")
        self.__process(self.__tokenizer.get_current_token()[1])
        if self.__tokenizer.get_current_token()[1] == "void":
            self.__process("void")
        else:
            self.__compile_type()
        self.__process_identifier()
        self.__process("(")
        self.__compile_parameter_list()
        self.__process(")")
        self.__compile_subroutine_body()
        self.__file.write("</subroutineDec>\n")

    def __compile_parameter_list(self) -> None:
        self.__file.write("<parameterList>\n")
        while self.__tokenizer.get_current_token()[1] != ")":
            self.__compile_type()
            self.__process_identifier()
            if self.__tokenizer.get_current_token()[1] == ",":
                self.__process(",")
        self.__file.write("</parameterList>\n")

    def __compile_subroutine_body(self) -> None:
        self.__file.write("<subroutineBody>\n")
        self.__process("{")
        while self.__tokenizer.get_current_token()[1] == "var":
            self.__compile_var_dec()
        self.__compile_statements()
        self.__process("}")
        self.__file.write("</subroutineBody>\n")

    def __compile_var_dec(self) -> None:
        self.__file.write("<varDec>\n")
        self.__process("var")
        self.__compile_type()
        self.__process_identifier()
        while self.__tokenizer.get_current_token()[1] == ",":
            self.__process(",")
            self.__process_identifier()
        self.__process(";")
        self.__file.write("</varDec>\n")

    def __compile_statements(self) -> None:
        self.__file.write("<statements>\n")
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
        self.__file.write("</statements>\n")

    def __compile_let(self) -> None:
        self.__file.write("<letStatement>\n")
        self.__process("let")
        self.__process_identifier()
        if self.__tokenizer.get_current_token()[1] == "[":
            self.__process("[")
            self.__compile_expression()
            self.__process("]")
        self.__process("=")
        self.__compile_expression()
        self.__process(";")
        self.__file.write("</letStatement>\n")

    def __compile_if(self) -> None:
        self.__file.write("<ifStatement>\n")
        self.__process("if")
        self.__process("(")
        self.__compile_expression()
        self.__process(")")
        self.__process("{")
        self.__compile_statements()
        self.__process("}")
        if self.__tokenizer.get_current_token()[1] == "else":
            self.__process("else")
            self.__process("{")
            self.__compile_statements()
            self.__process("}")
        self.__file.write("</ifStatement>\n")

    def __compile_while(self) -> None:
        self.__file.write("<whileStatement>\n")
        self.__process("while")
        self.__process("(")
        self.__compile_expression()
        self.__process(")")
        self.__process("{")
        self.__compile_statements()
        self.__process("}")
        self.__file.write("</whileStatement>\n")

    def __compile_do(self) -> None:
        self.__file.write("<doStatement>\n")
        self.__process("do")
        self.__process_subroutine_call()
        self.__process(";")
        self.__file.write("</doStatement>\n")

    def __compile_return(self) -> None:
        self.__file.write("<returnStatement>\n")
        self.__process("return")
        if self.__tokenizer.get_current_token()[1] != ";":
            self.__compile_expression()
        self.__process(";")
        self.__file.write("</returnStatement>\n")

    def __compile_expression(self) -> None:
        self.__file.write("<expression>\n")
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
            self.__process(self.__tokenizer.get_current_token()[1])
            self.__compile_term()
        self.__file.write("</expression>\n")

    def __compile_term(self) -> None:
        self.__file.write("<term>\n")
        token_type, token = self.__tokenizer.get_current_token()
        if token_type == TokenType.INT_CONST:
            self.__process(token)
        elif token_type == TokenType.STRING_CONST:
            self.__process(token)
        elif token in {
            "true",
            "false",
            "null",
            "this",
        }:
            self.__process(token)
        elif token == "(":
            self.__process("(")
            self.__compile_expression()
            self.__process(")")
        elif token in {
            "-",
            "~",
        }:
            self.__process(token)
            self.__compile_term()
        else:
            self.__process_identifier()
            if self.__tokenizer.get_current_token()[1] == "[":
                self.__process("[")
                self.__compile_expression()
                self.__process("]")
            elif self.__tokenizer.get_current_token()[1] == ".":
                self.__process(".")
                self.__process_subroutine_call()
            elif self.__tokenizer.get_current_token()[1] == "(":
                self.__process("(")
                self.__compile_expression_list()
                self.__process(")")
        self.__file.write("</term>\n")

    def __compile_expression_list(self) -> None:
        self.__file.write("<expressionList>\n")
        if self.__tokenizer.get_current_token()[1] != ")":
            self.__compile_expression()
            while self.__tokenizer.get_current_token()[1] == ",":
                self.__process(",")
                self.__compile_expression()
        self.__file.write("</expressionList>\n")

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


argparser = argparse.ArgumentParser(
    description="Syntax Analyzer of a Jack Compiler", prog="JackAnalyzer"
)
argparser.add_argument(
    "target",
    help=".jack file or folder containing .jack files to be analyzed. Each .jack file analyzed will produce a corresponding .xml file with the same name. If `tokenize` mode is selected, the file name will have a `T` suffix appended (i.e. Main.jack => MainT.xml)",
    type=str,
)
argparser.add_argument(
    "-m",
    "--mode",
    choices=[AnalyzerMode.TOKENIZE, AnalyzerMode.PARSE],
    default=AnalyzerMode.PARSE,
    help="action of the %(prog)s. t = tokenize, p = parse. (default: %(default)s)",
    type=str,
)


def main() -> None:
    args = argparser.parse_args()

    is_dir = os.path.isdir(args.target)
    files_to_analyze = []
    if is_dir:
        for file in os.listdir(args.target):
            if file.endswith(".jack"):
                file_name, _ = os.path.splitext(file)

                src_file = os.path.join(args.target, file)
                dst_file = os.path.join(
                    args.target,
                    f"{file_name}T.xml"
                    if args.mode == AnalyzerMode.TOKENIZE
                    else f"{file_name}.xml",
                )

                files_to_analyze.append((src_file, dst_file))
    else:
        file_path, _ = os.path.splitext(args.target)

        src_file = args.target
        dst_file = (
            f"{file_path}T.xml"
            if args.mode == AnalyzerMode.TOKENIZE
            else f"{file_path}.xml"
        )

        files_to_analyze.append((src_file, dst_file))

    for src_file, dst_file in files_to_analyze:
        analyzer = Analyzer(src_file, dst_file)
        analyzer.analyze(args.mode)


if __name__ == "__main__":
    main()
