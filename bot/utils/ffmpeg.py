import asyncio
import subprocess
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def convert_audio(
    input_path: Path,
    output_path: Path,
    sample_rate: int = 16000,
    channels: int = 1,
    format: str = "wav",
    quality: str = "high"
) -> Path:
    """
    Конвертирование аудио с использованием ffmpeg.
    
    Args:
        input_path: Путь к исходному файлу
        output_path: Путь к выходному файлу
        sample_rate: Частота дискретизации (по умолчанию 16000 Hz для GigaAM)
        channels: Количество каналов (1 - моно)
        format: Выходной формат (wav, mp3 и т.д.)
        quality: Качество конвертации (high, medium, low)
    
    Returns:
        Путь к конвертированному файлу
    """
    # Настройки качества
    bitrates = {"high": "192k", "medium": "128k", "low": "64k"}
    bitrate = bitrates.get(quality, "128k")
    
    # Команда ffmpeg
    cmd = [
        "ffmpeg",
        "-y",  # Перезаписать выходной файл
        "-i", str(input_path),
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-b:a", bitrate,
        "-f", format,
        str(output_path)
    ]
    
    logger.debug(f"Конвертирование: {input_path} → {output_path}")
    
    try:
        # Запускаем ffmpeg асинхронно
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        _, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=300  # 5 минут таймаут
        )
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore')
            logger.error(f"Ошибка ffmpeg: {error_msg}")
            raise RuntimeError(f"Ошибка конвертирования аудио: {error_msg}")
        
        logger.info(f"Успешно конвертировано: {output_path}")
        return output_path
        
    except asyncio.TimeoutError:
        logger.error(f"Таймаут конвертирования: {input_path}")
        raise RuntimeError("Таймаут конвертирования аудио")
    except Exception as e:
        logger.error(f"Ошибка конвертирования: {e}")
        raise


async def get_audio_duration(file_path: Path) -> float:
    """
    Получить длительность аудиофайла в секундах.
    
    Args:
        file_path: Путь к аудиофайлу
    
    Returns:
        Длительность в секундах
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, _ = await process.communicate()
        duration = float(stdout.decode('utf-8').strip())
        return duration
    except Exception as e:
        logger.error(f"Ошибка получения длительности: {e}")
        return 0.0


async def split_audio(
    input_path: Path,
    output_dir: Path,
    chunk_duration_sec: int = 20
) -> list[Path]:
    """
    Разбить аудиофайл на части.

    Args:
        input_path: Путь к исходному аудиофайлу
        output_dir: Директория для сохранения частей
        chunk_duration_sec: Длительность каждой части в секундах

    Returns:
        Список путей к созданным файлам
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-f", "segment",
        "-segment_time", str(chunk_duration_sec),
        "-c", "copy",
        "-reset_timestamps", "1",
        str(output_dir / "chunk_%03d.wav")
    ]

    logger.debug(f"Разбиение аудио на части: {input_path}")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        _, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=300
        )

        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore')
            raise RuntimeError(f"Ошибка разбиения аудио: {error_msg}")

        # Получаем список созданных файлов
        chunks = sorted(output_dir.glob("chunk_*.wav"))

        logger.info(f"Аудио разбито на {len(chunks)} частей")
        return chunks

    except asyncio.TimeoutError:
        raise RuntimeError("Таймаут разбиения аудио")
    except Exception as e:
        logger.error(f"Ошибка разбиения аудио: {e}")
        raise


async def extract_audio_from_video(
    input_path: Path,
    output_path: Path,
    sample_rate: int = 16000,
    channels: int = 1
) -> Path:
    """
    Извлечь аудиодорожку из видеофайла.
    
    Args:
        input_path: Путь к видеофайлу
        output_path: Путь к выходному аудиофайлу
        sample_rate: Частота дискретизации
        channels: Количество каналов
    
    Returns:
        Путь к извлеченному аудиофайлу
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-vn",  # Отключить видео
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-f", "wav",
        str(output_path)
    ]
    
    logger.debug(f"Извлечение аудио из видео: {input_path} → {output_path}")
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        _, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=300
        )
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore')
            raise RuntimeError(f"Ошибка извлечения аудио: {error_msg}")
        
        logger.info(f"Аудио извлечено: {output_path}")
        return output_path
        
    except asyncio.TimeoutError:
        raise RuntimeError("Таймаут извлечения аудио")
    except Exception as e:
        logger.error(f"Ошибка извлечения аудио: {e}")
        raise
