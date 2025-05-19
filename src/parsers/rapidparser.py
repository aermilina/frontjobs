import requests
import logging
from datetime import datetime
from src.utils.lastpublished import save_last_published_date
from src.utils.dateutils import to_utc, is_newer, update_last_published_date
from dateparser import parse
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)




def get_rapid_vacancies(rapidUrl, rapidHost, rapidKey, last_published_date,LAST_PUBLISHED_FILE):
    """
    Получение вакансий с Rapid API.
    :param api_url: URL API для получения вакансий.
    :param api_key: Ключ API для авторизации.
    :param query: Ключевые слова для поиска вакансий.
    :param location: Локация для поиска вакансий.
    :param last_published_date: Последняя обработанная дата публикации.
    :return: Список новых вакансий.
    """
    headers = {
        "x-rapidapi-key": rapidKey,
        "x-rapidapi-host": rapidHost
    }

    querystring = {
        "query": "frontend",
        "location": 'any',  # Поиск по всем локациям
        "remoteOnly": "true",  # Только удалённые вакансии
        "employmentTypes": "fulltime;parttime;intern;contractor",
        "datePosted": "today",  # Все вакансии
    }

    try:
        logger.info(f'Запрос вакансий с {rapidUrl}')
        response = requests.get(rapidUrl, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Ответ API (JSON): {data}")
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе API {rapidUrl}: {e}")
        return []
    except ValueError as e:
        logger.error(f"Ошибка при обработке JSON-ответа: {e}")
        return []

    vacancies = []

    if not isinstance(data, dict) or 'jobs' not in data:
        logger.error(f"Неожиданный формат данных API: {type(data)}")
        return []

    # Преобразуем last_published_date в UTC, если это необходимо
    if last_published_date:
        last_published_date = to_utc(last_published_date)

   
    new_last_published_date = last_published_date
    results = data.get('jobs', [])
    



    for item in results:
        title = item.get('title', 'Без названия')
        logger.info(f"Обработка вакансии: {title}")
        providers = item.get('jobProviders', [])
        logger.info(f"Обработка вакансии: {providers}")
        date_posted_str = item.get('datePosted', '')
        logger.info(f"date_posted_str: {date_posted_str}")
    

        # Преобразуем дату публикации в UTC
        if date_posted_str:
            try:
                parsed_date = parse(date_posted_str, settings={'TIMEZONE': 'UTC', 'TO_TIMEZONE': 'UTC'})
                logger.info(f"Дата публикации вакансии: {parsed_date}")
                if parsed_date:
                    date_published = to_utc(parsed_date)
                    logger.info(f"Дата публикации вакансии: {date_published}")
            except Exception as e:
                logger.warning(f"Ошибка при обработке даты: {date_posted_str}, {e}")


        # Проверяем, новее ли дата
        if date_published and is_newer(date_published, last_published_date):
            link = providers[0].get('url', '#') if providers else 'No link'
            vacancies.append((title,  link))
            logger.info(f'Добавлена вакансия: {title}, {link}')
            new_last_published_date = update_last_published_date(new_last_published_date, date_published)

    if new_last_published_date:
        save_last_published_date(new_last_published_date,LAST_PUBLISHED_FILE)

    return vacancies