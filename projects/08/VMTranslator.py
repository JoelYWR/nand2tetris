import argparse
import os
import random
import string

from io import TextIOWrapper

argparser = argparse.ArgumentParser(description="Translator for Jack VM Code")
argparser.add_argument(
    "target",
    help=".vm file or folder containing .vm files to be translated. The output will be a .asm file with the same name as the input file or folder.",
    type=str,
)


class VMParser:
    # First operand (below the top of the stack) is accessed by M, second operand (top of the stack) is accessed by D
    _ADDRESS_BINARY_OPERANDS = [
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",
        "A=A-1",
    ]

    # The operand (top of the stack) is accessed by M
    _ADDRESS_UNARY_OPERAND = [
        "@SP",
        "A=M-1",
    ]

    # Set the top of the stack to the value of D, and increment the stack pointer.
    # D is assumed to be already set.
    _PUSH_DATA_TO_STACK = [
        "@SP",
        "A=M",
        "M=D",
        "@SP",
        "M=M+1",
    ]

    # Decrement the stack pointer, and set D to the value at the top of the stack.
    _POP_DATA_FROM_STACK = [
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",
    ]

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

    _CURRENT_FUNCTION = ""

    _FUNCTION_RETURN_COUNTER_MAP = {"0": 0}

    def __init__(self, src_file: str, dst_file: str, file_name: str) -> None:
        self._src_file = src_file
        self._dst_file = dst_file
        self._file_name = file_name

    def bootstrap(self) -> None:
        with open(self._dst_file, "a") as dst_file:
            bootstrap_code = [
                "// Bootstrap code",
                "@256",
                "D=A",
                "@SP",
                "M=D",
            ]
            dst_file.write("\n".join(bootstrap_code) + "\n")
            self._CURRENT_FUNCTION = "Sys.init"
            self._FUNCTION_RETURN_COUNTER_MAP["Sys.init"] = 0
            self._parse_function("call Sys.init 0", dst_file)

    def parse(self) -> None:
        with open(self._src_file, "r") as src_file:
            with open(self._dst_file, "a") as dst_file:
                for line in src_file:
                    line = line.strip()
                    if not line or line.startswith("//"):
                        continue
                    if "//" in line:
                        line = line.split("//")[0].strip()
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
                    elif cmd in {"label", "goto", "if-goto"}:
                        self._parse_branch(line, dst_file)
                    elif cmd in {"call", "function", "return"}:
                        if cmd == "function":
                            function_name = line.split(" ")[1]
                            self._CURRENT_FUNCTION = function_name
                            self._FUNCTION_RETURN_COUNTER_MAP[function_name] = 0
                        self._parse_function(line, dst_file)
                    else:
                        raise ValueError(f"Invalid command: {cmd}")

    def _parse_push(self, line: str, dst_file: TextIOWrapper) -> None:
        _, segment, index = line.split(" ")
        if segment == "constant":
            SET_DATA_TO_D = [
                f"@{index}",
                "D=A",
            ]
        elif segment in self._SEGMENT_NAME_TO_POINTER_MAP:
            SET_DATA_TO_D = [
                f"@{index}",
                "D=A",
                f"@{self._SEGMENT_NAME_TO_POINTER_MAP[segment]}",
                "A=M+D",
                "D=M",
            ]
        elif segment == "static":
            SET_DATA_TO_D = [
                f"@{self._file_name}.{index}",
                "D=M",
            ]
        elif segment == "pointer":
            SET_DATA_TO_D = [
                f"@{self._POINTER_NUM_TO_THIS_THAT_MAP[index]}",
                "D=M",
            ]
        elif segment == "temp":
            SET_DATA_TO_D = [
                f"@{index}",
                "D=A",
                "@5",
                "A=A+D",
                "D=M",
            ]
        else:
            raise ValueError(f"Invalid segment: {segment}")

        OUTPUT_OPERATIONS = SET_DATA_TO_D + self._PUSH_DATA_TO_STACK
        dst_file.write("\n".join(OUTPUT_OPERATIONS) + "\n")

    def _parse_pop(self, line: str, dst_file: TextIOWrapper) -> None:
        _, segment, index = line.split(" ")
        if segment in self._SEGMENT_NAME_TO_POINTER_MAP:
            SET_ADDRESS_TO_R13 = [
                f"@{index}",
                "D=A",
                f"@{self._SEGMENT_NAME_TO_POINTER_MAP[segment]}",
                "D=M+D",
                "@R13",
                "M=D",
            ]
            SET_DATA_FROM_D = [
                "@R13",
                "A=M",
                "M=D",
            ]
        elif segment == "static":
            SET_ADDRESS_TO_R13 = []
            SET_DATA_FROM_D = [
                f"@{self._file_name}.{index}",
                "M=D",
            ]
        elif segment == "pointer":
            SET_ADDRESS_TO_R13 = []
            SET_DATA_FROM_D = [
                f"@{self._POINTER_NUM_TO_THIS_THAT_MAP[index]}",
                "M=D",
            ]
        elif segment == "temp":
            SET_ADDRESS_TO_R13 = [
                f"@{index}",
                "D=A",
                "@5",
                "D=A+D",
                "@R13",
                "M=D",
            ]
            SET_DATA_FROM_D = [
                "@R13",
                "A=M",
                "M=D",
            ]
        else:
            raise ValueError(f"Invalid segment: {segment}")

        OUTPUT_OPERATIONS = (
            SET_ADDRESS_TO_R13 + self._POP_DATA_FROM_STACK + SET_DATA_FROM_D
        )
        dst_file.write("\n".join(OUTPUT_OPERATIONS) + "\n")

    def _parse_arithmetic_or_logical(self, cmd: str, dst_file: TextIOWrapper) -> None:
        if cmd in {"add", "sub", "neg", "and", "or", "not"}:
            OUTPUT_OPERATIONS = (
                self._ADDRESS_BINARY_OPERANDS
                if cmd in {"add", "sub", "and", "or"}
                else self._ADDRESS_UNARY_OPERAND
            ) + [
                f"M={self._ARITHMETIC_AND_LOGICAL_COMMANDS_TO_HACK_ASSEMBLY_LANGUAGE_MAP[cmd]}",
            ]
        elif cmd in {"eq", "gt", "lt"}:
            letters = string.ascii_uppercase
            label = "".join(random.choice(letters) for _ in range(8))
            if self._CURRENT_FUNCTION:
                label = f"{self._CURRENT_FUNCTION}${label}"
            OUTPUT_OPERATIONS = self._ADDRESS_BINARY_OPERANDS + [
                "D=M-D",
                "M=0",
                f"@{label}_IF_TRUE",
                f"D;{self._ARITHMETIC_AND_LOGICAL_COMMANDS_TO_HACK_ASSEMBLY_LANGUAGE_MAP[cmd]}",
                f"@{label}_END",
                "0;JMP",
                f"({label}_IF_TRUE)",
                "@SP",
                "A=M-1",
                "M=-1",
                f"({label}_END)",
            ]
        else:
            raise ValueError(f"Invalid command: {cmd}")

        dst_file.write("\n".join(OUTPUT_OPERATIONS) + "\n")

    def _parse_branch(self, line: str, dst_file: TextIOWrapper) -> None:
        cmd, label = line.split(" ")
        if self._CURRENT_FUNCTION:
            label = f"{self._CURRENT_FUNCTION}${label}"
        if cmd == "label":
            OUTPUT_OPERATIONS = [
                f"({label})",
            ]
        elif cmd == "goto":
            OUTPUT_OPERATIONS = [
                f"@{label}",
                "0;JMP",
            ]
        elif cmd == "if-goto":
            OUTPUT_OPERATIONS = self._POP_DATA_FROM_STACK + [
                f"@{label}",
                "D;JNE",
            ]
        else:
            raise ValueError(f"Invalid command: {cmd}")

        dst_file.write("\n".join(OUTPUT_OPERATIONS) + "\n")

    def _parse_function(self, line: str, dst_file: TextIOWrapper) -> None:
        cmd = line.split(" ")[0]
        if cmd == "call":
            _, function_name, num_args = line.split(" ")
            return_addr_label = f"{self._CURRENT_FUNCTION}$ret.{self._FUNCTION_RETURN_COUNTER_MAP[self._CURRENT_FUNCTION]}"
            self._FUNCTION_RETURN_COUNTER_MAP[self._CURRENT_FUNCTION] += 1
            OUTPUT_OPERATIONS = (
                [
                    f"@{return_addr_label}",
                    "D=A",
                ]
                + self._PUSH_DATA_TO_STACK
                + [
                    "@LCL",
                    "D=M",
                ]
                + self._PUSH_DATA_TO_STACK
                + [
                    "@ARG",
                    "D=M",
                ]
                + self._PUSH_DATA_TO_STACK
                + [
                    "@THIS",
                    "D=M",
                ]
                + self._PUSH_DATA_TO_STACK
                + [
                    "@THAT",
                    "D=M",
                ]
                + self._PUSH_DATA_TO_STACK
                + [
                    "@SP",
                    "D=M",
                    f"@{int(num_args) + 5}",
                    "D=D-A",
                    "@ARG",
                    "M=D",
                    "@SP",
                    "D=M",
                    "@LCL",
                    "M=D",
                    f"@{function_name}",
                    "0;JMP",
                    f"({return_addr_label})",
                ]
            )
        elif cmd == "function":
            _, function_name, num_vars = line.split(" ")
            OUTPUT_OPERATIONS = [
                f"({function_name})",
            ] + [
                "@SP",
                "A=M",
                "M=0",
                "@SP",
                "M=M+1",
            ] * int(num_vars)
        elif cmd == "return":
            GET_SAVED_FRAME_ADDR_FROM_R13 = [
                "@R13",
                "M=M-1",
                "A=M",
                "D=M",
            ]
            OUTPUT_OPERATIONS = (
                [
                    "@LCL",
                    "D=M",
                    "@R13",  # Store endFrame in R13
                    "M=D",
                    "@5",
                    "A=D-A",
                    "D=M",
                    "@R14",  # Store returnAddr in R14
                    "M=D",
                ]
                + self._POP_DATA_FROM_STACK
                + [
                    "@ARG",
                    "A=M",
                    "M=D",
                    "@ARG",
                    "D=M+1",
                    "@SP",
                    "M=D",
                ]
                + GET_SAVED_FRAME_ADDR_FROM_R13
                + [
                    "@THAT",
                    "M=D",
                ]
                + GET_SAVED_FRAME_ADDR_FROM_R13
                + [
                    "@THIS",
                    "M=D",
                ]
                + GET_SAVED_FRAME_ADDR_FROM_R13
                + [
                    "@ARG",
                    "M=D",
                ]
                + GET_SAVED_FRAME_ADDR_FROM_R13
                + [
                    "@LCL",
                    "M=D",
                ]
                + [
                    "@R14",
                    "A=M",
                    "0;JMP",
                ]
            )
        else:
            raise ValueError(f"Invalid command: {cmd}")

        dst_file.write("\n".join(OUTPUT_OPERATIONS) + "\n")


def main() -> None:
    args = argparser.parse_args()

    is_dir = os.path.isdir(args.target)
    files_to_parse = []
    if is_dir:
        dir_name = os.path.basename(args.target)
        dst_file = f"{args.target}/{dir_name}.asm"
        if os.path.exists(dst_file):
            os.remove(dst_file)

        parser = VMParser("", dst_file, "")
        parser.bootstrap()

        for file in os.listdir(args.target):
            if file.endswith(".vm"):
                file_name, _ = os.path.splitext(file)

                src_file = os.path.join(args.target, file)

                files_to_parse.append((src_file, dst_file, file_name))
    else:
        file_path, _ = os.path.splitext(args.target)
        file_name = os.path.basename(args.target)
        file_name, _ = os.path.splitext(file_name)

        src_file = args.target
        dst_file = f"{file_path}.asm"
        if os.path.exists(dst_file):
            os.remove(dst_file)

        files_to_parse.append((src_file, dst_file, file_name))

    for src_file, dst_file, file_name in files_to_parse:
        parser = VMParser(src_file, dst_file, file_name)
        parser.parse()


if __name__ == "__main__":
    main()
