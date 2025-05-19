import requests
import logging
from datetime import datetime
from src.utils.lastpublished import save_last_published_date
from src.utils.dateutils import to_utc, is_newer, update_last_published_date

logger = logging.getLogger("JSONParser")

# Получение JSON-вакансий
def get_working_nomads_vacancy(json_feed, KEYWORDS,last_published_date,LAST_PUBLISHED_FILE):
    try:
        logger.info(f'Запрос ленты: {json_feed}')
        response = requests.get(json_feed, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе JSON {json_feed}: {e}")
        return []

    data = response.json()
    vacancies = []

    if isinstance(data, dict):
        items = data.get("vacancies", [])
    elif isinstance(data, list):
        items = data
    else:
        logger.error(f"Неожиданный формат данных JSON: {type(data)}")
        return []

    new_last_published_date = last_published_date
    keywords = KEYWORDS.split(',')
    logger.info(f'Ключевые слова: {keywords}')
    
    for item in items:
        title = item.get('title', 'Без названия')
        tags = item.get('tags', [])
        link = item.get('url', '#')
        date_published_str = item.get('pub_date', '')
        date_published = datetime.fromisoformat(date_published_str) if date_published_str else None
         # Удаляем информацию о временной зоне из date_published
        if date_published:
            date_published = to_utc(date_published)

        
        if is_newer(date_published, last_published_date):
            if any(keyword.lower() in (title.lower() + " ".join(tags).lower()) for keyword in keywords):
                vacancies.append((title, link))
                logger.info(f'Добавлена вакансия: {title}, {link}')
                if new_last_published_date is None or date_published > new_last_published_date:
                    new_last_published_date = update_last_published_date(new_last_published_date, date_published)

    if new_last_published_date:
        last_published_date = new_last_published_date
        save_last_published_date(new_last_published_date,LAST_PUBLISHED_FILE)

    return vacancies