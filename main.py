import logging
import asyncio
from src.scheduler import start_scheduler  # Импортируем функцию из scheduler

# Запуск асинхронной функции через asyncio
async def main():
    # Логируем запуск бота
    logging.info("Запуск бота и планировщика.")
    await start_scheduler()  # Ждем завершения работы планировщика

# Запуск главной асинхронной функции
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())  # Запуск асинхронной функции main()