import logging
import os
from logging.handlers import RotatingFileHandler
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError
from constants import TELEGRAM_TOKEN, CHANNEL_ID
import random

# Настройка логирования
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logger = logging.getLogger(__name__)

# Настройка ротации логов
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "bot.log")
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)  # 5 MB на файл, 5 резервных копий
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
        handler  # Ротация логов в файл
    ]
)

# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN)

async def get_updates() -> None:
    """
    Асинхронно получает обновления от Telegram бота.
    """
    try:
        updates = await bot.get_updates()
        for update in updates:
            if update.message and update.message.chat:
                logger.info(f"Сообщение от чата: {update.message.chat.id}")
            else:
                logger.debug("Обновление не содержит сообщения или чата")
    except TelegramError as e:
        logger.error(f"Ошибка при получении обновлений: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении обновлений: {e}")

async def send_selfpromo() -> None:
    messages = [
        "🚀 *Looking for a remote frontend job?*\n\n"
        "We post fresh frontend positions daily from multiple trusted sources.\n\n"
        "👉 Subscribe now: @FrontendinRemote",

        "👨‍💻 *Tired of searching job boards?*\n\n"
        "Get hand-picked remote frontend jobs delivered right here.\n\n"
        "*Join the channel:* @FrontendinRemote",

        "📌 *Daily remote frontend jobs.*\n"
        "*Just jobs. No spam.*\n\n"
        "Follow: @FrontendinRemote",

        "🧑‍💻 *Hey frontend devs!*\n\n"
        "We collect remote jobs from Remote OK, Remotive, We Work Remotely, Hiring Cafe, and other trusted sources — so you don't have to\n\n"
        "Stay updated: @FrontendinRemote"
    ]
    try:
        message = random.choice(messages)
        response = await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        logger.info(f"Самореклама отправлена: {response.message_id}")
    except TelegramError as e:
        logger.error(f"Ошибка при отправке саморекламы: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при саморекламе: {e}")

async def send_message(message: str) -> None:
    """
    Асинхронно отправляет отформатированное сообщение в Telegram канал.
    
    :param message: Готовое сообщение в формате Markdown.
    """
    try:
        response = await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        logger.info(f"Сообщение отправлено в канал {CHANNEL_ID}: {response.message_id}")
    except TelegramError as e:
        logger.error(f"Ошибка Telegram при отправке сообщения: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при отправке сообщения: {e}")