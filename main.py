import logging
import os
from src.scheduler import start_scheduler  # Импортируем функцию из scheduler

# Запуск асинхронной функции через asyncio
async def main():
    # Логируем запуск бота
    logging.info("Запуск бота и планировщика.")
    PORT = int(os.environ.get("PORT", 5000))  # Получаем порт из переменной окружения Render
    await start_scheduler()  # Ждем завершения работы планировщика

# Запуск главной асинхронной функции
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Используем uvicorn для запуска приложения
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)  # Подключение к порту из переменной окружения
