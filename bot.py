import os, time, yfinance as yf, requests
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

send_telegram("✅ BOT LIVE - Nifty 500 Scan (1-4%) Started")

while True:
    # Yaha aapka 8-step wala logic ayega
    # Abhi ke liye demo scan
    try:
        data = yf.Ticker("RELIANCE.NS").history(period="2d")
        change = ((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
        if 1 <= change <= 4:
            send_telegram(f"🔥 RELIANCE {round(change,2)}% - BUY Signal")
    except:
        pass
    time.sleep(900) # 15 min