from pathlib import Path
from datetime import datetime, timezone
import json, math
import yfinance as yf

ASSETS = [
("GOLD","GC=F","GOLD","USD"),("SILVER","SI=F","SILVER","USD"),("COPPER","HG=F","COPPER","USD"),
("ZINC","ZNC=F","ZINC","USD"),("LEAD","PB=F","LEAD","USD"),("MOLYBDENUM","MOLY=F","MOLYBDENUM","USD"),
("COAL","MTF=F","COAL","USD"),("NICKEL","NICKEL=F","NICKEL","USD"),
("Outcrop Silver","OCG.V","TSXV: OCG","CAD"),("Collective Mining","CNL","NYSE: CNL","USD"),
("Orosur Mining","OMI.V","TSXV: OMI","CAD"),("Max Resource","MAX.V","TSXV: MAX","CAD"),
("Quimbaya Gold","QIM.CN","CSE: QIM","CAD"),("Tiger Gold","TIGR.V","TSXV: TIGR","CAD"),
("Royal Road Minerals","RYR.V","TSXV: RYR","CAD"),("Andina Copper","ANDC.V","TSXV: ANDC","CAD"),
("Copper Giant Resources","CGNT.V","TSXV: CGNT","CAD"),("Terra Rossa Gold","TRR.V","TSXV: TRR","CAD"),
("Mineros","MSA.TO","TSX: MSA","CAD"),("Aris Mining","ARIS.TO","TSX: ARIS","CAD"),
("Soma Gold","SOMA.V","TSXV: SOMA","CAD"),("AngloGold Ashanti","AU","NYSE: AU","USD"),
("Glencore","GLNCY","OTC: GLNCY","USD"),("Zijin Mining","2899.HK","HKEX: 2899","HKD"),
("South32","S32.AX","ASX: S32","AUD"),("Denarius Metals","DNRSF","OTCQX: DNRSF","USD")
]

def num(x):
    try:
        x=float(x)
        return None if math.isnan(x) or math.isinf(x) else x
    except Exception:
        return None

items=[]
for name,symbol,display,currency in ASSETS:
    price=prev=None
    try:
        df=yf.download(symbol, period="5d", interval="1d", auto_adjust=False, progress=False, threads=False)
        if not df.empty:
            s=df["Close"]
            if getattr(s, "ndim", 1) > 1: s=s.iloc[:,0]
            vals=[num(v) for v in s.dropna().tolist()]
            vals=[v for v in vals if v is not None]
            if vals:
                price=vals[-1]
                if len(vals)>1: prev=vals[-2]
    except Exception as e:
        print(f"WARNING {symbol}: {e}")
    change=((price-prev)/prev*100) if price is not None and prev not in (None,0) else None
    items.append({"name":name,"symbol":symbol,"displaySymbol":display,"currency":currency,
                  "price":price,"changePercent":change})

Path("data").mkdir(exist_ok=True)
Path("data/market_data.json").write_text(json.dumps({
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "items": items
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("market_data.json written:", len(items), "assets")
