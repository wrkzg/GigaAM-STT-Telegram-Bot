import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.config import Config
from bot.services import FileService, AudioService, TranscribeService
from bot.handlers import VoiceHandler, AudioHandler, VideoNoteHandler, VideoHandler, DocumentHandler, CommandHandler as CmdHandler
from bot.utils import setup_logger, periodic_cleanup


# Настройка логирования
logger = setup_logger(
    name="bot",
    log_dir=Config.LOG_DIR,
    level=Config.LOG_LEVEL,
    retention_days=Config.LOG_RETENTION_DAYS
)


class TelegramGigaAMBot:
    """Главный класс бота."""
    
    def __init__(self):
        # Валидируем конфигурацию
        Config.validate()

        # Проверяем наличие ffmpeg
        self._check_ffmpeg()

        # Инициализируем сервисы
        self._initialize_services()

    def _check_ffmpeg(self):
        """Проверка наличия ffmpeg."""
        import shutil
        import sys

        # Сначала проверяем портативную версию в папке tools/
        project_root = Path(__file__).parent.parent.resolve()
        tools_dir = project_root / "tools"

        # Проверяем подпапки для Windows
        if sys.platform == "win32":
            ffmpeg_paths = [
                tools_dir / "ffmpeg.exe",
                tools_dir / "windows" / "ffmpeg.exe",
            ]
            ffprobe_paths = [
                tools_dir / "ffprobe.exe",
                tools_dir / "windows" / "ffprobe.exe",
            ]
        else:
            ffmpeg_paths = [
                tools_dir / "ffmpeg",
                tools_dir / "linux" / "ffmpeg",
            ]
            ffprobe_paths = [
                tools_dir / "ffprobe",
                tools_dir / "linux" / "ffprobe",
            ]

        ffmpeg_portable = None
        ffprobe_portable = None

        for path in ffmpeg_paths:
            if path.exists():
                ffmpeg_portable = path
                break

        for path in ffprobe_paths:
            if path.exists():
                ffprobe_portable = path
                break

        if ffmpeg_portable:
            # Добавляем папку с бинарниками в PATH
            bin_dir = ffmpeg_portable.parent
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
            # На Linux/macOS делаем бинарники исполняемыми
            if sys.platform != "win32":
                try:
                    os.chmod(ffmpeg_portable, 0o755)
                    if ffprobe_portable:
                        os.chmod(ffprobe_portable, 0o755)
                except Exception:
                    pass
            logger.info(f"[OK] Используется ffmpeg из {bin_dir}")
        else:
            # Проверяем ffmpeg в системном PATH
            ffmpeg_path = shutil.which("ffmpeg")
            if not ffmpeg_path:
                logger.error(
                    "ffmpeg не найден! Установите ffmpeg или поместите "
                    "бинарники ffmpeg и ffprobe в папку tools/. "
                    "Подробнее: docs/02-environment-setup.md"
                )
                raise RuntimeError("ffmpeg не найден")

            logger.info(f"[OK] ffmpeg найден: {ffmpeg_path}")

    def _initialize_services(self):
        """Инициализация сервисов бота."""
        # Инициализируем сервисы
        self.file_service = FileService(Config.TEMP_DIR)
        self.audio_service = AudioService(
            self.file_service,
            Config.TEMP_DIR,
            Config.MAX_FILE_SIZE_MB
        )
        self.transcribe_service = TranscribeService(
            model_name=Config.GIGAAM_MODEL,
            device=Config.get_device()
        )
    
        # Инициализируем обработчики
        self.command_handler = CmdHandler(
            self.audio_service,
            self.transcribe_service
        )
        self.voice_handler = VoiceHandler(
            self.audio_service,
            self.transcribe_service
        )
        self.audio_handler = AudioHandler(
            self.audio_service,
            self.transcribe_service
        )
        self.video_note_handler = VideoNoteHandler(
            self.audio_service,
            self.transcribe_service
        )
        self.video_handler = VideoHandler(
            self.audio_service,
            self.transcribe_service
        )
        self.document_handler = DocumentHandler(
            self.audio_service,
            self.transcribe_service
        )
        
        # Создаем приложение
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Регистрируем обработчики
        self._register_handlers()
        
        self._cleanup_task = None
    
    def _register_handlers(self):
        """Регистрация обработчиков команд."""
        # Команды
        self.application.add_handler(CommandHandler("start", self.command_handler.start))
        self.application.add_handler(CommandHandler("help", self.command_handler.help))
        self.application.add_handler(CommandHandler("about", self.command_handler.about))
        self.application.add_handler(CommandHandler("cleanup", self.command_handler.cleanup))
        
        # Голосовые сообщения
        self.application.add_handler(
            MessageHandler(filters.VOICE, self.voice_handler.handle)
        )
        
        # Аудиофайлы
        self.application.add_handler(
            MessageHandler(filters.AUDIO, self.audio_handler.handle)
        )
        
        # Видеосообщения
        self.application.add_handler(
            MessageHandler(filters.VIDEO_NOTE, self.video_note_handler.handle)
        )

        # Видеофайлы (отправленные как видео, не документы)
        self.application.add_handler(
            MessageHandler(filters.VIDEO, self.video_handler.handle)
        )

        # Документы (включая аудиофайлы, отправленные как документы)
        self.application.add_handler(
            MessageHandler(filters.Document.ALL, self.document_handler.handle)
        )

        # Все остальные текстовые сообщения (не команды)
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.command_handler.unknown_message
            )
        )

        # Debug: логируем все обновления
        async def debug_handler(update, context):
            if update.message:
                msg = update.message
                logger.info(f"Message from {msg.from_user.id}: {msg.message_id}")
                logger.info(f"Content: {list(msg.to_dict().keys())}")
                if msg.document:
                    logger.info(f"Document: {msg.document.file_name}, mime={msg.document.mime_type}")
                elif msg.video:
                    logger.info(f"Video: duration={msg.video.duration}")
                elif msg.video_note:
                    logger.info(f"Video note: duration={msg.video_note.duration}")
                elif msg.voice:
                    logger.info(f"Voice: duration={msg.voice.duration}")
                elif msg.audio:
                    logger.info(f"Audio: {msg.audio.file_name}")

        self.application.add_handler(MessageHandler(filters.ALL, debug_handler), group=-1)
    
    async def _startup_cleanup(self):
        """Очистка старых файлов при запуске."""
        from bot.utils.helpers import cleanup_old_files, cleanup_old_logs
        logger.info("Очистка старых временных файлов...")
        deleted = cleanup_old_files(Config.TEMP_DIR, max_age_hours=1)
        if deleted > 0:
            logger.info(f"Удалено {deleted} старых файлов из temp/")
        await cleanup_old_logs(Config.LOG_DIR, Config.LOG_RETENTION_DAYS)

    async def start_cleanup_task(self):
        """Запуск задачи периодической очистки."""
        self._cleanup_task = asyncio.create_task(
            periodic_cleanup(
                temp_dir=Config.TEMP_DIR,
                log_dir=Config.LOG_DIR,
                retention_days=Config.LOG_RETENTION_DAYS,
                check_interval=3600  # 1 час
            )
        )
    
    async def stop_cleanup_task(self):
        """Остановка задачи периодической очистки."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    def setup_signal_handlers(self):
        """Настройка обработчиков сигналов."""
        def signal_handler(signum, frame):
            logger.info(f"Получен сигнал {signum}, остановка...")
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _post_init(self, application):
        """Действия после инициализации приложения."""
        await self._startup_cleanup()
        await self.start_cleanup_task()

    def run(self):
        """Запуск бота."""
        logger.info("=" * 50)
        logger.info("Запуск Telegram GigaAM бота")
        logger.info(f"Модель: {Config.GIGAAM_MODEL}")
        logger.info(f"Устройство: {Config.get_device()}")
        logger.info(f"Лог-директория: {Config.LOG_DIR}")
        logger.info(f"Временная директория: {Config.TEMP_DIR}")
        logger.info("=" * 50)

        self.setup_signal_handlers()

        # Регистрируем post_init хук
        self.application.post_init = self._post_init

        try:
            # Запускаем бота
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
            raise
        finally:
            asyncio.run(self.stop_cleanup_task())
    
    def stop(self):
        """Остановка бота."""
        logger.info("Остановка бота...")
        self.application.stop_running()


def main():
    """Точка входа."""
    try:
        bot = TelegramGigaAMBot()
        bot.run()
    except Exception as e:
        logger.critical(f"Ошибка запуска бота: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
