import sys
from config import Config
from notifier import Notifier

def main():
    print("Loading configuration from environment/.env...")
    # Validate
    valid, errors = Config.validate()
    if not valid:
        print("Configuration validation failed:")
        for err in errors:
            print(f" - {err}")
        print("Please check your .env file.")
        sys.exit(1)
        
    print(f"Paribu URL: {Config.PARIBU_URL}")
    print(f"Biletinial URL: {Config.BILETINIAL_URL}")
    print(f"ntfy topic: {Config.NTFY_TOPIC}")
    print(f"Telegram Bot Token configured: {bool(Config.TELEGRAM_BOT_TOKEN)}")
    
    message = (
        "Eğer bu bildirimi görüyorsanız bilet takip sisteminiz "
        "başarıyla bildirim gönderiyor demektir!"
    )
    
    print("\nSending test notification...")
    success = Notifier.notify(
        Config, 
        message, 
        click_url=Config.PARIBU_URL,
        title="[TEST] Bilet Alarmı Sistem Kontrolü",
        priority="3",
        tags="white_check_mark,test"
    )

    
    if success:
        print("\nSUCCESS: Test notification sent successfully!")
    else:
        print("\nFAILED: Failed to send test notification. Check your log and .env configurations.")

if __name__ == "__main__":
    main()
