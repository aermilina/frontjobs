from datetime import datetime, timezone

def to_utc(date):
    """
    Преобразует дату в UTC.
    :param date: datetime объект.
    :return: datetime объект в UTC.
    """
    if date.tzinfo is None:
        return date.replace(tzinfo=timezone.utc)
    return date.astimezone(timezone.utc)

def is_newer(date, last_date):
    """
    Проверяет, является ли дата новее последней сохранённой даты.
    :param date: datetime объект.
    :param last_date: datetime объект или None.
    :return: True, если date > last_date или last_date == None.
    """
    return last_date is None or date > last_date

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