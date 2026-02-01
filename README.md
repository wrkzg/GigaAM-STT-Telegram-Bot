# STT Bot - Портативная версия

Telegram бот для распознавания русской речи с использованием модели GigaAM.

## Поддерживаемые платформы

- ✅ Windows 10/11
- ✅ Linux (Ubuntu, Debian, Fedora, Arch, и др.)

> **Примечание:** Бот протестирован на Windows 11. На других платформах работа может отличаться.

## Требования

### Windows
- Интернет-соединение (для первичной установки)
- Python 3.10/3.11 (установится автоматически)
- FFmpeg (установите, если не в системе)

### Linux
- Python 3.10/3.11
- FFmpeg
- pip, venv
- Интернет-соединение

## Установка FFmpeg

### Windows
Скачайте FFmpeg и добавьте в PATH:
1. Перейдите на https://www.gyan.dev/ffmpeg/builds/
2. Скачайте "release builds"
3. Распакуйте и добавьте `bin` в PATH

Или используйте установщик: https://ffmpeg.org/download.html#build-windows

### Linux
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Fedora/RHEL/CentOS
sudo dnf install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

## Быстрый старт

### Windows
1. Запустите `install.bat` — он установит Python и все зависимости
2. Откройте `.env` и укажите `TELEGRAM_BOT_TOKEN` (получить у [@BotFather](https://t.me/BotFather))
3. Запустите `run.bat`

### Linux
1. Установите зависимости:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install -y python3.10 python3.10-venv python3.10-dev ffmpeg

   # Fedora/RHEL/CentOS
   sudo dnf install python3.10 ffmpeg

   # Arch Linux
   sudo pacman -S python310 ffmpeg
   ```

2. Запустите `./install.sh`
3. Откройте `.env` и укажите `TELEGRAM_BOT_TOKEN`
4. Запустите `./run.sh`

**Важно:** Установщик автоматически найдёт Python 3.10/3.11 или установит его локально в папку проекта (Windows).

## Что делает установщик

### Windows
- **Ищет Python 3.10/3.11** в системе:
  - `%LOCALAPPDATA%\Programs\Python\Python*`
  - `C:\Program Files\Python*`
  - Локальная установка `portable/python310/`
- **Если не найден** — устанавливает Python 3.10.11 **локально в папку проекта** (~30MB)
- **Создаёт виртуальное окружение** (.venv)
- **Устанавливает зависимости**: PyTorch, GigaAM, python-telegram-bot
- **Создаёт .env**

### Linux
- **Проверяет Python** — требует 3.10 или 3.11
- **Проверяет FFmpeg** — использует системный
- **Создаёт виртуальное окружение** (.venv)
- **Устанавливает зависимости**
- **Создаёт .env**

## Настройка

Файл `.env` создастся автоматически при запуске установщика:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_здесь
GIGAAM_MODEL=rnnt
GIGAAM_DEVICE=auto  # auto, cuda, cpu
HF_TOKEN=
LOG_LEVEL=INFO
LOG_DIR=logs
TEMP_DIR=temp
MAX_FILE_SIZE_MB=100
MAX_AUDIO_DURATION_SEC=300
```

**Получить токен:** Напишите `/newbot` [@BotFather](https://t.me/BotFather) в Telegram

## Управление доступом

Для ограничения доступа к боту отредактируйте `bot/config/allowed_users.json`:

```json
{
  "allowed_users": [123456789]
}
```

- Если список пуст — доступ разрешён всем
- Узнать свой ID: [@userinfobot](https://t.me/userinfobot)

## Возможности бота

| Тип файла | Поддержка |
|-----------|-----------|
| Голосовые сообщения | ✅ |
| Аудиофайлы (MP3, WAV, OGG, M4A, FLAC, AAC, WMA) | ✅ |
| Видеосообщения (кружочки) | ✅ |
| Видеофайлы (MP4, MOV, AVI, MKV, WEBM) | ✅ |
| Документы (аудио/видео) | ✅ |

- Автоматическое извлечение аудио из видеофайлов
- Автоматическое разбиение длинных аудио на части
- Ограничение доступа по списку пользователей
- Очистка временных файлов после обработки

## Команды бота

- `/start` — Начать работу
- `/help` — Справка
- `/about` — О боте

## Ограничения

- Максимальный размер файла: 100 МБ
- Максимальная длительность: 5 минут

## Структура

```
portable/
├── install.bat           # Установщик Windows
├── install.ps1           # PowerShell установщик
├── install.sh            # Установщик Linux
├── run.bat               # Запуск Windows
├── run.sh                # Запуск Linux
├── package.bat           # Упаковка в архивы
├── .env.example          # Шаблон конфигурации
├── requirements.txt      # Зависимости
├── bot/                  # Код бота
│   ├── main.py          # Точка входа
│   ├── config.py        # Конфигурация
│   ├── config/          # Конфиг-файлы
│   ├── handlers/        # Обработчики
│   ├── services/        # Сервисы
│   ├── models/          # Модели данных
│   └── utils/           # Утилиты
├── python310/           # Локальная установка Python (Windows)
├── .venv/               # Виртуальное окружение
├── logs/                # Логи
└── temp/                # Временные файлы
```

## Первичный запуск

При первом запуске:
1. Модель GigaAM автоматически загрузится из интернета (~100 МБ)
2. Кэш модели сохранится в `~/.cache/gigaam/`
3. Последующие запуски будут использовать кэшированную модель

## Troubleshooting

### Windows

#### "Python не найден"
- Запустите `install.bat` — он установит Python автоматически

#### "Не удалось скачать Python"
Если автоматическая загрузка не работает, скачайте Python вручную:

**Основной источник:**
```
https://www.python.org/downloads/release/python-31011/
Файл: python-3.10.11-amd64.exe
```

**Альтернативные зеркала:**
```
https://ftp.nluug.nl/pub/python/3.10.11/python-3.10.11-amd64.exe
https://ftp.pasteur.fr/pub/python/3.10.11/python-3.10.11-amd64.exe
```

**После скачивания:**
```batch
python-3.10.11-amd64.exe /quiet InstallAllUsers=0 PrependPath=0 Include_test=0 TargetDir=python310
install.bat
```

### Linux

#### "Python 3.10/3.11 не найден"
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-dev

# Fedora/RHEL/CentOS
sudo dnf install python3.10

# Arch Linux
yay -S python310
```

#### "ffmpeg не найден"
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Fedora/RHEL/CentOS
sudo dnf install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

### Общие проблемы

#### "TELEGRAM_BOT_TOKEN не установлен"
- Откройте `.env` и укажите токен от [@BotFather](https://t.me/BotFather)

#### Ошибки при установке зависимостей
- Проверьте подключение к интернету
- Запустите установщик повторно

#### Ошибки при загрузке модели
- Проверьте подключение к интернету
- Модель загружается при первом запуске (~100 МБ)
- Убедитесь что нет firewall/proxy

## Лицензия

Используемые библиотеки:
- [GigaAM](https://huggingface.co/ai-sage) — модель распознавания речи от Salute
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) — Telegram Bot API
- [PyTorch](https://pytorch.org/) — машинное обучение
