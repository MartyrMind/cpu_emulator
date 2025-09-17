from loguru import logger

from cpu_emulator.core.exceptions import FlagException


class Flags:
    def __init__(self):
        self.flags = {
            'Z': 0,  # Zero flag
            'S': 0,  # Sign flag
            'C': 0,  # Carry flag
            'O': 0  # Overflow flag
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

    def update(self, op_result: int) -> None:
        op_result = op_result & 0xFFFFFFFF
        self.flags['Z'] = 1 if op_result == 0 else 0
        # проверяем, что установлен старший бит
        self.flags['S'] = 1 if op_result & 0x80000000 else 0
        logger.debug(f"Updated flags: Z={self.flags['Z']}, S={self.flags['S']}")

    def reset(self) -> None:
        for flag in self.flags:
            self.flags[flag] = 0
        logger.debug(f"Reset flags: {self.flags}")

    def _check_flag(self, flag_name: str) -> None:
        if self.flags.get(flag_name) is None:
            raise FlagException(f"Unknown flag: {flag_name}")

    def __getitem__(self, flag_name: str) -> int:
        return self.get(flag_name)

    def __setitem__(self, flag_name: str, value: int) -> None:
        self.set(flag_name, value)
