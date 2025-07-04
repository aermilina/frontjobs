import aiohttp
import logging
import os
from datetime import datetime
from typing import List, Tuple, Optional, Dict
from dateparser import parse
from src.utils.lastpublished import save_last_published_date
from src.utils.dateutils import to_utc, is_newer, update_last_published_date
from src.parsers.base_parser import VacancyParser
from src.utils.cleandescription import cleandescription
from src.utils.getflags import get_flag_emoji
from src.utils.normalizetags import normalize_tags, normalize_tag
from src.utils.escapehtml import escape_html


# Настройка логирования
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class JSONParser(VacancyParser):
    def __init__(
        self,
        url: str,
        keywords: str,
        last_published_date: Optional[datetime],
        last_published_file: str
    ):
        super().__init__(last_published_date, last_published_file)
        self.api_url = url
        self.keywords = [kw.strip().lower() for kw in keywords.split(',')] if keywords else []

    async def fetch_vacancies(self) -> List[Tuple[str, str, Dict]]:
        """
        Получает вакансии из JSON API и фильтрует их по ключевым словам и дате.
        """
        vacancies = []
        new_last_published_date = self.last_published_date

        if not self.api_url:
            logger.error("JSON_FEED не указан в .env")
            return []

        async with aiohttp.ClientSession() as session:
            logger.info(f"Запрос к JSON API: {self.api_url}")
            try:
                    async with session.get(self.api_url, ssl=False, timeout=10) as response:
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

            if not isinstance(data, list):
                logger.error(f"Неожиданный формат данных API: {type(data)}")
                return []

            for item in data:
                title = item.get('position', 'Без названия')
                link = item.get('apply_url', '#')
                raw_description = item.get('description', '')
                pub_date_str = item.get('date', '')
                tags = [tag.lower() for tag in item.get('tags', []) if tag]
                company = item.get('company', 'None')
                salarymin = item.get('salary_min','None')
                salarymax = item.get ('salary_max','None')
                raw_tags = item.get('tags', []) or []
                normalized_tags = normalize_tags(raw_tags)[:5]  # только 5, нормализуем
                location = item.get("location", "").strip()
                flag = get_flag_emoji(location)
                location_tag = normalize_tag(location)

                hashtags = [location_tag] if location_tag else []
                hashtags += normalized_tags

                # Очистка HTML из описания
                description = cleandescription(raw_description)
                salary = f"{str(salarymin)}$ - {str(salarymax)}$" if salarymin != '' or salarymax != '' else 'Not specified'


                # Парсинг даты
                date_published = None
                formatted_date = "Not specified"  # ← Значение по умолчанию

                if pub_date_str:
                    try:
                        parsed_date = parse(pub_date_str, settings={'TIMEZONE': 'UTC', 'TO_TIMEZONE': 'UTC'})
                        if parsed_date:
                            date_published = to_utc(parsed_date)
                            formatted_date = date_published.strftime('%d %B %Y')
                        else:
                            logger.warning(f"Не удалось разобрать дату: {pub_date_str}")
                    except Exception as e:
                        logger.warning(f"Ошибка при обработке даты: {pub_date_str}, {e}")
                
                metadata = {
                    "description": description[:100] + "..." if len(description) > 100 else description,
                    "company": company,
                    "published_date": date_published.strftime('%Y-%m-%d %H:%M:%S') if date_published else "Not specified",
                    "published_date_str": formatted_date,
                    "salary": salary,
                    "hashtags": hashtags,     # ← для Telegram
                    "location": location or "Not specified",
                    "flag": flag or ''
                }

                # Фильтрация
                content = f"{title.lower()} {description.lower()} {' '.join(tags)}".strip()
                logger.debug(f"Ключевые слова: {self.keywords}, Содержимое: {content}")
                if date_published and is_newer(date_published, self.last_published_date) and \
                   (not self.keywords or any(keyword in content for keyword in self.keywords)):
                    vacancies.append((title, link, metadata))
                    new_last_published_date = update_last_published_date(new_last_published_date, date_published)
                    logger.info(f"Добавлена вакансия: {title}, {link}")

        if new_last_published_date:
            self.last_published_date = new_last_published_date
            save_last_published_date(new_last_published_date, self.last_published_file)

        return vacancies

    from src.utils.escapehtml import escape_html

    def format_message(self, title: str, link: str, metadata: Dict) -> str:
        hashtags = metadata.get("hashtags", [])
        hashtags_str = " ".join(escape_html(tag) for tag in hashtags if tag)

        title = escape_html(title)
        description = escape_html(metadata["description"])
        company = escape_html(metadata.get("company", "Not specified"))
        salary = escape_html(metadata.get("salary", "Not specified"))
        location = escape_html(metadata.get("location", "Not specified"))
        flag = metadata.get("flag", "")

        return (
            f"📡 <b>{title}</b>\n"
            f"📍 Location: {flag} {location}\n\n"
            f"📅 Published: {metadata['published_date_str']}\n\n"
            f"🏢 Company: {company}\n"
            f"📝 Description: {description}\n\n"
            f"💵 Estimated salary: {salary}\n\n"
            f"👉 <a href=\"{link}\">APPLY NOW</a>\n\n"
            f"{hashtags_str}"
        )
