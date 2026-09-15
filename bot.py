import os, time, yfinance as yf, pandas as pd, requests
from datetime import datetime, time as dtime
import pytz
from flask import Flask
import threading

app = Flask('')
@app.route('/')
def home(): return "BOT LIVE - WAITING FOR /start"
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_flask).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

NIFTY500 = ["360ONE.NS","ABB.NS","ABCAPITAL.NS","ABFRL.NS","ABSLAMC.NS","ACC.NS","ACMESOLAR.NS","ADANIENSOL.NS","ADANIENT.NS","ADANIGREEN.NS","ADANIPORTS.NS","ADANIPOWER.NS","ATGL.NS","AWL.NS","ALKEM.NS","AMBUJACEM.NS","ANGELONE.NS","APLAPOLLO.NS","APOLLOHOSP.NS","APOLLOTYRE.NS","ASHOKLEY.NS","ASIANPAINT.NS","ASTRAL.NS","AUROPHARMA.NS","DMART.NS","AXISBANK.NS","BAJAJ-AUTO.NS","BAJAJFINSV.NS","BAJFINANCE.NS","BALKRISIND.NS","BANDHANBNK.NS","BANKBARODA.NS","BANKINDIA.NS","BATAINDIA.NS","BEL.NS","BHARATFORG.NS","BHARTIARTL.NS","BHEL.NS","BIOCON.NS","BOSCHLTD.NS","BRITANNIA.NS","CESC.NS","CGPOWER.NS","CHAMBLFERT.NS","CHOLAFIN.NS","CIPLA.NS","COALINDIA.NS","COFORGE.NS","COLPAL.NS","CONCOR.NS","CROMPTON.NS","CUMMINSIND.NS","DABUR.NS","DALBHARAT.NS","DEEPAKNTR.NS","DELHIVERY.NS","DIVISLAB.NS","DIXON.NS","DLF.NS","DRREDDY.NS","EICHERMOT.NS","ESCORTS.NS","EXIDEIND.NS","FEDERALBNK.NS","GAIL.NS","GLENMARK.NS","GODREJCP.NS","GODREJPROP.NS","GRASIM.NS","GUJGASLTD.NS","HAL.NS","HDFCAMC.NS","HDFCBANK.NS","HDFCLIFE.NS","HEROMOTOCO.NS","HINDALCO.NS","HINDUNILVR.NS","ICICIBANK.NS","ICICIGI.NS","IDFCFIRSTB.NS","INDIANB.NS","INDHOTEL.NS","INDIGO.NS","INDUSINDBK.NS","INFY.NS","IOC.NS","IRCTC.NS","IRFC.NS","ITC.NS","JINDALSTEL.NS","JSWENERGY.NS","JSWSTEEL.NS","JUBLFOOD.NS","KOTAKBANK.NS","LT.NS","LTIM.NS","LUPIN.NS","M&M.NS","MARICO.NS","MARUTI.NS","MOTHERSON.NS","MPHASIS.NS","MRF.NS","MUTHOOTFIN.NS","NESTLEIND.NS","NTPC.NS","ONGC.NS","PATANJALI.NS","PERSISTENT.NS","PIDILITIND.NS","POLYCAB.NS","POWERGRID.NS","RELIANCE.NS","SBIN.NS","SUNPHARMA.NS","TATAMOTORS.NS","TATAPOWER.NS","TATASTEEL.NS","TCS.NS","TECHM.NS","TITAN.NS","ULTRACEMCO.NS","WIPRO.NS"]

