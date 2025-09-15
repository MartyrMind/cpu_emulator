import sys
from pathlib import Path

import pytest
from loguru import logger

# Добавляем корень проекта в путь Python
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session", autouse=True)
def setup_test_logger():
    """Автоматически настраивает логгер для тестов"""

    # Удаляем все существующие handlers
    logger.remove()

    # Создаем директорию для тестовых логов в корне проекта
    test_logs_dir = project_root / "logs"
    test_logs_dir.mkdir(exist_ok=True)

    # Handler для тестов (всегда перезаписывает один и тот же файл)
    logger.add(
        str(test_logs_dir / "test_run.log"),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        mode="w",  # Перезапись файла
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    logger.info("🧪 Логгер настроен для тестов")
    yield
    logger.info("✅ Тесты завершены")


@pytest.fixture(autouse=True)
def log_test_function(request):
    """Логирует начало и конец каждого теста"""
    test_name = request.node.name
    logger.info(f"🚀 Начало теста: {test_name}")
    yield
    logger.info(f"✅ Завершение теста: {test_name}")
