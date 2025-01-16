import logging
import os
import uvicorn
from src.scheduler import start_scheduler  # Импортируем функцию из scheduler

from fastapi import FastAPI, HTTPException

app = FastAPI()

# Корень маршрута
@app.get("/")
def read_root():
    logging.info("Обрабатывается запрос на корень")
    return {"message": "Запуск бота и планировщика"}

# Асинхронная функция для запуска бота и планировщика через GET
@app.get("/start")
async def start_bot():
    logging.info("Запуск бота и планировщика.")
    
    try:
        port = os.getenv("PORT", 5000)  # Получаем порт из переменной окружения Render
        PORT = int(port)  # Преобразуем значение в целое число
        await start_scheduler()  # Ждем завершения работы планировщика
        logging.info(f"Порт для запуска: {PORT}")
        return {"message": "Бот запущен"}
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
        return {"error": "Не удалось запустить бота"}

# Асинхронная функция для запуска бота и планировщика через POST
@app.post("/start")
async def start_bot_post():
    logging.info("Запуск бота через POST.")
    
    try:
        port = os.getenv("PORT", 5000)  # Получаем порт из переменной окружения Render
        PORT = int(port)  # Преобразуем значение в целое число
        await start_scheduler()  # Ждем завершения работы планировщика
        logging.info(f"Порт для запуска: {PORT}")
        return {"message": "Бот запущен через POST"}
    except Exception as e:
        logging.error(f"Ошибка при запуске бота через POST: {e}")
        return {"error": "Не удалось запустить бота через POST"}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Используем uvicorn для запуска приложения
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))  # Подключение к порту из переменной окружения
