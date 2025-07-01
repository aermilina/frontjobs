import aiohttp
import logging
import os
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
from dateparser import parse
from src.utils.lastpublished import save_last_published_date
from src.utils.dateutils import to_utc, is_newer, update_last_published_date
from src.parsers.base_parser import VacancyParser
from src.utils.cleandescription import cleandescription
from src.utils.getflags import get_flag_emoji
from src.utils.normalizetags import normalize_tag
from src.utils.escapehtml import escape_html


# Настройка логирования
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class HHParser(VacancyParser):
    def __init__(
        self,
        url: str,
        last_published_date: Optional[datetime],
        last_published_file: str
    ):
        super().__init__(last_published_date, last_published_file)
        self.api_url = url
        self.search_text = 'frontend'
        self.schedule = 'remote'

    async def fetch_vacancies(self) -> List[Tuple[str, str, Dict]]:
        vacancies = []
        new_last_published_date = self.last_published_date

        if not self.api_url:
            logger.error("HH_API_URL не указан в .env")
            return []

        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        logger.info(f"Дата начала поиска: {yesterday}")
        logger.debug(f"Последняя сохранённая дата: {self.last_published_date}")

        params = {
            "text": self.search_text,
            "search_field": "name",
            "schedule": self.schedule,
            "date_from": yesterday,
            "per_page": 100
        }

        async with aiohttp.ClientSession() as session:
            page = 0
            while True:
                params["page"] = page
                logger.info(f"Запрос к API HeadHunter: {self.api_url}, страница {page}, params={params}")
                try:
                    async with session.request('GET', self.api_url, params=params, ssl=False, timeout=10) as response:
                        response.raise_for_status()
                        data = await response.json()
                except aiohttp.ClientResponseError as e:
                    logger.error(f"HTTP-ошибка при запросе API {self.api_url}: {e.status}, {e.message}")
                    return []
                except aiohttp.ClientError as e:
                    logger.error(f"Ошибка при запросе API {self.api_url}: {e}")
                    if "SSL" in str(e):
                        logger.warning("SSL-ошибка. Проверка SSL отключена. Рекомендуется обновить сертификаты.")
                    return []
                except ValueError as e:
                    logger.error(f"Ошибка декодирования JSON от {self.api_url}: {e}")
                    return []

                if data is None:
                    logger.error("Ответ API равен None")
                    return []
                items = data.get('items', [])
                logger.debug(f"Получено {len(items)} вакансий на странице {page}")
                if not isinstance(items, list) or not items:
                    logger.info(f"Нет больше вакансий на странице {page}")
                    break

                for item in items:
                    title = item.get('name') or ''
                    snippet = item.get('snippet') or {}
                    raw_description = snippet.get('responsibility') or snippet.get('requirement') or ''
                    employer = item.get('employer') or {}
                    company = employer.get('name', 'Не указано')
                    salary_data = item.get('salary') or {}
                    salarymin = salary_data.get('from', None)
                    salarymax = salary_data.get('to', None)
                    currency = salary_data.get('currency', '')
                    pub_date_str = item.get('published_at', '')
                    experience_data = item.get('experience') or {}
                    experience = experience_data.get('name', 'Не указано')
                    link = item.get('alternate_url', '#')
                    area = item.get('area', {}) or {}
                    location = area.get('name', '').strip()

                    # Парсинг даты
                    date_published = None
                    formatted_date = "Not specified"
                    if pub_date_str:
                        try:
                            parsed_date = parse(pub_date_str, settings={'TIMEZONE': 'UTC', 'TO_TIMEZONE': 'UTC'})
                            if parsed_date:
                                date_published = to_utc(parsed_date)
                                formatted_date = date_published.strftime('%d %B %Y')
                            else:
                                logger.warning(f"Не удалось разобрать дату: {pub_date_str}")
                                continue  # Пропускаем вакансию без даты
                        except Exception as e:
                            logger.warning(f"Ошибка при обработке даты: {pub_date_str}, {e}")
                            continue  # Пропускаем вакансию без даты
                    else:
                        logger.warning("Отсутствует дата публикации")
                        continue  # Пропускаем вакансию без даты

                    # Формируем теги после того, как есть experience и location
                    location_tag = normalize_tag(location)  # например #fr_moscow
                    experience_tag = normalize_tag(experience.lower())  # например #fr_junior

                    # Получаем эмодзи флага для локации
                    flag = get_flag_emoji(location)

                    # Формируем список хештегов (максимум 2 — локация и опыт)
                    hashtags = []
                    if location_tag:
                        hashtags.append(location_tag)
                    if experience_tag:
                        hashtags.append(experience_tag)

                    # Дебаг
                    logger.debug(f"Вакансия '{title}': salarymin={salarymin}, salarymax={salarymax}, currency={currency}, published_at={pub_date_str}")
                    description = cleandescription(raw_description)

                    # Формирование зарплаты
                    if salarymin and salarymax:
                        salary = f"{salarymin}–{salarymax} {currency}"
                    elif salarymin:
                        salary = f"from {salarymin} {currency}"
                    elif salarymax:
                        salary = f"to {salarymax} {currency}"
                    else:
                        salary = "Not specified"

                    metadata = {
                        "description": description[:100] + "..." if len(description) > 100 else description,
                        "experience": experience,
                        "company": company,
                        "published_date": date_published.strftime('%Y-%m-%d %H:%M:%S'),
                        "published_date_str": formatted_date,
                        "salary": salary,
                        "location": location or "Not specified",
                        "flag": flag or "",
                        "hashtags": hashtags
                    }

                    # Фильтрация только по дате
                    if date_published and is_newer(date_published, self.last_published_date):
                        vacancies.append((title, link, metadata))
                        new_last_published_date = update_last_published_date(new_last_published_date, date_published)
                        logger.info(f"Добавлена вакансия: {title}, {link}")
                    else:
                        logger.debug(f"Вакансия '{title}' не прошла фильтрацию: date_published={date_published}, last_published_date={self.last_published_date}")

                page += 1

        if new_last_published_date:
            self.last_published_date = new_last_published_date
            save_last_published_date(new_last_published_date, self.last_published_file)

        logger.info(f"Итоговое количество вакансий: {len(vacancies)}")
        return vacancies

    def format_message(self, title: str, link: str, metadata: Dict) -> str:
        hashtags = metadata.get("hashtags", [])
        hashtags_str = " ".join(escape_html(tag) for tag in hashtags if tag)

        title = escape_html(title)
        description = escape_html(metadata["description"])
        company = escape_html(metadata.get("company", "Not specified"))
        location = escape_html(metadata.get("location", "Not specified"))
        flag = metadata.get("flag", "")

        experience = escape_html(metadata.get("experience", "Not specified"))
        salary = escape_html(metadata.get("salary", "Not specified"))

        return (
            f"💼 <b>{title}</b>\n"
            f"📍 Location: {flag} {location}\n\n"
            f"📅 Published: {metadata['published_date_str']}\n\n"
            f"⌛️ Experience: {experience}\n\n"
            f"🏢 Company: {company}\n"
            f"📝 Description: {description}\n\n"
            f"💵 Salary: {salary}\n\n"
            f"👉 <a href=\"{link}\">APPLY NOW</a>\n\n"
            f"{hashtags_str}"
        )
