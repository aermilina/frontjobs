from constants import FLAGS
from typing import Optional
def get_flag_emoji(location: Optional[str]) -> str:
    if not location:
        return ""
    key = location.strip().lower()
    return FLAGS.get(key, "")