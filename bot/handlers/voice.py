from telegram import Update
from telegram.ext import ContextTypes
import logging
from datetime import datetime

from .base import BaseHandler
from bot.models.audio import TranscriptionResult

logger = logging.getLogger(__name__)


class VoiceHandler(BaseHandler):
    """Обработчик голосовых сообщений."""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка голосового сообщения."""
        user_id = update.effective_user.id
        message_id = update.message.message_id

        # Проверка доступа
        if not self.check_access(user_id):
            logger.warning(f"Доступ запрещён: user_id={user_id}")
            return

        logger.info(f"Получено голосовое сообщение: user_id={user_id}, msg_id={message_id}")
        
        # Отправляем уведомление о начале обработки
        status_message = await update.message.reply_text("⏳ Обрабатываю голосовое сообщение...")

        wav_path = None
        voice_path = None
        try:
            # Получаем файл
            voice_file = await update.message.voice.get_file()

            # Скачиваем файл
            from bot.services.file_service import FileService
            file_service = FileService(self.audio_service.file_service.temp_dir)

            voice_path = await file_service.download_file(voice_file.file_path)

            # Читаем байты и сразу удаляем исходный файл
            voice_bytes = voice_path.read_bytes()
            await file_service.delete_file(voice_path)
            voice_path = None

            # Подготавливаем аудио
            wav_path, duration = await self.audio_service.prepare_voice_message(
                voice_bytes,
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

            # Формируем ответ
            if isinstance(result, TranscriptionResult):
                if result.is_success:
                    response_text = (
                        f"📝 *Распознанный текст:*\n\n"
                        f"{result.text}\n\n"
                        f"⏱ Время обработки: {result.processing_time_sec:.2f}с"
                    )
                else:
                    response_text = f"❌ Ошибка распознавания: {result.error}"
            else:
                # LongTranscriptionResult
                response_text = "📝 *Распознанный текст:*\n\n"
                for utterance in result.utterances:
                    response_text += f"{utterance}\n"
                response_text += f"\n⏱ Общее время: {result.total_duration:.1f}с"
            
            await status_message.edit_text(response_text, parse_mode="Markdown")
            logger.info(f"Транскрибация успешно завершена: user_id={user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка обработки голосового сообщения: {e}", exc_info=True)
            await status_message.edit_text(
                f"❌ Произошла ошибка при обработке: {str(e)}"
            )
        finally:
            # Гарантированная очистка временных файлов
            if voice_path is not None:
                await file_service.delete_file(voice_path)
            if wav_path is not None:
                await self.audio_service.cleanup(wav_path)
