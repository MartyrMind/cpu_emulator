from __future__ import annotations


def program_array_sum() -> list[str]:
    """Array sum demo program assembly."""
    return [
        # Initialize array [10,20,30,40,50] at 2000..2016
        "MOV R1, #2000",
        "MOV R2, #10",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #20",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #30",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #40",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #50",
        "STORE [R1], R2",
        # Sum loop
        "MOV R0, #0",
        "MOV R1, #2000",
        "MOV R3, #5",
        "LOAD R2, [R1]",
        "ADD R0, R2",
        "ADD R1, #4",
        "SUB R3, #1",
        "CMP R3, #0",
        "JNZ 72",
        "HALT",
    ]


def program_convolution() -> list[str]:
    """Convolution of two arrays demo program assembly."""
    return [
        # Initialize A[1,2,3,4,5] at 3000..3016
        "MOV R1, #3000",
        "MOV R2, #1",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #2",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #3",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #4",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #5",
        "STORE [R1], R2",
        # Initialize B[5,4,3,2,1] at 4000..4016
        "MOV R1, #4000",
        "MOV R2, #5",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #4",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #3",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #2",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #1",
        "STORE [R1], R2",
        # Convolution loop
        "MOV R0, #0",
        "MOV R1, #3000",
        "MOV R2, #4000",
        "MOV R7, #5",
        "LOAD R3, [R1]",
        "LOAD R4, [R2]",
        "MUL R3, R4",
        "ADD R0, R3",
        "ADD R1, #4",
        "ADD R2, #4",
        "SUB R7, #1",
        "CMP R7, #0",
        "JNZ 136",
        "HALT",
    ]


def program_long_arithmetic() -> list[str]:
    """64-bit addition demo using 32-bit registers and carry."""
    return [
        # Initialize A = 0x00000001FFFFFFFF (low: 0xFFFFFFFF, high: 0x00000001)
        # Initialize B = 0x0000000000000001 (low: 0x00000001, high: 0x00000000)
        "MOV R0, #-1",     # A low
        "MOV R1, #1",      # A high
        "MOV R2, #1",      # B low
        "MOV R3, #0",      # B high
        # Long addition with carry
        "CLC",
        "ADD R0, R2",
        "ADDC R1, R3",
        "HALT",
    ]


def program_array_sum_long() -> list[str]:
    """Array sum with 64-bit accumulation in R1:R0 using carry."""
    return [
        # Initialize array [10,20,30,40,50] at 2000..2016
        "MOV R1, #2000",
        "MOV R2, #10",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #20",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #30",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #40",
        "STORE [R1], R2",
        "ADD R1, #4",
        "MOV R2, #50",
        "STORE [R1], R2",
        # 64-bit sum: R1:R0 accumulator, R4 pointer, R3 count, R6 zero for ADDC
        "MOV R0, #0",
        "MOV R1, #0",
        "MOV R4, #2000",
        "MOV R3, #5",
        "MOV R6, #0",
        # Loop starts at address 80
        "LOAD R2, [R4]",
        "CLC",
        "ADD R0, R2",
        "ADDC R1, R6",
        "ADD R4, #4",
        "SUB R3, #1",
        "CMP R3, #0",
        "JNZ 80",
        "HALT",
    ]


def list_demo_names() -> list[str]:
    return [
        "Сумма массива",
        "Свертка массивов",
        "Длинная арифметика",
        "Сумма массива (64-бит)",
    ]


def get_demo_by_name(name: str) -> list[str]:
    if name == "Сумма массива":
        return program_array_sum()
    if name == "Свертка массивов":
        return program_convolution()
    if name == "Длинная ариритметика" or name == "Длинная арифметика":
        return program_long_arithmetic()
    if name == "Сумма массива (64-бит)":
        return program_array_sum_long()
    raise KeyError(f"Unknown demo: {name}")


