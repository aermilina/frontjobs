from datetime import datetime, timezone
from typing import Optional

def to_utc(date):
    """
    Преобразует дату в UTC.
    :param date: datetime объект.
    :return: datetime объект в UTC.
    """
    if date.tzinfo is None:
        return date.replace(tzinfo=timezone.utc)
    return date.astimezone(timezone.utc)

def is_newer(date1: datetime, date2: Optional[datetime]) -> bool:
    from datetime import timezone
    if date2 is None:
        return True
    if date1.tzinfo is None:
        date1 = date1.replace(tzinfo=timezone.utc)
    if date2.tzinfo is None:
        date2 = date2.replace(tzinfo=timezone.utc)
    return date1 > date2

def update_last_published_date(current_last_date, new_date):
    """
    Обновляет последнюю сохранённую дату, если новая дата новее.
    :param current_last_date: datetime объект текущей последней даты.
    :param new_date: datetime объект новой даты.
    :return: datetime объект обновлённой даты.
    """
    if current_last_date:
        current_last_date = to_utc(current_last_date)
    new_date = to_utc(new_date)

    if current_last_date is None or new_date > current_last_date:
        return new_date
    return current_last_date