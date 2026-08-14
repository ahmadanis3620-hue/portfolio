import json, re, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from companies import FORTUNE100
from endpoints import ENDPOINTS

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
QUERIES = ["data analyst", "business analyst"]

# Strict + close variants: must contain "data analyst" or "business analyst"
TITLE_RE = re.compile(r"\b(data|business)\s+analyst\b", re.I)

STATES = ("Alabama Alaska Arizona Arkansas California Colorado Connecticut Delaware Florida Georgia Hawaii Idaho "
 "Illinois Indiana Iowa Kansas Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota Mississippi "
 "Missouri Montana Nebraska Nevada Hampshire Jersey Mexico York Carolina Dakota Ohio Oklahoma Oregon "
 "Pennsylvania Rhode Tennessee Texas Utah Vermont Virginia Washington Wisconsin Wyoming").split()
ABBR = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND "
           "OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split())
NON_US = ("India Canada Mexico Brazil China Japan Philippines Poland Ireland Kingdom Germany France Spain Italy "
 "Netherlands Singapore Australia Malaysia Costa Rica Argentina Colombia Romania Hungary Czech Israel Korea "
 "Taiwan Thailand Vietnam Turkey Egypt Africa Switzerland Sweden Belgium Denmark Norway Austria Portugal Greece "
 "Chile Peru Indonesia Pakistan Bangladesh Emirates Arabia Qatar Kenya Nigeria Morocco Ukraine Bulgaria Slovakia "
 "Lithuania Latvia Estonia Finland Iceland Luxembourg Croatia Serbia Zealand Kong Vietnam").split()

def is_us(loc):
    if not loc: return "unknown"
    l = loc.strip()
    if re.search(r"\b(United States|USA|U\.S\.|US-|US,)\b", l, re.I): return "yes"
    if any(n.lower() in l.lower() for n in NON_US): return "no"
    if re.search(r"\b(" + "|".join(STATES) + r")\b", l): return "yes"
    toks = re.split(r"[,\s\-/]+", l)
    if any(t in ABBR for t in toks): return "yes"
    if re.search(r"^\d+\s+Locations?$", l, re.I): return "unknown"
    if re.search(r"remote|work at home|work from home|virtual|nationwide|home office", l, re.I): return "unknown"
    return "unknown"

# posting-age buckets from Workday's postedOn string
def age_days(posted):
    if not posted: return None
    p = posted.lower()
    if "today" in p or "just posted" in p: return 0
    if "yesterday" in p: return 1
    m = re.search(r"(\d+)\+?\s*day", p)
    if m: return int(m.group(1))
    if re.search(r"(\d+)\+?\s*(month|year)", p): return 999
    return None

def fetch(tenant, host, site, q, offset, tries=3):
    url = f"https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    body = json.dumps({"appliedFacets":{},"limit":20,"offset":offset,"searchText":q}).encode()
    for a in range(tries):
        try:
            req = urllib.request.Request(url, data=body, method="POST",
                headers={"Content-Type":"application/json","Accept":"application/json","User-Agent":UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode())
        except Exception:
            if a == tries-1: return None
            time.sleep(1.5*(a+1))
    return None

def scrape(args):
    rank, name, (tenant, host, site) = args
    rows, seen = [], set()
    for q in QUERIES:
        for offset in (0, 20, 40):
            d = fetch(tenant, host, site, q, offset)
            if not d: break
            posts = d.get("jobPostings") or []
            if not posts: break
            for jp in posts:
                title = (jp.get("title") or "").strip()
                path  = jp.get("externalPath") or ""
                if path in seen: continue
                seen.add(path)
                if not TITLE_RE.search(title): continue
                ad = age_days(jp.get("postedOn"))
                if ad is None or ad > 7: continue
                loc = (jp.get("locationsText") or "").strip()
                us = is_us(loc)
                if us == "no": continue
                rows.append({
                    "rank": rank, "company": name, "title": title, "location": loc,
                    "us": us, "posted_raw": (jp.get("postedOn") or "").strip(), "age": ad,
                    "req": (jp.get("bulletFields") or [""])[0],
                    "url": f"https://{tenant}.{host}.myworkdayjobs.com/{site}{path}",
                })
            if len(posts) < 20: break
    return name, rows

tasks = [(r, n, ENDPOINTS[n]) for r, n, _ in FORTUNE100 if ENDPOINTS.get(n)]
print(f"scraping {len(tasks)} companies with live APIs...", file=sys.stderr)

all_rows, status = [], {}
with ThreadPoolExecutor(max_workers=14) as ex:
    for name, rows in ex.map(scrape, tasks):
        all_rows += rows
        status[name] = len(rows)
        print(f"  {name}: {len(rows)}", file=sys.stderr)

json.dump(all_rows, open("jobs_raw.json","w"), indent=1)
fresh = [r for r in all_rows if r["age"] <= 3]
print(f"\nTOTAL matched (<=7d): {len(all_rows)}   within 72h: {len(fresh)}", file=sys.stderr)
