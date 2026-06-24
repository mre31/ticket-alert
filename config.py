import os
from dotenv import load_dotenv

# Load env variables from .env if present
load_dotenv()

class Config:
    # Target enablement flags (default to True)
    MONITOR_PARIBU = os.getenv("MONITOR_PARIBU", "true").lower() in ("true", "1", "yes")
    MONITOR_BILETINIAL = os.getenv("MONITOR_BILETINIAL", "true").lower() in ("true", "1", "yes")

    # Down alert configurations (whether to notify when a site check fails)
    ALERT_ON_PARIBU_DOWN = os.getenv("ALERT_ON_PARIBU_DOWN", "true").lower() in ("true", "1", "yes")
    ALERT_ON_BILETINIAL_DOWN = os.getenv("ALERT_ON_BILETINIAL_DOWN", "true").lower() in ("true", "1", "yes")

    # 1. Paribu Cineverse Configuration
    PARIBU_URL = os.getenv("PARIBU_URL")
    if PARIBU_URL is not None:
        PARIBU_URL = PARIBU_URL.strip()
    else:
        PARIBU_URL = "https://www.paribucineverse.com/fantastik-filmleri/orumcek-adam-yepyeni-bir-gun-filmi-izle"
    
    # 2. Biletinial Configuration
    BILETINIAL_URL = os.getenv("BILETINIAL_URL")
    if BILETINIAL_URL is not None:
        BILETINIAL_URL = BILETINIAL_URL.strip()
    else:
        BILETINIAL_URL = "https://biletinial.com/tr-tr/sinema"
    
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
    LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "monitor.log")

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
        has_paribu = bool(cls.MONITOR_PARIBU and cls.PARIBU_URL)
        has_biletinial = bool(cls.MONITOR_BILETINIAL and cls.BILETINIAL_URL)
        if not has_paribu and not has_biletinial:
            errors.append("At least one active monitoring target/URL must be configured.")
            
        has_telegram = bool(cls.TELEGRAM_BOT_TOKEN and cls.TELEGRAM_CHAT_ID)
        has_ntfy = bool(cls.NTFY_TOPIC)
        
        if not (has_telegram or has_ntfy):
            errors.append("You must configure at least one notification channel (Telegram or ntfy).")
            
        return len(errors) == 0, errors


