import os
import json
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Конфигурация приложения."""

    # ========== Telegram ==========
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # ========== GigaAM ==========
    GIGAAM_MODEL: str = os.getenv("GIGAAM_MODEL", "rnnt")
    GIGAAM_DEVICE: str = os.getenv("GIGAAM_DEVICE", "auto")
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")

    # ========== Логирование ==========
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: Path = Path(os.getenv("LOG_DIR", "logs"))
    LOG_RETENTION_DAYS: int = int(os.getenv("LOG_RETENTION_DAYS", "30"))

    # ========== Временные файлы ==========
    TEMP_DIR: Path = Path(os.getenv("TEMP_DIR", "temp"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "100"))

    # ========== Настройки обработки ==========
    MAX_AUDIO_DURATION_SEC: int = int(os.getenv("MAX_AUDIO_DURATION_SEC", "300"))
    CONVERT_AUDIO_QUALITY: str = os.getenv("CONVERT_AUDIO_QUALITY", "high")

    # ========== Ограничения ==========
    MAX_CONCURRENT_TASKS: int = int(os.getenv("MAX_CONCURRENT_TASKS", "3"))
    TASK_TIMEOUT_SEC: int = int(os.getenv("TASK_TIMEOUT_SEC", "300"))

    # ========== Разрешённые пользователи ==========
    _allowed_users: List[int] = []

    @classmethod
    def _load_allowed_users(cls) -> None:
        """Загрузка списка разрешённых пользователей."""
        config_file = Path(__file__).parent / "config" / "allowed_users.json"
        try:
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cls._allowed_users = data.get("allowed_users", [])
                print(f"[OK] Загружено {len(cls._allowed_users)} разрешённых пользователей")
            else:
                cls._allowed_users = []
                print(f"[WARNING] Файл {config_file} не найден, доступ разрешён всем")
        except Exception as e:
            print(f"[ERROR] Ошибка загрузки allowed_users.json: {e}")
            cls._allowed_users = []

    @classmethod
    def is_user_allowed(cls, user_id: int) -> bool:
        """Проверка доступа пользователя."""
        # Если список пуст - доступ разрешён всем
        if not cls._allowed_users:
            return True
        return user_id in cls._allowed_users

    @classmethod
    def validate(cls) -> None:
        """Валидация конфигурации."""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env файле")

        # Загружаем список разрешённых пользователей
        cls._load_allowed_users()

        # Создаем необходимые директории
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)

        # Валидация устройства
        if cls.GIGAAM_DEVICE not in ("auto", "cuda", "cpu"):
            raise ValueError(f"Неверное значение GIGAAM_DEVICE: {cls.GIGAAM_DEVICE}")

    @classmethod
    def get_device(cls) -> str:
        """Получить устройство для модели."""
        import torch

        if cls.GIGAAM_DEVICE == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return cls.GIGAAM_DEVICE
