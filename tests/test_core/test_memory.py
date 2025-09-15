import allure
import pytest

from cpu_emulator.core.exceptions import BadAddressException


@allure.parent_suite("Тесты эмулятора")
@allure.suite("Тесты ядра")
@allure.sub_suite("Тесты памяти")
class TestMemory:
    test_data = [
        (0, 0, False, 0),
        (-1, 0, True, None),
        (0, 256, False, 0),
        (4, -1, False, 255),
        (3, -3, False, 253),
        (9, 1024, True, None),
    ]

    @pytest.mark.parametrize("test_data", test_data)
    @allure.title("Тест чтения-записи байта в память")
    def test_read_write_byte(self, memory_fabric, test_data):
        memory = memory_fabric(8)

        address, value, has_error, expected_value = test_data

        if has_error:
            with pytest.raises(BadAddressException):
                memory.write_byte(address, value)
                assert expected_value is None
        else:
            memory.write_byte(address, value)
            result = memory.read_byte(address)
            assert result == expected_value

    test_data = [
        ([0x4048F5C3, 0x0000002A], 0, False, [0x4048F5C3, 0x0000002A]),
        ([0x4048F5C3, 0x0000002A], 2, True, None),
        ([0x4048F5C3, 0x0000002A], 4, True, None),
    ]

    @pytest.mark.parametrize("test_data", test_data)
    @allure.title("Тест чтения-записи слов в память")
    def test_read_write_word(self, memory_fabric, test_data):
        words, start_address, has_error, expected = test_data
        memory = memory_fabric(8)
        address = start_address
        if has_error:
            with pytest.raises(BadAddressException):
                for word in words:
                    memory.write_word(address, word)
                    address += 4
                assert expected is None
        else:
            for word in words:
                memory.write_word(address, word)
                result = memory.read_word(address)
                assert result == word
                address += 4
