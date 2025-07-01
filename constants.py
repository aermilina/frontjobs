from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
RSS_FEEDS = os.getenv("RSS_FEEDS")
JSON_FEED = os.getenv("JSON_FEED")
CHANNEL_ID = os.getenv("CHANNEL_ID")
KEYWORDS = os.getenv("KEYWORDS")
CHECK_INTERVAL = 1440
HH_URL=os.getenv("HH_URL")
RAPIDKEY=os.getenv("RAPIDKEY")
RAPIDHOST=os.getenv("RAPIDHOST")
JOB_URL=os.getenv("JOBAPI_URL")
TIMEOUT = 10
WORKINGNOMADS_URL = os.getenv("WORKINGNOMADS")
HF_URL = os.getenv("HF_URL")

FLAGS = {
    "usa": "🇺🇸",
    "united states": "🇺🇸",
    "us": "🇺🇸",
    "canada": "🇨🇦",
    "eu": "🇪🇺",
    "european union": "🇪🇺",
    "netherlands": "🇪🇺",
    "spain":"🇪🇺",
    "uk": "🇬🇧",
    "great britain": "🇬🇧",
    "gb": "🇬🇧",
    "russia": "🇷🇺",
    "pl": "🇵🇱",
    "poland": "🇵🇱",
    "world": "🌍",
    "anywhere": "🌍",
    "anywhere in the world": "🌍",
    "global": "🌍",
    "shanghai": "🇨🇳",
    "china": "🇨🇳",
    "hk": "🇨🇳",
    "москва": "🇷🇺",
    "омск": "🇷🇺",
    "уфа": "🇷🇺",
    "нижний новгород":"🇷🇺",
    "тюмень": "🇷🇺",
    "пермь": "🇷🇺",
    "тбилиси": "🇬🇪",
    "грузия":  "🇬🇪",
    "минск": "🇧🇾",
    "кипр": "🇨🇾",
    "лимассол":"🇨🇾",
    "сербия": "🇷🇸",
    "белград": "🇷🇸",
    "in": "🇮🇳",
    "ca": "🇨🇦",
    "br": "🇧🇷",
    "cанкт-Петербург":"🇷🇺",
    "lu": "🇱🇺"
}