trade_count = 0
traded_stocks = set()
BOT_ACTIVE = False
last_update_id = 0

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def telegram_listener():
    global BOT_ACTIVE, last_update_id, trade_count, traded_stocks
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}&timeout=10"
            r = requests.get(url, timeout=15).json()
            for upd in r.get("result", []):
                last_update_id = upd["update_id"]
                msg = upd.get("message", {})
                text = msg.get("text", "").lower().strip()
                chat = str(msg.get("chat", {}).get("id"))
                if chat!= str(CHAT_ID): continue
                if text in ["/start", "start", "chalu", "on"]:
                    BOT_ACTIVE = True
                    trade_count = 0
                    traded_stocks.clear()
                    send("🟢 *BOT STARTED*\nAb 9:25-10:30 me har 5 min Top 10 Gainers (1-4%) scan karega.\nBand karne ke liye `/stop` likho.")
                elif text in ["/stop", "stop", "band", "off"]:
                    BOT_ACTIVE = False
                    send("🔴 *BOT STOPPED*")
        except: pass
        time.sleep(2)

threading.Thread(target=telegram_listener, daemon=True).start()

def get_top_gainers():
    gainers = []
    for sym in NIFTY500:
        try:
            hist = yf.Ticker(sym).history(period="2d")
            if len(hist) < 2: continue
            chg = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100
            if 1 <= chg <= 4:
                gainers.append((sym, chg))
        except: continue
    gainers.sort(key=lambda x: x[1], reverse=True)
    return gainers[:10]

def scan_stock(symbol, change):
    global trade_count
    try:
        # FIX 1: Poore din ka data lo (9:15 se) EMA sahi banega
        df = yf.download(symbol, period="1d", interval="5m", progress=False)
        if len(df) < 5: return
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        if df.index.tz is None: df.index = df.index.tz_localize('UTC').tz_convert(IST)
        else: df.index = df.index.tz_convert(IST)

        # EMA poore din ke data pe
        df['EMA20'] = df['Close'].ewm(span=20).mean()

        # FIX 2: Lowest RED dhoondne ke liye AAJ KI SAARI candles (9:15 se)
        df_today_all = df.between_time("09:15", "10:30")
        if df_today_all.empty: return

        red_all = df_today_all[df_today_all['Close'] < df_today_all['Open']]
        if red_all.empty: return

        # Yahi hai tumhari sahi line - aaj ki saari me se lowest
        lowest = red_all.loc[red_all['Volume'].idxmin()]

        # FIX 3: Entry check sirf 9:25-10:30 wali last candle pe
        df_930 = df.between_time("09:25", "10:30")
        if df_930.empty: return
        last = df_930.iloc[-1]

        # EMA 20 ke upar hona chahiye
        if last['Close'] < last['EMA20']: return

        buy = float(lowest['High'] + 0.3)
        sl = float(lowest['Low'] - 0.3)
        risk = buy - sl
        if risk <= 0: return
        qty = max(1, int(200 / risk))

        # Tenneco wala case ab pakdega - High break
        if last['Close'] > buy and symbol not in traded_stocks:
            if trade_count >= 5: return
            t1 = buy + (risk*2)
            t2 = buy + (risk*10)
            msg = f"""🚀 *LONG: {symbol.replace('.NS','')} ({round(change,2)}%)*\nLowest Red: {lowest.name.strftime('%H:%M')} Vol:{int(lowest['Volume'])}\n💰 Buy Above: `{round(buy,2)}`\n🛑 SL: `{round(sl,2)}`\n📦 Qty: `{qty}` (200₹ Risk)\n🎯 T1: `{round(t1,2)}` | T2: `{round(t2,2)}`"""
            send(msg)
            traded_stocks.add(symbol)
            trade_count += 1
    except Exception as e:
        print(f"Error {symbol}: {e}")

send("👋 Bot Ready! `/start` likho.")

while True:
    now = datetime.now(IST)
    if BOT_ACTIVE and dtime(9,25) <= now.time() <= dtime(10,30) and now.weekday() < 5:
        if trade_count < 5:
            top10 = get_top_gainers()
            if top10:
                for sym, chg in top10:
                    scan_stock(sym, chg)
                    time.sleep(1)
    if now.hour == 9 and now.minute == 15:
        if BOT_ACTIVE:
            trade_count = 0
            traded_stocks.clear()
    time.sleep(300)
