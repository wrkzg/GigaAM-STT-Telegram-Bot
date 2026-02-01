import asyncio
from pathlib import Path
from typing import Tuple
import logging

from .file_service import FileService
from ..utils import convert_audio, get_audio_duration, extract_audio_from_video
from ..utils.validators import validate_file_size, validate_audio_format, validate_video_format

logger = logging.getLogger(__name__)


class AudioService:
    """Сервис для обработки аудио."""
    
    def __init__(self, file_service: FileService, temp_dir: Path, max_file_size_mb: int = 100):
        self.file_service = file_service
        self.temp_dir = temp_dir
        self.max_file_size_mb = max_file_size_mb
    
    async def prepare_voice_message(
        self,
        voice_file: bytes,
        user_id: int,
        message_id: int
    ) -> Tuple[Path, float]:
        """
        Подготовка голосового сообщения для транскрибации.

        Args:
            voice_file: Байты голосового сообщения
            user_id: ID пользователя
            message_id: ID сообщения

        Returns:
            Кортеж (путь к WAV файлу, длительность)
        """
        from datetime import datetime

        # Сохраняем исходный файл
        ogg_path = self.file_service.generate_temp_path(prefix=f"voice_{user_id}", extension="ogg")
        await self.file_service.save_bytes(voice_file, ogg_path)

        try:
            # Проверяем размер
            if not validate_file_size(ogg_path, self.max_file_size_mb):
                raise ValueError(
                    f"Файл слишком большой (максимум {self.max_file_size_mb} МБ)"
                )

            # Конвертируем в WAV
            wav_path = self.file_service.generate_temp_path(prefix=f"audio_{user_id}", extension="wav")
            await convert_audio(ogg_path, wav_path, sample_rate=16000, channels=1)

            # Получаем длительность
            duration = await get_audio_duration(wav_path)

            logger.info(
                f"Голосовое сообщение подготовлено: "
                f"пользователь={user_id}, сообщение={message_id}, длительность={duration:.2f}с"
            )

            return wav_path, duration
        finally:
            # Гарантированно удаляем исходный файл
            await self.file_service.delete_file(ogg_path)
    
    async def prepare_audio_file(
        self,
        audio_file_path: Path,
        user_id: int,
        message_id: int
    ) -> Tuple[Path, float]:
        """
        Подготовка аудиофайла для транскрибации.

        Args:
            audio_file_path: Путь к скачанному аудиофайлу
            user_id: ID пользователя
            message_id: ID сообщения

        Returns:
            Кортеж (путь к WAV файлу, длительность)
        """
        try:
            # Проверяем формат
            if not validate_audio_format(audio_file_path):
                raise ValueError("Неподдерживаемый формат аудиофайла")

            # Проверяем размер
            if not validate_file_size(audio_file_path, self.max_file_size_mb):
                raise ValueError(
                    f"Файл слишком большой (максимум {self.max_file_size_mb} МБ)"
                )

            # Конвертируем в WAV
            wav_path = self.file_service.generate_temp_path(prefix=f"audio_{user_id}", extension="wav")
            await convert_audio(audio_file_path, wav_path, sample_rate=16000, channels=1)

            # Получаем длительность
            duration = await get_audio_duration(wav_path)

            logger.info(
                f"Аудиофайл подготовлен: "
                f"пользователь={user_id}, сообщение={message_id}, длительность={duration:.2f}с"
            )

            return wav_path, duration
        finally:
            # Гарантированно удаляем исходный файл
            await self.file_service.delete_file(audio_file_path)
    
    async def prepare_video_note(
        self,
        video_file_path: Path,
        user_id: int,
        message_id: int
    ) -> Tuple[Path, float]:
        """
        Подготовка видеосообщения для транскрибации.

        Args:
            video_file_path: Путь к скачанному видеофайлу
            user_id: ID пользователя
            message_id: ID сообщения

        Returns:
            Кортеж (путь к WAV файлу, длительность)
        """
        try:
            # Проверяем формат
            if not validate_video_format(video_file_path):
                raise ValueError("Неподдерживаемый формат видеофайла")

            # Проверяем размер
            if not validate_file_size(video_file_path, self.max_file_size_mb):
                raise ValueError(
                    f"Файл слишком большой (максимум {self.max_file_size_mb} МБ)"
                )

            # Извлекаем аудио и конвертируем в WAV
            wav_path = self.file_service.generate_temp_path(prefix=f"audio_{user_id}", extension="wav")
            await extract_audio_from_video(video_file_path, wav_path, sample_rate=16000, channels=1)

            # Получаем длительность
            duration = await get_audio_duration(wav_path)

            logger.info(
                f"Видеосообщение подготовлено: "
                f"пользователь={user_id}, сообщение={message_id}, длительность={duration:.2f}с"
            )

            return wav_path, duration
        finally:
            # Гарантированно удаляем исходный видеофайл
            await self.file_service.delete_file(video_file_path)
    
    async def cleanup(self, file_path: Path) -> None:
        """
        Очистка временных файлов.
        
        Args:
            file_path: Путь к файлу для удаления
        """
        await self.file_service.delete_file(file_path)
