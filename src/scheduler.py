import asyncio
from datetime import datetime, time, timedelta
from src.parsers.rss_parser import get_latest_vacancies
from src.parsers.json_parser import get_latest_json_vacancies
from src.parsers.hhparser import fetch_vacancies
from src.bot import send_message, get_updates
from constants import RSS_FEEDS, KEYWORDS, JSON_FEED, HH_URL, TIMEOUT

# Асинхронная задача, которая будет выполняться по расписанию
async def job():
    print(f"[{datetime.now()}] Начинается выполнение задачи...")
    await get_updates()  # Получаем обновления асинхронно

    # Получаем вакансии с RSS
    rss_vacancies = get_latest_vacancies(RSS_FEEDS, KEYWORDS)
    for title, link in rss_vacancies:
        await send_message(title, link)
        await asyncio.sleep(TIMEOUT)

    # Получаем вакансии с JSON
    json_vacancies = get_latest_json_vacancies(JSON_FEED, KEYWORDS)
    for title, link in json_vacancies:
        await send_message(title, link)
        await asyncio.sleep(TIMEOUT)

    # Получаем вакансии с HH
    hh_vacancies = fetch_vacancies(HH_URL)
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
        await wait_until(time(15, 25))
        await job()

        # Запускаем задачу в 20:00
        await wait_until(time(20, 00))
        await job()
