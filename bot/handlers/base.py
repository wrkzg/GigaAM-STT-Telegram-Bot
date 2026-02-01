import logging
from typing import Optional

from bot.config import Config

logger = logging.getLogger(__name__)


class BaseHandler:
    """Базовый класс для обработчиков."""

    def __init__(self, audio_service, transcribe_service, logger=None):
        self.audio_service = audio_service
        self.transcribe_service = transcribe_service
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def check_access(self, user_id: int) -> bool:
        """Проверка доступа пользователя."""
        return Config.is_user_allowed(user_id)

    async def process(
        self,
        update,
        context
    ) -> Optional[str]:
        """
        Обработка сообщения.

        Args:
            update: Объект обновления Telegram
            context: Контекст бота

        Returns:
            Текст ответа или None
        """
        raise NotImplementedError("Метод process должен быть переопределен")
