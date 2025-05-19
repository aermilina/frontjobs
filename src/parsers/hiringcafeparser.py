import requests
import logging
from datetime import datetime
from src.utils.lastpublished import save_last_published_date
from src.utils.dateutils import to_utc, is_newer, update_last_published_date

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_hiring_cafe_vacancies(api_url, KEYWORDS, last_published_date,LAST_PUBLISHED_FILE):
    """
    Получение вакансий с Hiring Cafe.
    :param api_url: URL API для получения вакансий.
    :param KEYWORDS: Ключевые слова для фильтрации вакансий.
    :param last_published_date: Последняя обработанная дата публикации.
    :return: Список новых вакансий.
    """
    headers = {
        'Content-Type': 'application/json',
    }

    payload = {
        "size": 20,  # Количество вакансий на странице
        "page": 0,   # Номер страницы
        "searchState": {
            "searchQuery": KEYWORDS,
            "sortBy": "date"  # Сортировка по дате
        }
    }

    try:
        logger.info(f'Запрос вакансий с {api_url}')
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Ответ API: {response}")  # Логируем полный ответ API
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе API {api_url}: {e}")
        return []

    data = response.json()
    logger.info(f"Ответ API: {data}")
    vacancies = []

    if not isinstance(data, dict) or 'results' not in data:
        logger.error(f"Неожиданный формат данных API: {type(data)}")
        return []

    # Преобразуем last_published_date в UTC, если это необходимо
    if last_published_date:
        last_published_date = to_utc(last_published_date)

    new_last_published_date = last_published_date
    results = data.get('results', [])

    for item in results:
        job_info = item.get('job_information', {})
        processed_data = item.get('v5_processed_job_data', {})
        title = job_info.get('title', 'Без названия')
        link = item.get('apply_url', '#')
        workplace_type = processed_data.get('workplace_type', '').lower()  # Тип работы (например, remote)
        date_published_str = processed_data.get('estimated_publish_date_millis', '')

        # Преобразуем дату публикации в UTC
        date_published = None
        if date_published_str:
            date_published = to_utc(datetime.utcfromtimestamp(int(date_published_str) / 1000))

        # Проверяем, новее ли дата и является ли вакансия удалённой
        if date_published and is_newer(date_published, last_published_date) and 'remote' in workplace_type:
            vacancies.append((title, link))
            logger.info(f'Добавлена вакансия: {title}, {link}')
            new_last_published_date = update_last_published_date(new_last_published_date, date_published)

    if new_last_published_date:
        save_last_published_date(new_last_published_date,LAST_PUBLISHED_FILE)

    return vacancies