from telegram import Update
from telegram.ext import ContextTypes
import logging

from .base import BaseHandler

logger = logging.getLogger(__name__)


class AudioHandler(BaseHandler):
    """Обработчик аудиофайлов."""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка аудиофайла."""
        user_id = update.effective_user.id
        message_id = update.message.message_id

        # Проверка доступа
        if not self.check_access(user_id):
            logger.warning(f"Доступ запрещён: user_id={user_id}")
            return

        audio_file = update.message.audio
        file_name = audio_file.file_name if audio_file.file_name else "audio"
        file_size = audio_file.file_size
        
        logger.info(
            f"Получен аудиофайл: user_id={user_id}, msg_id={message_id}, "
            f"name={file_name}, size={file_size}"
        )
        
        # Отправляем уведомление
        status_message = await update.message.reply_text(
            f"⏳ Обрабатываю аудиофайл: {file_name}..."
        )

        wav_path = None

        try:
            # Получаем файл
            file = await audio_file.get_file()
            
            # Скачиваем
            from bot.services.file_service import FileService
            from bot.config import Config
            file_service = FileService(self.audio_service.file_service.temp_dir)

            audio_path = await file_service.download_file(
                file.file_path,
                bot_token=Config.TELEGRAM_BOT_TOKEN
            )
            
            # Подготавливаем
            wav_path, duration = await self.audio_service.prepare_audio_file(
                audio_path,
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
            logger.info(f"Транскрибация аудиофайла завершена: user_id={user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка обработки аудиофайла: {e}", exc_info=True)
            await status_message.edit_text(
                f"❌ Произошла ошибка: {str(e)}"
            )
        finally:
            # Гарантированная очистка временных файлов
            if wav_path is not None:
                await self.audio_service.cleanup(wav_path)
