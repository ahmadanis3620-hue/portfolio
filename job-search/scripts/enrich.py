import json, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from endpoints import ENDPOINTS

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
rows = json.load(open("jobs_raw.json"))

def detail(row):
    ep = ENDPOINTS[row["company"]]
    tenant, host, site = ep
    path = row["url"].split(f"/{site}", 1)[1]
    url = f"https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}{path}"
    for a in range(3):
        try:
            req = urllib.request.Request(url, headers={"Accept":"application/json","User-Agent":UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode())
        except Exception:
            time.sleep(1.2*(a+1))
    return None

NON_US_HINT = re.compile(
 r"India|Bangalore|Bengaluru|Hyderabad|Pune|Chennai|Mumbai|Gurgaon|Gurugram|Noida|Delhi|Kolkata|Ahmedabad|"
 r"Canada|Toronto|Ontario|Vancouver|Montreal|Quebec|Calgary|Alberta|"
 r"Mexico|Guadalajara|Monterrey|Brazil|Sao Paulo|Argentina|Colombia|Bogota|Chile|Peru|Costa Rica|"
 r"China|Shanghai|Beijing|Shenzhen|Japan|Tokyo|Korea|Seoul|Taiwan|Taipei|Singapore|Malaysia|Kuala Lumpur|"
 r"Philippines|Manila|Cebu|Thailand|Vietnam|Indonesia|Jakarta|Hong Kong|Australia|Sydney|Melbourne|"
 r"New Zealand|United Kingdom|London|Ireland|Dublin|Germany|Berlin|Munich|France|Paris|Spain|Madrid|Barcelona|"
 r"Italy|Rome|Milan|Netherlands|Amsterdam|Poland|Krakow|Warsaw|Wroclaw|Romania|Bucharest|Hungary|Budapest|"
 r"Czech|Prague|Bulgaria|Sofia|Portugal|Lisbon|Switzerland|Sweden|Denmark|Norway|Finland|Belgium|Austria|"
 r"Israel|Turkey|Egypt|South Africa|Nigeria|Kenya|Morocco|Saudi|Emirates|Dubai|Qatar|Pakistan|Bangladesh|"
 r"Ukraine|Lithuania|Latvia|Estonia|Croatia|Serbia|Slovakia|Greece|Iceland|Luxembourg", re.I)

US_HINT = re.compile(r"\b(USA|United States|U\.S\.)\b|^US[ ,\-]", re.I)
ABBR = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND "
           "OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR".split())
STATE_RE = re.compile(r"\b(Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|"
 r"Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|"
 r"Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|"
 r"North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|"
 r"Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|Puerto Rico|District of Columbia)\b", re.I)

def classify(locs):
    """locs = list of location strings. Return (verdict, us_locs)."""
    us_locs, foreign = [], []
    for l in locs:
        l = (l or "").strip()
        if not l: continue
        if NON_US_HINT.search(l) and not US_HINT.search(l):
            foreign.append(l); continue
        if US_HINT.search(l) or STATE_RE.search(l) or any(t in ABBR for t in re.split(r"[,\s\-/]+", l)):
            us_locs.append(l); continue
        if re.search(r"remote|work at home|work from home|virtual|nationwide|home office|flexible", l, re.I):
            us_locs.append(l); continue
        foreign.append(l)
    if us_locs: return "US", us_locs
    if foreign: return "non-US", foreign
    return "unclear", locs

def work(row):
    d = detail(row)
    if not d:
        row["locations_resolved"] = [row["location"]]
        row["us_verdict"], _ = classify([row["location"]])
        return row
    jpi = d.get("jobPostingInfo") or {}
    locs = []
    if jpi.get("location"): locs.append(jpi["location"])
    for a in (jpi.get("additionalLocations") or []):
        if a: locs.append(a)
    if not locs: locs = [row["location"]]
    verdict, us_locs = classify(locs)
    row["locations_resolved"] = locs
    row["us_locations"] = us_locs
    row["us_verdict"] = verdict
    row["start_date"] = jpi.get("startDate") or ""
    row["posted_detail"] = jpi.get("postedOn") or row["posted_raw"]
    row["remote_type"] = jpi.get("remoteType") or ""
    row["time_type"] = jpi.get("timeType") or ""
    row["req_id"] = jpi.get("jobReqId") or row.get("req","")
    return row

print(f"enriching {len(rows)} rows...", file=sys.stderr)
with ThreadPoolExecutor(max_workers=10) as ex:
    out = list(ex.map(work, rows))

json.dump(out, open("jobs_enriched.json","w"), indent=1)
import collections
print(collections.Counter(r["us_verdict"] for r in out), file=sys.stderr)
us = [r for r in out if r["us_verdict"] == "US"]
print(f"US rows: {len(us)}  | within 72h: {len([r for r in us if r['age']<=3])}", file=sys.stderr)
print("\nsample start_dates:", [r.get("start_date") for r in out[:8]], file=sys.stderr)
