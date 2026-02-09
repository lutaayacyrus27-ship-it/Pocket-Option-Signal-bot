import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone
import time
import random
import os

# ===== Email Settings =====
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")  # sender email
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # app password
EMAIL_RECEIVER = "lutaayacyrus27@gmail.com"  # your email to receive signals

if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    raise ValueError("EMAIL_ADDRESS or EMAIL_PASSWORD not set in environment variables!")

# ===== Strategy Parameters =====
EMA_FAST = 5
EMA_SLOW = 10
RSI_OVERBOUGHT = 65
RSI_OVERSOLD = 35
ADX_MIN = 15
TRADE_DURATION = 30  # seconds
MIN_PAYOUT = 60      # minimum payout % to trade

# ===== List of assets (example) =====
ASSETS = ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD"]

# ===== Demo market data function =====
def get_market_data(asset):
    # Simulate EMA, RSI, ADX, and payout
    ema_fast = random.uniform(1.0, 1.5)
    ema_slow = random.uniform(1.0, 1.5)
    rsi = random.uniform(20, 80)
    adx = random.uniform(10, 30)
    payout = random.uniform(50, 90)  # payout %
    return ema_fast, ema_slow, rsi, adx, payout

# ===== Function to send email =====
def send_email(subject, message):
    try:
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_RECEIVER

        # Connect to Gmail SMTP server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"[EMAIL SENT] {subject}")
    except Exception as e:
        print("Email send failed:", e)

# ===== Main bot loop =====
def main():
    print("Bot started ✅")
    send_email("Bot Deployed", "✅ Bot deployed and running successfully!")

    while True:
        entry_time = datetime.now(timezone.utc)

        # Auto-switch asset based on payout
        best_asset = None
        best_payout = 0
        asset_data = {}

        for asset in ASSETS:
            ema_fast, ema_slow, rsi, adx, payout = get_market_data(asset)
            asset_data[asset] = (ema_fast, ema_slow, rsi, adx, payout)
            if payout >= MIN_PAYOUT and payout > best_payout:
                best_payout = payout
                best_asset = asset

        if not best_asset:
            print("[SKIP] No asset meets minimum payout")
            time.sleep(TRADE_DURATION)
            continue

        ema_fast, ema_slow, rsi, adx, payout = asset_data[best_asset]

        # Debug
        print(f"[DEBUG] Chosen Asset: {best_asset} | EMA_FAST={ema_fast:.5f} EMA_SLOW={ema_slow:.5f} RSI={rsi:.2f} ADX={adx:.2f} Payout={payout:.2f}%")

        # Skip if ADX too low
        if adx < ADX_MIN:
            print("[SKIP] ADX too low")
            time.sleep(TRADE_DURATION)
            continue

        # Determine signal
        signal = None
        if ema_fast > ema_slow and rsi < RSI_OVERSOLD:
            signal = "BUY"
        elif ema_fast < ema_slow and rsi > RSI_OVERBOUGHT:
            signal = "SELL"

        if signal:
            subject = f"📈 Trading Signal: {signal} | {best_asset}"
            message = (
                f"Signal: {signal}\n"
                f"Asset: {best_asset}\n"
                f"EMA Fast: {ema_fast:.2f}, EMA Slow: {ema_slow:.2f}\n"
                f"RSI: {rsi:.2f}, ADX: {adx:.2f}\n"
                f"Payout: {payout:.2f}%\n"
                f"Entry Time (UTC): {entry_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Trade Duration: {TRADE_DURATION} seconds"
            )
            send_email(subject, message)
        else:
            print("[NO SIGNAL] Conditions not met for", best_asset)

        # Wait for scalping interval
        time.sleep(TRADE_DURATION)

if __name__ == "__main__":
    main()
