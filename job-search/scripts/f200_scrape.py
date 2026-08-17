import json, re, sys, time, datetime, urllib.request, urllib.error, urllib.parse, gzip
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
PULL = datetime.date(2026, 8, 13)
TITLE_RE = re.compile(r"\b(data|business)\s+analyst\b", re.I)
JUNK_8FOLD = {"vs-errors", "app", "static", "assets"}

US_STATE = re.compile(r"\b(Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|"
 r"Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|"
 r"Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|"
 r"North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|"
 r"Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|Puerto Rico|District of Columbia)\b", re.I)
ABBR = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND "
           "OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR".split())
NON_US = re.compile(r"India|Bangalore|Bengaluru|Hyderabad|Pune|Chennai|Mumbai|Gurgaon|Gurugram|Noida|Delhi|Canada|"
 r"Toronto|Ontario|Vancouver|Montreal|Mexico|Brazil|China|Shanghai|Beijing|Japan|Tokyo|Korea|Seoul|Singapore|"
 r"Malaysia|Philippines|Manila|Thailand|Vietnam|Indonesia|Hong Kong|Australia|Sydney|New Zealand|United Kingdom|"
 r"London|Ireland|Dublin|Germany|Berlin|France|Paris|Spain|Madrid|Italy|Netherlands|Amsterdam|Poland|Krakow|Warsaw|"
 r"Romania|Bucharest|Hungary|Czech|Prague|Bulgaria|Portugal|Lisbon|Switzerland|Sweden|Denmark|Norway|Finland|"
 r"Belgium|Austria|Israel|Turkey|Egypt|South Africa|Nigeria|Saudi|Emirates|Dubai|Argentina|Colombia|Chile|Peru|"
 r"Costa Rica|Pakistan|Ukraine|Lithuania|Greece|Taiwan|Taipei|Switzerland", re.I)

def is_us(loc):
    l = (loc or "").strip()
    if not l: return False
    if NON_US.search(l): return False
    if re.search(r"\b(United States|USA|U\.S\.)\b", l, re.I) or l.upper().startswith("US"): return True
    if US_STATE.search(l): return True
    if any(t in ABBR for t in re.split(r"[,\s\-/|]+", l)): return True
    if re.search(r"remote|work at home|virtual|nationwide|anywhere|field", l, re.I): return True
    return False

def http(url, data=None, hdr=None, timeout=30, tries=3):
    for a in range(tries):
        try:
            h = {"User-Agent":UA,"Accept":"application/json","Accept-Encoding":"gzip"}
            if data is not None: h["Content-Type"] = "application/json"
            if hdr: h.update(hdr)
            req = urllib.request.Request(url, data=data, headers=h, method="POST" if data is not None else "GET")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    try: raw = gzip.decompress(raw)
                    except Exception: pass
                return json.loads(raw.decode("utf-8","replace"))
        except Exception:
            if a == tries-1: return None
            time.sleep(1.2*(a+1))
    return None

rows = []
STATUS = {}   # company -> (ok|failed, detail)
def add(rank, company, title, loc, pdate, url, req="", src=""):
    if not title or not TITLE_RE.search(title): return
    if not pdate: return
    age = (PULL - pdate).days
    if age < 0 or age > 7: return
    if not is_us(loc): return
    rows.append({"rank":rank,"company":company,"title":title.strip(),"location":(loc or "").strip(),
                 "start_date":pdate.isoformat(),"age":age,"url":url,"req_id":str(req or ""),
                 "source":src,"us_verdict":"US","posted_raw":f"Posted {pdate:%Y-%m-%d}","time_type":"-"})

def d_iso(s):
    try: return datetime.date.fromisoformat(str(s)[:10])
    except Exception: return None

def do_workday(rank, name, tenant, host, site):
    probe = http(f"https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs",
                 data=json.dumps({"appliedFacets":{},"limit":1,"offset":0,"searchText":"analyst"}).encode())
    if not probe or "jobPostings" not in probe:
        STATUS[name] = ("failed", f"Workday endpoint {tenant}.{host}/{site} did not respond")
        return []
    STATUS[name] = ("ok", f"Workday API ({tenant}.{host}/{site})")
    out=[]
    for kw in ("data analyst","business analyst"):
        for off in (0,20,40):
            j = http(f"https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs",
                     data=json.dumps({"appliedFacets":{},"limit":20,"offset":off,"searchText":kw}).encode())
            if not j: break
            posts = j.get("jobPostings") or []
            if not posts: break
            for jp in posts:
                po = (jp.get("postedOn") or "").lower()
                d = None
                if "today" in po or "just posted" in po: d = PULL
                elif "yesterday" in po: d = PULL - datetime.timedelta(days=1)
                else:
                    m = re.search(r"(\d+)\+?\s*day", po)
                    if m: d = PULL - datetime.timedelta(days=int(m.group(1)))
                out.append((rank,name,jp.get("title"),jp.get("locationsText"),d,
                    f"https://{tenant}.{host}.myworkdayjobs.com/{site}{jp.get('externalPath') or ''}",
                    (jp.get("bulletFields") or [""])[0], "Workday"))
            if len(posts) < 20: break
    return out

