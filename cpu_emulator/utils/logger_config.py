"""
Конфигурация логгера для всего проекта
"""

import os
import sys
from pathlib import Path

from loguru import logger

# Единый формат для всех логов
LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
)

SETUP_COMPLETE = False


def get_project_root() -> Path:
    """Получает корень проекта"""
    return Path(__file__).parent.parent.parent


def setup_logger(log_level: str = "DEBUG") -> None:
    global SETUP_COMPLETE
    logger.remove()

    project_root = get_project_root()
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    if not log_level:
        log_level = (
            "INFO"
            if os.getenv("ENVIRONMENT", "development").lower() == "production"
            else "DEBUG"
        )

    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        colorize=True,
        enqueue=True,
    )

    # Handler для файла с ротацией
    logger.add(
        "logs/cpu_emulator_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    mode = (
        "production"
        if os.getenv("ENVIRONMENT", "development") == "production"
        else "development"
    )
    logger.info(f"🚀 Логгер настроен для {mode} режима")
