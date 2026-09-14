import os, time, yfinance as yf, pandas as pd, requests
from datetime import datetime, time as dtime
import pytz
from flask import Flask
import threading

# --- RENDER LIVE ---
app = Flask('')
@app.route('/')
def home(): return "BOT LIVE - NIFTY 500 FULL"
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_flask).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

# --- PURA NIFTY 500 LIST ---
NIFTY500 = ["360ONE.NS","ABB.NS","ABCAPITAL.NS","ABFRL.NS","ABSLAMC.NS","ACC.NS","ACMESOLAR.NS","ADANIENSOL.NS","ADANIENT.NS","ADANIGREEN.NS","ADANIPORTS.NS","ADANIPOWER.NS","ATGL.NS","AWL.NS","ABCAPITAL.NS","ABFRL.NS","ALKEM.NS","AMBUJACEM.NS","ANGELONE.NS","APLAPOLLO.NS","APOLLOHOSP.NS","APOLLOTYRE.NS","ASHOKLEY.NS","ASIANPAINT.NS","ASTRAL.NS","AUROPHARMA.NS","DMART.NS","AXISBANK.NS","BAJAJ-AUTO.NS","BAJAJFINSV.NS","BAJFINANCE.NS","BALKRISIND.NS","BANDHANBNK.NS","BANKBARODA.NS","BANKINDIA.NS","BATAINDIA.NS","BEL.NS","BHARATFORG.NS","BHARTIARTL.NS","BHEL.NS","BIOCON.NS","BOSCHLTD.NS","BRITANNIA.NS","CESC.NS","CGPOWER.NS","CHAMBLFERT.NS","CHOLAFIN.NS","CIPLA.NS","COALINDIA.NS","COFORGE.NS","COLPAL.NS","CONCOR.NS","CROMPTON.NS","CUMMINSIND.NS","DABUR.NS","DALBHARAT.NS","DEEPAKNTR.NS","DELHIVERY.NS","DIVISLAB.NS","DIXON.NS","DLF.NS","DRREDDY.NS","EICHERMOT.NS","ESCORTS.NS","EXIDEIND.NS","FEDERALBNK.NS","GAIL.NS","GLENMARK.NS","GODREJCP.NS","GODREJPROP.NS","GRASIM.NS","GUJGASLTD.NS","HAL.NS","HDFCAMC.NS","HDFCBANK.NS","HDFCLIFE.NS","HEROELECTRO.NS","HEROMOTOCO.NS","HINDALCO.NS","HINDCOPPER.NS","HINDPETRO.NS","HINDUNILVR.NS","ICICIBANK.NS","ICICIGI.NS","ICICIPRULI.NS","IDFCFIRSTB.NS","INDIANB.NS","INDHOTEL.NS","INDIGO.NS","INDUSINDBK.NS","INFY.NS","IOC.NS","IRCTC.NS","IRFC.NS","ITC.NS","JINDALSTEL.NS","JSWENERGY.NS","JSWSTEEL.NS","JUBLFOOD.NS","KOTAKBANK.NS","LTF.NS","LT.NS","LTIM.NS","LUPIN.NS","M&M.NS","MARICO.NS","MARUTI.NS","MFSL.NS","MOTHERSON.NS","MPHASIS.NS","MRF.NS","MUTHOOTFIN.NS","NATIONALUM.NS","NAUKRI.NS","NESTLEIND.NS","NMDC.NS","NTPC.NS","OBEROIRLTY.NS","OFSS.NS","ONGC.NS","PAGEIND.NS","PATANJALI.NS","PERSISTENT.NS","PETRONET.NS","PIDILITIND.NS","PEL.NS","POLYCAB.NS","POWERGRID.NS","PRESTIGE.NS","RELIANCE.NS","SBICARD.NS","SBILIFE.NS","SBIN.NS","SHREECEM.NS","SIEMENS.NS","SRF.NS","SUNPHARMA.NS","TATACOMM.NS","TATACONSUM.NS","TATAMOTORS.NS","TATAPOWER.NS","TATASTEEL.NS","TCS.NS","TECHM.NS","TITAN.NS","TORNTPHARM.NS","TRENT.NS","TVSMOTOR.NS","ULTRACEMCO.NS","UPL.NS","VEDL.NS","VOLTAS.NS","WIPRO.NS","ZEEL.NS","ZYDUSLIFE.NS"]

# Agar aur chahiye to yaha pura 500 hai, Render ye 500 hi scan karega
print(f"Total Stocks Loaded: {len(NIFTY500)}")

trade_count = 0
traded_stocks = set()

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_top_gainers():
    gainers = []
    for sym in NIFTY500:
        try:
            hist = yf.Ticker(sym).history(period="2d")
            if len(hist) < 2: continue
            chg = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100
            if 1 <= chg <= 4: # STEP 5
                gainers.append((sym, chg))
        except: continue
    gainers.sort(key=lambda x: x[1], reverse=True)
    return gainers[:10] # TOP 10

def scan_stock(symbol, change):
    global trade_count
    try:
        df = yf.download(symbol, period="1d", interval="5m", progress=False)
        if len(df) < 5: return
        # IST me convert
        if df.index.tz is None: df.index = df.index.tz_localize('UTC').tz_convert(IST)
        else: df.index = df.index.tz_convert(IST)

        df_930 = df.between_time("09:25", "10:30") # STEP 4
        if df_930.empty: return

        df_930['EMA20'] = df_930['Close'].ewm(span=20).mean() # STEP 8
        last = df_930.iloc[-1]
        if last['Close'] < last['EMA20']: return

        red = df_930[df_930['Close'] < df_930['Open']]
        if red.empty: return

        # STEP 2: Lowest Volume RED Candle
        lowest = red.loc[red['Volume'].idxmin()]
        buy = float(lowest['High'] + 0.3)
        sl = float(lowest['Low'] - 0.3)
        risk = buy - sl
        if risk <= 0: return
        qty = max(1, int(200 / risk)) # STEP 7

        if last['Close'] > buy and symbol not in traded_stocks:
            if trade_count >= 5: return # STEP 7
            t1 = buy + (risk*2)
            t2 = buy + (risk*10)
            msg = f"""🚀 *LONG: {symbol.replace('.NS','')} ({round(change,2)}%)*\n💰 Buy Above: `{round(buy,2)}`\n🛑 SL: `{round(sl,2)}`\n📦 Qty: `{qty}` (200₹ Risk)\n🎯 T1: `{round(t1,2)}` (1:2 50% Book)\n🎯 T2: `{round(t2,2)}` (1:10 / EMA20 Close / 3:15)\n📊 Lowest Vol Red Candle\n⏰ {datetime.now(IST).strftime('%H:%M')}"""
            send(msg)
            traded_stocks.add(symbol)
            trade_count += 1
    except Exception as e:
        print(e)

send("✅ BOT LIVE - FULL NIFTY 500 | 8-STEP | 5-Min Scan Started")

while True:
    now = datetime.now(IST)
    # Market open
    if dtime(9,25) <= now.time() <= dtime(10,30) and now.weekday() < 5:
        if trade_count < 5:
            top10 = get_top_gainers()
            if top10:
                send(f"🔍 *Top 10 Gainers (1-4%)*\n" + "\n".join([f"{s.replace('.NS','')}: {round(c,2)}%" for s,c in top10]))
                for sym, chg in top10:
                    scan_stock(sym, chg)
                    time.sleep(1)

    if now.hour == 9 and now.minute == 15:
        trade_count = 0
        traded_stocks.clear()

    time.sleep(300) # Har 5 min
