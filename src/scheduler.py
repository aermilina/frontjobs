import asyncio
from datetime import datetime, time, timedelta
from src.parsers.rss_parser import get_latest_vacancies
from src.parsers.json_parser import get_latest_json_vacancies
from src.parsers.hhparser import fetch_vacancies
from src.parsers.workingnomads import get_working_nomads_vacancy
from src.parsers.hiringcafeparser import get_hiring_cafe_vacancies
from src.parsers.rapidparser import get_rapid_vacancies
from src.bot import send_message, get_updates
from constants import RSS_FEEDS, KEYWORDS, JSON_FEED, HH_URL, TIMEOUT, WORKINGNOMADS_URL,RAPIDHOST,RAPIDKEY,JOB_URL
from src.utils.lastpublished import load_last_published_date
# Асинхронная задача, которая будет выполняться по расписанию
async def job():
    print(f"[{datetime.now()}] Начинается выполнение задачи...")
    await get_updates()  # Получаем обновления асинхронно
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

    rapidvacanies = get_rapid_vacancies(JOB_URL,RAPIDHOST,RAPIDKEY,rapid_date,RAPIDFILE)
    for title, link in rapidvacanies:
        await send_message(title, link)
        await asyncio.sleep(TIMEOUT)

    # Получаем вакансии с Hiring Cafe   
    hiring_cafe_vacancies = get_hiring_cafe_vacancies(' https://hiring.cafe/api/search-jobs', KEYWORDS,HF_date,HF_FILE)
    for title, link in hiring_cafe_vacancies:
        await send_message(title, link)
        await asyncio.sleep(TIMEOUT)
    # Получаем вакансии с RSS

    rss_vacancies = get_latest_vacancies(RSS_FEEDS, KEYWORDS,rss_date,RSS_FILE)
    for title, link in rss_vacancies:
        await send_message(title, link)
        await asyncio.sleep(TIMEOUT)

    # Получаем вакансии с JSON
    json_vacancies = get_latest_json_vacancies(JSON_FEED, KEYWORDS,json_date,JSON_FILE)
    for title, link in json_vacancies:
        await send_message(title, link)
        await asyncio.sleep(TIMEOUT)

    working_nomads = get_working_nomads_vacancy(WORKINGNOMADS_URL, KEYWORDS,nomads_date,NOMADS_FILE)
    for title, link in working_nomads:
        await send_message(title, link)
        await asyncio.sleep(TIMEOUT)

    # Получаем вакансии с HH
    hh_vacancies = fetch_vacancies(HH_URL, hh_date, HH_FILE)
    for title, link in hh_vacancies:
        await send_message(title, link)
        await asyncio.sleep(TIMEOUT)

    print(f"[{datetime.now()}] Задача завершена.")

# Функция для ожидания заданного времени
async def wait_until(target_time: time):
    """Ожидание до наступления указанного времени"""
    now = datetime.now()
    target = datetime.combine(now.date(), target_time)
    if now > target:  # Если время уже прошло, ждем до следующего дня
        target = datetime.combine(now.date() + timedelta(days=1), target_time)
    await asyncio.sleep((target - now).total_seconds())

# Планировщик с asyncio
async def start_scheduler():
    while True:
        # Запускаем задачу в 08:00
        await wait_until(time(9,00))
        await job()

        # Запускаем задачу в 20:00
        await wait_until(time(20,00))
        await job()
