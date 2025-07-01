import aiohttp
import logging
import os
from datetime import datetime
from typing import List, Tuple, Optional, Dict
from src.utils.lastpublished import save_last_published_date
from src.utils.dateutils import to_utc, is_newer, update_last_published_date
from src.parsers.base_parser import VacancyParser
from dateparser import parse
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

class HiringCafeParser(VacancyParser):
    def __init__(
        self,
        url: str,
        last_published_date: Optional[datetime],
        last_published_file: str,
        keywords: str = "frontend"
    ):
        super().__init__(last_published_date, last_published_file)
        self.api_url = url
        self.keywords = keywords
        self.workplace_type = 'remote'

    async def fetch_vacancies(self) -> List[Tuple[str, str, Dict]]:
        vacancies = []
        new_last_published_date = self.last_published_date

        if not self.api_url:
            logger.error("HC_API_URL не указан в .env")
            return []

        payload = {
            "size": 20,
            "page": 0,
            "searchState": {
                "searchQuery": self.keywords,
                "sortBy": "date"
            }
        }

        async with aiohttp.ClientSession() as session:
            page = 0
            while True:
                payload["page"] = page
                logger.info(f"Запрос к API Hiring Cafe: {self.api_url}, страница {page}, payload={payload}")
                try:
                    async with session.post(self.api_url, json=payload, ssl=False, timeout=10) as response:
                        content = await response.text()
                        if response.status == 401:
                            logger.error("Ошибка авторизации (401): Возможно, требуется токен API Hiring Cafe.")
                            return []
                        response.raise_for_status()
                        try:
                            data = await response.json()
                        except ValueError as e:
                            logger.error(f"Ошибка декодирования JSON: {e}, содержимое: {content}")
                            return []
                except aiohttp.ClientResponseError as e:
                    logger.error(f"HTTP-ошибка при запросе API {self.api_url}: {e.status}, {e.message}")
                    return []
                except aiohttp.ClientError as e:
                    logger.error(f"Ошибка при запросе API {self.api_url}: {e}")
                    if "SSL" in str(e):
                        logger.warning("SSL-ошибка. Проверка SSL отключена. Рекомендуется обновить сертификаты.")
                    return []

                if not isinstance(data, dict) or 'results' not in data:
                    logger.error(f"Неожиданный формат данных API: {type(data)}")
                    return []
                results = data.get('results', [])

                if not results:
                    logger.info(f"Нет вакансий на странице {page}")
                    break

                all_old = True  # Флаг: все вакансии на странице старые

                for item in results:
                    processed_data = item.get('v5_processed_job_data', {})
                    title = processed_data.get('core_job_title', 'Без названия')
                    link = item.get('apply_url', '#')
                    workplace_type = processed_data.get('workplace_type', '').lower()
                    date_published_str = processed_data.get('estimated_publish_date', '')

                    # Парсинг даты
                    date_published = None
                    formatted_date = "Not specified"
                    if date_published_str:
                        try:
                            parsed_date = parse(date_published_str, settings={'TIMEZONE': 'UTC', 'TO_TIMEZONE': 'UTC'})
                            if parsed_date:
                                date_published = to_utc(parsed_date)
                                formatted_date = date_published.strftime('%d %B %Y')
                            else:
                                logger.warning(f"Не удалось разобрать дату: {date_published_str}")
                        except Exception as e:
                            logger.warning(f"Ошибка при обработке даты: {date_published_str}, {e}")

                    description = processed_data.get('requirements_summary', '')
                    cleaned_description = cleandescription(description)
                    company = processed_data.get('company_name', 'Not specified')
                    salaryrange = processed_data.get('listed_compensation_frequency', 'Не указано')
                    experience = processed_data.get('seniority_level', 'Not specified')
                    currency = processed_data.get('listed_compensation_currency', 'not specified')
                    languages = processed_data.get("language_requirements", [])
                    language_str = ", ".join(languages) if languages else "Not specified"

                    location = processed_data.get('workplace_countries', [])
                    location_name = location[0] if location else "Not specified"
                    location_tag = normalize_tag(location_name)
                    flag = get_flag_emoji(location_name)

                    experience_tag = normalize_tag(experience.lower())
                    language_tag = normalize_tag(language_str.lower())

                    hashtags = []
                    if location_name.lower() != "not specified" and location_tag:
                        hashtags.append(location_tag)
                    if experience_tag:
                        hashtags.append(experience_tag)
                    if language_tag:
                        hashtags.append(language_tag)

                    if salaryrange:
                        salarymin = processed_data.get(f'{salaryrange.lower()}_min_compensation') or ''
                        salarymax = processed_data.get(f'{salaryrange.lower()}_max_compensation') or ''
                        if salarymin and salarymax:
                            salary = f'{salarymin} {currency} - {salarymax} {currency} {salaryrange}'
                        elif salarymin:
                            salary = f'from {salarymin} {currency} {salaryrange}'
                        elif salarymax:
                            salary = f'to {salarymax} {currency} {salaryrange}'
                        else:
                            salary = 'Not specified'
                    else:
                        salary = 'Not specified'

                    metadata = {
                        "description": cleaned_description[:100] + "..." if len(cleaned_description) > 100 else cleaned_description,
                        "experience": experience,
                        "company": company,
                        "published_date": date_published.strftime('%Y-%m-%d %H:%M:%S') if date_published else "Not specified",
                        "published_date_str": formatted_date,
                        "salary": salary,
                        "language": language_str,
                        "location": location_name,
                        "flag": flag or "",
                        "hashtags": hashtags
                    }

                    if date_published and is_newer(date_published, self.last_published_date) and 'remote' in workplace_type:
                        all_old = False
                        vacancies.append((title, link, metadata))
                        new_last_published_date = update_last_published_date(new_last_published_date, date_published)
                        logger.info(f"Добавлена вакансия: {title}, {link}")
                    else:
                        logger.debug(f"Пропущена вакансия: {title} (дата: {date_published}, тип: {workplace_type})")

                if all_old:
                    logger.info(f"Все вакансии на странице {page} старые, дальнейший парсинг остановлен.")
                    break

                page += 1

        now = datetime.utcnow()
        self.last_published_date = now
        save_last_published_date(now, self.last_published_file)

        logger.info(f"Итоговое количество новых вакансий: {len(vacancies)}")
        return vacancies

    def format_message(self, title: str, link: str, metadata: Dict) -> str:
        hashtags = metadata.get("hashtags", [])
        hashtags_str = " ".join(escape_html(tag) for tag in hashtags if tag)

        title_html = escape_html(title)
        description_html = escape_html(metadata.get("description", ""))
        company_html = escape_html(metadata.get("company", "Not specified"))
        location_html = escape_html(metadata.get("location", "Not specified"))
        flag = metadata.get("flag", "")
        experience_html = escape_html(metadata.get("experience", "Not specified"))
        salary_html = escape_html(metadata.get("salary", "Not specified"))
        language_html = escape_html(metadata.get("language", "Not specified"))

        return (
            f"💼 <b>{title_html}</b>\n"
            f"📍 Location: {flag} {location_html}\n\n"
            f"📅 Published: {metadata.get('published_date_str', 'Not specified')}\n\n"
            f"⌛️ Experience: {experience_html}\n\n"
            f"🏢 Company: {company_html}\n"
            f"📝 Description:\n{description_html}\n\n"
            f"🔤 Language: {language_html}\n\n"
            f"💵 Salary: {salary_html}\n\n"
            f"👉 <a href=\"{link}\">APPLY NOW</a>\n\n"
            f"{hashtags_str}"
        )
