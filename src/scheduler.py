import asyncio
from datetime import datetime, time, timedelta
from src.parsers.hhparser import HHParser
from src.parsers.rss_parser import RSSParser
from src.parsers.workingnomads import WorkingNomadsParser
from src.parsers.json_parser import JSONParser
from src.parsers.hiringcafeparser import HiringCafeParser
from src.parsers.rapidparser import RapidParser
from src.bot import send_message, get_updates, send_selfpromo
from src.utils.lastpublished import load_last_published_date
from constants import RSS_FEEDS, KEYWORDS, JSON_FEED, HH_URL, TIMEOUT, WORKINGNOMADS_URL,RAPIDHOST,RAPIDKEY,JOB_URL,HF_URL
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def job():
    logger.info(f"[{datetime.now()}] Запуск саморекламы...")
    await send_selfpromo()
    """
    Асинхронная задача для получения и отправки вакансий.
    
    :param config: Конфигурация из config.yaml.
    """
    logger.info(f"[{datetime.now()}] Начинается выполнение задачи...")
    await get_updates()  # Получение обновлений от Telegram
    RAPIDFILE ='last_published_rapid.json'
    HF_FILE = 'last_published_HF.json'
    RSS_FILE = 'last_published_rss.json'
    JSON_FILE = 'last_published_json.json'
    HH_FILE = 'last_published_hh.json'
    NOMADS_FILE = 'last_published_nomads.json'
    rapid_date = load_last_published_date(RAPIDFILE)
    HF_date = load_last_published_date(HF_FILE)
    rss_date = load_last_published_date(RSS_FILE)
    json_date = load_last_published_date(JSON_FILE)
    hh_date = load_last_published_date(HH_FILE)
    nomads_date = load_last_published_date(NOMADS_FILE)

    # Инициализация парсеров
    parsers = [
        RSSParser(
            RSS_FEEDS,
            KEYWORDS,
            rss_date,
            RSS_FILE
        ),
        JSONParser(
            JSON_FEED,
            KEYWORDS,
            json_date,
            JSON_FILE
        ),
    
        WorkingNomadsParser(
            WORKINGNOMADS_URL,
            KEYWORDS,
            nomads_date,
            NOMADS_FILE
        ),
        HHParser(
            HH_URL,
            hh_date,
            HH_FILE
            
        ),
        HiringCafeParser(
            HF_URL,
            HF_date,
            HF_FILE
        ),
        RapidParser(
            JOB_URL,
            rapid_date,
            RAPIDFILE,
            RAPIDHOST,
            RAPIDKEY
        )
    ]

    # Обработка вакансий от каждого парсера
    for parser in parsers:
        try:
            vacancies = await parser.fetch_vacancies()
            logger.info(f"Получено {len(vacancies)} вакансий от {parser.__class__.__name__}")
            for title, link, metadata in vacancies:
                message = parser.format_message(title, link, metadata)
                await send_message(message)
                await asyncio.sleep(TIMEOUT)  # Задержка для избежания лимитов Telegram
        except Exception as e:
            logger.error(f"Ошибка при обработке парсера {parser.__class__.__name__}: {e}")

    logger.info(f"[{datetime.now()}] Задача завершена.")

async def wait_until(target_time: time) -> None:
    """
    Ожидание до наступления указанного времени.
    
    :param target_time: Время в формате time для ожидания.
    """
    now = datetime.now()
    target = datetime.combine(now.date(), target_time)
    if now > target:
        target = datetime.combine(now.date() + timedelta(days=1), target_time)
    seconds_to_wait = (target - now).total_seconds()
    logger.debug(f"Ожидание {seconds_to_wait} секунд до {target_time}")
    await asyncio.sleep(seconds_to_wait)

async def start_scheduler():
    while True:
            await wait_until(time(12,54))
            logger.info("Запускаю job в 08:00")
            await job()
            
            await wait_until(time(20,00))
            logger.info("Запускаю job в 20:00")
            await job()

