from loguru import logger

from cpu_emulator.core.exceptions import BadAddressException


class Memory:
    def __init__(self, size: int = 256 * 1024):
        self.size = size
        self.memory = bytearray(size)
        logger.debug(f"Memory size is {self.size} bytes created")

    def read_byte(self, address: int) -> int:
        """
        Читает байт по адресу
        :param address: адрес байта
        :return: значение байта в int
        """
        self._check_address_range(address)
        byte = self.memory[address]
        logger.debug(f"Read byte from 0x{address:05X} got 0x{byte:02X}")
        return byte

    def write_byte(self, address: int, value: int) -> None:
        """
        Записывает байт по адресу
        :param address: адрес байта
        :param value: значение байта
        :return: None
        """
        self._check_address_range(address)
        # обрезаем value до младшего байта
        self.memory[address] = value & 0xFF
        logger.debug(f"Write byte 0x{self.memory[address]:02X} to 0x{address:05X}")

    def read_word(self, address: int) -> int:
        """
        Читает слово (4 байта) из памяти
        :param address: начальный выравненный адрес
        :return: прочитанное слово в little endian порядке
        """
        self._check_word_address(address)
        word_bytes = [self.read_byte(address + i) for i in range(4)]
        # собираем в little endian порядке
        word = (
            (word_bytes[3] << 24)
            | (word_bytes[2] << 16)
            | (word_bytes[1] << 8)
            | (word_bytes[0])
        )
        logger.debug(f"Read word from 0x{address:05X} got 0x{word:02X}")
        return word

    def write_word(self, address: int, value: int) -> None:
        """
        Записывает 4 байта слова последовательно в память
        :param address: начальный адрес
        :param value: слово
        :return: None
        """
        self._check_word_address(address)
        for i in range(4):
            self.write_byte(address + i, value >> (i * 8) & 0xFF)
        logger.debug(f"Write word 0x{value:08X} to 0x{address:05X}")

    def _check_address_range(self, address: int, end_address: int = 0) -> None:
        if not 0 <= address < self.size:
            raise BadAddressException(f"Invalid address: {address} out of range")
        if not 0 <= end_address < self.size:
            raise BadAddressException(
                f"Invalid end address: {end_address} out of range"
            )

    def _check_word_address(self, address: int) -> None:
        self._check_address_range(address, address + 3)
        if address % 4 != 0:
            raise BadAddressException(f"Unaligned address: {address}")

    def __getitem__(self, address: int) -> int:
        return self.read_word(address)

    def __setitem__(self, address: int, value: int) -> None:
        self.write_word(address, value)
