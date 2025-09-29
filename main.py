import argparse

from cpu_emulator.core.cpu import CPU
from cpu_emulator.core.program_loader import ProgramLoader
from cpu_emulator.utils.logger_config import setup_logger
from cpu_emulator.gui import run_gui

setup_logger(log_level="INFO")


def print_cpu_state(cpu: CPU):
    """Вывод состояния CPU"""
    state = cpu.get_state()

    print("  Регистры:")
    for i in range(8):
        print(
            f"    R{i}: {state['registers'][f'R{i}']:10d} (0x{state['registers'][f'R{i}']:08X})"
        )

    # В RISC-V стиле SP доступен как R8
    print(
        f"    R8 (SP): {state['registers']['R8']:10d} (0x{state['registers']['R8']:08X})"
    )

    print("  Специальные регистры:")
    print(f"    PC: 0x{state['pc']:05X}")

    print("  Флаги:")
    flags_str = " ".join([f"{flag}={value}" for flag, value in state["flags"].items()])
    print(f"    {flags_str}")

    print(f"  Состояние: running={state['running']}, halted={state['halted']}")


def demo_array_sum():
    """Демонстрация программы суммирования массива"""
    print("\n=== Программа: Сумма элементов массива ===")

    cpu = CPU()
    loader = ProgramLoader()

    # Программа суммирования массива [10, 20, 30, 40, 50]
    program_assembly = [
        # Инициализация массива в памяти (адреса 2000, 2004, 2008, 2012, 2016)
        "MOV R1, #2000",  # R1 = базовый адрес массива
        "MOV R2, #10",  # Первый элемент = 10
        "STORE [R1], R2",  # Memory[2000] = 10
        "ADD R1, #4",  # R1 = 2004
        "MOV R2, #20",  # Второй элемент = 20
        "STORE [R1], R2",  # Memory[2004] = 20
        "ADD R1, #4",  # R1 = 2008
        "MOV R2, #30",  # Третий элемент = 30
        "STORE [R1], R2",  # Memory[2008] = 30
        "ADD R1, #4",  # R1 = 2012
        "MOV R2, #40",  # Четвертый элемент = 40
        "STORE [R1], R2",  # Memory[2012] = 40
        "ADD R1, #4",  # R1 = 2016
        "MOV R2, #50",  # Пятый элемент = 50
        "STORE [R1], R2",  # Memory[2016] = 50
        # Основной алгоритм суммирования
        "MOV R0, #0",  # R0 = сумма (аккумулятор)
        "MOV R1, #2000",  # R1 = текущий адрес массива
        "MOV R3, #5",  # R3 = счетчик элементов
        # Цикл суммирования (начинается с адреса 68)
        "LOAD R2, [R1]",  # R2 = текущий элемент массива
        "ADD R0, R2",  # R0 += R2 (накапливаем сумму)
        "ADD R1, #4",  # R1 += 4 (переход к следующему элементу)
        "SUB R3, #1",  # R3-- (уменьшаем счетчик)
        "CMP R3, #0",  # Проверяем, остались ли элементы
        "JNZ 68",  # Если R3 != 0, переходим к началу цикла
        "HALT",  # Завершение программы
    ]

    print("Программа суммирования массива [10, 20, 30, 40, 50]:")
    for i, line in enumerate(program_assembly):
        addr = i * 4
        print(f"  {addr:3d}: {line}")

    machine_code = loader.assemble_simple(program_assembly)
    cpu.load_program(machine_code)

    print("\nВыполнение программы...")
    cpu.run(max_cycles=1000)

    result = cpu.registers[0]  # Результат в R0
    print(f"\nРезультат суммирования: {result}")
    print("Ожидаемый результат: 150 (10+20+30+40+50)")
    print(f"Правильность: {'✅' if result == 150 else '❌'}")

    print_cpu_state(cpu)


