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
        """
        Получает вакансии из API HeadHunter с пагинацией и фильтрует их по дате.
        """
        vacancies = []
        new_last_published_date = self.last_published_date

        if not self.api_url:
            logger.error("HH_API_URL не указан в .env")
            return []

        # Рассчитываем дату за вчера
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
                    async with session.request('GET',self.api_url, params=params, ssl=False, timeout=10) as response:
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

                # Проверка структуры ответа
                if data is None:
                    logger.error("Ответ API равен None")
                    return []
                items = data.get('items', [])
                logger.debug(f"Получено {len(items)} вакансий на странице {page}")
                if not isinstance(items, list) or not items:
                    logger.info(f"Нет больше вакансий на странице {page}")
                    break

                for item in items:
                    title = item.get('name' ) or ''
                    snippet = item.get('snippet') or {}
                    raw_description = snippet.get('responsibility') or snippet.get('requirement') or ''
                    employer = item.get('employer') or {}
                    company = employer.get('name', 'Не указано')
                    salary_data = item.get('salary') or {}
                    salarymin = salary_data.get('from', 'Не указано')
                    salarymax = salary_data.get('to', 'Не указано')
                    currency = salary_data.get('currency', '')
                    pub_date_str = item.get('published_at', '')
                    experience_data = item.get('experience') or {}
                    experience = experience_data.get('name', 'Не указано')
                    link = item.get('alternate_url', '#')

                    # Дебаг
                    logger.debug(f"Вакансия '{title}': salarymin={salarymin}, salarymax={salarymax}, currency={currency}, published_at={pub_date_str}")
                    description = cleandescription(raw_description)

                    # Формирование зарплаты
                    if salary_data:
                        if salarymin and salarymax:
                            salary = f"{salarymin}–{salarymax} {currency}"
                        elif salarymin:
                            salary = f"from {salarymin} {currency}"
                        elif salarymax:
                            salary = f"to {salarymax} {currency}"
                        else:
                             salary = f"Not specified"
                    else:
                        salary = "Not specified"

                  

                    # Парсинг даты
                    date_published = None
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
                      # Метаданные
                    metadata = {
                        "description": description[:100] + "..." if len(description) > 100 else description,
                        "experience": experience,
                        "company": company,
                        "published_date": date_published.strftime('%Y-%m-%d %H:%M:%S'),
                        "published_date_str": formatted_date,
                        "salary": salary
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
        """
        Форматирует сообщение для Telegram.
        """
        return (
            f"💼 **{title}**\n\n"
            f"📅 Published: {metadata['published_date_str']}\n\n"
            f"⌛️ Experience: {metadata['experience']}\n\n"
            f"🏢 Company: {metadata['company']}\n\n"
            f"📝 Description: {metadata['description']}\n\n"
            f"💵 Salary: {metadata['salary']}\n\n"
            f"👉[APPLY NOW]({link})"
        )