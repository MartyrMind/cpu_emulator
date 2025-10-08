import argparse

from cpu_emulator.core.cpu import CPU
from cpu_emulator.core.program_loader import ProgramLoader
from cpu_emulator.utils.logger_config import setup_logger
from cpu_emulator.gui import run_gui
from cpu_emulator.utils.demo_programs import (
    program_array_sum,
    program_convolution,
    program_long_arithmetic,
    program_array_sum_long,
)

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

    program_assembly = program_array_sum()

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
    program_assembly = program_convolution()

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
    
    program_assembly = program_long_arithmetic()
    
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


def demo_array_sum_long():
    """Демонстрация суммирования массива с 64-битным аккумулятором (R1:R0)."""
    print("\n=== Программа: Сумма элементов массива (64-бит) ===")

    cpu = CPU()
    loader = ProgramLoader()

    program_assembly = program_array_sum_long()
    for i, line in enumerate(program_assembly):
        addr = i * 4
        print(f"  {addr:3d}: {line}")

    machine_code = loader.assemble_simple(program_assembly)
    cpu.load_program(machine_code)

    print("\nВыполнение программы...")
    cpu.run(max_cycles=400)

    result_low = cpu.registers[0] & 0xFFFFFFFF
    result_high = cpu.registers[1] & 0xFFFFFFFF
    result_64 = (result_high << 32) | result_low
    expected = 10 + 20 + 30 + 40 + 50
    print(f"\nРезультат (R1:R0): 0x{result_high:08X}:0x{result_low:08X} -> 0x{result_64:016X}")
    print(f"Ожидаемый:          {expected} (0x{expected:016X})")
    print(f"Правильность: {'✅' if result_64 == expected else '❌'}")

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
        demo_array_sum_long()
        # demo_long_arithmetic()

        print("\n=== Демонстрация завершена успешно! ===")

    except Exception as e:
        print(f"Ошибка во время выполнения: {e}")
        import traceback

        traceback.print_exc()

        color_dict = {
            "north": 1,
            "south": 2,
            "west": 3,
        }
        y = lambda x: color_dict[x]


if __name__ == "__main__":
    main()
