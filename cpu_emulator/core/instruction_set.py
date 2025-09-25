"""
Определение набора команд для эмулятора CPU
Фон-неймановская архитектура с двухадресными командами

Формат команды: 32 бита
┌─────────────┬─────────────┬─────────────────────────────┐
│   Opcode    │   Dest/Reg1 │    Source/Reg2/Immediate    │
│   8 бит     │   8 бит     │         16 бит              │
└─────────────┴─────────────┴─────────────────────────────┘

Двухадресные команды: OPERATION DEST, SOURCE
- DEST = DEST OP SOURCE
- Результат сохраняется в первом операнде (DEST)

Примеры:
- ADD R1, R2    ; R1 = R1 + R2
- ADD R1, #100  ; R1 = R1 + 100
- MOV R1, R2    ; R1 = R2
- LOAD R1, [R2] ; R1 = Memory[R2]
"""

from dataclasses import dataclass
from enum import IntEnum


class OpCode(IntEnum):
    """Опкоды команд для двухадресной архитектуры"""

    # Системные команды
    NOP = 0x00  # Нет операции
    HALT = 0x01  # Остановка процессора

    # Команды перемещения данных
    MOV_REG = 0x10  # MOV R1, R2 - R1 = R2 (копирование между регистрами)
    MOV_IMM = 0x11  # MOV R1, #imm - R1 = imm (загрузка константы)
    LOAD = 0x12  # LOAD R1, [R2] - R1 = Memory[R2] (загрузка из памяти)
    STORE = 0x13  # STORE [R1], R2 - Memory[R1] = R2 (сохранение в память)

    # Арифметические команды (двухадресные: DEST = DEST OP SOURCE)
    ADD_REG = 0x20  # ADD R1, R2 - R1 = R1 + R2
    ADD_IMM = 0x21  # ADD R1, #imm - R1 = R1 + imm
    SUB_REG = 0x22  # SUB R1, R2 - R1 = R1 - R2
    SUB_IMM = 0x23  # SUB R1, #imm - R1 = R1 - imm
    MUL_REG = 0x24  # MUL R1, R2 - R1 = R1 * R2
    MUL_IMM = 0x25  # MUL R1, #imm - R1 = R1 * imm
    DIV_REG = 0x26  # DIV R1, R2 - R1 = R1 / R2
    DIV_IMM = 0x27  # DIV R1, #imm - R1 = R1 / imm

    # Логические команды (двухадресные)
    AND_REG = 0x30  # AND R1, R2 - R1 = R1 & R2
    AND_IMM = 0x31  # AND R1, #imm - R1 = R1 & imm
    OR_REG = 0x32  # OR R1, R2 - R1 = R1 | R2
    OR_IMM = 0x33  # OR R1, #imm - R1 = R1 | imm
    XOR_REG = 0x34  # XOR R1, R2 - R1 = R1 ^ R2
    XOR_IMM = 0x35  # XOR R1, #imm - R1 = R1 ^ imm
    NOT = 0x36  # NOT R1 - R1 = ~R1 (унарная операция)

    # Команды сдвига (двухадресные)
    SHL_REG = 0x40  # SHL R1, R2 - R1 = R1 << R2
    SHL_IMM = 0x41  # SHL R1, #imm - R1 = R1 << imm
    SHR_REG = 0x42  # SHR R1, R2 - R1 = R1 >> R2 (логический)
    SHR_IMM = 0x43  # SHR R1, #imm - R1 = R1 >> imm (логический)
    SAR_REG = 0x44  # SAR R1, R2 - R1 = R1 >> R2 (арифметический)
    SAR_IMM = 0x45  # SAR R1, #imm - R1 = R1 >> imm (арифметический)

    # Команды сравнения (не изменяют операнды, только флаги)
    CMP_REG = 0x50  # CMP R1, R2 - сравнить R1 и R2
    CMP_IMM = 0x51  # CMP R1, #imm - сравнить R1 и константу

    # Команды условных переходов (одноадресные)
    JMP = 0x60  # JMP addr - безусловный переход
    JZ = 0x61  # JZ addr - переход если Zero flag
    JNZ = 0x62  # JNZ addr - переход если не Zero flag
    JC = 0x63  # JC addr - переход если Carry flag
    JNC = 0x64  # JNC addr - переход если не Carry flag
    JS = 0x65  # JS addr - переход если Sign flag
    JNS = 0x66  # JNS addr - переход если не Sign flag

    # В RISC-V стиле нет отдельных PUSH/POP команд
    # Стековые операции выполняются через базовые инструкции:
    # PUSH R1 ≡ SUB SP, SP, #4; STORE [SP], R1
    # POP R1  ≡ LOAD R1, [SP]; ADD SP, SP, #4


