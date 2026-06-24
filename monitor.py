import os
import sys
import time
import json
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from config import Config
from notifier import Notifier

# Configure Logging
log_dir = os.path.dirname(Config.LOG_FILE_PATH)
if log_dir:
    os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Config.LOG_FILE_PATH, encoding="utf-8")
    ],
    force=True
)
logger = logging.getLogger("monitor")

def load_state():
    """Loads the previous sale status of all targets from the state file."""
    if os.path.exists(Config.STATE_FILE_PATH):
        try:
            with open(Config.STATE_FILE_PATH, "r", encoding="utf-8") as f:
                content = json.load(f)
                # Ensure it returns a dictionary
                if isinstance(content, dict):
                    return content
        except Exception as e:
            logger.warning(f"Could not read state file: {e}. Starting fresh.")
    return {}

def save_state(target_key, tickets_on_sale):
    """Saves the status of a specific target to the state file."""
    state = load_state()
    state[target_key] = {
        "tickets_on_sale": tickets_on_sale,
        "last_checked": datetime.now().isoformat()
    }
    try:
        with open(Config.STATE_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)
    except Exception as e:
        logger.error(f"Could not save state file: {e}")

def check_paribu(html_content):
    """Parses Paribu Cineverse HTML content to check if tickets are on sale."""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        # Find all anchor tags that have 'cgv-btn' in their class list
        anchors = soup.find_all("a", class_="cgv-btn")
        for a in anchors:
            href = a.get("href", "")
            text = a.get_text()
            
            # Check if the href contains '/biletleme/' and text contains 'Hemen Bilet Al'
            if "/biletleme/" in href.lower() and "hemen bilet al" in text.lower():
                logger.info(f"Paribu match found: href='{href}', text='{text.strip()}'")
                return True
        return False
    except Exception as e:
        logger.error(f"Error parsing Paribu HTML: {e}")
        return False

def check_biletinial(html_content, keywords):
    """Parses Biletinial HTML content to check if target keywords are present."""
    if not keywords:
        return False
    try:
        content_lower = html_content.lower()
        for kw in keywords:
            if kw in content_lower:
                logger.info(f"Biletinial match found: keyword='{kw}'")
                return True
        return False
    except Exception as e:
        logger.error(f"Error parsing Biletinial HTML: {e}")
        return False

def fetch_page(url):
    """Fetches a URL with realistic browser headers."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch page at {url}: {e}")
        return None

def run_once():
    """Runs a single check loop across all configured targets."""
    # Define active targets from configurations
    targets = []
    
    if Config.PARIBU_URL:
        targets.append({
            "key": "paribu",
            "name": "Paribu Cineverse",
            "url": Config.PARIBU_URL,
            "check_fn": check_paribu,
            "on_sale_message": (
                "<b>Paribu Cineverse Biletleri Satışta!</b>\n\n"
                "Örümcek-Adam: Yepyeni Bir Gün filminin biletleri satışa çıktı!\n"
                f"Bilet almak için hemen tıklayın: <a href='{Config.PARIBU_URL}'>Paribu Cineverse</a>"
            )
        })
        
    if Config.BILETINIAL_URL:
        keywords = Config.get_biletinial_keywords()
        targets.append({
            "key": "biletinial",
            "name": "Biletinial",
            "url": Config.BILETINIAL_URL,
            "check_fn": lambda html: check_biletinial(html, keywords),
            "on_sale_message": (
                "<b>Biletinial Bildirimi!</b>\n\n"
                "Biletinial sayfasında aradığınız film (Spider-Man/Örümcek) bulundu!\n"
                f"Kontrol etmek için tıklayın: <a href='{Config.BILETINIAL_URL}'>Biletinial Sinema</a>"
            )
        })

    if not targets:
        logger.warning("No monitoring targets are active. Check configuration.")
        return

    all_states = load_state()
    
    for target in targets:
        logger.info(f"Checking target [{target['name']}] at URL: {target['url']}")
        html = fetch_page(target["url"])
        if html is None:
            logger.warning(f"Could not retrieve website HTML for {target['name']}. Skipping.")
            continue
            
        tickets_available = target["check_fn"](html)
        
        # Get previous state for this target
        target_state = all_states.get(target["key"], {})
        previous_status = target_state.get("tickets_on_sale", False)
        
        if tickets_available:
            if not previous_status:
                logger.info(f"[{target['name']}] TICKETS ARE ON SALE! Sending notifications...")
                notified = Notifier.notify(Config, target["on_sale_message"], click_url=target["url"])
                if notified:
                    logger.info(f"Notifications sent for {target['name']}. Updating state.")
                    save_state(target["key"], tickets_on_sale=True)
                else:
                    logger.error(f"Failed to send notifications for {target['name']}. Will retry next time.")
            else:
                logger.info(f"[{target['name']}] Tickets are still on sale. Notification already sent previously.")
        else:
            if previous_status:
                logger.info(f"[{target['name']}] Tickets are no longer detected on sale. Resetting state.")
                save_state(target["key"], tickets_on_sale=False)
            else:
                logger.info(f"[{target['name']}] Tickets are not on sale yet.")
                save_state(target["key"], tickets_on_sale=False)

def main():
    # Validate configuration
    valid, errors = Config.validate()
    if not valid:
        for err in errors:
            logger.error(err)
        sys.exit(1)
        
    logger.info("Starting Multi-Target Ticket Monitor...")
    logger.info(f"Checking every {Config.CHECK_INTERVAL_SECONDS} seconds.")
    
    # If run with --once argument, execute once and exit (for cron)
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_once()
        sys.exit(0)
        
    # Otherwise run in daemon loop mode
    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user.")
            break
        except Exception as e:
            logger.critical(f"Unexpected error in monitor loop: {e}", exc_info=True)
            
        time.sleep(Config.CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
