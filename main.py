import logging
import asyncio
import os
from src.scheduler import start_scheduler  # Импортируем функцию из scheduler

# Запуск асинхронной функции через asyncio
async def main():
    logging.info("Запуск бота и планировщика.")
    
    
    PORT = os.getenv("PORT", 5000)
    
    # Открытие порта для HTTP-сервера или другой обработки HTTP-запросов
    await start_scheduler()  # Ждем завершения работы планировщика

# Запуск главной асинхронной функции
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())  # Запуск асинхронной функции main()
