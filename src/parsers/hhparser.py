import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("JSONParser")
last_published_date = None

# Функция для получения вакансий за последний день
def fetch_vacancies(HH_URL):
    global last_published_date
    # Рассчитываем дату за последний день в формате ISO 8601
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    logger.info(f'yesterday: {yesterday}')
    params = {
        "text": "frontend",  # Поиск всех вакансий
        "search_field": "name",  # Искать только по названию вакансии
        "schedule": "remote",  # Только удалёнка
        "date_from": yesterday,  # Дата начала поиска
        "page": 0,  # Начальная страница
        "per_page": 100,  # Максимальное количество на страницу
    }

    vacancies = []
    new_last_published_date = last_published_date
    while True:
        try:
            req = requests.Request('GET', HH_URL, params=params)
            prepared = req.prepare()
            logger.info(f'Запрос ленты: {prepared.url}')
            response = requests.get(HH_URL, params=params)
            logger.info(f'response: {response}')
            response.raise_for_status()
            
            # Debugging: Log the response content
            logger.debug(f'Response content: {response.content}')
            
            # Check if there are vacancies in the response
            data = response.json()
            if 'items' not in data or not data['items']:
                logger.info('No vacancies found in the response.')
                break
            
            # Process vacancies
            for item in data['items']:
                published_date = datetime.fromisoformat(item['published_at'])
                if new_last_published_date is None or published_date > new_last_published_date:
                    vacancies.append((item['name'], item['alternate_url']))
                    new_last_published_date = published_date
            
            # Check if there are more pages
            if params['page'] >= data['pages'] - 1:
                break
            params['page'] += 1
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе JSON {HH_URL}: {e}")
            break

    last_published_date = new_last_published_date
    logger.info(f'last_published_date: {last_published_date}')
    return vacancies