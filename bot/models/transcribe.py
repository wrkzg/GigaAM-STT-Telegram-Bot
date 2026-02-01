from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class Utterance:
    """Одна реплика из длинной транскрибации."""
    text: str
    start_time: float
    end_time: float
    
    def __str__(self) -> str:
        return f"[{self.start_time:.2f} - {self.end_time:.2f}]: {self.text}"


@dataclass
class LongTranscriptionResult:
    """Результат транскрибации длинного аудио."""
    utterances: List[Utterance]
    total_duration: float
    full_text: str
    
    @classmethod
    def from_dict(cls, data: List[Dict[str, Any]]) -> "LongTranscriptionResult":
        """Создание результата из словаря (формат GigaAM)."""
        utterances = [
            Utterance(
                text=utt["transcription"],
                start_time=utt["boundaries"][0],
                end_time=utt["boundaries"][1]
            )
            for utt in data
        ]
        
        total_duration = utterances[-1].end_time if utterances else 0.0
        full_text = " ".join(utt.text for utt in utterances)
        
        return cls(
            utterances=utterances,
            total_duration=total_duration,
            full_text=full_text
        )
