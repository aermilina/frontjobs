import asyncio
from src.parsers.rss_parser import get_latest_vacancies
from src.parsers.json_parser import get_latest_json_vacancies
from src.parsers.hhparser import fetch_vacancies
from src.parsers.linkedinparser import fetch_linkedin_jobs
from src.bot import send_message, get_updates  # Убедитесь, что эти функции асинхронные
from constants import RSS_FEEDS, CHECK_INTERVAL, KEYWORDS,JSON_FEED, HH_URL, JOB_URL, RAPIDKEY, RAPIDHOST,TIMEOUT
# Асинхронная версия функции job
async def job():
    # Получаем вакансии с RSS
    while True:
        await get_updates()
        vacancies = get_latest_vacancies(RSS_FEEDS,KEYWORDS)
        # Отправляем вакансии в канал
        for title, link in vacancies:
            await send_message(title, link)  # Используем await для асинхронной функции
            await asyncio.sleep(TIMEOUT)
        jsonvacancies = get_latest_json_vacancies(JSON_FEED,KEYWORDS)
        for title, link in jsonvacancies:
            await send_message(title, link)
            await asyncio.sleep(TIMEOUT)  # Используем await для асинхронной функции
        hhvacancies = fetch_vacancies(HH_URL)
        for title, link in hhvacancies:
            await send_message(title, link)
            await asyncio.sleep(TIMEOUT)
        await asyncio.sleep(CHECK_INTERVAL * 60)
# Функция для запуска планировщика с использованием asyncio
        #linkedin_vacancies = fetch_linkedin_jobs(JOB_URL, RAPIDKEY, RAPIDHOST)
        #for title, link in linkedin_vacancies:
            #await send_message(title, link)
            #await asyncio.sleep(TIMEOUT)  # Wait for the specified timeout between sending messages
        #await asyncio.sleep(CHECK_INTERVAL * 60)  # Wait for the specified interval before fetching vacancies again
async def start_scheduler():
    # Запуск цикла событий asyncio
    loop = asyncio.get_event_loop()

    # Планирование задачи
    loop.create_task(job())
    while True:
        await asyncio.sleep(10)
    