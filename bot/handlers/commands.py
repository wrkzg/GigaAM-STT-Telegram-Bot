from telegram import Update
from telegram.ext import ContextTypes
import logging
from pathlib import Path

from .base import BaseHandler
from bot.config import Config

logger = logging.getLogger(__name__)


class CommandHandler(BaseHandler):
    """Обработчик команд бота."""

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Команда /start."""
        user_id = update.effective_user.id

        # Проверка доступа
        if not self.check_access(user_id):
            return

        welcome_text = (
            "👋 Привет! Я бот для распознавания речи.\n\n"
            "Отправьте мне:\n"
            "🎤 Голосовое сообщение\n"
            "🎵 Аудиофайл\n"
            "🎬 Видеосообщение (кружочек)\n\n"
            "И я распознаю текст!\n\n"
            "Доступные команды:\n"
            "/start - Начать работу\n"
            "/help - Справка\n"
            "/about - О боте\n"
            "/cleanup - Очистить временные файлы"
        )

        await update.message.reply_text(welcome_text)
        logger.info(f"Команда /start от пользователя {update.effective_user.id}")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Команда /help."""
        user_id = update.effective_user.id

        # Проверка доступа
        if not self.check_access(user_id):
            return

        help_text = (
            "📖 *Справка по использованию*\n\n"
            "Я могу распознавать речь из:\n"
            "• Голосовых сообщений\n"
            "• Аудиофайлов (любой формат)\n"
            "• Видеосообщений (кружочки)\n\n"
            "*Ограничения:*\n"
            "• Максимальный размер файла: 100 МБ\n"
            "• Максимальная длительность: 5 минут\n"
            "• Форматы аудио: WAV, MP3, OGG, M4A, FLAC, AAC, WMA\n"
            "• Форматы видео: MP4, MOV, AVI, MKV, WEBM\n\n"
            "*Примечание:* Длинные аудио автоматически разбиваются на части."
        )

        await update.message.reply_text(help_text, parse_mode="Markdown")
        logger.info(f"Команда /help от пользователя {update.effective_user.id}")

    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Команда /about."""
        user_id = update.effective_user.id

        # Проверка доступа
        if not self.check_access(user_id):
            return

        from bot.config import Config

        device = Config.get_device()

        about_text = (
            "ℹ️ *О боте*\n\n"
            f"Модель: `{Config.GIGAAM_MODEL}`\n"
            f"Устройство: {device.upper()}\n"
            "Библиотека: GigaAM (ai-sage/GigaAM-v3)\n\n"
            "Бот использует современную модель "
            "распознавания речи на русском языке "
            "от команды Salute."
        )

        await update.message.reply_text(about_text, parse_mode="Markdown")
        logger.info(f"Команда /about от пользователя {update.effective_user.id}")

    async def unknown_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка нераспознаванных типов сообщений."""
        user_id = update.effective_user.id

        # Проверка доступа
        if not self.check_access(user_id):
            return  # Игнорируем сообщения от неразрешённых пользователей

        help_text = (
            "❓ Я понимаю только:\n\n"
            "🎤 Голосовые сообщения\n"
            "🎵 Аудиофайлы\n"
            "🎬 Видеосообщения (кружочки)\n\n"
            "Отправьте /help для подробной справки."
        )

        await update.message.reply_text(help_text)
        logger.info(f"Неизвестный тип сообщения от пользователя {update.effective_user.id}")

    async def cleanup(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Команда /cleanup - очистка временных файлов."""
        user_id = update.effective_user.id

        # Проверка доступа
        if not self.check_access(user_id):
            return

        from bot.utils.helpers import cleanup_old_files

        logger.info(f"Команда /cleanup от пользователя {user_id}")

        # Очищаем все временные файлы (независимо от возраста)
        temp_dir = Config.TEMP_DIR
        deleted_count = 0

        if temp_dir.exists():
            try:
                for file_path in temp_dir.glob("*"):
                    if file_path.is_file():
                        try:
                            file_path.unlink()
                            deleted_count += 1
                        except Exception as e:
                            logger.warning(f"Ошибка удаления {file_path}: {e}")
            except Exception as e:
                logger.error(f"Ошибка очистки temp директории: {e}")

        response_text = (
            f"🧹 Очистка завершена\n\n"
            f"Удалено файлов: {deleted_count}\n"
            f"Директория: {temp_dir}"
        )

        await update.message.reply_text(response_text)
        logger.info(f"Очистка завершена: удалено {deleted_count} файлов")
