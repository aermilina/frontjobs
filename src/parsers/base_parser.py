from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Tuple, Optional

class VacancyParser(ABC):
    def __init__(self, last_published_date: Optional[datetime], last_published_file: str):
        self.last_published_date = last_published_date
        self.last_published_file = last_published_file

    @abstractmethod
    async def fetch_vacancies(self) -> List[Tuple[str, str, dict]]:
        """Возвращает список вакансий: (title, link, metadata)."""
        pass

    @abstractmethod
    def format_message(self, title: str, link: str, metadata: dict) -> str:
        """Форматирует сообщение для вакансии."""
        pass