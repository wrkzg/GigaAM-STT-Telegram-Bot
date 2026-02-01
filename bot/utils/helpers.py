import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List
import logging
import asyncio

logger = logging.getLogger(__name__)


def format_duration(seconds: float) -> str:
    """
    Форматирование длительности в человекочитаемый формат.
    
    Args:
        seconds: Длительность в секундах
    
    Returns:
        Отформатированная строка (например, "1:23", "0:45")
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def generate_filename(prefix: str = "audio", extension: str = "wav") -> Path:
    """
    Генерация уникального имени файла.
    
    Args:
        prefix: Префикс имени файла
        extension: Расширение файла
    
    Returns:
        Путь к файлу
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = os.urandom(4).hex()
    filename = f"{prefix}_{timestamp}_{random_suffix}.{extension}"
    return Path(filename)


def cleanup_old_files(
    directory: Path,
    max_age_hours: int = 1,
    pattern: str = "*"
) -> int:
    """
    Очистка старых файлов из директории.
    
    Args:
        directory: Директория для очистки
        max_age_hours: Максимальный возраст файла в часах
        pattern: Шаблон имен файлов
    
    Returns:
        Количество удаленных файлов
    """
    if not directory.exists():
        return 0
    
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    deleted_count = 0
    
    try:
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"Удален старый файл: {file_path}")
                    except Exception as e:
                        logger.warning(f"Ошибка удаления {file_path}: {e}")
    except Exception as e:
        logger.error(f"Ошибка очистки директории {directory}: {e}")
    
    if deleted_count > 0:
        logger.info(f"Удалено {deleted_count} старых файлов из {directory}")
    
    return deleted_count


async def cleanup_old_logs(
    log_dir: Path,
    retention_days: int
) -> int:
    """
    Очистка старых логов.
    
    Args:
        log_dir: Директория с логами
        retention_days: Количество дней хранения
    
    Returns:
        Количество удаленных файлов
    """
    return cleanup_old_files(log_dir, max_age_hours=retention_days * 24, pattern="*.log*")


async def periodic_cleanup(
    temp_dir: Path,
    log_dir: Path,
    retention_days: int,
    check_interval: int = 3600  # 1 час
):
    """
    Периодическая очистка старых файлов.
    
    Args:
        temp_dir: Директория временных файлов
        log_dir: Директория логов
        retention_days: Количество дней хранения логов
        check_interval: Интервал проверки в секундах
    """
    while True:
        try:
            # Очистка временных файлов (старше 1 часа)
            cleanup_old_files(temp_dir, max_age_hours=1)
            
            # Очистка старых логов
            await cleanup_old_logs(log_dir, retention_days)
            
        except Exception as e:
            logger.error(f"Ошибка периодической очистки: {e}")
        
        await asyncio.sleep(check_interval)
