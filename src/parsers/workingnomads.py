import aiohttp
import logging
import os
from datetime import datetime
from typing import List, Tuple, Optional, Dict
from dotenv import load_dotenv
from dateparser import parse
from src.utils.lastpublished import save_last_published_date
from src.utils.dateutils import to_utc, is_newer, update_last_published_date
from src.parsers.base_parser import VacancyParser
from src.utils.cleandescription import cleandescription
from src.utils.getflags import get_flag_emoji
from src.utils.normalizetags import normalize_tags, normalize_tag
from src.utils.escapehtml import escape_html


load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class WorkingNomadsParser(VacancyParser):
    def __init__(
        self,
        url:str,
        keywords:str,
        last_published_date: Optional[datetime],
        last_published_file: str
    ):
        super().__init__(last_published_date, last_published_file)
        self.api_url = url
        self.keywords =  [kw.strip().lower() for kw in keywords.split(',')] if keywords else []
        self.headers = {
            "User-Agent": os.getenv("RSS_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"),
            "Accept": "application/json"
        }

    async def fetch_vacancies(self) -> List[Tuple[str, str, Dict]]:
        vacancies = []
        new_last_published_date = self.last_published_date

        if not self.api_url:
            logger.error("WORKINGNOMADS_URL не указан в .env")
            return []

        async with aiohttp.ClientSession() as session:
            logger.info(f"Запрос к API Working Nomads: {self.api_url}")
            try:
                    async with session.get(self.api_url, headers=self.headers, timeout=10,ssl=False) as response:
                        response.raise_for_status()
                        data = await response.json()
                        
            except aiohttp.ClientResponseError as e:
                logger.error(f"Ошибка HTTP при запросе API {self.api_url}: {e.status}, message='{e.message}'")

            except aiohttp.ClientError as e:
                logger.error(f"Ошибка при запросе API {self.api_url}: {e}")

            except ValueError as e:
                logger.error(f"Ошибка декодирования JSON от {self.api_url}: {e}")



            if not isinstance(data, list):
                logger.error(f"Неожиданный формат данных API: {type(data)}")
                return []

            for item in data:
                title = item.get('title', 'Без названия')
                link = item.get('url', '#')
                raw_description = item.get('description', '')
                pub_date_str = item.get('pub_date', '')
                tags_str = item.get('tags', '')  # Теги приходят как строка

                tags = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
                location = item.get("location", "").strip()
                flag = get_flag_emoji(location)
                location_tag = normalize_tag(location)
                normalized_tags = normalize_tags(tags)[:5]  # максимум 5 тегов

                hashtags = [location_tag] if location_tag else []
                hashtags += normalized_tags

            

                description = cleandescription(raw_description)


                # Парсинг даты публикации
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
                 # Метаданные для сообщения
                metadata = {
                    "source": "Working Nomads",
                    "description": description[:100] + "..." if len(description) > 100 else description,
                    "company": item.get('company_name', 'None'),
                    "published_date": date_published.strftime('%Y-%m-%d %H:%M:%S'),
                    "published_date_str": formatted_date,
                    "location": location or "Not specified",
                    "flag": flag or '',
                    "hashtags": hashtags    
                }

                # Фильтрация по ключевым словам
                content = (title.lower() + " ".join(tags).lower())

                if date_published and is_newer(date_published, self.last_published_date):
                   if any(keyword in content for keyword in self.keywords):
                    
                    vacancies.append((title, link, metadata))
                    new_last_published_date = update_last_published_date(new_last_published_date, date_published)
                    logger.info(f"Добавлена вакансия: {title}, {link}")

            if new_last_published_date:
                self.last_published_date = new_last_published_date
                save_last_published_date(new_last_published_date, self.last_published_file)

            return vacancies

    def format_message(self, title: str, link: str, metadata: Dict) -> str:
        hashtags = metadata.get("hashtags", [])
        hashtags_str = " ".join(escape_html(tag) for tag in hashtags if tag)

        title = escape_html(title)
        description = escape_html(metadata["description"])
        company = escape_html(metadata.get("company", "Not specified"))
        location = escape_html(metadata.get("location", "Not specified"))
        flag = metadata.get("flag", "")

        return (
            f"🌍 <b>{title}</b>\n"
            f"📍 Location: {flag} {location}\n\n"
            f"📅 Published: {metadata['published_date_str']}\n\n"
            f"🏢 Company: {company}\n"
            f"📝 Description: {description}\n\n"
            f"👉 <a href=\"{link}\">APPLY NOW</a>\n\n"
            f"{hashtags_str}"
        )