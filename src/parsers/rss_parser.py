import feedparser
import logging 
import os
import requests


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
last_published_date={}

def get_latest_vacancies(RSS_FEEDS,KEYWORDS):
    global last_published_date
    new_vacancies=[]

    rss_feeds= RSS_FEEDS.split(',')
    keywords = KEYWORDS.split(',')
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
        
            if published_date and (rss_url not in last_published_date or published_date > last_published_date[rss_url]):
                if any(keyword in (entry.title.lower() + entry.description.lower()) for keyword in keywords):
                    new_vacancies.append((entry.title, entry.link))
    
    # Обновляем последнюю дату публикации
        if feed.entries:
            last_published_date[rss_url] = max(entry.get("published_parsed") for entry in feed.entries if entry.get("published_parsed"))
    
    return new_vacancies
