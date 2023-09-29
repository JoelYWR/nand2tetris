import argparse
import os
import random
import string

from io import TextIOWrapper
from textwrap import dedent

argparser = argparse.ArgumentParser(description="Translator for Jack VM Code")
argparser.add_argument(
    "file",
    help=".vm file to be translated. This file is assumed to be error-free. The output will be a .asm file with the same name as the input file.",
    type=str,
)


class VMParser:
    # First operand (below the top of the stack) is accessed by M, second operand (top of the stack) is accessed by D
    _ADDRESS_BINARY_OPERANDS = """\
        @SP
        M=M-1
        A=M
        D=M
        A=A-1
    """

    # The operand (top of the stack) is accessed by M
    _ADDRESS_UNARY_OPERAND = """\
        @SP
        A=M-1
    """

    # Set the top of the stack to the value of D, and increment the stack pointer.
    # D is assumed to be already set.
    _PUSH_DATA_TO_STACK = """\
        @SP
        A=M
        M=D
        @SP
        M=M+1
    """

    # Decrement the stack pointer, and set D to the value at the top of the stack.
    _POP_DATA_FROM_STACK = """\
        @SP
        M=M-1
        A=M
        D=M
    """

    _ARITHMETIC_AND_LOGICAL_COMMANDS_TO_HACK_ASSEMBLY_LANGUAGE_MAP = {
        "add": "D+M",
        "sub": "M-D",
        "neg": "-M",
        "eq": "JEQ",
        "gt": "JGT",
        "lt": "JLT",
        "and": "D&M",
        "or": "D|M",
        "not": "!M",
    }

    _POINTER_NUM_TO_THIS_THAT_MAP = {
        "0": "THIS",
        "1": "THAT",
    }

    _SEGMENT_NAME_TO_POINTER_MAP = {
        "local": "LCL",
        "argument": "ARG",
        "this": "THIS",
        "that": "THAT",
    }

    def __init__(self, file: str) -> None:
        file_path, _ = os.path.splitext(file)
        file_name = os.path.basename(file)
        file_name, _ = os.path.splitext(file_name)

        self._src_file = file
        self._dst_file = f"{file_path}.asm"
        self._file_name = file_name

    def parse(self) -> None:
        with open(self._src_file, "r") as src_file:
            with open(self._dst_file, "w") as dst_file:
                for line in src_file:
                    line = line.strip()
                    if not line or line.startswith("//"):
                        continue
                    dst_file.write(f"// {line}\n")
                    cmd = line.split(" ")[0]
                    if cmd == "push":
                        self._parse_push(line, dst_file)
                    elif cmd == "pop":
                        self._parse_pop(line, dst_file)
                    elif (
                        cmd
                        in self._ARITHMETIC_AND_LOGICAL_COMMANDS_TO_HACK_ASSEMBLY_LANGUAGE_MAP
                    ):
                        self._parse_arithmetic_or_logical(cmd, dst_file)
                    else:
                        raise ValueError(f"Invalid command: {cmd}")

    def _parse_push(self, line: str, dst_file: TextIOWrapper) -> None:
        _, segment, index = line.split(" ")
        if segment == "constant":
            SET_DATA_TO_D = f"""\
                @{index}
                D=A
            """
        elif segment in self._SEGMENT_NAME_TO_POINTER_MAP:
            SET_DATA_TO_D = f"""\
                @{index}
                D=A
                @{self._SEGMENT_NAME_TO_POINTER_MAP[segment]}
                A=M+D
                D=M
            """
        elif segment == "static":
            SET_DATA_TO_D = f"""\
                @{self._file_name}.{index}
                D=M
            """
        elif segment == "pointer":
            SET_DATA_TO_D = f"""\
                @{self._POINTER_NUM_TO_THIS_THAT_MAP[index]}
                D=M
            """
        elif segment == "temp":
            SET_DATA_TO_D = f"""\
                @{index}
                D=A
                @5
                A=A+D
                D=M
            """
        else:
            raise ValueError(f"Invalid segment: {segment}")

        dst_file.write(dedent(SET_DATA_TO_D))
        dst_file.write(dedent(self._PUSH_DATA_TO_STACK))

    def _parse_pop(self, line: str, dst_file: TextIOWrapper) -> None:
        _, segment, index = line.split(" ")
        if segment in self._SEGMENT_NAME_TO_POINTER_MAP:
            SET_ADDRESS_TO_R13 = f"""\
                @{index}
                D=A
                @{self._SEGMENT_NAME_TO_POINTER_MAP[segment]}
                D=M+D
                @R13
                M=D
            """
            SET_DATA_FROM_D = f"""\
                @R13
                A=M
                M=D
            """
        elif segment == "static":
            SET_ADDRESS_TO_R13 = ""
            SET_DATA_FROM_D = f"""\
                @{self._file_name}.{index}
                M=D
            """
        elif segment == "pointer":
            SET_ADDRESS_TO_R13 = ""
            SET_DATA_FROM_D = f"""\
                @{self._POINTER_NUM_TO_THIS_THAT_MAP[index]}
                M=D
            """
        elif segment == "temp":
            SET_ADDRESS_TO_R13 = f"""\
                @{index}
                D=A
                @5
                D=A+D
                @R13
                M=D
            """
            SET_DATA_FROM_D = f"""\
                @R13
                A=M
                M=D
            """
        else:
            raise ValueError(f"Invalid segment: {segment}")

        dst_file.write(dedent(SET_ADDRESS_TO_R13))
        dst_file.write(dedent(self._POP_DATA_FROM_STACK))
        dst_file.write(dedent(SET_DATA_FROM_D))

    def _parse_arithmetic_or_logical(self, cmd: str, dst_file: TextIOWrapper) -> None:
        if cmd in {"add", "sub", "neg", "and", "or", "not"}:
            OUTPUT_OPERATIONS = f"M={self._ARITHMETIC_AND_LOGICAL_COMMANDS_TO_HACK_ASSEMBLY_LANGUAGE_MAP[cmd]}\n"
            if cmd in {"add", "sub", "and", "or"}:
                dst_file.write(dedent(self._ADDRESS_BINARY_OPERANDS))
            else:
                dst_file.write(dedent(self._ADDRESS_UNARY_OPERAND))
            dst_file.write(OUTPUT_OPERATIONS)
        else:
            letters = string.ascii_uppercase
            label = "".join(random.choice(letters) for _ in range(8))
            OUTPUT_OPERATIONS = f"""\
                D=M-D
                M=0
                @{label}_TRUE
                D;{self._ARITHMETIC_AND_LOGICAL_COMMANDS_TO_HACK_ASSEMBLY_LANGUAGE_MAP[cmd]}
                @{label}_END
                0;JMP
                ({label}_TRUE)
                @SP
                A=M-1
                M=-1
                ({label}_END)
            """
            dst_file.write(dedent(self._ADDRESS_BINARY_OPERANDS))
            dst_file.write(dedent(OUTPUT_OPERATIONS))


def main() -> None:
    args = argparser.parse_args()

    vmparser = VMParser(args.file)
    vmparser.parse()


if __name__ == "__main__":
    main()
