"""
Загрузчик программ для эмулятора CPU
Поддерживает различные форматы программ
"""

import struct

from loguru import logger

from cpu_emulator.core.decoder import InstructionDecoder, create_instruction
from cpu_emulator.core.instruction_set import OpCode


class ProgramLoader:
    """
    Загрузчик программ для CPU эмулятора

    Поддерживаемые форматы:
    - Машинный код (массив 32-битных команд)
    - Простой ассемблер (текстовые мнемоники)
    """

    def __init__(self):
        self.decoder = InstructionDecoder()
        logger.debug("ProgramLoader initialized")

    def assemble_simple(self, assembly_lines: list[str]) -> bytes:
        """
        Простой ассемблер для базовых команд с поддержкой RISC-V стиля

        Args:
            assembly_lines: Список строк с мнемониками

        Returns:
            bytes: Машинный код

        Example:
            lines = [
                "MOV R0, #100",    # Загрузить 100 в R0
                "MOV R1, #200",    # Загрузить 200 в R1
                "ADD R0, R1",      # R0 = R0 + R1
                "PUSH R0",         # Автоматически разворачивается в SUB R8, #4; STORE [R8], R0
                "POP R1",          # Автоматически разворачивается в LOAD R1, [R8]; ADD R8, #4
                "HALT"             # Остановка
            ]
        """
        instructions = []

        for line_num, line in enumerate(assembly_lines, 1):
            try:
                line = line.strip()
                if not line or line.startswith(";"):  # Пустые строки и комментарии
                    continue

                # Обрабатываем PUSH/POP в RISC-V стиле
                parts = line.replace(",", "").split()
                if parts and parts[0].upper() == "PUSH":
                    # PUSH R1 → SUB R8, R8, #4; STORE [R8], R1
                    source_reg = self._parse_register(parts[1])
                    instructions.append(
                        create_instruction(OpCode.SUB_IMM, dest_reg=8, immediate=4)
                    )
                    instructions.append(
                        create_instruction(
                            OpCode.STORE, dest_reg=8, source_reg=source_reg
                        )
                    )
                elif parts and parts[0].upper() == "POP":
                    # POP R1 → LOAD R1, [R8]; ADD R8, R8, #4
                    dest_reg = self._parse_register(parts[1])
                    instructions.append(
                        create_instruction(OpCode.LOAD, dest_reg=dest_reg, source_reg=8)
                    )
                    instructions.append(
                        create_instruction(OpCode.ADD_IMM, dest_reg=8, immediate=4)
                    )
                else:
                    # Обычные команды
                    instruction = self._parse_assembly_line(line)
                    if instruction:
                        instructions.append(instruction)

            except Exception as e:
                raise ValueError(f"Assembly error on line {line_num}: '{line}' - {e}")

        # Кодируем команды в машинный код
        machine_code = bytearray()
        for instruction in instructions:
            encoded = self.decoder.encode(instruction)
            machine_code.extend(struct.pack("<I", encoded))  # Little-endian 32-bit

        logger.info(
            f"Assembled {len(instructions)} instructions into {len(machine_code)} bytes"
        )
        return bytes(machine_code)

    def _parse_assembly_line(self, line: str):
        """Парсинг одной строки ассемблера"""
        parts = line.replace(",", "").split()
        if not parts:
            return None

        mnemonic = parts[0].upper()

        # Системные команды
        if mnemonic in ["NOP", "HALT"]:
            return create_instruction(OpCode[mnemonic])

        # Команды перемещения данных
        elif mnemonic == "MOV":
            return self._parse_mov(parts[1:])
        elif mnemonic == "LOAD":
            return self._parse_load(parts[1:])
        elif mnemonic == "STORE":
            return self._parse_store(parts[1:])

        # Арифметические команды
        elif mnemonic == "ADD":
            return self._parse_arithmetic(OpCode.ADD_REG, OpCode.ADD_IMM, parts[1:])
        elif mnemonic == "SUB":
            return self._parse_arithmetic(OpCode.SUB_REG, OpCode.SUB_IMM, parts[1:])
        elif mnemonic == "MUL":
            return self._parse_arithmetic(OpCode.MUL_REG, OpCode.MUL_IMM, parts[1:])
        elif mnemonic == "DIV":
            return self._parse_arithmetic(OpCode.DIV_REG, OpCode.DIV_IMM, parts[1:])

        # Логические команды
        elif mnemonic == "AND":
            return self._parse_arithmetic(OpCode.AND_REG, OpCode.AND_IMM, parts[1:])
        elif mnemonic == "OR":
            return self._parse_arithmetic(OpCode.OR_REG, OpCode.OR_IMM, parts[1:])
        elif mnemonic == "XOR":
            return self._parse_arithmetic(OpCode.XOR_REG, OpCode.XOR_IMM, parts[1:])
        elif mnemonic == "NOT":
            return self._parse_not(parts[1:])

        # Команды сдвига
        elif mnemonic == "SHL":
            return self._parse_arithmetic(OpCode.SHL_REG, OpCode.SHL_IMM, parts[1:])
        elif mnemonic == "SHR":
            return self._parse_arithmetic(OpCode.SHR_REG, OpCode.SHR_IMM, parts[1:])
        elif mnemonic == "SAR":
            return self._parse_arithmetic(OpCode.SAR_REG, OpCode.SAR_IMM, parts[1:])

        # Команды сравнения
        elif mnemonic == "CMP":
            return self._parse_arithmetic(OpCode.CMP_REG, OpCode.CMP_IMM, parts[1:])

        # Команды переходов
        elif mnemonic == "JMP":
            return self._parse_jump(OpCode.JMP, parts[1:])
        elif mnemonic == "JZ":
            return self._parse_jump(OpCode.JZ, parts[1:])
        elif mnemonic == "JNZ":
            return self._parse_jump(OpCode.JNZ, parts[1:])
        elif mnemonic == "JC":
            return self._parse_jump(OpCode.JC, parts[1:])
        elif mnemonic == "JNC":
            return self._parse_jump(OpCode.JNC, parts[1:])
        elif mnemonic == "JS":
            return self._parse_jump(OpCode.JS, parts[1:])
        elif mnemonic == "JNS":
            return self._parse_jump(OpCode.JNS, parts[1:])

        else:
            raise ValueError(f"Unknown mnemonic: {mnemonic}")

    def _parse_register(self, reg_str: str) -> int:
        """Парсинг номера регистра из строки типа 'R0', 'R1', etc."""
        if not reg_str.upper().startswith("R"):
            raise ValueError(f"Invalid register format: {reg_str}")

        try:
            reg_num = int(reg_str[1:])
            # R0-R7: обычные регистры, R8: SP (в RISC-V стиле)
            if not (0 <= reg_num <= 8):
                raise ValueError(f"Register number out of range: {reg_num}")
            return reg_num
        except ValueError:
            raise ValueError(f"Invalid register number: {reg_str}")

    def _parse_immediate(self, imm_str: str) -> int:
        """Парсинг непосредственного значения из строки типа '#100', '#0xFF'"""
        if not imm_str.startswith("#"):
            raise ValueError(f"Immediate value must start with #: {imm_str}")

        value_str = imm_str[1:]

        try:
            # Поддерживаем шестнадцатеричные числа
            if value_str.lower().startswith("0x"):
                return int(value_str, 16)
            else:
                return int(value_str)
        except ValueError:
            raise ValueError(f"Invalid immediate value: {imm_str}")

    def _parse_address(self, addr_str: str) -> int:
        """Парсинг адреса для переходов"""
        try:
            if addr_str.lower().startswith("0x"):
                return int(addr_str, 16)
            else:
                return int(addr_str)
        except ValueError:
            raise ValueError(f"Invalid address: {addr_str}")

    def _parse_mov(self, operands: list[str]):
        """Парсинг команды MOV"""
        if len(operands) != 2:
            raise ValueError("MOV requires 2 operands")

        dest_reg = self._parse_register(operands[0])

        if operands[1].startswith("#"):
            # MOV R1, #imm
            immediate = self._parse_immediate(operands[1])
            return create_instruction(
                OpCode.MOV_IMM, dest_reg=dest_reg, immediate=immediate
            )
        else:
            # MOV R1, R2
            source_reg = self._parse_register(operands[1])
            return create_instruction(
                OpCode.MOV_REG, dest_reg=dest_reg, source_reg=source_reg
            )

    def _parse_load(self, operands: list[str]):
        """Парсинг команды LOAD"""
        if len(operands) != 2:
            raise ValueError("LOAD requires 2 operands")

        dest_reg = self._parse_register(operands[0])

        # LOAD R1, [R2]
        if operands[1].startswith("[") and operands[1].endswith("]"):
            source_reg_str = operands[1][1:-1]  # Убираем скобки
            source_reg = self._parse_register(source_reg_str)
            return create_instruction(
                OpCode.LOAD, dest_reg=dest_reg, source_reg=source_reg
            )
        else:
            raise ValueError("LOAD requires memory reference in brackets: [R1]")

    def _parse_store(self, operands: list[str]):
        """Парсинг команды STORE"""
        if len(operands) != 2:
            raise ValueError("STORE requires 2 operands")

        # STORE [R1], R2
        if operands[0].startswith("[") and operands[0].endswith("]"):
            dest_reg_str = operands[0][1:-1]  # Убираем скобки
            dest_reg = self._parse_register(dest_reg_str)
            source_reg = self._parse_register(operands[1])
            return create_instruction(
                OpCode.STORE, dest_reg=dest_reg, source_reg=source_reg
            )
        else:
            raise ValueError("STORE requires memory reference in brackets: [R1]")

    def _parse_arithmetic(
        self, reg_opcode: OpCode, imm_opcode: OpCode, operands: list[str]
    ):
        """Парсинг двухадресных арифметических команд"""
        if len(operands) != 2:
            raise ValueError("Arithmetic operation requires 2 operands")

        dest_reg = self._parse_register(operands[0])

        if operands[1].startswith("#"):
            # ADD R1, #imm
            immediate = self._parse_immediate(operands[1])
            return create_instruction(
                imm_opcode, dest_reg=dest_reg, immediate=immediate
            )
        else:
            # ADD R1, R2
            source_reg = self._parse_register(operands[1])
            return create_instruction(
                reg_opcode, dest_reg=dest_reg, source_reg=source_reg
            )

    def _parse_not(self, operands: list[str]):
        """Парсинг команды NOT (унарная)"""
        if len(operands) != 1:
            raise ValueError("NOT requires 1 operand")

        dest_reg = self._parse_register(operands[0])
        return create_instruction(OpCode.NOT, dest_reg=dest_reg)

    def _parse_jump(self, opcode: OpCode, operands: list[str]):
        """Парсинг команд переходов"""
        if len(operands) != 1:
            raise ValueError("Jump instruction requires 1 operand")

        address = self._parse_address(operands[0])
        return create_instruction(opcode, address=address)

    def load_from_bytes(self, machine_code: bytes) -> list[int]:
        """
        Загрузка программы из машинного кода

        Args:
            machine_code: Машинный код (последовательность 32-битных команд)

        Returns:
            List[int]: Список 32-битных команд
        """
        if len(machine_code) % 4 != 0:
            raise ValueError(
                f"Machine code length must be multiple of 4, got {len(machine_code)}"
            )

        instructions = []
        for i in range(0, len(machine_code), 4):
            instruction = struct.unpack("<I", machine_code[i : i + 4])[0]
            instructions.append(instruction)

        logger.info(f"Loaded {len(instructions)} instructions from machine code")
        return instructions
