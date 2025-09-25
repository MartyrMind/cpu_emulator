import allure
import pytest

from cpu_emulator.core.exceptions import FlagException
from cpu_emulator.core.flags import Flags


@allure.parent_suite("Тесты эмулятора")
@allure.suite("Тесты ядра")
@allure.sub_suite("Тесты флагов процессора")
class TestFlags:
    @allure.title("Инициализация флагов")
    @allure.description("Проверяет правильность инициализации всех флагов процессора")
    def test_init(self):
        """Тест инициализации флагов"""
        flags = Flags()
        assert flags.flags["Z"] == 0
        assert flags.flags["S"] == 0
        assert flags.flags["C"] == 0
        assert flags.flags["O"] == 0
        assert flags.flags["P"] == 0

    @allure.title("Установка и чтение флагов")
    @allure.description(
        "Проверяет корректность операций установки и чтения значений флагов"
    )
    def test_get_set_flags(self):
        """Тест установки и чтения флагов"""
        flags = Flags()

        flags.set("Z", 1)
        assert flags.get("Z") == 1

        flags["S"] = 1  # Тест через __setitem__
        assert flags["S"] == 1  # Тест через __getitem__

    @allure.title("Обработка неизвестного флага")
    @allure.description(
        "Проверяет корректность обработки ошибок при работе с несуществующими флагами"
    )
    def test_invalid_flag(self):
        """Тест обработки неизвестного флага"""
        flags = Flags()

        with pytest.raises(FlagException):
            flags.get("X")

        with pytest.raises(FlagException):
            flags.set("Y", 1)

    @pytest.mark.parametrize(
        "value, expected_z, expected_s, expected_p, description",
        [
            (0x00000000, 1, 0, 1, "нулевой результат"),
            (0x80000000, 0, 1, 1, "отрицательный результат"),
            (0x12345678, 0, 0, 1, "положительный результат"),
            (0x7FFFFFFF, 0, 0, 1, "максимальное положительное"),
            (0xFFFFFFFF, 0, 1, 1, "все биты установлены"),
            (0x00000001, 0, 0, 0, "единица (нечетная четность)"),
            (0x00000003, 0, 0, 1, "три (четная четность)"),
        ],
        ids=[
            "zero",
            "negative",
            "positive",
            "max_positive",
            "all_bits",
            "odd_parity",
            "even_parity",
        ],
    )
    @allure.title("Базовое обновление флагов: {description}")
    @allure.description(
        "Проверяет правильность установки флагов Z, S, P при базовом обновлении"
    )
    def test_basic_update(self, value, expected_z, expected_s, expected_p, description):
        """Тест базового обновления флагов"""
        flags = Flags()
        flags.basic_update(value)

        assert flags["Z"] == expected_z, f"Zero flag failed for {description}"
        assert flags["S"] == expected_s, f"Sign flag failed for {description}"
        assert flags["P"] == expected_p, f"Parity flag failed for {description}"

    @pytest.mark.parametrize(
        "value, expected_parity, description",
        [
            (0xFF, 1, "8 единиц"),
            (0x0F, 1, "4 единицы"),
            (0x07, 0, "3 единицы"),
            (0x01, 0, "1 единица"),
            (0x00, 1, "0 единиц"),
            (0x03, 1, "2 единицы"),
            (0x15, 0, "3 единицы (0x15)"),
            (0x55, 1, "4 единицы (0x55)"),
        ],
        ids=[
            "8bits",
            "4bits",
            "3bits",
            "1bit",
            "0bits",
            "2bits",
            "3bits_alt",
            "4bits_alt",
        ],
    )
    @allure.title("Вычисление четности: {description}")
    @allure.description(
        "Проверяет правильность вычисления флага четности для различных значений"
    )
    def test_parity_calculation(self, value, expected_parity, description):
        """Тест вычисления четности"""
        flags = Flags()
        assert flags._calculate_parity(value) == expected_parity, (
            f"Failed for {description}"
        )

    @pytest.mark.parametrize(
        "a, b, operation, expected_z, expected_s, expected_c, expected_o, description",
        [
            # Тесты сложения
            (0x10000000, 0x20000000, "ADD", 0, 0, 0, 0, "ADD: без переполнения"),
            (0xFFFFFFFF, 0x00000001, "ADD", 1, 0, 1, 0, "ADD: с переносом"),
            (0x7FFFFFFF, 0x00000001, "ADD", 0, 1, 0, 1, "ADD: с переполнением"),
            (0x80000000, 0x80000000, "ADD", 1, 0, 1, 1, "ADD: отрицательных"),
            # Тесты вычитания
            (0x00000001, 0x00000002, "SUB", 0, 1, 1, 0, "SUB: с займом"),
            (0x20000000, 0x10000000, "SUB", 0, 0, 0, 0, "SUB: без займа"),
            (0x80000000, 0x00000001, "SUB", 0, 0, 0, 1, "SUB: с переполнением"),
            (0x12345678, 0x12345678, "SUB", 1, 0, 0, 0, "SUB: равных чисел"),
            # Тесты сравнения
            (0x100, 0x100, "CMP", 1, 0, 0, 0, "CMP: равные числа"),
            (0x50, 0x100, "CMP", 0, 1, 1, 0, "CMP: меньшее с большим"),
            (0x100, 0x50, "CMP", 0, 0, 0, 0, "CMP: большее с меньшим"),
        ],
        ids=[
            "add_normal",
            "add_carry",
            "add_overflow",
            "add_negative",
            "sub_borrow",
            "sub_normal",
            "sub_overflow",
            "sub_equal",
            "cmp_equal",
            "cmp_less",
            "cmp_greater",
        ],
    )
    @allure.title("Арифметическое обновление флагов: {description}")
    @allure.description(
        "Проверяет правильность обновления флагов при арифметических операциях и сравнении"
    )
    def test_arithmetic_update(
        self,
        a,
        b,
        operation,
        expected_z,
        expected_s,
        expected_c,
        expected_o,
        description,
    ):
        """Тест арифметического обновления флагов"""
        flags = Flags()
        if operation == "ADD":
            result = (a + b) & 0xFFFFFFFF
        elif operation in ["SUB", "CMP"]:
            result = (a - b) & 0xFFFFFFFF

        flags.arithmetic_update(a, b, result, operation)

        assert flags["Z"] == expected_z, f"Zero flag failed for {description}"
        assert flags["S"] == expected_s, f"Sign flag failed for {description}"
        assert flags["C"] == expected_c, f"Carry flag failed for {description}"
        assert flags["O"] == expected_o, f"Overflow flag failed for {description}"

    @allure.title("Логическое обновление флагов")
    @allure.description(
        "Проверяет правильность обновления флагов при логических операциях"
    )
    def test_logical_update(self):
        """Тест обновления флагов для логических операций"""
        flags = Flags()
        result = 0x12345678

        flags.logical_update(result)

        assert flags["Z"] == 0  # Результат не ноль
        assert flags["S"] == 0  # Результат положительный
        assert flags["C"] == 0  # Логические операции сбрасывают C
        assert flags["O"] == 0  # Логические операции сбрасывают O

    @allure.title("Обновление флагов при сдвиге")
    @allure.description("Проверяет правильность обновления флагов при операциях сдвига")
    def test_shift_update(self):
        """Тест обновления флагов для операций сдвига"""
        flags = Flags()
        result = 0x12345678
        carry_out = 1

        flags.shift_update(result, carry_out)

        assert flags["Z"] == 0  # Результат не ноль
        assert flags["S"] == 0  # Результат положительный
        assert flags["C"] == 1  # Перенос из сдвига
        assert flags["O"] == 0  # Сдвиги сбрасывают O

    @allure.title("Сброс всех флагов")
    @allure.description(
        "Проверяет правильность сброса всех флагов в исходное состояние"
    )
    def test_reset(self):
        """Тест сброса всех флагов"""
        flags = Flags()

        # Устанавливаем все флаги
        for flag in flags.flags:
            flags.set(flag, 1)

        # Сбрасываем
        flags.reset()

        # Проверяем, что все сброшены
        for flag in flags.flags:
            assert flags.get(flag) == 0

    @pytest.mark.parametrize(
        "result, full_result, expected_z, expected_c, description",
        [
            (0x12345678, 0x12345678, 0, 0, "умножение без переноса"),
            (0xFFFFFFFE, 0x1FFFFFFFF, 0, 1, "умножение с переносом"),
            (0x00000000, 0x00000000, 1, 0, "умножение с нулевым результатом"),
            (0x80000000, 0x80000000, 0, 0, "умножение с отрицательным результатом"),
            (0xFFFFFFFF, 0x1FFFFFFFE, 0, 1, "умножение с максимальным переносом"),
        ],
        ids=["no_carry", "carry", "zero", "negative", "max_carry"],
    )
    @allure.title("Обновление флагов при умножении: {description}")
    @allure.description(
        "Проверяет правильность обновления флагов при операции умножения"
    )
    def test_multiplication_update(
        self, result, full_result, expected_z, expected_c, description
    ):
        """Тест обновления флагов для умножения"""
        flags = Flags()
        flags.multiplication_update(result, full_result)

        assert flags["Z"] == expected_z, f"Zero flag failed for {description}"
        assert flags["C"] == expected_c, f"Carry flag failed for {description}"
        assert flags["O"] == 0, f"Overflow flag should be 0 for {description}"

    @pytest.mark.parametrize(
        "quotient, expected_z, description",
        [
            (0x12345678, 0, "деление с ненулевым результатом"),
            (0x00000000, 1, "деление с нулевым результатом"),
            (0x80000000, 0, "деление с отрицательным результатом"),
            (0xFFFFFFFF, 0, "деление с максимальным результатом"),
        ],
        ids=["nonzero", "zero", "negative", "max"],
    )
    @allure.title("Обновление флагов при делении: {description}")
    @allure.description("Проверяет правильность обновления флагов при операции деления")
    def test_division_update(self, quotient, expected_z, description):
        """Тест обновления флагов для деления"""
        flags = Flags()
        flags.division_update(quotient)

        assert flags["Z"] == expected_z, f"Zero flag failed for {description}"
        assert flags["C"] == 0, f"Carry flag should be 0 for {description}"
        assert flags["O"] == 0, f"Overflow flag should be 0 for {description}"

    @pytest.mark.parametrize(
        "original, count, result, expected_z, expected_c, description",
        [
            (0x12345678, 4, 0x23456780, 0, 1, "сдвиг влево с выносом старшего бита"),
            (0x12345678, 0, 0x12345678, 0, 0, "сдвиг влево на 0 позиций"),
            (0x80000000, 1, 0x00000000, 1, 1, "сдвиг влево отрицательного числа"),
            (0x00000001, 1, 0x00000002, 0, 0, "сдвиг влево единицы"),
            (0x40000000, 1, 0x80000000, 0, 0, "сдвиг влево без переноса"),
        ],
        ids=["with_carry", "zero_count", "negative", "one", "no_carry"],
    )
    @allure.title("Обновление флагов при сдвиге влево: {description}")
    @allure.description("Проверяет правильность обновления флагов при сдвиге влево")
    def test_shift_left_update(
        self, original, count, result, expected_z, expected_c, description
    ):
        """Тест обновления флагов для сдвига влево"""
        flags = Flags()
        flags.shift_left_update(original, count, result)

        assert flags["Z"] == expected_z, f"Zero flag failed for {description}"
        assert flags["C"] == expected_c, f"Carry flag failed for {description}"
        assert flags["O"] == 0, f"Overflow flag should be 0 for {description}"

    @pytest.mark.parametrize(
        "original, count, result, expected_z, expected_c, description",
        [
            (0x12345678, 4, 0x01234567, 0, 1, "сдвиг вправо с выносом младшего бита"),
            (0x12345678, 0, 0x12345678, 0, 0, "сдвиг вправо на 0 позиций"),
            (0x00000001, 1, 0x00000000, 1, 1, "сдвиг вправо единицы"),
            (0x00000002, 1, 0x00000001, 0, 0, "сдвиг вправо двойки"),
            (0xFFFFFFFF, 1, 0x7FFFFFFF, 0, 1, "сдвиг вправо максимального числа"),
        ],
        ids=["with_carry", "zero_count", "one_to_zero", "two", "max_number"],
    )
    @allure.title("Обновление флагов при сдвиге вправо: {description}")
    @allure.description("Проверяет правильность обновления флагов при сдвиге вправо")
    def test_shift_right_update(
        self, original, count, result, expected_z, expected_c, description
    ):
        """Тест обновления флагов для сдвига вправо"""
        flags = Flags()
        flags.shift_right_update(original, count, result)

        assert flags["Z"] == expected_z, f"Zero flag failed for {description}"
        assert flags["C"] == expected_c, f"Carry flag failed for {description}"
        assert flags["O"] == 0, f"Overflow flag should be 0 for {description}"

    @pytest.mark.parametrize(
        "result, carry_out, expected_z, expected_c, description",
        [
            (0x12345678, 1, 0, 1, "поворот с переносом"),
            (0x00000000, 0, 1, 0, "поворот с нулевым результатом"),
            (0x80000000, 1, 0, 1, "поворот отрицательного числа"),
            (0x7FFFFFFF, 0, 0, 0, "поворот максимального положительного"),
        ],
        ids=["with_carry", "zero", "negative", "max_positive"],
    )
    @allure.title("Обновление флагов при повороте: {description}")
    @allure.description(
        "Проверяет правильность обновления флагов при операциях поворота"
    )
    def test_rotate_update(
        self, result, carry_out, expected_z, expected_c, description
    ):
        """Тест обновления флагов для поворота"""
        flags = Flags()
        flags.rotate_update(result, carry_out)

        assert flags["Z"] == expected_z, f"Zero flag failed for {description}"
        assert flags["C"] == expected_c, f"Carry flag failed for {description}"
        assert flags["O"] == 0, f"Overflow flag should be 0 for {description}"
