import allure
import pytest

from cpu_emulator.core.exceptions import FlagException


@allure.parent_suite("Тесты эмулятора")
@allure.suite("Тесты ядра")
@allure.sub_suite("Тесты флагов")
class TestFlags:

    test_data = [
        ('Z', 1, False, 1),
        ('ZZ', 1, True, None)
    ]
    @pytest.mark.parametrize("test_data", test_data)
    @allure.title('Тест чтения-записи флагов')
    def test_read_write_flags(self, flag_fabric, test_data):
        flags = flag_fabric()

        flag_name, value, has_error, expected = test_data

        if has_error:
            with pytest.raises(FlagException):
                flags[flag_name] = value
                assert expected is None
        else:
            flags[flag_name] = value
            got_result = flags[flag_name]
            assert got_result == expected

    test_data = [
        (42, {'Z': 0, 'S': 0, 'C': 0, 'O': 0}),
        (0, {'Z': 1, 'S': 0, 'C': 0, 'O': 0}),
        (-1, {'Z': 0, 'S': 1, 'C': 0, 'O': 0}),
    ]

    @pytest.mark.parametrize("test_data", test_data)
    @allure.title('Тест обновления флагов')
    def test_update_flag(self, flag_fabric, test_data):
        flags = flag_fabric()
        value, result = test_data


