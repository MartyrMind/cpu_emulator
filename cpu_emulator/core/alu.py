from loguru import logger

from cpu_emulator.core.flags import Flags
from cpu_emulator.core.registers import Registers


class ALU:
    def __init__(self, registers: Registers, flags: Flags):
        self.registers = registers
        self.flags = flags
        logger.debug(f"ALU initialized")

    def add(self, a: int, b: int) -> int:
        pass


