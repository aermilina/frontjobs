

from bs4 import BeautifulSoup


def cleandescription(html_text: str) -> str:
    """
    Удаляет HTML-теги и возвращает чистый текст.
    """
    if not html_text:
        return ""
    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        return soup.get_text(separator=' ').strip()
    except Exception as e:
        return ""