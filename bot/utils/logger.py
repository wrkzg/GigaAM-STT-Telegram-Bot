import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from typing import Optional


def setup_logger(
    name: str,
    log_dir: Path,
    level: str = "INFO",
    retention_days: int = 30,
    console_output: bool = True
) -> logging.Logger:
    """
    Настройка логирования с ротацией по времени.
    
    Args:
        name: Имя логгера
        log_dir: Директория для хранения логов
        level: Уровень логирования
        retention_days: Количество дней хранения логов
        console_output: Вывод в консоль
    
    Returns:
        Настроенный логгер
    """
    # Создаем директорию для логов
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()  # Очищаем существующие хендлеры
    
    # Форматтер
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Файловый хендлер с ротацией по дням
    log_file = log_dir / f"bot_{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=retention_days,
        encoding="utf-8"
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    # Отдельный хендлер для ошибок
    error_file = log_dir / f"error_{datetime.now().strftime('%Y-%m-%d')}.log"
    error_handler = TimedRotatingFileHandler(
        filename=error_file,
        when="midnight",
        interval=1,
        backupCount=retention_days,
        encoding="utf-8"
    )
    error_handler.suffix = "%Y-%m-%d"
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)
    
    # Консольный хендлер
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, level.upper()))
        logger.addHandler(console_handler)
    
    return logger
