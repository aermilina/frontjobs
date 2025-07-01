import re
from typing import Optional,List

def normalize_tag(tag: str) -> Optional[str]:
    if not tag:
        return None
    return f"#fr_{tag.strip().lower().replace(' ', '')}"

def normalize_tags(raw_tags: List[str]) -> List[str]:
    result = []
    for raw in raw_tags:
        parts = re.split(r'[,&/]| and ', raw)  # разделяем
        for p in parts:
            clean = p.strip().lower().replace(' ', '')
            if clean:
                result.append(f"#fr_{clean}")
    return result
