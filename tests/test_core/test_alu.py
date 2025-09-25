import allure
import pytest

from cpu_emulator.core.alu import ALU
from cpu_emulator.core.flags import Flags
from cpu_emulator.core.registers import Registers


@allure.parent_suite("Тесты эмулятора")
@allure.suite("Тесты ядра")
@allure.sub_suite("Тесты арифметическо-логического устройства")
class TestALU:
    @pytest.fixture
    def alu_setup(self):
        """Фикстура для создания ALU с регистрами и флагами"""
        registers = Registers()
        flags = Flags()
        alu = ALU(registers, flags)
        return alu, registers, flags

    @allure.title("Инициализация ALU")
    @allure.description(
        "Проверяет правильность инициализации арифметическо-логического устройства"
    )
    def test_alu_init(self, alu_setup):
        """Тест инициализации ALU"""
        alu, registers, flags = alu_setup
        assert alu.registers is registers
        assert alu.flags is flags

    # Тесты арифметических операций
    @pytest.mark.parametrize(
        "a, b, expected_result, expected_z, expected_s, expected_c, expected_o, description",
        [
            (10, 20, 30, 0, 0, 0, 0, "простое сложение"),
            (0xFFFFFFFF, 0x00000001, 0, 1, 0, 1, 0, "с переносом"),
            (0x7FFFFFFF, 0x00000001, 0x80000000, 0, 1, 0, 1, "с переполнением"),
            (0, 0, 0, 1, 0, 0, 0, "нулей"),
            (0x12345678, 0x87654321, 0x99999999, 0, 1, 0, 0, "больших чисел"),
            (0x80000000, 0x80000000, 0, 1, 0, 1, 1, "отрицательных"),
        ],
        ids=["simple", "carry", "overflow", "zeros", "large", "negative"],
    )
    @allure.title("Сложение: {description}")
    @allure.description(
        "Проверяет правильность выполнения операции сложения и обновления флагов"
    )
    def test_add(
        self,
        alu_setup,
        a,
        b,
        expected_result,
        expected_z,
        expected_s,
        expected_c,
        expected_o,
        description,
    ):
        """Тест операции сложения"""
        alu, registers, flags = alu_setup

        result = alu.add(a, b)
        assert result == expected_result, f"Result failed for {description}"

        # Проверяем флаги
        assert flags["Z"] == expected_z, f"Zero flag failed for {description}"
        assert flags["S"] == expected_s, f"Sign flag failed for {description}"
        assert flags["C"] == expected_c, f"Carry flag failed for {description}"
        assert flags["O"] == expected_o, f"Overflow flag failed for {description}"

    @pytest.mark.parametrize(
        "a, b, expected_result, expected_z, expected_s, expected_c, description",
        [
            (30, 10, 20, 0, 0, 0, "простое"),
            (10, 20, 0xFFFFFFF6, 0, 1, 1, "с займом"),
            (0x12345678, 0x12345678, 0, 1, 0, 0, "равных чисел"),
            (0x80000000, 0x00000001, 0x7FFFFFFF, 0, 0, 0, "с переполнением"),
            (0, 1, 0xFFFFFFFF, 0, 1, 1, "из нуля"),
            (0xFFFFFFFF, 0x7FFFFFFF, 0x80000000, 0, 1, 0, "больших чисел"),
        ],
        ids=["simple", "borrow", "equal", "overflow", "from_zero", "large"],
    )
    @allure.title("Вычитание: {description}")
    @allure.description(
        "Проверяет правильность выполнения операции вычитания и обновления флагов"
    )
    def test_sub(
        self,
        alu_setup,
        a,
        b,
        expected_result,
        expected_z,
        expected_s,
        expected_c,
        description,
    ):
        """Тест операции вычитания"""
        alu, registers, flags = alu_setup

        result = alu.sub(a, b)
        assert result == expected_result, f"Result failed for {description}"

        # Проверяем флаги
        assert flags["Z"] == expected_z, f"Zero flag failed for {description}"
        assert flags["S"] == expected_s, f"Sign flag failed for {description}"
        assert flags["C"] == expected_c, f"Carry flag failed for {description}"

    @allure.title("Простое умножение")
    @allure.description(
        "Проверяет правильность выполнения операции умножения без переполнения"
    )
    def test_mul_simple(self, alu_setup):
        """Тест простого умножения"""
        alu, registers, flags = alu_setup

        result = alu.mul(10, 20)
        assert result == 200

        # Проверяем флаги
        assert flags["Z"] == 0  # Результат не ноль
        assert flags["C"] == 0  # Нет переноса

    @allure.title("Умножение с переполнением")
    @allure.description(
        "Проверяет правильность выполнения операции умножения с переполнением"
    )
    def test_mul_with_overflow(self, alu_setup):
        """Тест умножения с переполнением"""
        alu, registers, flags = alu_setup

        result = alu.mul(0xFFFFFFFF, 0x00000002)
        assert result == 0xFFFFFFFE  # Младшие 32 бита

        # Проверяем флаги
        assert flags["C"] == 1  # Есть перенос (результат не помещается в 32 бита)

    @allure.title("Простое деление")
    @allure.description("Проверяет правильность выполнения операции деления")
    def test_div_simple(self, alu_setup):
        """Тест простого деления"""
        alu, registers, flags = alu_setup

        quotient, remainder = alu.div(100, 7)
        assert quotient == 14
        assert remainder == 2

        # Проверяем флаги по частному
        assert flags["Z"] == 0  # Частное не ноль

    @allure.title("Деление на ноль")
    @allure.description("Проверяет правильность обработки ошибки деления на ноль")
    def test_div_by_zero(self, alu_setup):
        """Тест деления на ноль"""
        alu, registers, flags = alu_setup

        with pytest.raises(ZeroDivisionError):
            alu.div(100, 0)

    @pytest.mark.parametrize(
        "a, b, expected_z, expected_s, expected_c, description",
        [
            (100, 100, 1, 0, 0, "равные числа"),
            (50, 100, 0, 1, 1, "a < b"),
            (100, 50, 0, 0, 0, "a > b"),
            (0, 0, 1, 0, 0, "нули"),
            (0x7FFFFFFF, 0x80000000, 0, 1, 1, "pos vs neg"),
            (0x80000000, 0x7FFFFFFF, 0, 0, 0, "neg vs pos"),
        ],
        ids=["equal", "less", "greater", "zeros", "pos_vs_neg", "neg_vs_pos"],
    )
    @allure.title("Сравнение: {description}")
    @allure.description(
        "Проверяет правильность выполнения операции сравнения и установки флагов"
    )
    def test_compare(
        self, alu_setup, a, b, expected_z, expected_s, expected_c, description
    ):
        """Тест операции сравнения"""
        alu, registers, flags = alu_setup

        alu.compare(a, b)

        # Проверяем флаги
        assert flags["Z"] == expected_z, f"Zero flag failed for {description}"
        assert flags["S"] == expected_s, f"Sign flag failed for {description}"
        assert flags["C"] == expected_c, f"Carry flag failed for {description}"

    # Тесты логических операций
    @pytest.mark.parametrize(
        "a, b, expected_result, expected_z, expected_s, description",
        [
            (0xFF00FF00, 0x00FF00FF, 0x00000000, 1, 0, "AND с нулевым результатом"),
            (
                0xFFFFFFFF,
                0x12345678,
                0x12345678,
                0,
                0,
                "AND с сохранением второго операнда",
            ),
            (0x00000000, 0x12345678, 0x00000000, 1, 0, "AND с нулем"),
            (0xAAAAAAAA, 0x55555555, 0x00000000, 1, 0, "AND противоположных битов"),
            (0xF0F0F0F0, 0x0F0F0F0F, 0x00000000, 1, 0, "AND чередующихся битов"),
        ],
        ids=[
            "zero_result",
            "preserve_second",
            "with_zero",
            "opposite_bits",
            "alternating",
        ],
    )
    @allure.title("Логическое И: {description}")
    @allure.description("Проверяет правильность выполнения операции логического И")
    def test_logical_and(
        self, alu_setup, a, b, expected_result, expected_z, expected_s, description
    ):
        """Тест логического И"""
        alu, registers, flags = alu_setup

        result = alu.logical_and(a, b)
        assert result == expected_result, f"Result failed for {description}"

        # Проверяем флаги (логические операции всегда сбрасывают C и O)
        assert flags["Z"] == expected_z, f"Zero flag failed for {description}"
        assert flags["S"] == expected_s, f"Sign flag failed for {description}"
        assert flags["C"] == 0, f"Carry flag should be 0 for {description}"
        assert flags["O"] == 0, f"Overflow flag should be 0 for {description}"

    @pytest.mark.parametrize(
        "a, b, expected_result, expected_z, expected_s, description",
        [
            (0xFF00FF00, 0x00FF00FF, 0xFFFFFFFF, 0, 1, "OR с полным результатом"),
            (0x00000000, 0x12345678, 0x12345678, 0, 0, "OR с нулем"),
            (0x12345678, 0x00000000, 0x12345678, 0, 0, "OR второго с нулем"),
            (0xAAAAAAAA, 0x55555555, 0xFFFFFFFF, 0, 1, "OR дополняющих битов"),
        ],
        ids=["full_result", "first_zero", "second_zero", "complementary"],
    )
    @allure.title("Логическое ИЛИ: {description}")
    @allure.description("Проверяет правильность выполнения операции логического ИЛИ")
    def test_logical_or(
        self, alu_setup, a, b, expected_result, expected_z, expected_s, description
    ):
        """Тест логического ИЛИ"""
        alu, registers, flags = alu_setup

        result = alu.logical_or(a, b)
        assert result == expected_result, f"Result failed for {description}"

        assert flags["Z"] == expected_z, f"Zero flag failed for {description}"
        assert flags["S"] == expected_s, f"Sign flag failed for {description}"
        assert flags["C"] == 0, f"Carry flag should be 0 for {description}"
        assert flags["O"] == 0, f"Overflow flag should be 0 for {description}"

    @pytest.mark.parametrize(
        "a, b, expected_result, expected_z, expected_s, description",
        [
            (0xFF00FF00, 0xFF00FF00, 0x00000000, 1, 0, "XOR одинаковых чисел"),
            (0xFF00FF00, 0x00FF00FF, 0xFFFFFFFF, 0, 1, "XOR противоположных битов"),
            (0x12345678, 0x00000000, 0x12345678, 0, 0, "XOR с нулем"),
            (0xAAAAAAAA, 0x55555555, 0xFFFFFFFF, 0, 1, "XOR дополняющих битов"),
        ],
        ids=["same_numbers", "opposite_bits", "with_zero", "complementary"],
    )
    @allure.title("Логическое исключающее ИЛИ: {description}")
    @allure.description(
        "Проверяет правильность выполнения операции логического исключающего ИЛИ"
    )
    def test_logical_xor(
        self, alu_setup, a, b, expected_result, expected_z, expected_s, description
    ):
        """Тест логического исключающего ИЛИ"""
        alu, registers, flags = alu_setup

        result = alu.logical_xor(a, b)
        assert result == expected_result, f"Result failed for {description}"

        assert flags["Z"] == expected_z, f"Zero flag failed for {description}"
        assert flags["S"] == expected_s, f"Sign flag failed for {description}"
        assert flags["C"] == 0, f"Carry flag should be 0 for {description}"
        assert flags["O"] == 0, f"Overflow flag should be 0 for {description}"

    @pytest.mark.parametrize(
        "a, expected_result, expected_z, expected_s, description",
        [
            (0xFF00FF00, 0x00FF00FF, 0, 0, "NOT чередующихся битов"),
            (0x00000000, 0xFFFFFFFF, 0, 1, "NOT нуля"),
            (0xFFFFFFFF, 0x00000000, 1, 0, "NOT всех единиц"),
            (0x12345678, 0xEDCBA987, 0, 1, "NOT произвольного числа"),
        ],
        ids=["alternating", "zero", "all_ones", "arbitrary"],
    )
    @allure.title("Логическое НЕ: {description}")
    @allure.description(
        "Проверяет правильность выполнения операции логического НЕ (инверсии)"
    )
    def test_logical_not(
        self, alu_setup, a, expected_result, expected_z, expected_s, description
    ):
        """Тест логического НЕ"""
        alu, registers, flags = alu_setup

        result = alu.logical_not(a)
        assert result == expected_result, f"Result failed for {description}"

        assert flags["Z"] == expected_z, f"Zero flag failed for {description}"
        assert flags["S"] == expected_s, f"Sign flag failed for {description}"
        assert flags["C"] == 0, f"Carry flag should be 0 for {description}"
        assert flags["O"] == 0, f"Overflow flag should be 0 for {description}"

    # Тесты операций сдвига
    @allure.title("Логический сдвиг влево")
    @allure.description("Проверяет правильность выполнения логического сдвига влево")
    def test_shift_left(self, alu_setup):
        """Тест логического сдвига влево"""
        alu, registers, flags = alu_setup

        result = alu.shift_left(0x12345678, 4)
        assert result == 0x23456780

        # Проверяем флаги
        assert flags["Z"] == 0  # Результат не ноль
        assert flags["C"] == 1  # Старший бит исходного числа (0x1...)

    @allure.title("Сдвиг влево на 0 позиций")
    @allure.description("Проверяет корректность обработки сдвига на 0 позиций")
    def test_shift_left_zero_count(self, alu_setup):
        """Тест сдвига влево на 0 позиций"""
        alu, registers, flags = alu_setup

        result = alu.shift_left(0x12345678, 0)
        assert result == 0x12345678  # Без изменений

    @allure.title("Логический сдвиг вправо")
    @allure.description("Проверяет правильность выполнения логического сдвига вправо")
    def test_shift_right(self, alu_setup):
        """Тест логического сдвига вправо"""
        alu, registers, flags = alu_setup

        result = alu.shift_right(0x12345678, 4)
        assert result == 0x01234567

        # Проверяем флаги
        assert flags["Z"] == 0  # Результат не ноль
        assert flags["C"] == 1  # Младшие биты исходного числа (...8)

    @allure.title("Арифметический сдвиг вправо (положительное число)")
    @allure.description(
        "Проверяет арифметический сдвиг вправо для положительного числа"
    )
    def test_arithmetic_shift_right_positive(self, alu_setup):
        """Тест арифметического сдвига вправо для положительного числа"""
        alu, registers, flags = alu_setup

        result = alu.arithmetic_shift_right(0x12345678, 4)
        assert result == 0x01234567  # Как логический сдвиг для положительных

    @allure.title("Арифметический сдвиг вправо (отрицательное число)")
    @allure.description(
        "Проверяет арифметический сдвиг вправо для отрицательного числа с сохранением знака"
    )
    def test_arithmetic_shift_right_negative(self, alu_setup):
        """Тест арифметического сдвига вправо для отрицательного числа"""
        alu, registers, flags = alu_setup

        result = alu.arithmetic_shift_right(0x80000000, 1)
        # Арифметический сдвиг сохраняет знак
        assert result == 0xC0000000

    @allure.title("Поворот влево")
    @allure.description("Проверяет правильность выполнения поворота влево")
    def test_rotate_left(self, alu_setup):
        """Тест поворота влево"""
        alu, registers, flags = alu_setup

        result = alu.rotate_left(0x12345678, 4)
        assert result == 0x23456781  # Старшие биты перешли в младшие

    @allure.title("Поворот вправо")
    @allure.description("Проверяет правильность выполнения поворота вправо")
    def test_rotate_right(self, alu_setup):
        """Тест поворота вправо"""
        alu, registers, flags = alu_setup

        result = alu.rotate_right(0x12345678, 4)
        assert result == 0x81234567  # Младшие биты перешли в старшие

    @allure.title("Поворот на 0 позиций")
    @allure.description("Проверяет корректность обработки поворота на 0 позиций")
    def test_rotate_zero_count(self, alu_setup):
        """Тест поворота на 0 позиций"""
        alu, registers, flags = alu_setup

        result = alu.rotate_left(0x12345678, 0)
        assert result == 0x12345678  # Без изменений

    # Тесты граничных случаев
    @allure.title("Операции с большими числами")
    @allure.description("Проверяет корректность обработки чисел больше 32 бит")
    def test_operations_with_large_numbers(self, alu_setup):
        """Тест операций с большими числами"""
        alu, registers, flags = alu_setup

        # Проверяем, что числа правильно обрезаются до 32 бит
        result = alu.add(0x1FFFFFFFF, 0x200000000)  # Больше 32 бит
        expected = (
            (0x1FFFFFFFF & 0xFFFFFFFF) + (0x200000000 & 0xFFFFFFFF)
        ) & 0xFFFFFFFF
        assert result == expected

    @allure.title("Сдвиг на большое количество позиций")
    @allure.description("Проверяет ограничение количества позиций сдвига до 31 бита")
    def test_shift_large_count(self, alu_setup):
        """Тест сдвига на большое количество позиций"""
        alu, registers, flags = alu_setup

        # Сдвиг ограничивается 31 битом
        result = alu.shift_left(
            0x12345678, 100
        )  # Эквивалентно сдвигу на 4 (100 & 0x1F)
        expected = alu.shift_left(0x12345678, 4)
        assert result == expected
