from loguru import logger

from cpu_emulator.core.exceptions import RegisterException


class Registers:
    def __init__(self, gpr_count: int = 8):
        self.gpr = [0] * gpr_count
        self.gpr_count = gpr_count

        self.pc = 0  # счетчик команд
        self.ir = 0  # хранение команды
        self.sp = 0  # указатель стека

        logger.debug(f"Initialized {gpr_count} GPR registers")

    def get(self, reg_num: int) -> int:
        return self._operate_register(reg_num, op="get")

    def set(self, reg_num: int, value: int) -> None:
        value = value & 0xFFFFFFFF
        self._operate_register(reg_num, value, "set")

    def reset(self) -> None:
        self.gpr = [0] * self.gpr_count
        self.pc = 0
        self.ir = 0
        self.sp = 0

    def _operate_register(
        self, reg_num: int, value: int | None = None, op: str | None = "get"
    ) -> int | None:
        # В RISC-V стиле SP доступен как обычный регистр
        # R0-R7: обычные регистры, R8: SP (stack pointer)
        if reg_num == 8:  # SP как R8 для RISC-V стиля
            if op == "get":
                value = self.sp
                logger.debug(f"Got 0x{value:08X} from SP (R8)")
                return value
            else:
                self.sp = value
                logger.debug(f"Set 0x{value:08X} to SP (R8)")
                return None

        special_reg_mapping = {0x10: "pc", 0x11: "ir", 0x12: "sp"}
        if 0 <= reg_num < self.gpr_count:
            if op == "get":
                value = self.gpr[reg_num]
                logger.debug(f"Got 0x{value:08X} from GPR{reg_num}")
                return value
            else:
                self.gpr[reg_num] = value
                logger.debug(f"Set 0x{value:08X} to GPR{reg_num}")
                return None
        if not special_reg_mapping.get(reg_num):
            raise RegisterException(f"Unknown register num 0x{reg_num:02X}")
        register_name = special_reg_mapping[reg_num]
        if op == "get":
            value = getattr(self, register_name)
            logger.debug(f"Got 0x{value:08X} from {register_name.upper()}")
            return value
        if op == "set":
            setattr(self, register_name, value)
            logger.debug(f"Set 0x{value:08X} to {register_name.upper()}")
            return None

    def __getitem__(self, reg_num: int) -> int:
        return self.get(reg_num)

    def __setitem__(self, reg_num: int, value: int) -> None:
        self.set(reg_num, value)

    def __len__(self) -> int:
        return self.gpr_count
