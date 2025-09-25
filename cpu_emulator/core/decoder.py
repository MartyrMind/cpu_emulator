"""
Декодер команд для двухадресной архитектуры CPU

Формат команды: 32 бита
┌─────────────┬─────────────┬─────────────────────────────┐
│   Opcode    │   Dest/Reg1 │    Source/Reg2/Immediate    │
│   8 бит     │   8 бит     │         16 бит              │
└─────────────┴─────────────┴─────────────────────────────┘
"""


from loguru import logger

from cpu_emulator.core.exceptions import RegisterException
from cpu_emulator.core.instruction_set import (
    Instruction,
    InstructionType,
    OpCode,
    get_instruction_type,
)


class InstructionDecoder:
    """Декодер команд для двухадресной архитектуры"""

    def __init__(self):
        logger.debug("InstructionDecoder initialized")

    def decode(self, raw_instruction: int) -> Instruction:
        """
        Декодирует 32-битную команду в структуру Instruction

        Args:
            raw_instruction: 32-битная команда

        Returns:
            Instruction: Декодированная команда

        Raises:
            ValueError: Если опкод неизвестен
            RegisterException: Если номер регистра некорректен
        """
        # Извлекаем поля команды
        opcode_value = (raw_instruction >> 24) & 0xFF  # Старшие 8 бит
        reg1 = (raw_instruction >> 16) & 0xFF  # Следующие 8 бит
        operand = raw_instruction & 0xFFFF  # Младшие 16 бит

        logger.debug(
            f"Decoding instruction: 0x{raw_instruction:08X} -> "
            f"opcode=0x{opcode_value:02X}, reg1=0x{reg1:02X}, operand=0x{operand:04X}"
        )

        # Преобразуем опкод в enum
        try:
            opcode = OpCode(opcode_value)
        except ValueError:
            raise ValueError(f"Unknown opcode: 0x{opcode_value:02X}")

        # Определяем тип команды
        instruction_type = get_instruction_type(opcode)

        # Создаем базовую структуру команды
        instruction = Instruction(opcode=opcode, instruction_type=instruction_type)

        # Заполняем поля в зависимости от типа команды
        if instruction_type == InstructionType.NO_OPERANDS:
            # NOP, HALT - нет операндов
            pass

        elif instruction_type == InstructionType.REG_REG:
            # ADD R1, R2 - двухадресная операция
            self._validate_register(reg1)
            reg2 = operand & 0xFF  # Младшие 8 бит операнда
            self._validate_register(reg2)

            instruction.dest_reg = reg1
            instruction.source_reg = reg2

        elif instruction_type == InstructionType.REG_IMM:
            # ADD R1, #100 - операция с константой
            self._validate_register(reg1)

            # Знаковое расширение 16-битного значения до 32-бит
            immediate = self._sign_extend_16_to_32(operand)

            instruction.dest_reg = reg1
            instruction.immediate = immediate

        elif instruction_type == InstructionType.REG_UNARY:
            # NOT R1 - унарная операция
            self._validate_register(reg1)
            instruction.dest_reg = reg1

        elif instruction_type == InstructionType.LOAD:
            # LOAD R1, [R2] - загрузка из памяти
            self._validate_register(reg1)
            reg2 = operand & 0xFF
            self._validate_register(reg2)

            instruction.dest_reg = reg1
            instruction.source_reg = reg2

        elif instruction_type == InstructionType.STORE:
            # STORE [R1], R2 - сохранение в память
            self._validate_register(reg1)
            reg2 = operand & 0xFF
            self._validate_register(reg2)

            instruction.dest_reg = reg1  # Адрес в памяти
            instruction.source_reg = reg2  # Данные для записи

        elif instruction_type == InstructionType.JUMP:
            # JMP addr - переходы
            # Для переходов используем полные 16 бит как адрес
            instruction.address = operand

        elif instruction_type == InstructionType.STACK:
            # PUSH R1, POP R1 - стековые операции
            self._validate_register(reg1)
            instruction.dest_reg = reg1

        else:
            raise ValueError(f"Unknown instruction type: {instruction_type}")

        logger.debug(f"Decoded instruction: {instruction}")
        return instruction

    def encode(self, instruction: Instruction) -> int:
        """
        Кодирует структуру Instruction в 32-битную команду

        Args:
            instruction: Структура команды

        Returns:
            int: 32-битная команда
        """
        raw_instruction = 0

        # Устанавливаем опкод (старшие 8 бит)
        raw_instruction |= (instruction.opcode.value & 0xFF) << 24

        # Заполняем поля в зависимости от типа команды
        if instruction.instruction_type == InstructionType.NO_OPERANDS:
            pass  # Только опкод

        elif instruction.instruction_type == InstructionType.REG_REG:
            raw_instruction |= (instruction.dest_reg & 0xFF) << 16
            raw_instruction |= instruction.source_reg & 0xFF

        elif instruction.instruction_type == InstructionType.REG_IMM:
            raw_instruction |= (instruction.dest_reg & 0xFF) << 16
            raw_instruction |= instruction.immediate & 0xFFFF

        elif instruction.instruction_type == InstructionType.REG_UNARY:
            raw_instruction |= (instruction.dest_reg & 0xFF) << 16

        elif instruction.instruction_type in [
            InstructionType.LOAD,
            InstructionType.STORE,
        ]:
            raw_instruction |= (instruction.dest_reg & 0xFF) << 16
            raw_instruction |= instruction.source_reg & 0xFF

        elif instruction.instruction_type == InstructionType.JUMP:
            raw_instruction |= instruction.address & 0xFFFF

        elif instruction.instruction_type == InstructionType.STACK:
            raw_instruction |= (instruction.dest_reg & 0xFF) << 16

        logger.debug(f"Encoded instruction {instruction} -> 0x{raw_instruction:08X}")
        return raw_instruction

    def _validate_register(self, reg_num: int) -> None:
        """Проверяет корректность номера регистра"""
        # R0-R7: обычные регистры, R8: SP (в RISC-V стиле)
        if not (0 <= reg_num <= 8):
            raise RegisterException(f"Invalid register number: {reg_num}")

    def _sign_extend_16_to_32(self, value: int) -> int:
        """Знаковое расширение 16-битного значения до 32-бит"""
        if value & 0x8000:  # Если старший бит установлен (отрицательное число)
            return value | 0xFFFF0000  # Заполняем старшие биты единицами
        else:
            return value & 0x0000FFFF  # Заполняем старшие биты нулями


def create_instruction(opcode: OpCode, **kwargs) -> Instruction:
    """
    Вспомогательная функция для создания команд

    Args:
        opcode: Опкод команды
        **kwargs: Параметры команды (dest_reg, source_reg, immediate, address)

    Returns:
        Instruction: Созданная команда
    """
    instruction_type = get_instruction_type(opcode)

    instruction = Instruction(
        opcode=opcode, instruction_type=instruction_type, **kwargs
    )

    return instruction
