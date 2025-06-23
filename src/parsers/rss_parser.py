import feedparser
import logging
import subprocess
from datetime import datetime
from typing import List, Tuple, Optional, Dict
from urllib.parse import urlparse

from src.utils.lastpublished import save_last_published_date
from src.utils.dateutils import to_utc, is_newer, update_last_published_date
from src.parsers.base_parser import VacancyParser
from src.utils.cleandescription import cleandescription

logger = logging.getLogger(__name__)

class RSSParser(VacancyParser):
    def __init__(
        self,
        rss_feeds: str,
        keywords: str,
        last_published_date: Optional[datetime],
        last_published_file: str
    ):
        super().__init__(last_published_date, last_published_file)
        self.rss_feeds = rss_feeds.split(',') if rss_feeds else []
        self.keywords = [kw.strip().lower() for kw in keywords.split(',')] if keywords else []

    def fetch_with_curl(self, url: str, referer: str) -> Optional[str]:
        try:
            result = subprocess.run([
                "curl", "-sL", url,
                "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "-H", "Accept: application/rss+xml",
                "-H", f"Referer: {referer}"
            ], capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                logger.error(f"curl завершился с ошибкой: {result.stderr.strip()}")
                return None

            return result.stdout

        except Exception as e:
            logger.error(f"Ошибка при curl-запросе к {url}: {e}")
            return None

    async def fetch_vacancies(self) -> List[Tuple[str, str, Dict]]:
        vacancies = []
        new_last_published_date = self.last_published_date

        for rss_url in self.rss_feeds:
            logger.info(f"Запрос RSS-ленты через curl: {rss_url}")

            parsed_url = urlparse(rss_url)
            referer = f"{parsed_url.scheme}://{parsed_url.netloc}/"

            feed_content = self.fetch_with_curl(rss_url, referer)
            if not feed_content:
                logger.error(f"Не удалось получить RSS: {rss_url}")
                continue

            feed = feedparser.parse(feed_content)
            if feed.bozo:
                logger.error(f"Ошибка парсинга RSS {rss_url}: {feed.bozo_exception}")
                continue

            logger.info(f"Успешно получена RSS-лента: {rss_url}")

            for entry in feed.entries:
                title = entry.get('title', 'Без названия')
                link = entry.get('link', '#')
                published_date = entry.get('published_parsed', None)
                raw_description = entry.get('description', '')

                description = cleandescription(raw_description)

                date_published = None
                formatted_date = "Not specified"
                if published_date:
                    try:
                        date_published = to_utc(datetime(*published_date[:6]))
                        formatted_date = date_published.strftime('%d %B %Y')
                    except Exception as e:
                        logger.warning(f"Ошибка обработки даты для {title}: {e}")

                metadata = {
                    "source": "RSS",
                    "description": description[:100] + "..." if len(description) > 100 else description,
                    "published_date": date_published.strftime('%Y-%m-%d %H:%M:%S') if date_published else "None",
                    "published_date_str": formatted_date
                }

                vacancy = (title, link, metadata)

                content = f"{title.lower()} {description.lower()}".strip()
                if date_published and is_newer(date_published, self.last_published_date) and \
                   any(keyword in content for keyword in self.keywords):
                    vacancies.append(vacancy)
                    logger.info(f"Добавлена вакансия: {title}, {link}")
                    new_last_published_date = update_last_published_date(new_last_published_date, date_published)

        if new_last_published_date:
            self.last_published_date = new_last_published_date
            save_last_published_date(new_last_published_date, self.last_published_file)

        return vacancies

    def format_message(self, title: str, link: str, metadata: Dict) -> str:
        return (
            f"📰 **{title}**\n\n"
            f"📅 Published: {metadata['published_date_str']}\n\n"
            f"📝 Description: {metadata['description']}\n\n"
            f"👉[APPLY NOW]({link})"
        )
