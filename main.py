import requests
from datetime import datetime, timezone
import time
import random
import os  # for environment variables

# ===== Telegram Bot Settings (from Railway environment variables) =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))

if not BOT_TOKEN or not CHANNEL_ID:
    raise ValueError("BOT_TOKEN or CHANNEL_ID is not set in environment variables!")

# ===== Strategy Parameters (example EMA/RSI/ADX) =====
EMA_FAST = 5
EMA_SLOW = 10
RSI_OVERBOUGHT = 65
RSI_OVERSOLD = 35
ADX_MIN = 15

# ===== Demo function to simulate market indicators =====
def get_market_data():
    # Replace this with your real market calculations
    ema_fast = random.uniform(1.0, 1.5)
    ema_slow = random.uniform(1.0, 1.5)
    rsi = random.uniform(20, 80)
    adx = random.uniform(10, 30)
    return ema_fast, ema_slow, rsi, adx

# ===== Function to send Telegram messages =====
def send_telegram_message(message):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHANNEL_ID, "text": message}
        )
    except Exception as e:
        print("Telegram send failed:", e)

# ===== Main trading loop =====
def main():
    print("Bot started ✅")
    send_telegram_message("✅ Bot deployed and connected to Telegram channel")

    while True:
        # Get current UTC hour (timezone-aware)
        hour = datetime.now(timezone.utc).hour

        # Simulate market data
        ema_fast, ema_slow, rsi, adx = get_market_data()

        # Debug logs to see why trades are skipped
        print(
            f"[DEBUG] EMA_FAST={ema_fast:.5f} | EMA_SLOW={ema_slow:.5f} | "
            f"RSI={rsi:.2f} | ADX={adx:.2f} | Hour={hour}"
        )

        # ===== Strategy logic =====
        if adx < ADX_MIN:
            print("[SKIP] ADX too low")
            time.sleep(5)
            continue

        signal = None
        if ema_fast > ema_slow and rsi < RSI_OVERSOLD:
            signal = "BUY"
        elif ema_fast < ema_slow and rsi > RSI_OVERBOUGHT:
            signal = "SELL"

        if signal:
            message = f"📈 Signal: {signal}\nEMA Fast: {ema_fast:.2f}, EMA Slow: {ema_slow:.2f}\nRSI: {rsi:.2f}, ADX: {adx:.2f}"
            print("[SIGNAL]", message)
            send_telegram_message(message)
        else:
            print("[NO SIGNAL] Conditions not met")

        # Wait 30 seconds (scalping interval)
        time.sleep(30)

if __name__ == "__main__":
    main()
