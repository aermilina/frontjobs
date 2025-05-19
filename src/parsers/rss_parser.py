import feedparser
import logging 
import os
import requests
from datetime import datetime
from src.utils.lastpublished import  save_last_published_date
from src.utils.dateutils import to_utc, is_newer, update_last_published_date


# Путь для логов
log_dir = "logs"
log_file = os.path.join(log_dir, "rss_requests.log")

# Создание папки для логов, если она не существует
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
        logging.FileHandler(log_file)  # Логи в файл
    ]
)

logger = logging.getLogger("RSSParser")


def get_latest_vacancies(RSS_FEEDS,KEYWORDS,last_published_date,LAST_PUBLISHED_FILE):
    new_vacancies=[]

    rss_feeds= RSS_FEEDS.split(',')
    keywords = KEYWORDS.split(',')

    if last_published_date and last_published_date.tzinfo is None:
        last_published_date = to_utc(last_published_date)

    for rss_url in rss_feeds:
        logger.info(f'Запрос ленты: {rss_url}')
        response = requests.get(rss_url, verify=False)
        feed = feedparser.parse(response.text)
    
        if feed.bozo:
            logger.error(f"Ошибка при парсинге RSS: {feed.bozo_exception}")
            continue
    
        logger.info(f"Успешно получена RSS-лента: {rss_url}")

        for entry in feed.entries:
            published_date = entry.get("published_parsed", None)
            if published_date:
                published_date = to_utc(datetime(*published_date[:6])) 
        
            if published_date and is_newer(published_date, last_published_date):
                if any(keyword in (entry.title.lower() + entry.description.lower()) for keyword in keywords):
                    new_vacancies.append((entry.title, entry.link))
    
    # Обновляем последнюю дату публикации
        if feed.entries:
            latest_date = max(
                datetime(*entry.get("published_parsed")[:6]) for entry in feed.entries if entry.get("published_parsed")
            )
            last_published_date = update_last_published_date(last_published_date, latest_date)
            save_last_published_date(last_published_date,LAST_PUBLISHED_FILE)  # Сохраняем обновлённую дату

    return new_vacancies
