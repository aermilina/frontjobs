import logging
import os
from telegram import Bot
from telegram.constants import ParseMode
from constants import TELEGRAM_TOKEN, CHANNEL_ID

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Токен вашего бота
bot = Bot(token=TELEGRAM_TOKEN)


# Асинхронная функция для получения обновлений
async def get_updates():
    try:
        # Получаем обновления от бота
        updates = await bot.get_updates()
        for update in updates:
            if update.message:
            # Извлекаем chat_id
                user_chat_id = update.message.chat.id
                logger.info(f"Сообщение от чата: {user_chat_id}")  # Логируем chat_id
            else:
                logger.info("Обновление не содержит сообщения")
    except Exception as e:
        logger.error(f"Ошибка при получении обновлений: {e}")

# Асинхронная функция для отправки сообщений в канал
async def send_message(title, link):
    try:
        # Отправка сообщения в канал
        message = f"{title}\n\n[Link to apply]({link})"
        response = await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode=ParseMode.MARKDOWN,disable_web_page_preview=True)
        logger.info(f"Сообщение отправлено в канал: {CHANNEL_ID}")
        logger.info(f"Ответ от Telegram: {response}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
