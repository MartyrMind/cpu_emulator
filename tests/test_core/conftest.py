import pytest

from cpu_emulator.core.memory import Memory


@pytest.fixture
def memory_fabric():
    def _create(size: int = 0):
        return Memory(size)

    return _create
