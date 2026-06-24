import logging
import requests

logger = logging.getLogger(__name__)

class Notifier:
    @staticmethod
    def send_telegram(token, chat_id, message, title=None):
        """Sends a message via Telegram Bot API."""
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        full_message = message
        if title:
            full_message = f"<b>{title}</b>\n\n{message}"
        payload = {
            "chat_id": chat_id,
            "text": full_message,
            "parse_mode": "HTML"
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Telegram notification sent successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False

    @staticmethod
    def send_ntfy(server, topic, message, click_url=None, title=None, priority=None, tags=None):
        """Sends a message via ntfy.sh with optional custom title, priority, and tags."""
        from email.header import Header
        url = f"{server}/{topic}"
        
        raw_title = title if title is not None else "Biletler Satista!"
        try:
            encoded_title = Header(raw_title, 'utf-8').encode()
        except Exception:
            encoded_title = raw_title
            
        headers = {
            "Title": encoded_title,
            "Priority": str(priority) if priority is not None else "5",
            "Tags": tags if tags is not None else "rotating_light,ticket,popcorn"
        }
        if click_url:
            headers["Click"] = click_url
            
        try:
            # We encode message to utf-8
            response = requests.post(
                url, 
                data=message.encode("utf-8"), 
                headers=headers, 
                timeout=10
            )
            response.raise_for_status()
            logger.info("ntfy notification sent successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to send ntfy notification: {e}")
            return False

    @classmethod
    def notify(cls, config, message, click_url=None, title=None, priority=None, tags=None):
        """Sends notifications to all configured channels with custom parameters."""
        success = False
        
        # Check Telegram
        if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
            logger.info("Triggering Telegram notification...")
            tel_success = cls.send_telegram(
                config.TELEGRAM_BOT_TOKEN, 
                config.TELEGRAM_CHAT_ID, 
                message,
                title=title
            )
            if tel_success:
                success = True

        # Check ntfy
        if config.NTFY_TOPIC:
            logger.info("Triggering ntfy notification...")
            # For Telegram, HTML is fine. For ntfy, we strip HTML tags or use plain text.
            plain_message = message.replace("<b>", "").replace("</b>", "").replace("<a href=", "").replace(">Link</a>", "")
            ntfy_success = cls.send_ntfy(
                config.NTFY_SERVER, 
                config.NTFY_TOPIC, 
                plain_message,
                click_url=click_url,
                title=title,
                priority=priority,
                tags=tags
            )
            if ntfy_success:
                success = True
                
        return success

