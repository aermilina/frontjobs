from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
RSS_FEEDS = os.getenv("RSS_FEEDS")
JSON_FEED = os.getenv("JSON_FEED")
CHANNEL_ID = os.getenv("CHANNEL_ID")
KEYWORDS = os.getenv("KEYWORDS")
CHECK_INTERVAL = 60
HH_URL=os.getenv("HH_URL")
RAPIDKEY=os.getenv("RAPIDKEY")
RAPIDHOST=os.getenv("RAPIDHOST")
JOB_URL=os.getenv("JOBAPI_URL")
TIMEOUT = 10