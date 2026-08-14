import json, re, sys, time, datetime, urllib.request, urllib.error, gzip
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
PULL = datetime.date(2026, 8, 13)
TITLE_RE = re.compile(r"\b(data|business)\s+analyst\b", re.I)

ORACLE = {  # company -> (host, siteNumber, careers_url)
 "Oracle":                ("eeho.fa.us2.oraclecloud.com","CX_45001","https://careers.oracle.com/jobs"),
 "Kroger":                ("eluq.fa.us2.oraclecloud.com","CX_2001","https://jobs.kroger.com/"),
 "JPMorgan Chase":        ("jpmc.fa.oraclecloud.com","CX_1001","https://careers.jpmorgan.com/us/en/jobs"),
 "Albertsons":            ("eofd.fa.us6.oraclecloud.com","CX_1001","https://careers.albertsons.com/"),
 "American Express":      ("egug.fa.us2.oraclecloud.com","CX_1","https://www.americanexpress.com/en-us/careers/"),
 "Uber Technologies":     ("iaziqy.fa.ocs.oraclecloud.com","CX_1","https://www.uber.com/us/en/careers/list/"),
}
PHENOM = {
 "Costco Wholesale":      ("careers.costco.com","https://careers.costco.com/"),
 "State Farm Insurance":  ("jobs.statefarm.com","https://jobs.statefarm.com/"),
 "PepsiCo":               ("www.pepsicojobs.com","https://www.pepsicojobs.com/"),
}
GREENHOUSE = {"Galaxy Digital": ("galaxydigitalservices","https://www.galaxy.com/careers/")}

RANK = {"Amazon":1,"Kroger":27,"JPMorgan Chase":12,"Costco Wholesale":13,"State Farm Insurance":32,
        "PepsiCo":46,"American Express":56,"Albertsons":57,"Oracle":82,"Uber Technologies":92,
        "Galaxy Digital":76}

US_STATE = re.compile(r"\b(Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|"
 r"Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|"
 r"Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|"
 r"North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|"
 r"Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|Puerto Rico|District of Columbia)\b", re.I)
ABBR = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND "
           "OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR".split())
NON_US = re.compile(r"India|Bangalore|Bengaluru|Hyderabad|Pune|Chennai|Mumbai|Gurgaon|Gurugram|Noida|Canada|Toronto|"
 r"Ontario|Vancouver|Mexico|Brazil|China|Shanghai|Japan|Tokyo|Korea|Singapore|Malaysia|Philippines|Manila|Thailand|"
 r"Vietnam|Indonesia|Hong Kong|Australia|Sydney|New Zealand|United Kingdom|London|Ireland|Dublin|Germany|France|"
 r"Spain|Italy|Netherlands|Poland|Krakow|Warsaw|Romania|Hungary|Czech|Bulgaria|Portugal|Switzerland|Sweden|Denmark|"
 r"Norway|Finland|Belgium|Austria|Israel|Turkey|Egypt|South Africa|Nigeria|Saudi|Emirates|Dubai|Argentina|Colombia|"
 r"Chile|Peru|Costa Rica|Pakistan|Ukraine|Lithuania|Greece|Taiwan|Taipei", re.I)

def is_us(loc):
    l = (loc or "").strip()
    if not l: return False
    if NON_US.search(l): return False
    if re.search(r"\b(United States|USA|U\.S\.)\b", l, re.I) or l.upper().startswith("US"): return True
    if US_STATE.search(l): return True
    if any(t in ABBR for t in re.split(r"[,\s\-/|]+", l)): return True
    if re.search(r"remote|work at home|virtual|nationwide|anywhere", l, re.I): return True
    return False

def http(url, data=None, hdr=None, timeout=30, tries=3):
    for a in range(tries):
        try:
            h = {"User-Agent":UA,"Accept":"application/json","Accept-Encoding":"gzip"}
            if hdr: h.update(hdr)
            req = urllib.request.Request(url, data=data, headers=h, method="POST" if data else "GET")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    try: raw = gzip.decompress(raw)
                    except Exception: pass
                return json.loads(raw.decode("utf-8","replace"))
        except Exception:
            if a == tries-1: return None
            time.sleep(1.5*(a+1))
    return None

rows = []
def add(company, title, loc, pdate, url, req="", src=""):
    if not TITLE_RE.search(title): return
    if not pdate: return
    age = (PULL - pdate).days
    if age < 0 or age > 7: return
    if not is_us(loc): return
    rows.append({"rank":RANK.get(company,999),"company":company,"title":title.strip(),
                 "location":loc.strip(),"start_date":pdate.isoformat(),"age":age,
                 "url":url,"req_id":req,"source":src,"us_verdict":"US",
                 "posted_raw":f"Posted {pdate:%Y-%m-%d}","time_type":"-"})

