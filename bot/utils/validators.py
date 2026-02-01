from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def validate_file_size(file_path: Path, max_size_mb: int) -> bool:
    """
    Проверка размера файла.
    
    Args:
        file_path: Путь к файлу
        max_size_mb: Максимальный размер в МБ
    
    Returns:
        True если размер допустим, иначе False
    """
    file_size = file_path.stat().st_size
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        logger.warning(
            f"Файл {file_path.name} слишком большой: "
            f"{file_size / (1024*1024):.2f} МБ > {max_size_mb} МБ"
        )
        return False
    
    return True


def validate_audio_format(file_path: Path) -> bool:
    """
    Проверка формата аудиофайла.
    
    Args:
        file_path: Путь к файлу
    
    Returns:
        True если формат допустим, иначе False
    """
    allowed_extensions = {'.wav', '.mp3', '.ogg', '.m4a', '.flac', '.aac', '.wma'}
    return file_path.suffix.lower() in allowed_extensions


def validate_video_format(file_path: Path) -> bool:
    """
    Проверка формата видеофайла.
    
    Args:
        file_path: Путь к файлу
    
    Returns:
        True если формат допустим, иначе False
    """
    allowed_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
    return file_path.suffix.lower() in allowed_extensions