def demo_array_convolution():
    """Демонстрация программы свертки двух массивов"""
    print("\n=== Программа: Свертка двух массивов ===")

    cpu = CPU()
    loader = ProgramLoader()

    # Программа свертки массивов A=[1,2,3,4,5] и B=[5,4,3,2,1]
    program_assembly = [
        # === Инициализация массива A [1,2,3,4,5] по адресам 3000-3016 ===
        "MOV R1, #3000",  # Базовый адрес массива A
        "MOV R2, #1",  # A[0] = 1
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #2",  # A[1] = 2
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #3",  # A[2] = 3
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #4",  # A[3] = 4
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #5",  # A[4] = 5
        "STORE [R1], R2",
        # === Инициализация массива B [5,4,3,2,1] по адресам 4000-4016 ===
        "MOV R1, #4000",  # Базовый адрес массива B
        "MOV R2, #5",  # B[0] = 5
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #4",  # B[1] = 4
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #3",  # B[2] = 3
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #2",  # B[3] = 2
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #1",  # B[4] = 1
        "STORE [R1], R2",
        # === Основной алгоритм свертки ===
        "MOV R0, #0",  # R0 = результат свертки (аккумулятор)
        "MOV R1, #3000",  # R1 = указатель на массив A
        "MOV R2, #4000",  # R2 = указатель на массив B
        "MOV R7, #5",  # R7 = счетчик элементов
        # Цикл свертки (начинается с адреса 136)
        "LOAD R3, [R1]",  # R3 = A[i] (адрес 136)
        "LOAD R4, [R2]",  # R4 = B[i] (адрес 140)
        "MUL R3, R4",  # R3 = A[i] * B[i] (адрес 144)
        "ADD R0, R3",  # R0 += A[i] * B[i] (адрес 148)
        "ADD R1, #4",  # Переход к следующему элементу A (адрес 152)
        "ADD R2, #4",  # Переход к следующему элементу B (адрес 156)
        "SUB R7, #1",  # Уменьшаем счетчик (адрес 160)
        "CMP R7, #0",  # Проверяем окончание (адрес 164)
        "JNZ 136",  # Если не закончили, переходим к началу цикла (адрес 136)
        "HALT",  # Завершение программы
    ]

    print("Программа свертки массивов A=[1,2,3,4,5] и B=[5,4,3,2,1]:")
    print("Вычисляет: A[0]*B[0] + A[1]*B[1] + A[2]*B[2] + A[3]*B[3] + A[4]*B[4]")
    print("         = 1*5 + 2*4 + 3*3 + 4*2 + 5*1 = 5 + 8 + 9 + 8 + 5 = 35")

    machine_code = loader.assemble_simple(program_assembly)
    cpu.load_program(machine_code)

    print("\nВыполнение программы...")
    cpu.run(max_cycles=400)

    result = cpu.registers[0]  # Результат в R0
    print(f"\nРезультат свертки: {result}")
    print("Ожидаемый результат: 35")
    print(f"Правильность: {'✅' if result == 35 else '❌'}")

    print_cpu_state(cpu)


def demo_long_arithmetic():
    """Демонстрация длинной арифметики - сложение 64-битных чисел"""
    print("\n=== Программа: Длинная арифметика (64-битные числа) ===")
    
    cpu = CPU()
    loader = ProgramLoader()
    
    # Программа сложения двух 64-битных чисел:
    # A = 0x123456789ABCDEF0 (младшие 32 бита: 0x9ABCDEF0, старшие: 0x12345678)
    # B = 0x0FEDCBA987654321 (младшие 32 бита: 0x87654321, старшие: 0x0FEDCBA9)
    # Результат должен быть: A + B = 0x2222222222222211
    
    program_assembly = [
        # Упрощенный пример: сложение двух 64-битных чисел
        # A = 0x00000001FFFFFFFF (младшие: 0xFFFFFFFF, старшие: 0x00000001)
        # B = 0x0000000000000001 (младшие: 0x00000001, старшие: 0x00000000)
        # Результат: 0x0000000200000000
        
        # Инициализация первого числа A
        "MOV R0, #-1",           # R0 = 0xFFFFFFFF (младшие 32 бита A)
        "MOV R1, #1",            # R1 = 0x00000001 (старшие 32 бита A)
        
        # Инициализация второго числа B
        "MOV R2, #1",            # R2 = 0x00000001 (младшие 32 бита B)
        "MOV R3, #0",            # R3 = 0x00000000 (старшие 32 бита B)
        
        # Длинное сложение: A + B
        "CLC",                   # Очистить флаг переноса
        "ADD R0, R2",            # R0 = A_low + B_low (должен быть перенос)
        "ADDC R1, R3",           # R1 = A_high + B_high + Carry
        
        # Результат в R1:R0
        "HALT"
    ]
    
    print("Программа сложения 64-битных чисел:")
    print("A = 0x00000001FFFFFFFF")
    print("B = 0x0000000000000001")
    print("Ожидаемый результат: 0x0000000200000000")
    print()
    
    for i, line in enumerate(program_assembly):
        addr = i * 4
        print(f"  {addr:3d}: {line}")
    
    machine_code = loader.assemble_simple(program_assembly)
    cpu.load_program(machine_code)
    
    print("\nВыполнение программы...")
    cpu.run(max_cycles=50)
    
    # Получаем результат
    result_low = cpu.registers[0] & 0xFFFFFFFF
    result_high = cpu.registers[1] & 0xFFFFFFFF
    
    # Формируем 64-битный результат
    result_64bit = (result_high << 32) | result_low
    expected = 0x0000000200000000
    
    print(f"\nРезультат длинного сложения:")
    print(f"  R0 (младшие 32 бита): 0x{result_low:08X}")
    print(f"  R1 (старшие 32 бита): 0x{result_high:08X}")
    print(f"  Полный 64-битный результат: 0x{result_64bit:016X}")
    print(f"  Ожидаемый результат:        0x{expected:016X}")
    print(f"  Правильность: {'✅' if result_64bit == expected else '❌'}")
    
    print_cpu_state(cpu)


def main():
    """Главная функция: запуск GUI или демонстраций"""
    parser = argparse.ArgumentParser(description="CPU Emulator")
    parser.add_argument("--gui", action="store_true", help="Run Tkinter GUI")
    args = parser.parse_args()

    if args.gui:
        run_gui()
        return

    try:
        # demo_basic_operations()
        # demo_conditional_jumps()
        # demo_stack_operations()
        demo_array_sum()
        demo_array_convolution()
        # demo_long_arithmetic()

        print("\n=== Демонстрация завершена успешно! ===")

    except Exception as e:
        print(f"Ошибка во время выполнения: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
