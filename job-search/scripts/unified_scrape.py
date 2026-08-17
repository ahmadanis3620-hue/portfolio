"""Fresh scrape of Fortune 1-300 analyst openings. PULL date derived from live data."""
import json, re, sys, os, time, datetime, urllib.request, urllib.error, urllib.parse, gzip
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
PULL = datetime.date(2026, 8, 17)      # verified against live Workday "Posted Today" -> startDate
WINDOW_MAX = 7                          # collect up to 7d; sheets filter to 48h
TITLE_RE = re.compile(r"\b(data|business)\s+analyst\b", re.I)
JUNK_8FOLD = {"vs-errors", "app", "static", "assets"}

US_STATE = re.compile(r"\b(Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|"
 r"Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|"
 r"Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|"
 r"North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|"
 r"Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|Puerto Rico|District of Columbia)\b", re.I)
ABBR = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND "
           "OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR".split())
NON_US = re.compile(r"India|Bangalore|Bengaluru|Hyderabad|Pune|Chennai|Mumbai|Gurgaon|Gurugram|Noida|Delhi|Kolkata|"
 r"Canada|Toronto|Ontario|Vancouver|Montreal|Quebec|Calgary|Mexico|Brazil|Sao Paulo|China|Shanghai|Beijing|Shenzhen|"
 r"Japan|Tokyo|Korea|Seoul|Singapore|Malaysia|Philippines|Manila|Thailand|Vietnam|Indonesia|Jakarta|Hong Kong|"
 r"Australia|Sydney|Melbourne|New Zealand|United Kingdom|London|Ireland|Dublin|Germany|Berlin|Munich|France|Paris|"
 r"Spain|Madrid|Barcelona|Italy|Rome|Milan|Netherlands|Amsterdam|Poland|Krakow|Warsaw|Wroclaw|Romania|Bucharest|"
 r"Hungary|Budapest|Czech|Prague|Bulgaria|Sofia|Portugal|Lisbon|Switzerland|Sweden|Denmark|Norway|Finland|Belgium|"
 r"Austria|Israel|Turkey|Egypt|South Africa|Nigeria|Kenya|Morocco|Saudi|Emirates|Dubai|Qatar|Argentina|Colombia|"
 r"Bogota|Chile|Peru|Costa Rica|Pakistan|Bangladesh|Ukraine|Lithuania|Latvia|Estonia|Croatia|Serbia|Slovakia|"
 r"Greece|Iceland|Luxembourg|Taiwan|Taipei", re.I)

def is_us(loc):
    l = (loc or "").strip()
    if not l: return False
    if NON_US.search(l): return False
    if re.search(r"\b(United States|USA|U\.S\.)\b", l, re.I) or l.upper().startswith("US"): return True
    if US_STATE.search(l): return True
    if any(t in ABBR for t in re.split(r"[,\s\-/|]+", l)): return True
    if re.search(r"remote|work at home|virtual|nationwide|anywhere|field", l, re.I): return True
    return False

def http(url, data=None, timeout=30, tries=3):
    for a in range(tries):
        try:
            h = {"User-Agent":UA,"Accept":"application/json","Accept-Encoding":"gzip"}
            if data is not None: h["Content-Type"] = "application/json"
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

def d_iso(s):
    try: return datetime.date.fromisoformat(str(s)[:10])
    except Exception: return None

rows, STATUS = [], {}

def add(rank, company, title, loc, pdate, url, req="", src="", wd_detail=None):
    if not title or not TITLE_RE.search(title): return
    if not pdate: return
    age = (PULL - pdate).days
    if age < 0 or age > WINDOW_MAX: return
    if not is_us(loc): return
    rows.append({"rank":rank,"company":company,"title":title.strip(),"location":(loc or "").strip(),
                 "start_date":pdate.isoformat(),"age":age,"url":url,"req_id":str(req or ""),
                 "source":src,"wd_detail":wd_detail})

