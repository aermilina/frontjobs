import aiohttp
import logging
import os
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
from dateparser import parse
from src.utils.lastpublished import save_last_published_date, load_last_published_date
from src.utils.dateutils import to_utc, is_newer, update_last_published_date
from src.parsers.base_parser import VacancyParser
from src.utils.cleandescription import cleandescription
from src.utils.normalizetags import normalize_tag
from src.utils.escapehtml import escape_html
from src.utils.normalizetags import normalize_tags
from src.utils.getflags import get_flag_emoji




# Настройка логирования
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class RapidParser(VacancyParser):
    def __init__(
        self,
        url: str,
        last_published_date: Optional[datetime],
        last_published_file: str,
        host: str = "",
        key: str = ""
    ):
        super().__init__(last_published_date, last_published_file)
        self.api_url = url
        self.host = host
        self.key = key

    async def fetch_vacancies(self) -> List[Tuple[str, str, Dict]]:
        """
        Получает вакансии из API Rapid с фильтрацией по дате.
        """
        vacancies = []
        new_last_published_date = self.last_published_date

        if not self.api_url:
            logger.error("RAPID_API_URL не указан")
            return []

        # Рассчитываем дату за вчера
        yesterday = datetime.now() - timedelta(days=1)
        logger.info(f"Дата начала поиска: {yesterday}")
        logger.debug(f"Последняя сохранённая дата: {self.last_published_date}")

        headers = {}
        if self.host and self.key:
            headers = {
                "x-rapidapi-key": self.key,
                "x-rapidapi-host": self.host
            }

        querystring = {
            "query": "frontend",
            "location": "any",
            "remoteOnly": "true",
            "employmentTypes": "fulltime;parttime;intern;contractor",
            "datePosted": "today"
        }

        async with aiohttp.ClientSession() as session:
            logger.info(f"Запрос к API Rapid: {self.api_url}, params={querystring}")
            try:
                async with session.request('GET', self.api_url, headers=headers, params=querystring, ssl=False, timeout=10) as response:
                    content = await response.text()
                    logger.debug(f"Содержимое ответа API: {content}")
                    if response.status == 401:
                        logger.error("Ошибка авторизации (401): Возможно, требуется валидный ключ API Rapid.")
                        return []
                    response.raise_for_status()
                    try:
                        data = await response.json()
                    except ValueError as e:
                        logger.error(f"Ошибка декодирования JSON: {e}, содержимое: {content}")
                        return []
                    logger.debug(f"Ответ API: {data}")
            except aiohttp.ClientResponseError as e:
                logger.error(f"HTTP-ошибка при запросе API {self.api_url}: {e.status}, {e.message}")
                return []
            except aiohttp.ClientError as e:
                logger.error(f"Ошибка при запросе API {self.api_url}: {e}")
                if "SSL" in str(e):
                    logger.warning("SSL-ошибка. Проверка SSL отключена. Рекомендуется обновить сертификаты.")
                return []

            # Проверка структуры ответа
            if not isinstance(data, dict) or 'jobs' not in data:
                logger.error(f"Неожиданный формат данных API: {type(data)}")
                return []
            results = data.get('jobs', [])
            logger.debug(f"Получено {len(results)} вакансий")

            for item in results:
                title = item.get('title', 'Without title')
                logger.info(f"Обработка вакансии: {title}")
                providers = item.get('jobProviders', [])
                date_posted_str = item.get('datePosted', '')
                logger.info(f"date_posted_str: {date_posted_str}")

                # Парсинг даты
                date_published = None
                if date_posted_str:
                    try:
                        parsed_date = parse(date_posted_str, settings={'TIMEZONE': 'UTC', 'TO_TIMEZONE': 'UTC'})
                        logger.info(f"Дата публикации вакансии: {parsed_date}")
                        if parsed_date:
                            date_published = to_utc(parsed_date)
                            formatted_date = date_published.strftime('%d %B %Y')
                            logger.info(f"Дата публикации вакансии (UTC): {date_published}")
                    except Exception as e:
                        logger.warning(f"Ошибка при обработке даты: {date_posted_str}, {e}")

                # Метаданные (для совместимости с другими парсерами)
                description = item.get('description', '')
                cleaned_description = cleandescription(description)
                company = item.get('company', 'Not specified')
                salaryrange = item.get('salaryRange', 'Not specified')
                location = item.get('location', 'Not specified')
                flag = get_flag_emoji(location)
                location_tag = normalize_tag(location)
                hashtags = []
                if location.lower() != "not specified" and location_tag:
                    hashtags.append(location_tag)

                if salaryrange:
                    salary = salaryrange
                else:
                    salary = f'Not specified'

                metadata = {
                    "description": cleaned_description[:100] + "..." if len(cleaned_description) > 100 else cleaned_description,
                    "company": company,
                    "published_date": date_published.strftime('%Y-%m-%d %H:%M:%S') if date_published else "Not specified",
                    "published_date_str": formatted_date,
                    "salary": salary,
                    "location": location,
                    "flag": flag or "",
                    "hashtags": hashtags
                }

                # Фильтрация по дате
                if date_published and is_newer(date_published, self.last_published_date):
                    link = providers[0].get('url', '#') if providers else 'No link'
                    vacancies.append((title, link, metadata))
                    logger.info(f"Добавлена вакансия: {title}, {link}")
                    new_last_published_date = update_last_published_date(new_last_published_date, date_published)
                else:
                    logger.debug(f"Вакансия '{title}' не прошла фильтрацию: date_published={date_published}, last_published_date={self.last_published_date}")

        if new_last_published_date:
            self.last_published_date = new_last_published_date
            save_last_published_date(new_last_published_date, self.last_published_file)

        logger.info(f"Итоговое количество вакансий: {len(vacancies)}")
        return vacancies

    def format_message(self, title: str, link: str, metadata: Dict) -> str:
        hashtags = metadata.get("hashtags", [])
        hashtags_str = " ".join(escape_html(tag) for tag in hashtags if tag)

        title_escaped = escape_html(title)
        description = escape_html(metadata.get("description", ""))
        company = escape_html(metadata.get("company", "Not specified"))
        raw_location = metadata.get("location", "").strip()
        location = escape_html(raw_location) if raw_location else "Not specified"
        flag = metadata.get("flag", "")
        salary = escape_html(metadata.get("salary", "Not specified"))
        published_date_str = escape_html(metadata.get("published_date_str", "Not specified"))

        return (
            f"💼 <b>{title_escaped}</b>\n"
            f"📍 Location: {flag} {location}\n\n"
            f"📅 Published: {published_date_str}\n\n"
            f"🏢 Company: {company}\n"
            f"📝 Description: {description}\n\n"
            f"💵 Salary: {salary}\n\n"
            f"👉 <a href=\"{link}\">APPLY NOW</a>\n\n"
            f"{hashtags_str}"
        )