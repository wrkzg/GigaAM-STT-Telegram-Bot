import os
import aiofiles
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FileService:
    """Сервис для работы с файлами."""
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def download_file(
        self,
        file_url: str,
        destination: Optional[Path] = None,
        bot_token: Optional[str] = None
    ) -> Path:
        """
        Скачивание файла по URL или telegram file_path.

        Args:
            file_url: URL файла или file_path от Telegram
            destination: Путь для сохранения (если None - создается автоматически)
            bot_token: Токен бота (если file_url - это file_path от Telegram)

        Returns:
            Путь к скачанному файлу
        """
        import aiohttp

        # Если это file_path от Telegram (относительный путь), формируем полный URL
        if bot_token and not file_url.startswith('http'):
            file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_url}"

        if destination is None:
            # Генерируем имя файла на основе URL
            filename = file_url.split('/')[-1]
            destination = self.temp_dir / filename

        logger.debug(f"Скачивание файла: {file_url} → {destination}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    response.raise_for_status()

                    async with aiofiles.open(destination, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)

            logger.info(f"Файл скачан: {destination}")
            return destination

        except Exception as e:
            logger.error(f"Ошибка скачивания файла: {e}")
            raise
    
    async def save_bytes(
        self,
        data: bytes,
        filename: Path
    ) -> Path:
        """
        Сохранение байтов в файл.

        Args:
            data: Байты данных
            filename: Путь для сохранения

        Returns:
            Путь к сохраненному файлу
        """
        async with aiofiles.open(filename, 'wb') as f:
            await f.write(data)
        logger.debug(f"Байты сохранены: {filename}")
        return filename
    
    async def delete_file(self, file_path: Path) -> bool:
        """
        Удаление файла.
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            True если файл успешно удален
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Файл удален: {file_path}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Ошибка удаления файла {file_path}: {e}")
            return False
    
    def generate_temp_path(self, prefix: str = "temp", extension: str = "tmp") -> Path:
        """
        Генерация пути к временному файлу.
        
        Args:
            prefix: Префикс имени
            extension: Расширение файла
        
        Returns:
            Путь к временному файлу
        """
        import random
        import string
        
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        filename = f"{prefix}_{random_str}.{extension}"
        return self.temp_dir / filename
