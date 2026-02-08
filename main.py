import os
import requests
import pandas as pd
import ta
import time
from datetime import datetime

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = {
    "EURUSD": "EURUSDT",
    "GBPUSD": "GBPUSDT",
    "USDJPY": "USDJPY"
}

CHECK_INTERVAL = 30  # seconds
BINANCE_API = "https://api.binance.com/api/v3/klines"

ADX_MIN = 20  # strength filter
LAST_SIGNAL = {}
TEST_MESSAGE_SENT = False

# ============================================

def send_signal(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def in_trading_session():
    hour = datetime.utcnow().hour
    # London (07–10 UTC) + NY (12–16 UTC)
    return (7 <= hour <= 10) or (12 <= hour <= 16)

def get_candles(symbol):
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 100
    }
    r = requests.get(BINANCE_API, params=params, timeout=10)
    data = r.json()

    if not isinstance(data, list) or len(data) < 30:
        return None

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "ct","qv","n","tb","tq","ignore"
    ])

    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    return df

def analyze_pair(pair_name, symbol):
    df = get_candles(symbol)
    if df is None:
        return None

    df["ema5"] = ta.trend.EMAIndicator(df["close"], 5).ema_indicator()
    df["ema20"] = ta.trend.EMAIndicator(df["close"], 20).ema_indicator()
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], 14).rsi()
    df["adx"] = ta.trend.ADXIndicator(
        df["high"], df["low"], df["close"], 14
    ).adx()

    df.dropna(inplace=True)
    if len(df) < 2:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if last["adx"] < ADX_MIN:
        return None

    # BUY
    if (
        prev["ema5"] < prev["ema20"] and
        last["ema5"] > last["ema20"] and
        last["rsi"] > 50
    ):
        return "BUY"

    # SELL
    if (
        prev["ema5"] > prev["ema20"] and
        last["ema5"] < last["ema20"] and
        last["rsi"] < 50
    ):
        return "SELL"

    return None

# ================== MAIN LOOP ==================
print("🚀 Pocket Option PRO Signal Bot running on Railway...")

while True:
    try:
        # ---- Step 5 test message ----
        if not TEST_MESSAGE_SENT:
            send_signal("✅ Bot connected | ADX + Sessions + Multi-Pairs active")
            TEST_MESSAGE_SENT = True

        if not in_trading_session():
            time.sleep(60)
            continue

        for pair, symbol in SYMBOLS.items():
            signal = analyze_pair(pair, symbol)
            now = datetime.utcnow()

            if signal:
                last_time = LAST_SIGNAL.get(pair)
                if last_time and (now - last_time).seconds < 120:
                    continue

                LAST_SIGNAL[pair] = now

                msg = f"""
📊 <b>POCKET OPTION SIGNAL</b>

💱 Pair: <b>{pair}</b>
📈 Direction: <b>{signal}</b>
⏱ Expiry: <b>30s–1m</b>
🕒 Time: <b>{now.strftime('%H:%M:%S UTC')}</b>
🔥 Strength: <b>ADX Confirmed</b>

⚠️ Risk 1–2% per trade
"""
                send_signal(msg)
                print(f"{pair} → {signal}")
                time.sleep(60)

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print("Error:", e)
        time.sleep(15)
