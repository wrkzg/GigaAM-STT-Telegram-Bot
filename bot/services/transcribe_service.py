import asyncio
import os
import time
from pathlib import Path
from typing import Optional, Union, List, Dict
import logging

from bot.models.audio import TranscriptionResult, AudioInfo
from bot.models.transcribe import LongTranscriptionResult

logger = logging.getLogger(__name__)


class TranscribeService:
    """Сервис для транскрибации с использованием GigaAM."""
    
    def __init__(self, model_name: str = "v3_e2e_rnnt", device: str = "auto"):
        self.model_name = model_name
        self.device = self._get_device(device)
        self.model = None
        self._load_model()
    
    def _get_device(self, device: str) -> str:
        """Определение устройства."""
        import torch
        
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    def _load_model(self):
        """Загрузка модели GigaAM."""
        try:
            import gigaam
            
            logger.info(f"Загрузка модели GigaAM: {self.model_name} на {self.device}")
            self.model = gigaam.load_model(
                self.model_name,
                device=self.device
            )
            logger.info(f"Модель GigaAM успешно загружена")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели GigaAM: {e}")
            raise
    
    def _set_hf_token(self, hf_token: Optional[str] = None):
        """Установка HF токена для длинных аудио."""
        if hf_token:
            os.environ["HF_TOKEN"] = hf_token
            logger.debug("HF токен установлен")
    
    async def transcribe(
        self,
        audio_path: Path,
        max_duration_sec: int = 300
    ) -> TranscriptionResult:
        """
        Транскрибация аудио с автоматическим разбиением на части.

        Args:
            audio_path: Путь к аудиофайлу
            max_duration_sec: Максимальная длительность аудио

        Returns:
            Результат транскрибации
        """
        from datetime import datetime
        from bot.utils import get_audio_duration
        import shutil

        audio_info = AudioInfo(
            file_path=str(audio_path),
            duration=audio_path.stat().st_size,
            format=audio_path.suffix,
            size_bytes=audio_path.stat().st_size,
            sample_rate=16000,
            channels=1,
            user_id=0,
            message_id=0,
            received_at=datetime.now()
        )

        start_time = time.time()

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.model.transcribe,
                str(audio_path)
            )

            processing_time = time.time() - start_time
            logger.info(f"Транскрибация завершена за {processing_time:.2f}с")

            return TranscriptionResult(
                text=result,
                audio_info=audio_info,
                processing_time_sec=processing_time,
                model_name=self.model_name,
                error=None
            )

        except ValueError as e:
            if "Too long" in str(e):
                logger.warning("Аудио слишком длинное, разбиваем на части")
                return await self._transcribe_chunked(audio_path, audio_info, start_time)
            raise
        except Exception as e:
            logger.error(f"Ошибка транскрибации: {e}")
            return TranscriptionResult(
                text="",
                audio_info=audio_info,
                processing_time_sec=time.time() - start_time,
                model_name=self.model_name,
                error=str(e)
            )

    async def _transcribe_chunked(
        self,
        audio_path: Path,
        audio_info,
        start_time: float
    ) -> TranscriptionResult:
        """Транскрибация длинного аудио с разбивкой на части."""
        from bot.utils import split_audio
        import tempfile
        import shutil

        chunk_dir = Path(tempfile.mkdtemp(prefix="chunks_"))
        all_text = []

        try:
            # Разбиваем аудио на части по 20 секунд
            chunks = await split_audio(audio_path, chunk_dir, chunk_duration_sec=20)
            logger.info(f"Аудио разбито на {len(chunks)} частей")

            # Транскрибируем каждую часть
            for i, chunk_path in enumerate(chunks):
                logger.info(f"Транскрибация части {i + 1}/{len(chunks)}")
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    self.model.transcribe,
                    str(chunk_path)
                )
                if result:
                    all_text.append(result)

            processing_time = time.time() - start_time
            combined_text = " ".join(all_text)

            logger.info(f"Чанковая транскрибация завершена за {processing_time:.2f}с")

            return TranscriptionResult(
                text=combined_text,
                audio_info=audio_info,
                processing_time_sec=processing_time,
                model_name=self.model_name,
                error=None
            )

        except Exception as e:
            logger.error(f"Ошибка чанковой транскрибации: {e}")
            return TranscriptionResult(
                text=" ".join(all_text),
                audio_info=audio_info,
                processing_time_sec=time.time() - start_time,
                model_name=self.model_name,
                error=str(e)
            )
        finally:
            # Удаляем временную директорию с чанками
            shutil.rmtree(chunk_dir, ignore_errors=True)
    
    async def transcribe_long(
        self,
        audio_path: Path,
        hf_token: Optional[str] = None,
        max_duration_sec: int = 300
    ) -> LongTranscriptionResult:
        """
        Транскрибация длинного аудио с использованием VAD.
        
        Args:
            audio_path: Путь к аудиофайлу
            hf_token: Токен Hugging Face (требуется для pyannote.audio)
            max_duration_sec: Максимальная длительность аудио
        
        Returns:
            Результат транскрибации длинного аудио
        """
        self._set_hf_token(hf_token)
        
        start_time = time.time()
        
        try:
            import asyncio
            
            # Запускаем транскрибацию в отдельном потоке
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.model.transcribe_longform,
                str(audio_path)
            )
            
            processing_time = time.time() - start_time
            
            logger.info(f"Длинная транскрибация завершена за {processing_time:.2f}с")
            
            return LongTranscriptionResult.from_dict(result)
            
        except Exception as e:
            logger.error(f"Ошибка длинной транскрибации: {e}")
            raise
    
    async def transcribe_auto(
        self,
        audio_path: Path,
        hf_token: Optional[str] = None,
        max_duration_sec: int = 300
    ) -> Union[TranscriptionResult, LongTranscriptionResult]:
        """
        Автоматический выбор метода транскрибации.

        Args:
            audio_path: Путь к аудиофайлу
            hf_token: Токен Hugging Face (для длинных аудио с VAD)
            max_duration_sec: Максимальная длительность аудио

        Returns:
            Результат транскрибации
        """
        from bot.utils import get_audio_duration

        # Получаем длительность аудио
        duration = await get_audio_duration(audio_path)

        # Используем longform только если есть HF токен
        if hf_token:
            logger.info(f"Используем длинную транскрибацию с VAD ({duration:.2f}с)")
            return await self.transcribe_long(audio_path, hf_token, max_duration_sec)
        # Иначе используем обычную транскрибацию с авто-разбиением
        else:
            logger.info(f"Используем транскрибацию с авто-разбиением ({duration:.2f}с)")
            return await self.transcribe(audio_path, max_duration_sec)
