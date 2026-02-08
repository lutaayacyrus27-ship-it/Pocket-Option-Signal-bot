import os
import requests
import pandas as pd
import ta
import time
from datetime import datetime

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOL = "EURUSD"
CHECK_INTERVAL = 30  # seconds
BINANCE_API = "https://api.binance.com/api/v3/klines"

LAST_SIGNAL = None
LAST_SIGNAL_TIME = None

# ============================================

def send_signal(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def get_candles():
    params = {
        "symbol": "EURUSDT",
        "interval": "1m",
        "limit": 100
    }
    response = requests.get(BINANCE_API, params=params, timeout=10)
    data = response.json()

    if not isinstance(data, list) or len(data) < 30:
        return None

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "ct","qv","n","tb","tq","ignore"
    ])

    df["close"] = df["close"].astype(float)
    return df

def analyze_market():
    global LAST_SIGNAL, LAST_SIGNAL_TIME

    df = get_candles()
    if df is None or len(df) < 30:
        return None

    df["ema5"] = ta.trend.EMAIndicator(df["close"], 5).ema_indicator()
    df["ema20"] = ta.trend.EMAIndicator(df["close"], 20).ema_indicator()
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], 14).rsi()

    df.dropna(inplace=True)
    if len(df) < 2:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    signal = None

    if (
        prev["ema5"] < prev["ema20"] and
        last["ema5"] > last["ema20"] and
        50 < last["rsi"] < 70
    ):
        signal = "BUY"

    elif (
        prev["ema5"] > prev["ema20"] and
        last["ema5"] < last["ema20"] and
        30 < last["rsi"] < 50
    ):
        signal = "SELL"

    if signal:
        now = datetime.utcnow()
        if signal == LAST_SIGNAL and LAST_SIGNAL_TIME:
            if (now - LAST_SIGNAL_TIME).seconds < 60:
                return None

        LAST_SIGNAL = signal
        LAST_SIGNAL_TIME = now
        return signal

    return None

# ================== MAIN LOOP ==================
print("🚀 Pocket Option Signal Bot running on Railway...")

while True:
    try:
        signal = analyze_market()

        if signal:
            time_now = datetime.utcnow().strftime("%H:%M:%S UTC")
            message = f"""
📊 <b>POCKET OPTION SIGNAL</b>

💱 Pair: <b>{SYMBOL}</b>
📈 Direction: <b>{signal}</b>
⏱ Expiry: <b>30s–1m</b>
🕒 Time: <b>{time_now}</b>

⚠️ Use proper risk management
"""
            send_signal(message)
            print(f"Signal sent: {signal}")

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print("Error:", e)
        time.sleep(15)
