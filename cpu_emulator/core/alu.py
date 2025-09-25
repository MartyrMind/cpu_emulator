from loguru import logger

from cpu_emulator.core.flags import Flags
from cpu_emulator.core.registers import Registers


class ALU:
    def __init__(self, registers: Registers, flags: Flags):
        self.registers = registers
        self.flags = flags
        logger.debug("ALU initialized")

    # Арифметические операции
    def add(self, a: int, b: int) -> int:
        """Сложение двух чисел с обновлением флагов"""
        a = a & 0xFFFFFFFF
        b = b & 0xFFFFFFFF
        result = (a + b) & 0xFFFFFFFF
        self.flags.arithmetic_update(a, b, result, "ADD")
        logger.debug(f"ADD: 0x{a:08X} + 0x{b:08X} = 0x{result:08X}")
        return result

    def sub(self, a: int, b: int) -> int:
        """Вычитание двух чисел с обновлением флагов"""
        a = a & 0xFFFFFFFF
        b = b & 0xFFFFFFFF
        result = (a - b) & 0xFFFFFFFF
        self.flags.arithmetic_update(a, b, result, "SUB")
        logger.debug(f"SUB: 0x{a:08X} - 0x{b:08X} = 0x{result:08X}")
        return result

    def mul(self, a: int, b: int) -> int:
        """Умножение двух чисел (младшие 32 бита результата)"""
        a = a & 0xFFFFFFFF
        b = b & 0xFFFFFFFF
        full_result = a * b
        result = full_result & 0xFFFFFFFF

        self.flags.multiplication_update(result, full_result)

        logger.debug(
            f"MUL: 0x{a:08X} * 0x{b:08X} = 0x{result:08X} (full: 0x{full_result:016X})"
        )
        return result

    def div(self, a: int, b: int) -> tuple[int, int]:
        """Деление двух чисел, возвращает частное и остаток"""
        if b == 0:
            raise ZeroDivisionError("Division by zero")

        a = a & 0xFFFFFFFF
        b = b & 0xFFFFFFFF
        quotient = (a // b) & 0xFFFFFFFF
        remainder = (a % b) & 0xFFFFFFFF

        self.flags.division_update(quotient)

        logger.debug(
            f"DIV: 0x{a:08X} / 0x{b:08X} = 0x{quotient:08X} остаток 0x{remainder:08X}"
        )
        return quotient, remainder

    def compare(self, a: int, b: int) -> None:
        """Сравнение двух чисел (как вычитание, но без сохранения результата)"""
        a = a & 0xFFFFFFFF
        b = b & 0xFFFFFFFF
        result = (a - b) & 0xFFFFFFFF
        self.flags.arithmetic_update(a, b, result, "CMP")
        logger.debug(f"CMP: 0x{a:08X} vs 0x{b:08X}")

    # Логические операции
    def logical_and(self, a: int, b: int) -> int:
        """Логическое И с обновлением флагов"""
        a = a & 0xFFFFFFFF
        b = b & 0xFFFFFFFF
        result = (a & b) & 0xFFFFFFFF
        self.flags.logical_update(result)
        logger.debug(f"AND: 0x{a:08X} & 0x{b:08X} = 0x{result:08X}")
        return result

    def logical_or(self, a: int, b: int) -> int:
        """Логическое ИЛИ с обновлением флагов"""
        a = a & 0xFFFFFFFF
        b = b & 0xFFFFFFFF
        result = (a | b) & 0xFFFFFFFF
        self.flags.logical_update(result)
        logger.debug(f"OR: 0x{a:08X} | 0x{b:08X} = 0x{result:08X}")
        return result

    def logical_xor(self, a: int, b: int) -> int:
        """Логическое исключающее ИЛИ с обновлением флагов"""
        a = a & 0xFFFFFFFF
        b = b & 0xFFFFFFFF
        result = (a ^ b) & 0xFFFFFFFF
        self.flags.logical_update(result)
        logger.debug(f"XOR: 0x{a:08X} ^ 0x{b:08X} = 0x{result:08X}")
        return result

    def logical_not(self, a: int) -> int:
        """Логическое НЕ (инверсия) с обновлением флагов"""
        a = a & 0xFFFFFFFF
        result = (~a) & 0xFFFFFFFF
        self.flags.logical_update(result)
        logger.debug(f"NOT: ~0x{a:08X} = 0x{result:08X}")
        return result

    # Операции сдвига
    def shift_left(self, a: int, count: int) -> int:
        """Логический сдвиг влево"""
        a = a & 0xFFFFFFFF
        count = count & 0x1F  # Ограничиваем сдвиг 31 битом

        result = (a << count) & 0xFFFFFFFF
        self.flags.shift_left_update(a, count, result)

        logger.debug(f"SHL: 0x{a:08X} << {count} = 0x{result:08X}")
        return result

    def shift_right(self, a: int, count: int) -> int:
        """Логический сдвиг вправо"""
        a = a & 0xFFFFFFFF
        count = count & 0x1F  # Ограничиваем сдвиг 31 битом

        result = (a >> count) & 0xFFFFFFFF
        self.flags.shift_right_update(a, count, result)

        logger.debug(f"SHR: 0x{a:08X} >> {count} = 0x{result:08X}")
        return result

    def arithmetic_shift_right(self, a: int, count: int) -> int:
        """Арифметический сдвиг вправо (с сохранением знака)"""
        a = a & 0xFFFFFFFF
        count = count & 0x1F  # Ограничиваем сдвиг 31 битом

        # Преобразуем в знаковое число
        signed_a = a if a < 0x80000000 else a - 0x100000000

        # Выполняем арифметический сдвиг
        result = (signed_a >> count) & 0xFFFFFFFF

        self.flags.shift_right_update(a, count, result)
        logger.debug(f"SAR: 0x{a:08X} >> {count} = 0x{result:08X} (arithmetic)")
        return result

    def rotate_left(self, a: int, count: int) -> int:
        """Поворот влево"""
        a = a & 0xFFFFFFFF
        count = count & 0x1F  # Ограничиваем поворот 31 битом

        if count == 0:
            return a

        result = ((a << count) | (a >> (32 - count))) & 0xFFFFFFFF
        carry_out = result & 1  # Младший бит результата

        self.flags.rotate_update(result, carry_out)
        logger.debug(f"ROL: 0x{a:08X} rotate left {count} = 0x{result:08X}")
        return result

    def rotate_right(self, a: int, count: int) -> int:
        """Поворот вправо"""
        a = a & 0xFFFFFFFF
        count = count & 0x1F  # Ограничиваем поворот 31 битом

        if count == 0:
            return a

        result = ((a >> count) | (a << (32 - count))) & 0xFFFFFFFF
        carry_out = (result >> 31) & 1  # Старший бит результата

        self.flags.rotate_update(result, carry_out)
        logger.debug(f"ROR: 0x{a:08X} rotate right {count} = 0x{result:08X}")
        return result
