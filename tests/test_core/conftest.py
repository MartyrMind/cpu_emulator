import pytest

from cpu_emulator.core.memory import Memory
from cpu_emulator.core.registers import Registers


@pytest.fixture
def memory_fabric():
    def _create(size: int = 8):
        return Memory(size)

    return _create


@pytest.fixture
def registers_fabric():
    def _create(size: int = 8):
        return Registers(size)

    return _create
