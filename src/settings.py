from datetime import timedelta
from os import getenv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SRC_FOLDER = Path(__file__).parent
ROOT_FOLDER = SRC_FOLDER.parent

DATABASE_NAME = getenv("DATABASE_NAME", default="postgres")
DATABASE_URL = f"postgresql+asyncpg://{getenv('DB_USER', 'postgres')}:{getenv('DB_PASSWORD', 'postgres')}@{getenv('DB_HOST', 'postgres')}:{getenv('DB_PORT', '5432')}/{getenv('DATABASE_NAME', 'family_budget')}"

CACHE_TTL: timedelta = timedelta(
    seconds=int(getenv("CACHE_TTL", default="86400"))
)

USERS_WHITE_LIST: list[int] = [
    int(el) for el in getenv("USERS_WHITE_LIST", default="").split(",") if el
]


TELEGRAM_BOT_API_KEY: str | None = getenv("TELEGRAM_BOT_API_KEY")
TELEGRAM_MESSAGE_MAX_LEN = 4096
