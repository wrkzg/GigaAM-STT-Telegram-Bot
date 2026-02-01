from telegram import Update
from telegram.ext import ContextTypes
import logging

from .base import BaseHandler

logger = logging.getLogger(__name__)

AUDIO_MIME_TYPES = {
    'audio/mpeg',      # mp3
    'audio/mp3',       # mp3 (alternative)
    'audio/wav',       # wav
    'audio/wave',      # wav (alternative)
    'audio/x-wav',     # wav (alternative)
    'audio/ogg',       # ogg
    'audio/x-m4a',     # m4a
    'audio/mp4',       # m4a/aac
    'audio/aac',       # aac
    'audio/flac',      # flac
    'audio/x-flac',    # flac (alternative)
    'audio/x-wma',     # wma
}

AUDIO_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.m4a', '.flac', '.aac', '.wma'}

VIDEO_MIME_TYPES = {
    'video/mp4',       # mp4
    'video/quicktime', # mov
    'video/x-msvideo', # avi
    'video/x-matroska',# mkv
    'video/webm',      # webm
}

VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}


class DocumentHandler(BaseHandler):
    """Обработчик документов (включая аудио и видео, отправленные как документы)."""

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка документа."""
        user_id = update.effective_user.id
        message_id = update.message.message_id

        # Проверка доступа
        if not self.check_access(user_id):
            return

        document = update.message.document
        file_name = document.file_name if document.file_name else "document"
        mime_type = document.mime_type

        # Проверяем, является ли документ аудиофайлом
        is_audio = (
            mime_type in AUDIO_MIME_TYPES or
            any(file_name.lower().endswith(ext) for ext in AUDIO_EXTENSIONS)
        )

        # Проверяем, является ли документ видеофайлом
        is_video = (
            mime_type in VIDEO_MIME_TYPES or
            any(file_name.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)
        )

        if not is_audio and not is_video:
            logger.info(
                f"Пропуск не-аудио/видео документа: user_id={user_id}, "
                f"name={file_name}, mime={mime_type}"
            )
            # Не отвечаем на другие типы документов
            return

        file_size = document.file_size
        file_type = "видео" if is_video else "аудио"

        logger.info(
            f"Получен {file_type}-документ: user_id={user_id}, msg_id={message_id}, "
            f"name={file_name}, size={file_size}, mime={mime_type}"
        )

        # Отправляем уведомление
        status_message = await update.message.reply_text(
            f"⏳ Обрабатываю {file_type}файл: {file_name}..."
        )

        wav_path = None

        try:
            # Получаем файл
            file = await document.get_file()

            # Скачиваем
            from bot.services.file_service import FileService
            from bot.config import Config
            file_service = FileService(self.audio_service.file_service.temp_dir)

            doc_path = await file_service.download_file(
                file.file_path,
                bot_token=Config.TELEGRAM_BOT_TOKEN
            )

            # Подготавливаем аудио (для видео извлекаем аудиодорожку)
            if is_video:
                wav_path, duration = await self.audio_service.prepare_video_note(
                    doc_path,
                    user_id,
                    message_id
                )
            else:
                wav_path, duration = await self.audio_service.prepare_audio_file(
                    doc_path,
                    user_id,
                    message_id
                )

            # Обновляем статус
            await status_message.edit_text(f"⏳ Распознаю речь ({duration:.1f}с)...")

            # Транскрибация
            from bot.config import Config
            result = await self.transcribe_service.transcribe_auto(
                wav_path,
                hf_token=Config.HF_TOKEN
            )

            # Ответ
            from bot.models.audio import TranscriptionResult

            if isinstance(result, TranscriptionResult):
                if result.is_success:
                    response_text = (
                        f"📝 *Распознанный текст ({file_name}):*\n\n"
                        f"{result.text}\n\n"
                        f"⏱ Время обработки: {result.processing_time_sec:.2f}с"
                    )
                else:
                    response_text = f"❌ Ошибка распознавания: {result.error}"
            else:
                response_text = "📝 *Распознанный текст:*\n\n"
                for utterance in result.utterances:
                    response_text += f"{utterance}\n"

            await status_message.edit_text(response_text, parse_mode="Markdown")
            logger.info(f"Транскрибация {file_type}-документа завершена: user_id={user_id}")

        except Exception as e:
            logger.error(f"Ошибка обработки {file_type}-документа: {e}", exc_info=True)
            await status_message.edit_text(
                f"❌ Произошла ошибка: {str(e)}"
            )
        finally:
            # Гарантированная очистка временных файлов
            if wav_path is not None:
                await self.audio_service.cleanup(wav_path)
