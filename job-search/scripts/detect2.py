import re, sys, json, urllib.request, urllib.error, gzip, io
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

SITES = {
 "UnitedHealth Group": ["https://careers.unitedhealthgroup.com/","https://careers.unitedhealthgroup.com/job-search-results/"],
 "Exxon Mobil": ["https://jobs.exxonmobil.com/","https://corporate.exxonmobil.com/careers"],
 "Bank of America": ["https://careers.bankofamerica.com/en-us/job-search"],
 "Ford Motor": ["https://careers.ford.com/","https://careers.ford.com/en/search-jobs"],
 "Phillips 66": ["https://jobs.phillips66.com/"],
 "StoneX Group": ["https://www.stonex.com/en/careers/"],
 "AT&T": ["https://www.att.jobs/search-jobs","https://www.att.jobs/"],
 "Valero Energy": ["https://www.valero.com/careers","https://jobs.valero.com/"],
 "Progressive": ["https://careers.progressive.com/","https://careers.progressive.com/careers/jobs"],
 "Energy Transfer": ["https://www.energytransfer.com/careers/"],
 "Albertsons": ["https://www.albertsonscompanies.com/careers/","https://careers.albertsons.com/"],
 "Archer Daniels Midland": ["https://careers.adm.com/","https://www.adm.com/en-us/careers/"],
 "MetLife": ["https://careers.metlife.com/","https://jobs.metlife.com/"],
 "Lockheed Martin": ["https://www.lockheedmartinjobs.com/","https://www.lockheedmartinjobs.com/search-jobs"],
 "New York Life Insurance": ["https://jobs.newyorklife.com/","https://www.newyorklife.com/careers"],
 "Delta Air Lines": ["https://careers.delta.com/","https://delta.avature.net/careers"],
 "Publix Super Markets": ["https://careers.publix.com/","https://corporate.publix.com/careers"],
 "TD Synnex": ["https://careers.tdsynnex.com/"],
 "AbbVie": ["https://careers.abbvie.com/en","https://careers.abbvie.com/en/jobs"],
 "Performance Food Group": ["https://www.pfgc.com/Careers","https://careers.pfgc.com/"],
 "United Airlines Holdings": ["https://careers.united.com/","https://careers.united.com/us/en/search-results"],
 "Charter Communications": ["https://jobs.spectrum.com/","https://jobs.spectrum.com/search-jobs"],
 "American Airlines Group": ["https://jobs.aa.com/","https://jobs.aa.com/search-jobs"],
 "Enterprise Products Partners": ["https://www.enterpriseproducts.com/careers"],
 "Ingram Micro Holding": ["https://jobs.ingrammicro.com/","https://www.ingrammicro.com/en-us/careers"],
 "Liberty Mutual Insurance Group": ["https://jobs.libertymutualgroup.com/"],
 "IBM": ["https://www.ibm.com/careers/search","https://www.ibm.com/careers"],
 "Goldman Sachs Group": ["https://higher.gs.com/roles","https://www.goldmansachs.com/careers"],
 "Uber Technologies": ["https://www.uber.com/us/en/careers/list/"],
 "Meta Platforms": ["https://www.metacareers.com/jobs"],
 "Galaxy Digital": ["https://www.galaxy.com/careers/"],
 "Berkshire Hathaway": ["https://www.berkshirehathaway.com/careers/careers.html"],
 "American Express": ["https://www.americanexpress.com/en-us/careers/","https://aexp.eightfold.ai/careers"],
 "Apple": ["https://jobs.apple.com/en-us/search"],
 "Alphabet (Google)": ["https://www.google.com/about/careers/applications/jobs/results/"],
 "Tesla": ["https://www.tesla.com/careers/search/"],
 "Microsoft": ["https://jobs.careers.microsoft.com/global/en/search"],
 "Costco Wholesale": ["https://careers.costco.com/"],
}

PATTERNS = [
 ("oracle_host", re.compile(r"([a-z0-9-]+\.fa\.[a-z0-9-]*\.?oraclecloud\.com)", re.I)),
 ("oracle_site", re.compile(r"siteNumber[=:\"']+\s*(CX_\d+)", re.I)),
 ("eightfold",   re.compile(r"([a-z0-9-]+)\.eightfold\.ai", re.I)),
 ("smartrec",    re.compile(r"smartrecruiters\.com/([A-Za-z0-9]+)", re.I)),
 ("greenhouse",  re.compile(r"boards\.greenhouse\.io/([a-z0-9]+)|job-boards\.greenhouse\.io/([a-z0-9]+)", re.I)),
 ("lever",       re.compile(r"jobs\.lever\.co/([a-z0-9-]+)", re.I)),
 ("workday",     re.compile(r"([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/([A-Za-z0-9_-]+)", re.I)),
 ("icims",       re.compile(r"([a-z0-9-]+)\.icims\.com", re.I)),
 ("avature",     re.compile(r"([a-z0-9-]+)\.avature\.net", re.I)),
 ("phenom_api",  re.compile(r"/api/apply/v2/jobs|ph_widget|phenompeople", re.I)),
 ("radancy",     re.compile(r"radancy|tmp\.com", re.I)),
 ("successf",    re.compile(r"successfactors\.(com|eu)", re.I)),
]

def get(url, timeout=28):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9", "Accept-Encoding": "gzip"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                try: raw = gzip.decompress(raw)
                except Exception: pass
            return r.status, raw.decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, ""

def scan(item):
    name, urls = item
    found = {}
    for u in urls:
        code, body = get(u)
        if code != 200 or not body:
            found.setdefault("_http", []).append(f"{u} -> {code}")
            continue
        for key, rx in PATTERNS:
            for m in rx.finditer(body):
                v = next((g for g in m.groups() if g), m.group(0)) if m.groups() else m.group(0)
                found.setdefault(key, set()).add(v)
        if any(k in found for k in ("oracle_host","eightfold","smartrec","greenhouse","lever","workday")):
            break
    out = {k: sorted(v)[:3] for k, v in found.items() if k != "_http" and isinstance(v, set)}
    return name, out

print(f"scanning {len(SITES)} careers sites...", file=sys.stderr)
res = {}
with ThreadPoolExecutor(max_workers=12) as ex:
    for name, out in ex.map(scan, SITES.items()):
        res[name] = out
        tag = ", ".join(f"{k}={v}" for k, v in out.items() if k in
                        ("oracle_host","oracle_site","eightfold","smartrec","greenhouse","lever","workday","icims","avature"))
        print(f"  {name:32} {tag or ('|'.join(out.keys()) or 'nothing')}", file=sys.stderr)
json.dump({k: {kk: list(vv) for kk, vv in v.items()} for k, v in res.items()}, open("detect2.json","w"), indent=1)
