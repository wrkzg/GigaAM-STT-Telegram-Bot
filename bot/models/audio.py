from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class AudioInfo:
    """Информация об аудиофайле."""
    file_path: str
    duration: float
    format: str
    size_bytes: int
    sample_rate: int
    channels: int
    user_id: int
    message_id: int
    received_at: datetime
    
    @property
    def size_mb(self) -> float:
        """Размер в мегабайтах."""
        return self.size_bytes / (1024 * 1024)


@dataclass
class TranscriptionResult:
    """Результат транскрибации."""
    text: str
    audio_info: AudioInfo
    processing_time_sec: float
    model_name: str
    confidence: Optional[float] = None
    error: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        """Успешная ли транскрибация."""
        return self.error is None
