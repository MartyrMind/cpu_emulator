"""
Центральный процессор (CPU) для эмулятора
Фон-неймановская архитектура с двухадресными командами
"""


from loguru import logger

from cpu_emulator.core.alu import ALU
from cpu_emulator.core.decoder import InstructionDecoder
from cpu_emulator.core.exceptions import BadAddressException
from cpu_emulator.core.flags import Flags
from cpu_emulator.core.instruction_set import Instruction, OpCode
from cpu_emulator.core.memory import Memory
from cpu_emulator.core.registers import Registers


class CPUException(Exception):
    """Базовое исключение для CPU"""

    pass


class InvalidInstructionException(CPUException):
    """Исключение для некорректных команд"""

    pass


class CPU:
    """
    Центральный процессор эмулятора

    Архитектура:
    - Фон-неймановская (команды и данные в одной памяти)
    - Двухадресные команды
    - 8 регистров общего назначения (R0-R7)
    - 32-битная разрядность
    """

    def __init__(self, memory_size: int = 256 * 1024, stack_size: int = 1024):
        """
        Инициализация CPU

        Args:
            memory_size: Размер памяти в байтах (по умолчанию 256KB)
            stack_size: Размер стека в байтах (по умолчанию 1KB)
        """
        # Инициализация компонентов
        self.memory = Memory(memory_size)
        self.registers = Registers(gpr_count=8)
        self.flags = Flags()
        self.alu = ALU(self.registers, self.flags)
        self.decoder = InstructionDecoder()

        # Состояние CPU
        self.running = False
        self.halted = False
        self.cycle_count = 0

        # Настройка стека
        self.stack_base = memory_size - stack_size  # Стек растет вниз от конца памяти
        self.registers.sp = self.stack_base

        logger.info(
            f"CPU initialized: memory={memory_size}B, stack_base=0x{self.stack_base:05X}"
        )

    def reset(self) -> None:
        """Сброс CPU в начальное состояние"""
        self.registers.reset()
        self.flags.reset()
        self.running = False
        self.halted = False
        self.cycle_count = 0
        self.registers.sp = self.stack_base

        logger.info("CPU reset completed")

    def load_program(self, program: bytes, start_address: int = 0) -> None:
        """
        Загрузка программы в память

        Args:
            program: Машинный код программы
            start_address: Адрес загрузки (по умолчанию 0)
        """
        if start_address + len(program) > self.memory.size:
            raise CPUException(
                f"Program too large: {len(program)} bytes, "
                f"available: {self.memory.size - start_address} bytes"
            )

        # Загружаем программу в память
        for i, byte in enumerate(program):
            self.memory.write_byte(start_address + i, byte)

        # Устанавливаем PC на начало программы
        self.registers.pc = start_address

        logger.info(f"Program loaded: {len(program)} bytes at 0x{start_address:05X}")

    def run(self, max_cycles: int | None = None) -> None:
        """
        Запуск выполнения программы

        Args:
            max_cycles: Максимальное количество циклов (None = без ограничений)
        """
        self.running = True
        self.halted = False
        cycles_executed = 0

        logger.info("CPU execution started")

        try:
            while self.running and not self.halted:
                if max_cycles and cycles_executed >= max_cycles:
                    logger.warning(
                        f"Execution stopped: max cycles ({max_cycles}) reached"
                    )
                    break

                self.step()
                cycles_executed += 1

        except Exception as e:
            logger.error(f"CPU execution error: {e}")
            self.running = False
            raise

        logger.info(f"CPU execution finished: {cycles_executed} cycles")

    def step(self) -> None:
        """Выполнить один цикл команды (Fetch-Decode-Execute)"""
        if self.halted:
            return

        try:
            # FETCH: Загрузка команды из памяти
            instruction_word = self.fetch_instruction()

            # DECODE: Декодирование команды
            instruction = self.decoder.decode(instruction_word)

            # EXECUTE: Выполнение команды
            self.execute_instruction(instruction)

            self.cycle_count += 1

        except Exception as e:
            logger.error(f"Error in CPU cycle {self.cycle_count}: {e}")
            self.running = False
            raise

    def fetch_instruction(self) -> int:
        """
        Загрузка команды из памяти по адресу PC

        Returns:
            int: 32-битная команда
        """
        try:
            pc = self.registers.pc
            instruction = self.memory.read_word(pc)

            # Увеличиваем PC на 4 байта (размер команды)
            self.registers.pc = (pc + 4) & 0xFFFFFFFF

            logger.debug(f"Fetched instruction 0x{instruction:08X} from PC=0x{pc:05X}")
            return instruction

        except BadAddressException as e:
            raise InvalidInstructionException(f"Invalid PC address: {e}")

    def execute_instruction(self, instruction: Instruction) -> None:
        """
        Выполнение декодированной команды

        Args:
            instruction: Декодированная команда
        """
        opcode = instruction.opcode
        logger.debug(f"Executing: {instruction}")

        try:
            # Системные команды
            if opcode == OpCode.NOP:
                pass  # Ничего не делаем

            elif opcode == OpCode.HALT:
                self.halted = True
                self.running = False
                logger.info("CPU halted by HALT instruction")

            # Команды перемещения данных
            elif opcode == OpCode.MOV_REG:
                self._execute_mov_reg(instruction)
            elif opcode == OpCode.MOV_IMM:
                self._execute_mov_imm(instruction)
            elif opcode == OpCode.LOAD:
                self._execute_load(instruction)
            elif opcode == OpCode.STORE:
                self._execute_store(instruction)

            # Арифметические команды
            elif opcode == OpCode.ADD_REG:
                self._execute_add_reg(instruction)
            elif opcode == OpCode.ADD_IMM:
                self._execute_add_imm(instruction)
            elif opcode == OpCode.SUB_REG:
                self._execute_sub_reg(instruction)
            elif opcode == OpCode.SUB_IMM:
                self._execute_sub_imm(instruction)
            elif opcode == OpCode.MUL_REG:
                self._execute_mul_reg(instruction)
            elif opcode == OpCode.MUL_IMM:
                self._execute_mul_imm(instruction)
            elif opcode == OpCode.DIV_REG:
                self._execute_div_reg(instruction)
            elif opcode == OpCode.DIV_IMM:
                self._execute_div_imm(instruction)

            # Логические команды
            elif opcode == OpCode.AND_REG:
                self._execute_and_reg(instruction)
            elif opcode == OpCode.AND_IMM:
                self._execute_and_imm(instruction)
            elif opcode == OpCode.OR_REG:
                self._execute_or_reg(instruction)
            elif opcode == OpCode.OR_IMM:
                self._execute_or_imm(instruction)
            elif opcode == OpCode.XOR_REG:
                self._execute_xor_reg(instruction)
            elif opcode == OpCode.XOR_IMM:
                self._execute_xor_imm(instruction)
            elif opcode == OpCode.NOT:
                self._execute_not(instruction)

            # Команды сдвига
            elif opcode == OpCode.SHL_REG:
                self._execute_shl_reg(instruction)
            elif opcode == OpCode.SHL_IMM:
                self._execute_shl_imm(instruction)
            elif opcode == OpCode.SHR_REG:
                self._execute_shr_reg(instruction)
            elif opcode == OpCode.SHR_IMM:
                self._execute_shr_imm(instruction)
            elif opcode == OpCode.SAR_REG:
                self._execute_sar_reg(instruction)
            elif opcode == OpCode.SAR_IMM:
                self._execute_sar_imm(instruction)

            # Команды сравнения
            elif opcode == OpCode.CMP_REG:
                self._execute_cmp_reg(instruction)
            elif opcode == OpCode.CMP_IMM:
                self._execute_cmp_imm(instruction)

            # Команды переходов
            elif opcode == OpCode.JMP:
                self._execute_jmp(instruction)
            elif opcode == OpCode.JZ:
                self._execute_jz(instruction)
            elif opcode == OpCode.JNZ:
                self._execute_jnz(instruction)
            elif opcode == OpCode.JC:
                self._execute_jc(instruction)
            elif opcode == OpCode.JNC:
                self._execute_jnc(instruction)
            elif opcode == OpCode.JS:
                self._execute_js(instruction)
            elif opcode == OpCode.JNS:
                self._execute_jns(instruction)

            # В RISC-V стиле нет отдельных PUSH/POP команд
            # Стековые операции выполняются через базовые инструкции:
            # PUSH R1 ≡ SUB R8, R8, #4; STORE [R8], R1
            # POP R1  ≡ LOAD R1, [R8]; ADD R8, R8, #4
            # где R8 - это указатель стека (SP)

            else:
                raise InvalidInstructionException(
                    f"Unimplemented instruction: {opcode}"
                )

        except Exception as e:
            logger.error(f"Error executing {instruction}: {e}")
            raise

    # Реализация команд перемещения данных
    def _execute_mov_reg(self, instruction: Instruction) -> None:
        """MOV R1, R2 - R1 = R2"""
        source_value = self.registers[instruction.source_reg]
        self.registers[instruction.dest_reg] = source_value

    def _execute_mov_imm(self, instruction: Instruction) -> None:
        """MOV R1, #imm - R1 = imm"""
        self.registers[instruction.dest_reg] = instruction.immediate

    def _execute_load(self, instruction: Instruction) -> None:
        """LOAD R1, [R2] - R1 = Memory[R2]"""
        address = self.registers[instruction.source_reg]
        value = self.memory.read_word(address)
        self.registers[instruction.dest_reg] = value

    def _execute_store(self, instruction: Instruction) -> None:
        """STORE [R1], R2 - Memory[R1] = R2"""
        address = self.registers[instruction.dest_reg]
        value = self.registers[instruction.source_reg]
        self.memory.write_word(address, value)

    # Реализация арифметических команд (двухадресные)
    def _execute_add_reg(self, instruction: Instruction) -> None:
        """ADD R1, R2 - R1 = R1 + R2"""
        dest_value = self.registers[instruction.dest_reg]
        source_value = self.registers[instruction.source_reg]
        result = self.alu.add(dest_value, source_value)
        self.registers[instruction.dest_reg] = result

    def _execute_add_imm(self, instruction: Instruction) -> None:
        """ADD R1, #imm - R1 = R1 + imm"""
        dest_value = self.registers[instruction.dest_reg]
        result = self.alu.add(dest_value, instruction.immediate)
        self.registers[instruction.dest_reg] = result

    def _execute_sub_reg(self, instruction: Instruction) -> None:
        """SUB R1, R2 - R1 = R1 - R2"""
        dest_value = self.registers[instruction.dest_reg]
        source_value = self.registers[instruction.source_reg]
        result = self.alu.sub(dest_value, source_value)
        self.registers[instruction.dest_reg] = result

    def _execute_sub_imm(self, instruction: Instruction) -> None:
        """SUB R1, #imm - R1 = R1 - imm"""
        dest_value = self.registers[instruction.dest_reg]
        result = self.alu.sub(dest_value, instruction.immediate)
        self.registers[instruction.dest_reg] = result

    def _execute_mul_reg(self, instruction: Instruction) -> None:
        """MUL R1, R2 - R1 = R1 * R2"""
        dest_value = self.registers[instruction.dest_reg]
        source_value = self.registers[instruction.source_reg]
        result = self.alu.mul(dest_value, source_value)
        self.registers[instruction.dest_reg] = result

    def _execute_mul_imm(self, instruction: Instruction) -> None:
        """MUL R1, #imm - R1 = R1 * imm"""
        dest_value = self.registers[instruction.dest_reg]
        result = self.alu.mul(dest_value, instruction.immediate)
        self.registers[instruction.dest_reg] = result

    def _execute_div_reg(self, instruction: Instruction) -> None:
        """DIV R1, R2 - R1 = R1 / R2"""
        dest_value = self.registers[instruction.dest_reg]
        source_value = self.registers[instruction.source_reg]
        quotient, remainder = self.alu.div(dest_value, source_value)
        self.registers[instruction.dest_reg] = quotient
        # Остаток можно сохранить в специальный регистр, пока просто игнорируем

    def _execute_div_imm(self, instruction: Instruction) -> None:
        """DIV R1, #imm - R1 = R1 / imm"""
        dest_value = self.registers[instruction.dest_reg]
        quotient, remainder = self.alu.div(dest_value, instruction.immediate)
        self.registers[instruction.dest_reg] = quotient

    # Реализация логических команд
    def _execute_and_reg(self, instruction: Instruction) -> None:
        """AND R1, R2 - R1 = R1 & R2"""
        dest_value = self.registers[instruction.dest_reg]
        source_value = self.registers[instruction.source_reg]
        result = self.alu.logical_and(dest_value, source_value)
        self.registers[instruction.dest_reg] = result

    def _execute_and_imm(self, instruction: Instruction) -> None:
        """AND R1, #imm - R1 = R1 & imm"""
        dest_value = self.registers[instruction.dest_reg]
        result = self.alu.logical_and(dest_value, instruction.immediate)
        self.registers[instruction.dest_reg] = result

    def _execute_or_reg(self, instruction: Instruction) -> None:
        """OR R1, R2 - R1 = R1 | R2"""
        dest_value = self.registers[instruction.dest_reg]
        source_value = self.registers[instruction.source_reg]
        result = self.alu.logical_or(dest_value, source_value)
        self.registers[instruction.dest_reg] = result

    def _execute_or_imm(self, instruction: Instruction) -> None:
        """OR R1, #imm - R1 = R1 | imm"""
        dest_value = self.registers[instruction.dest_reg]
        result = self.alu.logical_or(dest_value, instruction.immediate)
        self.registers[instruction.dest_reg] = result

    def _execute_xor_reg(self, instruction: Instruction) -> None:
        """XOR R1, R2 - R1 = R1 ^ R2"""
        dest_value = self.registers[instruction.dest_reg]
        source_value = self.registers[instruction.source_reg]
        result = self.alu.logical_xor(dest_value, source_value)
        self.registers[instruction.dest_reg] = result

    def _execute_xor_imm(self, instruction: Instruction) -> None:
        """XOR R1, #imm - R1 = R1 ^ imm"""
        dest_value = self.registers[instruction.dest_reg]
        result = self.alu.logical_xor(dest_value, instruction.immediate)
        self.registers[instruction.dest_reg] = result

    def _execute_not(self, instruction: Instruction) -> None:
        """NOT R1 - R1 = ~R1"""
        dest_value = self.registers[instruction.dest_reg]
        result = self.alu.logical_not(dest_value)
        self.registers[instruction.dest_reg] = result

    # Реализация команд сдвига
    def _execute_shl_reg(self, instruction: Instruction) -> None:
        """SHL R1, R2 - R1 = R1 << R2"""
        dest_value = self.registers[instruction.dest_reg]
        shift_count = self.registers[instruction.source_reg]
        result = self.alu.shift_left(dest_value, shift_count)
        self.registers[instruction.dest_reg] = result

    def _execute_shl_imm(self, instruction: Instruction) -> None:
        """SHL R1, #imm - R1 = R1 << imm"""
        dest_value = self.registers[instruction.dest_reg]
        result = self.alu.shift_left(dest_value, instruction.immediate)
        self.registers[instruction.dest_reg] = result

    def _execute_shr_reg(self, instruction: Instruction) -> None:
        """SHR R1, R2 - R1 = R1 >> R2 (логический)"""
        dest_value = self.registers[instruction.dest_reg]
        shift_count = self.registers[instruction.source_reg]
        result = self.alu.shift_right(dest_value, shift_count)
        self.registers[instruction.dest_reg] = result

    def _execute_shr_imm(self, instruction: Instruction) -> None:
        """SHR R1, #imm - R1 = R1 >> imm (логический)"""
        dest_value = self.registers[instruction.dest_reg]
        result = self.alu.shift_right(dest_value, instruction.immediate)
        self.registers[instruction.dest_reg] = result

    def _execute_sar_reg(self, instruction: Instruction) -> None:
        """SAR R1, R2 - R1 = R1 >> R2 (арифметический)"""
        dest_value = self.registers[instruction.dest_reg]
        shift_count = self.registers[instruction.source_reg]
        result = self.alu.arithmetic_shift_right(dest_value, shift_count)
        self.registers[instruction.dest_reg] = result

    def _execute_sar_imm(self, instruction: Instruction) -> None:
        """SAR R1, #imm - R1 = R1 >> imm (арифметический)"""
        dest_value = self.registers[instruction.dest_reg]
        result = self.alu.arithmetic_shift_right(dest_value, instruction.immediate)
        self.registers[instruction.dest_reg] = result

    # Реализация команд сравнения
    def _execute_cmp_reg(self, instruction: Instruction) -> None:
        """CMP R1, R2 - сравнить R1 и R2 (обновляет только флаги)"""
        value1 = self.registers[instruction.dest_reg]
        value2 = self.registers[instruction.source_reg]
        self.alu.compare(value1, value2)

    def _execute_cmp_imm(self, instruction: Instruction) -> None:
        """CMP R1, #imm - сравнить R1 и константу"""
        value1 = self.registers[instruction.dest_reg]
        self.alu.compare(value1, instruction.immediate)

    # Реализация команд переходов
    def _execute_jmp(self, instruction: Instruction) -> None:
        """JMP addr - безусловный переход"""
        self.registers.pc = instruction.address

    def _execute_jz(self, instruction: Instruction) -> None:
        """JZ addr - переход если Zero flag"""
        if self.flags["Z"]:
            self.registers.pc = instruction.address

    def _execute_jnz(self, instruction: Instruction) -> None:
        """JNZ addr - переход если не Zero flag"""
        if not self.flags["Z"]:
            self.registers.pc = instruction.address

    def _execute_jc(self, instruction: Instruction) -> None:
        """JC addr - переход если Carry flag"""
        if self.flags["C"]:
            self.registers.pc = instruction.address

    def _execute_jnc(self, instruction: Instruction) -> None:
        """JNC addr - переход если не Carry flag"""
        if not self.flags["C"]:
            self.registers.pc = instruction.address

    def _execute_js(self, instruction: Instruction) -> None:
        """JS addr - переход если Sign flag"""
        if self.flags["S"]:
            self.registers.pc = instruction.address

    def _execute_jns(self, instruction: Instruction) -> None:
        """JNS addr - переход если не Sign flag"""
        if not self.flags["S"]:
            self.registers.pc = instruction.address

    # В RISC-V стиле стековые операции реализуются через базовые команды:
    # PUSH R1: SUB R8, R8, #4; STORE [R8], R1
    # POP R1:  LOAD R1, [R8]; ADD R8, R8, #4
    # где R8 - указатель стека (SP)

    def get_state(self) -> dict:
        """Получить текущее состояние CPU для отладки"""
        registers = {f"R{i}": self.registers[i] for i in range(8)}
        registers["R8"] = self.registers[8]  # SP как R8 в RISC-V стиле

        return {
            "registers": registers,
            "pc": self.registers.pc,
            "sp": self.registers.sp,
            "flags": {flag: self.flags[flag] for flag in ["Z", "S", "C", "O", "P"]},
            "running": self.running,
            "halted": self.halted,
            "cycle_count": self.cycle_count,
        }
