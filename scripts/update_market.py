from pathlib import Path
from datetime import datetime, timezone
import json, time
from curl_cffi import requests
from urllib.parse import quote

ASSETS=[
("GOLD",["GC=F"],"GOLD","USD"),("SILVER",["SI=F"],"SILVER","USD"),("COPPER",["HG=F"],"COPPER","USD"),
("ZINC",["ZNC=F"],"ZINC","USD"),("LEAD",["PB=F"],"LEAD","USD"),("MOLYBDENUM",["MOLY=F"],"MOLYBDENUM","USD"),
("COAL",["MTF=F"],"COAL","USD"),("NICKEL",["NICKEL=F"],"NICKEL","USD"),
("Outcrop Silver",["OCG.V"],"TSXV: OCG","CAD"),("Collective Mining",["CNL"],"NYSE: CNL","USD"),
("Orosur Mining",["OMI.V"],"TSXV: OMI","CAD"),("Max Resource",["MAX.V"],"TSXV: MAX","CAD"),
("Quimbaya Gold",["QIM.CN"],"CSE: QIM","CAD"),("Tiger Gold",["TIGR.V"],"TSXV: TIGR","CAD"),
("Royal Road Minerals",["RYR.V"],"TSXV: RYR","CAD"),("Andina Copper",["ANDC.V"],"TSXV: ANDC","CAD"),
("Copper Giant Resources",["CGNT.V"],"TSXV: CGNT","CAD"),("Terra Rossa Gold",["TRR.V"],"TSXV: TRR","CAD"),
("Mineros",["MSA.TO"],"TSX: MSA","CAD"),("Aris Mining",["ARIS.TO"],"TSX: ARIS","CAD"),
("Soma Gold",["SOMA.V"],"TSXV: SOMA","CAD"),("AngloGold Ashanti",["AU"],"NYSE: AU","USD"),
("Glencore",["GLNCY"],"OTC: GLNCY","USD"),("Zijin Mining",["2899.HK"],"HKEX: 2899","HKD"),
("South32",["S32.AX"],"ASX: S32","AUD"),("Denarius Metals",["DMET.NE","DNRSF"],"Cboe CA: DMET","CAD")]
HEADERS={"User-Agent":"Mozilla/5.0"}
def q(symbol):
 u="https://query1.finance.yahoo.com/v8/finance/chart/"+quote(symbol,safe="")
 r=requests.get(u,params={"range":"5d","interval":"1d"},headers=HEADERS,impersonate="chrome",timeout=20)
 r.raise_for_status(); o=r.json()["chart"]["result"][0]; m=o.get("meta",{})
 p=m.get("regularMarketPrice"); prev=m.get("chartPreviousClose") or m.get("previousClose")
 if p is None:
  vals=[x for x in o["indicators"]["quote"][0]["close"] if x is not None]
  if vals: p=vals[-1]
  if len(vals)>1: prev=vals[-2]
 return p,prev,m.get("currency")
items=[]
for name,symbols,display,currency in ASSETS:
 p=prev=cur=None; used=symbols[0]
 for s in symbols:
  try:
   p,prev,cur=q(s); used=s
   if p is not None: break
  except Exception as e: print("WARNING",s,e)
  time.sleep(.1)
 ch=((p-prev)/prev*100) if p is not None and prev not in (None,0) else None
 items.append({"name":name,"symbol":used,"displaySymbol":display,"currency":cur or currency,"price":p,"changePercent":ch})
Path("data").mkdir(exist_ok=True)
Path("data/market_data.json").write_text(json.dumps({"updated_at":datetime.now(timezone.utc).isoformat(),"items":items},indent=2),encoding="utf-8")
ok=sum(x["price"] is not None for x in items)
print("Prices obtained:",ok,"/",len(items))
if ok==0: raise SystemExit("No prices retrieved")