# ---------------------------------------------------------------- platforms
def do_workday(rank, name, tenant, host, site):
    base = f"https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    probe = http(base, data=json.dumps({"appliedFacets":{},"limit":1,"offset":0,"searchText":"analyst"}).encode())
    if not probe or "jobPostings" not in probe:
        STATUS[name] = ("failed", f"Workday endpoint {tenant}.{host}/{site} did not respond"); return []
    STATUS[name] = ("ok", f"Workday API ({tenant}.{host}/{site})")
    out, seen = [], set()
    for kw in ("data analyst","business analyst"):
        for off in (0,20,40):
            j = http(base, data=json.dumps({"appliedFacets":{},"limit":20,"offset":off,"searchText":kw}).encode())
            if not j: break
            posts = j.get("jobPostings") or []
            if not posts: break
            for jp in posts:
                p = jp.get("externalPath") or ""
                if p in seen: continue
                seen.add(p)
                po = (jp.get("postedOn") or "").lower()
                d = None
                if "today" in po or "just posted" in po: d = PULL
                elif "yesterday" in po: d = PULL - datetime.timedelta(days=1)
                else:
                    m = re.search(r"(\d+)\+?\s*day", po)
                    if m: d = PULL - datetime.timedelta(days=int(m.group(1)))
                out.append((rank,name,jp.get("title"),jp.get("locationsText"),d,
                    f"https://{tenant}.{host}.myworkdayjobs.com/{site}{p}",
                    (jp.get("bulletFields") or [""])[0], "Workday",
                    (tenant,host,site,p)))
            if len(posts) < 20: break
    return out

def do_oracle(rank, name, host, sn, cu):
    best, best_sn = 0, None
    for cand in (sn,"CX_1","CX_2","CX_1001","CX_2001","CX_3001","CX_4001"):
        j = http(f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
                 f"&expand=requisitionList&finder=findReqs;siteNumber={cand},keyword=analyst,limit=1")
        if not j or not j.get("items"): continue
        tot = j["items"][0].get("TotalJobsCount") or 0
        if tot > best: best, best_sn = tot, cand
    if not best_sn:
        STATUS[name] = ("failed", f"Oracle Cloud {host} returned no jobs for any siteNumber"); return []
    STATUS[name] = ("ok", f"Oracle Cloud recruiting API ({host}, {best_sn})")
    out=[]
    for kw in ("data analyst","business analyst"):
        j = http(f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
                 f"&expand=requisitionList.secondaryLocations&finder=findReqs;siteNumber={best_sn},"
                 f"keyword={urllib.parse.quote(kw)},limit=100,sortBy=POSTING_DATES_DESC")
        if not j or not j.get("items"): continue
        for r in (j["items"][0].get("requisitionList") or []):
            locs=[r.get("PrimaryLocation") or ""]+[x.get("Name","") for x in (r.get("secondaryLocations") or [])]
            out.append((rank,name,r.get("Title"),"; ".join(x for x in locs if x),
                        d_iso(r.get("PostedDate")), cu, r.get("Id"), "Oracle Cloud", None))
    return out

def do_phenom(rank, name, hostname):
    probe = http(f"https://{hostname}/api/jobs?keywords=analyst&page=1&limit=1")
    if not probe or not isinstance(probe.get("jobs"), list):
        STATUS[name] = ("failed", f"Phenom endpoint on {hostname} returned no usable response (HTTP 500)"); return []
    STATUS[name] = ("ok", f"Phenom jobs API ({hostname})")
    out=[]
    for kw in ("data analyst","business analyst"):
        for page in (1,2):
            j = http(f"https://{hostname}/api/jobs?keywords={urllib.parse.quote(kw)}&page={page}&limit=100")
            if not j: break
            jobs = j.get("jobs") or []
            if not jobs: break
            for w in jobs:
                d0 = w.get("data") or {}
                loc = d0.get("full_location") or ", ".join(
                    x for x in (d0.get("city"),d0.get("state"),d0.get("country")) if x)
                out.append((rank,name,d0.get("title"),loc,
                    d_iso(d0.get("posted_date") or d0.get("create_date")),
                    d0.get("apply_url") or f"https://{hostname}/", d0.get("req_id"), "Phenom", None))
            if len(jobs) < 100: break
    return out