# ---------------- Oracle Cloud
def do_oracle(item):
    company,(host,sn,cu) = item
    out=[]
    for kw in ("data analyst","business analyst"):
        u=(f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
           f"&expand=requisitionList.secondaryLocations&finder=findReqs;siteNumber={sn},"
           f"keyword={urllib.parse.quote(kw)},limit=100,sortBy=POSTING_DATES_DESC")
        j=http(u)
        if not j or not j.get("items"): continue
        for r in (j["items"][0].get("requisitionList") or []):
            pd=r.get("PostedDate")
            try: d=datetime.date.fromisoformat(pd[:10]) if pd else None
            except Exception: d=None
            locs=[r.get("PrimaryLocation") or ""]+[s.get("Name","") for s in (r.get("secondaryLocations") or [])]
            out.append((company,r.get("Title") or "", "; ".join(x for x in locs if x), d,
                        f"{cu}", str(r.get("Id") or ""), "Oracle Cloud"))
    return out

# ---------------- Phenom
def do_phenom(item):
    company,(hostname,cu)=item
    out=[]
    for kw in ("data analyst","business analyst"):
        for page in (1,2,3):
            j=http(f"https://{hostname}/api/jobs?keywords={urllib.parse.quote(kw)}&page={page}&limit=100")
            if not j: break
            jobs=j.get("jobs") or []
            if not jobs: break
            for w in jobs:
                d0=w.get("data") or {}
                pd=d0.get("posted_date") or d0.get("create_date")
                try: d=datetime.date.fromisoformat(pd[:10]) if pd else None
                except Exception: d=None
                loc=d0.get("full_location") or ", ".join(x for x in (d0.get("city"),d0.get("state"),d0.get("country")) if x)
                out.append((company, d0.get("title") or "", loc, d,
                            d0.get("apply_url") or cu, str(d0.get("req_id") or ""), "Phenom"))
            if len(jobs)<100: break
    return out

# ---------------- Amazon
def do_amazon(_):
    out=[]
    for kw in ("data analyst","business analyst"):
        for off in (0,100):
            j=http("https://www.amazon.jobs/en/search.json?"
                   f"base_query={urllib.parse.quote(kw)}&country=USA&result_limit=100&offset={off}&sort=recent")
            if not j: break
            jobs=j.get("jobs") or []
            if not jobs: break
            for w in jobs:
                pd=w.get("posted_date")
                d=None
                if pd:
                    for fmt in ("%B %d, %Y","%b %d, %Y"):
                        try: d=datetime.datetime.strptime(pd,fmt).date(); break
                        except Exception: pass
                out.append(("Amazon", w.get("title") or "", w.get("normalized_location") or w.get("location") or "",
                            d, "https://www.amazon.jobs"+(w.get("job_path") or ""), str(w.get("id_icims") or ""), "amazon.jobs"))
            if len(jobs)<100: break
    return out

# ---------------- Greenhouse
def do_gh(item):
    company,(board,cu)=item
    j=http(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=false")
    out=[]
    for w in (j or {}).get("jobs",[]):
        pd=w.get("updated_at") or w.get("first_published")
        try: d=datetime.date.fromisoformat(pd[:10]) if pd else None
        except Exception: d=None
        out.append((company, w.get("title") or "", (w.get("location") or {}).get("name",""), d,
                    w.get("absolute_url") or cu, str(w.get("id") or ""), "Greenhouse"))
    return out

import urllib.parse
jobs_lists=[]
with ThreadPoolExecutor(max_workers=10) as ex:
    futs=[]
    futs += list(ex.map(do_oracle, ORACLE.items()))
    futs += list(ex.map(do_phenom, PHENOM.items()))
    futs += list(ex.map(do_gh, GREENHOUSE.items()))
    futs += list(ex.map(do_amazon, [None]))
for lst in futs:
    for t in lst: add(*t)

# de-dup
seen=set(); uniq=[]
for r in rows:
    k=(r["company"], r["title"].lower(), r["location"].lower(), r["start_date"])
    if k in seen: continue
    seen.add(k); uniq.append(r)

json.dump(uniq, open("jobs_round2.json","w"), indent=1)
import collections
print("round2 US matches <=7d:", len(uniq), file=sys.stderr)
print("within 72h:", len([r for r in uniq if r["age"]<=3]), file=sys.stderr)
print(collections.Counter(r["company"] for r in uniq), file=sys.stderr)