class InstructionType(IntEnum):
    """Типы команд по формату операндов для двухадресной архитектуры"""

    NO_OPERANDS = 0  # NOP, HALT
    REG_REG = 1  # ADD R1, R2 (двухадресная: R1 = R1 + R2)
    REG_IMM = 2  # ADD R1, #100 (двухадресная с константой)
    REG_UNARY = 3  # NOT R1 (унарная операция)
    LOAD = 4  # LOAD R1, [R2] (загрузка из памяти)
    STORE = 5  # STORE [R1], R2 (сохранение в память)
    JUMP = 6  # JMP addr (переходы)
    # В RISC-V стиле нет отдельного типа стековых команд


@dataclass
class Instruction:
    """Структура команды после декодирования для двухадресной архитектуры"""

    opcode: OpCode
    instruction_type: InstructionType
    dest_reg: int | None = None  # Регистр назначения (первый операнд)
    source_reg: int | None = None  # Исходный регистр (второй операнд)
    immediate: int | None = None  # Непосредственное значение
    address: int | None = None  # Адрес для переходов

    def __str__(self) -> str:
        """Строковое представление команды для отладки"""
        opcode_name = self.opcode.name.replace("_REG", "").replace("_IMM", "")

        if self.instruction_type == InstructionType.NO_OPERANDS:
            return f"{opcode_name}"
        elif self.instruction_type == InstructionType.REG_REG:
            return f"{opcode_name} R{self.dest_reg}, R{self.source_reg}"
        elif self.instruction_type == InstructionType.REG_IMM:
            return f"{opcode_name} R{self.dest_reg}, #{self.immediate}"
        elif self.instruction_type == InstructionType.REG_UNARY:
            return f"{opcode_name} R{self.dest_reg}"
        elif self.instruction_type == InstructionType.LOAD:
            return f"LOAD R{self.dest_reg}, [R{self.source_reg}]"
        elif self.instruction_type == InstructionType.STORE:
            return f"STORE [R{self.dest_reg}], R{self.source_reg}"
        elif self.instruction_type == InstructionType.JUMP:
            return f"{opcode_name} 0x{self.address:04X}"
        elif self.instruction_type == InstructionType.STACK:
            return f"{opcode_name} R{self.dest_reg}"
        else:
            return f"{opcode_name} (unknown format)"


# Словарь для определения типа команды по опкоду (двухадресная архитектура)
INSTRUCTION_FORMATS = {
    # Системные команды
    OpCode.NOP: InstructionType.NO_OPERANDS,
    OpCode.HALT: InstructionType.NO_OPERANDS,
    # Команды перемещения данных
    OpCode.MOV_REG: InstructionType.REG_REG,
    OpCode.MOV_IMM: InstructionType.REG_IMM,
    OpCode.LOAD: InstructionType.LOAD,
    OpCode.STORE: InstructionType.STORE,
    # Арифметические команды (двухадресные)
    OpCode.ADD_REG: InstructionType.REG_REG,
    OpCode.ADD_IMM: InstructionType.REG_IMM,
    OpCode.SUB_REG: InstructionType.REG_REG,
    OpCode.SUB_IMM: InstructionType.REG_IMM,
    OpCode.MUL_REG: InstructionType.REG_REG,
    OpCode.MUL_IMM: InstructionType.REG_IMM,
    OpCode.DIV_REG: InstructionType.REG_REG,
    OpCode.DIV_IMM: InstructionType.REG_IMM,
    # Логические команды (двухадресные)
    OpCode.AND_REG: InstructionType.REG_REG,
    OpCode.AND_IMM: InstructionType.REG_IMM,
    OpCode.OR_REG: InstructionType.REG_REG,
    OpCode.OR_IMM: InstructionType.REG_IMM,
    OpCode.XOR_REG: InstructionType.REG_REG,
    OpCode.XOR_IMM: InstructionType.REG_IMM,
    OpCode.NOT: InstructionType.REG_UNARY,
    # Команды сдвига (двухадресные)
    OpCode.SHL_REG: InstructionType.REG_REG,
    OpCode.SHL_IMM: InstructionType.REG_IMM,
    OpCode.SHR_REG: InstructionType.REG_REG,
    OpCode.SHR_IMM: InstructionType.REG_IMM,
    OpCode.SAR_REG: InstructionType.REG_REG,
    OpCode.SAR_IMM: InstructionType.REG_IMM,
    # Команды сравнения
    OpCode.CMP_REG: InstructionType.REG_REG,
    OpCode.CMP_IMM: InstructionType.REG_IMM,
    # Команды переходов
    OpCode.JMP: InstructionType.JUMP,
    OpCode.JZ: InstructionType.JUMP,
    OpCode.JNZ: InstructionType.JUMP,
    OpCode.JC: InstructionType.JUMP,
    OpCode.JNC: InstructionType.JUMP,
    OpCode.JS: InstructionType.JUMP,
    OpCode.JNS: InstructionType.JUMP,
    # В RISC-V стиле нет отдельных PUSH/POP команд
}


def get_instruction_type(opcode: OpCode) -> InstructionType:
    """Получить тип команды по опкоду"""
    return INSTRUCTION_FORMATS.get(opcode, InstructionType.NO_OPERANDS)