def do_oracle(rank, name, host, sn, cu):
    """Sweep candidate siteNumbers -- CX_1 is often empty even when the tenant is live."""
    best, best_sn = 0, None
    for cand in (sn, "CX_1", "CX_2", "CX_1001", "CX_2001", "CX_3001", "CX_4001"):
        j = http(f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
                 f"&expand=requisitionList&finder=findReqs;siteNumber={cand},keyword=analyst,limit=1")
        if not j or not j.get("items"): continue
        tot = j["items"][0].get("TotalJobsCount") or 0
        if tot > best: best, best_sn = tot, cand
    if not best_sn:
        STATUS[name] = ("failed", f"Oracle Cloud {host} returned no jobs for any siteNumber")
        return []
    STATUS[name] = ("ok", f"Oracle Cloud recruiting API ({host}, {best_sn})")
    out = []
    for kw in ("data analyst", "business analyst"):
        j = http(f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
                 f"&expand=requisitionList.secondaryLocations&finder=findReqs;siteNumber={best_sn},"
                 f"keyword={urllib.parse.quote(kw)},limit=100,sortBy=POSTING_DATES_DESC")
        if not j or not j.get("items"): continue
        for r in (j["items"][0].get("requisitionList") or []):
            locs = [r.get("PrimaryLocation") or ""] + [x.get("Name","") for x in (r.get("secondaryLocations") or [])]
            out.append((rank, name, r.get("Title"), "; ".join(x for x in locs if x),
                        d_iso(r.get("PostedDate")), cu, r.get("Id"), "Oracle Cloud"))
    return out

def do_phenom(rank, name, hostname):
    probe = http(f"https://{hostname}/api/jobs?keywords=analyst&page=1&limit=1")
    if not probe or not isinstance(probe.get("jobs"), list):
        STATUS[name] = ("failed", f"Phenom endpoint on {hostname} did not respond (HTTP 500 / not a jobs API)")
        return []
    STATUS[name] = ("ok", f"Phenom jobs API ({hostname})")
    out = []
    for kw in ("data analyst", "business analyst"):
        for page in (1, 2):
            j = http(f"https://{hostname}/api/jobs?keywords={urllib.parse.quote(kw)}&page={page}&limit=100")
            if not j: break
            jobs = j.get("jobs") or []
            if not jobs: break
            for w in jobs:
                d0 = w.get("data") or {}
                loc = d0.get("full_location") or ", ".join(
                    x for x in (d0.get("city"), d0.get("state"), d0.get("country")) if x)
                out.append((rank, name, d0.get("title"), loc,
                    d_iso(d0.get("posted_date") or d0.get("create_date")),
                    d0.get("apply_url") or f"https://{hostname}/", d0.get("req_id"), "Phenom"))
            if len(jobs) < 100: break
    return out

def do_eightfold(rank, name, tenant):
    STATUS[name] = ("ok", f"Eightfold API ({tenant}.eightfold.ai)")
    out=[]
    for dom in (f"{name.split()[0].lower()}.com", f"{tenant}.com"):
        for kw in ("data analyst","business analyst"):
            j = http(f"https://{tenant}.eightfold.ai/api/apply/v2/jobs?domain={dom}"
                     f"&start=0&num=100&query={urllib.parse.quote(kw)}")
            if not j: continue
            for p in (j.get("positions") or []):
                ts = p.get("t_create")
                d = None
                if ts:
                    try: d = datetime.datetime.utcfromtimestamp(int(ts)).date()
                    except Exception: d = d_iso(ts)
                out.append((rank,name,p.get("name"),p.get("location"),d,
                    f"https://{tenant}.eightfold.ai/careers?pid={p.get('id')}", p.get("id"), "Eightfold"))
        if out: break
    return out

eps = json.load(open("f200_endpoints.json"))
tasks = []
for o in eps:
    rank, name = o["rank"], o["name"]
    if "workday" in o:
        t,h,s = o["workday"]; tasks.append(("wd", rank, name, (t,h,s)))
    elif "oracle_host" in o:
        tasks.append(("or", rank, name, (o["oracle_host"], o.get("oracle_site","CX_1"), o.get("careers",""))))
    elif "phenom_host" in o:
        tasks.append(("ph", rank, name, (o["phenom_host"],)))
    elif "eightfold" in o and o["eightfold"] not in JUNK_8FOLD:
        tasks.append(("ef", rank, name, (o["eightfold"],)))

def run(t):
    kind, rank, name, args = t
    try:
        if kind=="wd": return do_workday(rank, name, *args)
        if kind=="or": return do_oracle(rank, name, args[0], args[1], args[2] or f"https://{args[0]}")
        if kind=="ph": return do_phenom(rank, name, args[0])
        if kind=="ef": return do_eightfold(rank, name, args[0])
    except Exception as e:
        print(f"  ERR {name}: {e}", file=sys.stderr)
    return []

print(f"scraping {len(tasks)} companies (ranks 101-200)...", file=sys.stderr)
with ThreadPoolExecutor(max_workers=12) as ex:
    for res in ex.map(run, tasks):
        for tup in res: add(*tup)

seen=set(); uniq=[]
for r in rows:
    k=(r["company"], r["title"].lower(), r["location"].lower(), r["start_date"])
    if k in seen: continue
    seen.add(k); uniq.append(r)

json.dump(uniq, open("jobs_f200.json","w"), indent=1)
json.dump(STATUS, open("f200_status.json","w"), indent=1)
ok = sum(1 for v in STATUS.values() if v[0]=="ok")
print(f"searched OK: {ok} | endpoint failed: {len(STATUS)-ok}", file=sys.stderr)
import collections
print(f"\nF200 US matches <=7d: {len(uniq)} | within 72h: {len([r for r in uniq if r['age']<=3])}", file=sys.stderr)
print(collections.Counter(r["company"] for r in uniq), file=sys.stderr)
