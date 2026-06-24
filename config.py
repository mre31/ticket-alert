import os
from dotenv import load_dotenv

# Load env variables from .env if present
load_dotenv()

class Config:
    # 1. Paribu Cineverse Configuration
    PARIBU_URL = os.getenv(
        "PARIBU_URL", 
        "https://www.paribucineverse.com/fantastik-filmleri/orumcek-adam-yepyeni-bir-gun-filmi-izle"
    )
    
    # 2. Biletinial Configuration
    BILETINIAL_URL = os.getenv(
        "BILETINIAL_URL",
        "https://biletinial.com/tr-tr/sinema"
    )
    
    # Biletinial keywords to search, comma separated
    BILETINIAL_KEYWORDS_RAW = os.getenv(
        "BILETINIAL_KEYWORDS",
        "spider,örümcek,orumcek"
    )

    @classmethod
    def get_biletinial_keywords(cls):
        """Parses comma-separated keywords into a list of lowercase strings."""
        if not cls.BILETINIAL_KEYWORDS_RAW:
            return []
        return [kw.strip().lower() for kw in cls.BILETINIAL_KEYWORDS_RAW.split(",") if kw.strip()]

    # Global/common settings
    try:
        CHECK_INTERVAL_SECONDS = max(10, int(os.getenv("CHECK_INTERVAL_SECONDS", "300")))
    except ValueError:
        CHECK_INTERVAL_SECONDS = 300

    STATE_FILE_PATH = os.getenv("STATE_FILE_PATH", "state.json")

    # Telegram Bot configurations
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # ntfy configurations
    NTFY_TOPIC = os.getenv("NTFY_TOPIC")
    NTFY_SERVER = os.getenv("NTFY_SERVER", "https://ntfy.sh").rstrip("/")

    @classmethod
    def validate(cls):
        """Validates that the configuration has at least one valid notification channel."""
        errors = []
        if not cls.PARIBU_URL and not cls.BILETINIAL_URL:
            errors.append("At least one monitoring URL must be configured (PARIBU_URL or BILETINIAL_URL).")
            
        has_telegram = bool(cls.TELEGRAM_BOT_TOKEN and cls.TELEGRAM_CHAT_ID)
        has_ntfy = bool(cls.NTFY_TOPIC)
        
        if not (has_telegram or has_ntfy):
            errors.append("You must configure at least one notification channel (Telegram or ntfy).")
            
        return len(errors) == 0, errors
