import os
import requests

# Load local .env file by looking up from script directory
def load_dotenv():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to workspace root
    base_dir = os.path.dirname(script_dir)
    filepath = os.path.join(base_dir, ".env")
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip().strip("'").strip('"')

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print(f"TELEGRAM_BOT_TOKEN is {'configured' if TELEGRAM_BOT_TOKEN else 'MISSING'}")
print(f"TELEGRAM_CHAT_ID is {'configured' if TELEGRAM_CHAT_ID else 'MISSING'}")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("\n[FAIL] Please configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your local env or GitHub secrets.")
else:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': "🤖 <b>Test Message</b>\n\nConnection verified from Roshini's Home Products AI Marketing Engine!",
        'parse_mode': 'HTML'
    }
    
    print("\nSending test message to Telegram...")
    try:
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            print("[SUCCESS] Test message sent successfully! Check your Telegram channel.")
        else:
            print(f"[FAIL] Telegram API returned status code {res.status_code}")
            print(f"Error Details: {res.text}")
            print("\nTroubleshooting tips:")
            print("1. Verify that your bot has been added as an Administrator inside your Telegram Channel/Group.")
            print("2. Ensure the bot has 'Post Messages' permission enabled.")
            print("3. Check that the chat ID is correct (public channels start with @, private groups/channels are negative numbers starting with -100).")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
