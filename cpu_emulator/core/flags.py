from loguru import logger

from cpu_emulator.core.exceptions import FlagException


class Flags:
    def __init__(self):
        self.flags = {
            "Z": 0,  # Zero flag
            "S": 0,  # Sign flag
            "C": 0,  # Carry flag
            "O": 0,  # Overflow flag
            "P": 0,  # Parity flag
        }

    def get(self, flag_name: str) -> int:
        self._check_flag(flag_name)
        value = self.flags[flag_name]
        logger.debug(f"Read flag {flag_name} got 0x{value:08X}")
        return value

    def set(self, flag_name: str, value: int) -> None:
        self._check_flag(flag_name)
        self.flags[flag_name] = value
        logger.debug(f"Set flag {flag_name} to {value}")

    def basic_update(self, op_result: int) -> None:
        op_result = op_result & 0xFFFFFFFF
        self.flags["Z"] = 1 if op_result == 0 else 0
        # проверяем, что установлен старший бит
        self.flags["S"] = 1 if op_result & 0x80000000 else 0
        # вычисляем четность младших 8 бит
        self.flags["P"] = self._calculate_parity(op_result & 0xFF)
        logger.debug(
            f"Updated flags: Z={self.flags['Z']}, S={self.flags['S']}, P={self.flags['P']}"
        )

    def arithmetic_update(self, a: int, b: int, result: int, operation: str) -> None:
        a = a & 0xFFFFFFFF
        b = b & 0xFFFFFFFF
        result = result & 0xFFFFFFFF

        self.basic_update(result)

        if operation == "ADD":
            self._update_flags_for_add(a, b, result)
        elif operation == "SUB":
            self._update_flags_for_sub(a, b, result)
        elif operation == "CMP":
            self._update_flags_for_sub(a, b, a - b)

        logger.debug(
            f"Arithmetic flags updated: Z={self.flags['Z']}, S={self.flags['S']}, "
            f"C={self.flags['C']}, O={self.flags['O']}"
        )

    def logical_update(self, result: int) -> None:
        """Обновление флагов для логических операций (AND, OR, XOR, NOT)"""
        result = result & 0xFFFFFFFF
        self.basic_update(result)
        # Логические операции сбрасывают флаги переноса и переполнения
        self.flags["C"] = 0
        self.flags["O"] = 0
        logger.debug(
            f"Logical flags updated: Z={self.flags['Z']}, S={self.flags['S']}, "
            f"C={self.flags['C']}, O={self.flags['O']}, P={self.flags['P']}"
        )

    def shift_update(self, result: int, carry_out: int = 0) -> None:
        """Обновление флагов для операций сдвига"""
        result = result & 0xFFFFFFFF
        self.basic_update(result)
        self.flags["C"] = carry_out & 1
        # Для сдвигов флаг переполнения обычно не определен или равен 0
        self.flags["O"] = 0
        logger.debug(
            f"Shift flags updated: Z={self.flags['Z']}, S={self.flags['S']}, "
            f"C={self.flags['C']}, O={self.flags['O']}, P={self.flags['P']}"
        )

    def shift_left_update(self, original: int, count: int, result: int) -> None:
        """Обновление флагов для сдвига влево"""
        if count == 0:
            self.basic_update(result)
            return

        carry_out = (original >> (32 - count)) & 1 if count <= 32 else 0
        self.shift_update(result, carry_out)

    def shift_right_update(self, original: int, count: int, result: int) -> None:
        """Обновление флагов для логического сдвига вправо"""
        if count == 0:
            self.basic_update(result)
            return

        carry_out = (original >> (count - 1)) & 1 if count > 0 else 0
        self.shift_update(result, carry_out)

    def rotate_update(self, result: int, carry_out: int = 0) -> None:
        """Обновление флагов для операций поворота"""
        self.shift_update(result, carry_out)

    def multiplication_update(self, result: int, full_result: int) -> None:
        """Обновление флагов для операции умножения"""
        result = result & 0xFFFFFFFF
        self.basic_update(result)
        # Флаг переноса устанавливается, если результат не помещается в 32 бита
        self.flags["C"] = 1 if full_result > 0xFFFFFFFF else 0
        # Флаг переполнения для умножения обычно не определен
        self.flags["O"] = 0
        logger.debug(
            f"Multiplication flags updated: Z={self.flags['Z']}, S={self.flags['S']}, "
            f"C={self.flags['C']}, O={self.flags['O']}, P={self.flags['P']}"
        )

    def division_update(self, quotient: int) -> None:
        """Обновление флагов для операции деления"""
        quotient = quotient & 0xFFFFFFFF
        self.basic_update(quotient)
        # Деление не устанавливает флаги переноса и переполнения
        self.flags["C"] = 0
        self.flags["O"] = 0
        logger.debug(
            f"Division flags updated: Z={self.flags['Z']}, S={self.flags['S']}, "
            f"C={self.flags['C']}, O={self.flags['O']}, P={self.flags['P']}"
        )

    def reset(self) -> None:
        for flag in self.flags:
            self.flags[flag] = 0
        logger.debug(f"Reset flags: {self.flags}")

    def _check_flag(self, flag_name: str) -> None:
        if self.flags.get(flag_name) is None:
            raise FlagException(f"Unknown flag: {flag_name}")

    def _update_flags_for_add(self, a: int, b: int, result: int) -> None:
        # Carry flag (unsigned overflow)
        # Происходит, когда сумма больше 0xFFFFFFFF
        unsigned_sum = a + b
        self.flags["C"] = 1 if unsigned_sum > 0xFFFFFFFF else 0

        # Overflow flag (signed overflow)
        # Происходит, когда складываем два числа одного знака,
        # а результат другого знака
        a_signed = a if a < 0x80000000 else a - 0x100000000
        b_signed = b if b < 0x80000000 else b - 0x100000000
        result_signed = result if result < 0x80000000 else result - 0x100000000

        # Overflow: если оба операнда одного знака, а результат другого
        same_sign_operands = (a_signed >= 0) == (b_signed >= 0)
        different_sign_result = (a_signed >= 0) != (result_signed >= 0)

        self.flags["O"] = 1 if same_sign_operands and different_sign_result else 0

    def _update_flags_for_sub(self, a: int, b: int, result: int) -> None:
        self.flags["C"] = 1 if a < b else 0

        # Overflow flag для вычитания
        # Происходит, когда операнды разных знаков, а результат не соответствует
        a_signed = a if a < 0x80000000 else a - 0x100000000
        b_signed = b if b < 0x80000000 else b - 0x100000000
        result_signed = result if result < 0x80000000 else result - 0x100000000

        # Overflow: если операнды разных знаков, а результат не соответствует первому
        different_signs = (a_signed >= 0) != (b_signed >= 0)
        wrong_result = (a_signed >= 0) != (result_signed >= 0)

        self.flags["O"] = 1 if different_signs and wrong_result else 0

    def _calculate_parity(self, value: int) -> int:
        """Вычисляет четность (1 для четного количества единиц, 0 для нечетного)"""
        count = 0
        while value:
            count += value & 1
            value >>= 1
        return 1 if count % 2 == 0 else 0

    def __getitem__(self, flag_name: str) -> int:
        return self.get(flag_name)

    def __setitem__(self, flag_name: str, value: int) -> None:
        self.set(flag_name, value)
