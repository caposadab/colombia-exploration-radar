from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote
import csv, io, json, time
from curl_cffi import requests

# Equities: Yahoo. Confirmed correction: Outcrop is TSX -> OCG.TO.
EQUITIES=[
("Outcrop Silver","OCG.TO","TSX: OCG","CAD"),
("Collective Mining","CNL","NYSE: CNL","USD"),
("Orosur Mining","OMI.V","TSXV: OMI","CAD"),
("Max Resource","MAX.V","TSXV: MAX","CAD"),
("Quimbaya Gold","QIM.CN","CSE: QIM","CAD"),
("Tiger Gold","TIGR.V","TSXV: TIGR","CAD"),
("Royal Road Minerals","RYR.V","TSXV: RYR","CAD"),
("Andina Copper","ANDC.V","TSXV: ANDC","CAD"),
("Copper Giant Resources","CGNT.V","TSXV: CGNT","CAD"),
("Terra Rossa Gold","TRR.V","TSXV: TRR","CAD"),
("Mineros","MSA.TO","TSX: MSA","CAD"),
("Aris Mining","ARIS.TO","TSX: ARIS","CAD"),
("Soma Gold","SOMA.V","TSXV: SOMA","CAD"),
("AngloGold Ashanti","AU","NYSE: AU","USD"),
("Glencore","GLNCY","OTC: GLNCY","USD"),
("Zijin Mining","2899.HK","HKEX: 2899","HKD"),
("South32","S32.AX","ASX: S32","AUD"),
("Denarius Metals","DMET.NE","Cboe CA: DMET","CAD"),
]

# Commodities: Stooq snapshot first, Yahoo fallback where available.
# Stooq documented symbols include gc.f, si.f, hg.f, zi.f, ni.f.
COMMODITIES=[
("GOLD","gc.f","GC=F","GOLD","USD"),
("SILVER","si.f","SI=F","SILVER","USD"),
("COPPER","hg.f","HG=F","COPPER","USD"),
("ZINC","zi.f","ZNC=F","ZINC","USD"),
("LEAD","pb.f","PB=F","LEAD","USD"),
("MOLYBDENUM","mo.f","MOLY=F","MOLYBDENUM","USD"),
("COAL","coal","MTF=F","COAL","USD"),
("NICKEL","ni.f","NICKEL=F","NICKEL","USD"),
]
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/142 Safari/537.36"}

def yahoo(symbol):
    u="https://query1.finance.yahoo.com/v8/finance/chart/"+quote(symbol,safe="")
    r=requests.get(u,params={"range":"5d","interval":"1d"},headers=UA,impersonate="chrome",timeout=20)
    r.raise_for_status()
    o=r.json()["chart"]["result"][0]; m=o.get("meta",{})
    p=m.get("regularMarketPrice")
    prev=m.get("chartPreviousClose") or m.get("previousClose")
    vals=[x for x in o.get("indicators",{}).get("quote",[{}])[0].get("close",[]) if x is not None]
    if p is None and vals: p=vals[-1]
    if prev is None and len(vals)>1: prev=vals[-2]
    return p,prev,m.get("currency")

def stooq_snapshot(symbol):
    u="https://stooq.com/q/l/"
    r=requests.get(u,params={"s":symbol,"f":"sd2t2ohlcvp","h":"","e":"csv"},
                   headers=UA,impersonate="chrome",timeout=20)
    r.raise_for_status()
    rows=list(csv.DictReader(io.StringIO(r.text)))
    if not rows: return None,None
    row=rows[0]
    # Field names vary by endpoint configuration; normalize.
    low={str(k).lower():v for k,v in row.items() if k}
    close=low.get("close")
    prev=low.get("prev") or low.get("previous")
    def n(v):
        try:
            if v in (None,"","N/D","-"): return None
            return float(v)
        except: return None
    return n(close),n(prev)

items=[]
for name,stq,yf,display,currency in COMMODITIES:
    p=prev=None; source=None
    try:
        p,prev=stooq_snapshot(stq)
        if p is not None: source="Stooq"
    except Exception as e: print("Stooq",name,e)
    if p is None:
        try:
            p,prev,_=yahoo(yf)
            if p is not None: source="Yahoo"
        except Exception as e: print("Yahoo",name,e)
    ch=((p-prev)/prev*100) if p is not None and prev not in (None,0) else None
    items.append({"name":name,"symbol":stq if source=="Stooq" else yf,"displaySymbol":display,
                  "currency":currency,"price":p,"changePercent":ch,"source":source})
    time.sleep(.1)

for name,symbol,display,currency in EQUITIES:
    p=prev=cur=None
    try: p,prev,cur=yahoo(symbol)
    except Exception as e: print("Yahoo",symbol,e)
    ch=((p-prev)/prev*100) if p is not None and prev not in (None,0) else None
    items.append({"name":name,"symbol":symbol,"displaySymbol":display,"currency":cur or currency,
                  "price":p,"changePercent":ch,"source":"Yahoo" if p is not None else None})
    time.sleep(.1)

Path("data").mkdir(exist_ok=True)
Path("data/market_data.json").write_text(json.dumps({
 "updated_at":datetime.now(timezone.utc).isoformat(),"items":items
},ensure_ascii=False,indent=2),encoding="utf-8")
ok=sum(x["price"] is not None for x in items)
print(f"Prices obtained: {ok}/{len(items)}")
if ok==0: raise SystemExit("No market prices retrieved; refusing to publish empty feed.")
