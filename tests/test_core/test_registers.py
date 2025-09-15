import allure
import pytest

from cpu_emulator.core.exceptions import RegisterException


@allure.parent_suite("Тесты эмулятора")
@allure.suite("Тесты ядра")
@allure.sub_suite("Тесты регистров")
class TestRegisters:
    test_data = [
        (0, 256, False, 256),
        (0x10, -2, False, 4294967294),
        (0xFF, 10, True, None),
    ]

    @pytest.mark.parametrize("test_data", test_data)
    @allure.title("Тест чтения-записи в регистры")
    def test_registers(self, registers_fabric, test_data):
        registers = registers_fabric()
        reg_num, value, has_error, expected = test_data
        if has_error:
            with pytest.raises(RegisterException):
                registers[reg_num] = value
                assert expected is None
        else:
            registers[reg_num] = value
            got_value = registers[reg_num]
            assert expected == got_value
