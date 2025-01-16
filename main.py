import logging
import os
import uvicorn
from src.scheduler import start_scheduler  # Импортируем функцию из scheduler

from fastapi import FastAPI

app = FastAPI()

# Корень маршрута
@app.get("/")
def read_root():
    logging.info("Обрабатывается запрос на корень")
    return {"message": "Запуск бота и планировщика"}

# Асинхронная функция для запуска бота и планировщика
@app.get("/start")
async def start_bot():
    logging.info("Запуск бота и планировщика.")
    port = os.getenv("PORT", 5000)  # Получаем порт из переменной окружения Render
    PORT = int(port)  # Преобразуем значение в целое число
    await start_scheduler()  # Ждем завершения работы планировщика
    return {"message": "Бот запущен"}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Используем uvicorn для запуска приложения
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))  # Подключение к порту из переменной окружения
