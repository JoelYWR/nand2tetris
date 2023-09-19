import argparse

parser = argparse.ArgumentParser(description="Assembler for Hack Assembly Language")
parser.add_argument(
    "-f",
    "--file",
    help=".asm file to be assembled. This file is assumed to be error-free. The output will be a .hack file with the same name as the input file.",
    required=True,
    type=str,
)

SYMBOL_TABLE = {
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
    "R0": 0,
    "R1": 1,
    "R2": 2,
    "R3": 3,
    "R4": 4,
    "R5": 5,
    "R6": 6,
    "R7": 7,
    "R8": 8,
    "R9": 9,
    "R10": 10,
    "R11": 11,
    "R12": 12,
    "R13": 13,
    "R14": 14,
    "R15": 15,
    "SCREEN": 16384,
    "KBD": 24576,
}

COMP_TABLE = {
    "0": "0101010",
    "1": "0111111",
    "-1": "0111010",
    "D": "0001100",
    "A": "0110000",
    "!D": "0001101",
    "!A": "0110001",
    "-D": "0001111",
    "-A": "0110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "D+A": "0000010",
    "D-A": "0010011",
    "A-D": "0000111",
    "D&A": "0000000",
    "D|A": "0010101",
    "M": "1110000",
    "!M": "1110001",
    "-M": "1110011",
    "M+1": "1110111",
    "M-1": "1110010",
    "D+M": "1000010",
    "D-M": "1010011",
    "M-D": "1000111",
    "D&M": "1000000",
    "D|M": "1010101",
}

DEST_TABLE = {
    "null": "000",
    "M": "001",
    "D": "010",
    "MD": "011",
    "A": "100",
    "AM": "101",
    "AD": "110",
    "AMD": "111",
}

JUMP_TABLE = {
    "null": "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}

if __name__ == "__main__":
    args = parser.parse_args()
    file_name = args.file.rsplit(".", 1)[0]

    # First Pass
    instruction_count = 0
    with open(args.file, "r") as s_file:
        with open(f"{file_name}.clean.asm", "w") as t_file:
            for line in s_file:
                line = line.strip()
                # Ignore comments and empty lines
                if line.startswith("//") or line == "":
                    continue
                # Handle label symbols
                if line.startswith("(") and line.endswith(")"):
                    symbol = line[1:-1]
                    SYMBOL_TABLE[symbol] = instruction_count
                    continue
                # Handle inline comments
                if "//" in line:
                    line = line.split("//")[0].strip()
                t_file.write(f"{line}\n")
                instruction_count += 1

    # Second Pass
    next_available_address = 16
    with open(f"{file_name}.clean.asm", "r") as s_file:
        with open(f"{file_name}.hack", "w") as t_file:
            for line in s_file:
                line = line.strip()
                # A-Instruction
                if line.startswith("@"):
                    symbol = line[1:]
                    if symbol.isdigit():
                        value = int(symbol)
                    elif symbol in SYMBOL_TABLE:
                        value = SYMBOL_TABLE[symbol]
                    # Handle new variable symbols
                    else:
                        value = next_available_address
                        SYMBOL_TABLE[symbol] = next_available_address
                        next_available_address += 1
                    t_file.write(f"0{value:015b}\n")
                # C-Instruction
                else:
                    dest = "null"
                    jump = "null"
                    if "=" in line:
                        dest, line = line.split("=")
                    if ";" in line:
                        line, jump = line.split(";")
                    comp = line
                    t_file.write(
                        f"111{COMP_TABLE[comp]}{DEST_TABLE[dest]}{JUMP_TABLE[jump]}\n"
                    )
