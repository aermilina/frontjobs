import os
import json
from datetime import datetime



def load_last_published_date(LAST_PUBLISHED_FILE):
    """
    Загружает дату последней обработки вакансий из файла.
    :return: datetime или None, если файл отсутствует или пуст.
    """
    if os.path.exists(LAST_PUBLISHED_FILE):
        try:
            with open(LAST_PUBLISHED_FILE, "r") as file:
                data = json.load(file)
                return datetime.fromisoformat(data["last_published_date"])
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Ошибка при загрузке last_published_date: {e}")
    return None

def save_last_published_date(date,LAST_PUBLISHED_FILE):
    """
    Сохраняет дату последней обработки вакансий в файл.
    :param date: datetime объект, который нужно сохранить.
    """
    try:
        with open(LAST_PUBLISHED_FILE, "w") as file:
            json.dump({"last_published_date": date.isoformat()}, file)
    except Exception as e:
        print(f"Ошибка при сохранении last_published_date: {e}")