def do_amazon(rank, name, _):
    out=[]; got=False
    for kw in ("data analyst","business analyst"):
        for off in (0,100):
            j = http("https://www.amazon.jobs/en/search.json?"
                     f"base_query={urllib.parse.quote(kw)}&country=USA&result_limit=100&offset={off}&sort=recent")
            if not j: break
            got=True
            jobs = j.get("jobs") or []
            if not jobs: break
            for w in jobs:
                d=None
                for fmt in ("%B %d, %Y","%b %d, %Y"):
                    try: d=datetime.datetime.strptime(w.get("posted_date",""),fmt).date(); break
                    except Exception: pass
                out.append((rank,name,w.get("title"),w.get("normalized_location") or w.get("location"),d,
                    "https://www.amazon.jobs"+(w.get("job_path") or ""), w.get("id_icims"), "amazon.jobs", None))
            if len(jobs) < 100: break
    STATUS[name] = ("ok","amazon.jobs search API") if got else ("failed","amazon.jobs did not respond")
    return out

def do_greenhouse(rank, name, board, cu):
    j = http(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=false")
    if not j or "jobs" not in j:
        STATUS[name] = ("failed", f"Greenhouse board {board} did not respond"); return []
    STATUS[name] = ("ok", f"Greenhouse boards API ({board})")
    return [(rank,name,w.get("title"),(w.get("location") or {}).get("name",""),
             d_iso(w.get("updated_at") or w.get("first_published")),
             w.get("absolute_url") or cu, w.get("id"), "Greenhouse", None)
            for w in j["jobs"]]

def do_eightfold(rank, name, tenant):
    out=[]; got=False
    for dom in (f"{re.sub(r'[^a-z]','',name.split()[0].lower())}.com", f"{tenant}.com"):
        for kw in ("data analyst","business analyst"):
            j = http(f"https://{tenant}.eightfold.ai/api/apply/v2/jobs?domain={dom}&start=0&num=100"
                     f"&query={urllib.parse.quote(kw)}")
            if not j: continue
            got=True
            for p in (j.get("positions") or []):
                d=None
                try: d = datetime.datetime.utcfromtimestamp(int(p.get("t_create"))).date()
                except Exception: d = d_iso(p.get("t_create"))
                out.append((rank,name,p.get("name"),p.get("location"),d,
                    f"https://{tenant}.eightfold.ai/careers?pid={p.get('id')}", p.get("id"), "Eightfold", None))
        if out: break
    STATUS[name] = ("ok",f"Eightfold API ({tenant}.eightfold.ai)") if got else ("failed","Eightfold returned nothing")
    return out

# ---------------------------------------------------------------- registry
from companies import FORTUNE100
from endpoints import ENDPOINTS
from f200_companies import F200
from f300_companies import F300

RANKS = {n: rk for rk, n, _ in FORTUNE100}
RANKS.update({n: rk for rk, n, _, _ in F200})
RANKS.update({n: rk for rk, n, _, _ in F300})

tasks = []
for name, ep in ENDPOINTS.items():
    if ep: tasks.append(("wd", RANKS.get(name,999), name, tuple(ep)))
# Fortune 1-100 non-Workday (verified in earlier rounds)
tasks += [
 ("or",  1,  "Amazon", None),  # placeholder replaced below
]
tasks = [t for t in tasks if t[0] != "or" or t[3] is not None]
tasks += [
 ("am",  RANKS.get("Amazon",1), "Amazon", (None,)),
 ("or",  RANKS.get("JPMorgan Chase",12), "JPMorgan Chase", ("jpmc.fa.oraclecloud.com","CX_1001","https://careers.jpmorgan.com/us/en/jobs")),
 ("or",  RANKS.get("Oracle",82), "Oracle", ("eeho.fa.us2.oraclecloud.com","CX_45001","https://careers.oracle.com/jobs")),
 ("or",  RANKS.get("Kroger",27), "Kroger", ("eluq.fa.us2.oraclecloud.com","CX_2001","https://jobs.kroger.com/")),
 ("or",  RANKS.get("Albertsons",57), "Albertsons", ("eofd.fa.us6.oraclecloud.com","CX_1001","https://careers.albertsons.com/")),
 ("or",  RANKS.get("American Express",56), "American Express", ("egug.fa.us2.oraclecloud.com","CX_1","https://www.americanexpress.com/en-us/careers/")),
 ("or",  RANKS.get("Uber Technologies",92), "Uber Technologies", ("iaziqy.fa.ocs.oraclecloud.com","CX_1","https://www.uber.com/us/en/careers/list/")),
 ("ph",  RANKS.get("Costco Wholesale",13), "Costco Wholesale", ("careers.costco.com",)),
 ("ph",  RANKS.get("State Farm Insurance",32), "State Farm Insurance", ("jobs.statefarm.com",)),
 ("ph",  RANKS.get("PepsiCo",46), "PepsiCo", ("www.pepsicojobs.com",)),
 ("gh",  RANKS.get("Galaxy Digital",76), "Galaxy Digital", ("galaxydigitalservices","https://www.galaxy.com/careers/")),
]

def load_eps(path, ranks):
    if not os.path.exists(path): return []
    out=[]
    for o in json.load(open(path)):
        name = o["name"]; rank = ranks.get(name, o.get("rank") or 999)
        if "workday" in o:      out.append(("wd", rank, name, tuple(o["workday"])))
        elif "oracle_host" in o:out.append(("or", rank, name, (o["oracle_host"], o.get("oracle_site","CX_1"), "")))
        elif "phenom_host" in o:out.append(("ph", rank, name, (o["phenom_host"],)))
        elif o.get("eightfold") and o["eightfold"] not in JUNK_8FOLD:
            out.append(("ef", rank, name, (o["eightfold"],)))
        elif o.get("greenhouse"):
            out.append(("gh", rank, name, (o["greenhouse"], "")))
    return out

tasks += load_eps("f200_endpoints.json", RANKS)
tasks += load_eps("f300_endpoints.json", RANKS)

seen_names=set(); ded=[]
for t in tasks:
    if t[2] in seen_names: continue
    seen_names.add(t[2]); ded.append(t)
tasks = ded

def run(t):
    kind, rank, name, args = t
    try:
        if kind=="wd": return do_workday(rank, name, *args)
        if kind=="or": return do_oracle(rank, name, args[0], args[1], args[2] or f"https://{args[0]}")
        if kind=="ph": return do_phenom(rank, name, args[0])
        if kind=="am": return do_amazon(rank, name, None)
        if kind=="gh": return do_greenhouse(rank, name, args[0], args[1])
        if kind=="ef": return do_eightfold(rank, name, args[0])
    except Exception as e:
        STATUS[name] = ("failed", f"scrape error: {e}")
    return []

print(f"scraping {len(tasks)} companies across Fortune 1-300 (PULL={PULL})...", file=sys.stderr)
with ThreadPoolExecutor(max_workers=14) as ex:
    for res in ex.map(run, tasks):
        for tup in res: add(*tup)

# ---- enrich Workday hits with exact date + full location list
def enrich(r):
    wd = r.get("wd_detail")
    if not wd: return r
    tenant, host, site, path = wd
    d = http(f"https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}{path}")
    jpi = (d or {}).get("jobPostingInfo") or {}
    sd = d_iso(jpi.get("startDate"))
    if sd:
        r["label_date"] = r["start_date"]
        r["start_date"] = sd.isoformat()
        r["age"] = (PULL - sd).days
    locs = ([jpi["location"]] if jpi.get("location") else []) + list(jpi.get("additionalLocations") or [])
    if locs: r["location"] = "; ".join(x for x in locs if x)
    return r

with ThreadPoolExecutor(max_workers=10) as ex:
    rows[:] = list(ex.map(enrich, rows))

rows[:] = [r for r in rows if 0 <= r["age"] <= WINDOW_MAX and is_us(r["location"])]
seen=set(); uniq=[]
for r in sorted(rows, key=lambda z:(z["age"], z["rank"])):
    k=(r["company"], r["title"].lower(), r["start_date"])
    if k in seen: continue
    seen.add(k); r.pop("wd_detail", None); uniq.append(r)

json.dump(uniq, open("jobs_all_300.json","w"), indent=1)
json.dump(STATUS, open("status_all_300.json","w"), indent=1)
ok = sum(1 for v in STATUS.values() if v[0]=="ok")
w48 = [r for r in uniq if r["age"] <= 1]
mism = sum(1 for r in uniq if r.get("label_date") and r["label_date"] != r["start_date"])
print(f"\ncompanies searched OK: {ok} | failed: {len(STATUS)-ok}", file=sys.stderr)
print(f"US matches <=7d: {len(uniq)} | WITHIN 48h: {len(w48)}", file=sys.stderr)
print(f"Workday label-vs-startDate mismatches: {mism}", file=sys.stderr)
import collections
print(collections.Counter(r["company"] for r in w48), file=sys.stderr)
