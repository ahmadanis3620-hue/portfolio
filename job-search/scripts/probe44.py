import json, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

# company -> candidate careers hostnames to try the Phenom /api/jobs pattern on
CAND = {
 "UnitedHealth Group": ["careers.unitedhealthgroup.com","careers.optum.com"],
 "Exxon Mobil": ["jobs.exxonmobil.com","careers.exxonmobil.com"],
 "Costco Wholesale": ["www.costco.com","careers.costco.com"],
 "Bank of America": ["careers.bankofamerica.com"],
 "Ford Motor": ["careers.ford.com"],
 "Kroger": ["jobs.kroger.com","careers.kroger.com"],
 "Phillips 66": ["jobs.phillips66.com","careers.phillips66.com"],
 "StoneX Group": ["careers.stonex.com","jobs.stonex.com"],
 "State Farm Insurance": ["jobs.statefarm.com","careers.statefarm.com"],
 "AT&T": ["www.att.jobs","att.jobs"],
 "Valero Energy": ["jobs.valero.com","careers.valero.com"],
 "PepsiCo": ["www.pepsicojobs.com"],
 "Progressive": ["careers.progressive.com","jobs.progressive.com"],
 "Energy Transfer": ["careers.energytransfer.com","jobs.energytransfer.com"],
 "Albertsons": ["careers.albertsonscompanies.com","www.albertsonscompanies.com"],
 "Archer Daniels Midland": ["careers.adm.com","jobs.adm.com"],
 "MetLife": ["careers.metlife.com","jobs.metlife.com"],
 "Lockheed Martin": ["www.lockheedmartinjobs.com","jobs.lockheedmartin.com"],
 "New York Life Insurance": ["jobs.newyorklife.com","careers.newyorklife.com"],
 "Delta Air Lines": ["careers.delta.com","jobs.delta.com"],
 "Publix Super Markets": ["careers.publix.com","jobs.publix.com"],
 "TD Synnex": ["careers.tdsynnex.com","jobs.tdsynnex.com"],
 "AbbVie": ["careers.abbvie.com","jobs.abbvie.com"],
 "Performance Food Group": ["careers.pfgc.com","jobs.pfgc.com"],
 "United Airlines Holdings": ["careers.united.com","jobs.united.com"],
 "Charter Communications": ["jobs.spectrum.com","careers.spectrum.com"],
 "American Airlines Group": ["jobs.aa.com","careers.aa.com"],
 "Enterprise Products Partners": ["careers.enterpriseproducts.com","jobs.enterpriseproducts.com"],
 "Ingram Micro Holding": ["jobs.ingrammicro.com","careers.ingrammicro.com"],
 "Liberty Mutual Insurance Group": ["jobs.libertymutualgroup.com","careers.libertymutualgroup.com"],
 "IBM": ["www.ibm.com","careers.ibm.com"],
 "Goldman Sachs Group": ["higher.gs.com"],
 "JPMorgan Chase": ["careers.jpmorgan.com"],
 "Oracle": ["careers.oracle.com"],
 "Uber Technologies": ["www.uber.com"],
 "Meta Platforms": ["www.metacareers.com"],
 "Galaxy Digital": ["www.galaxy.com"],
 "Berkshire Hathaway": ["www.berkshirehathaway.com"],
}

def get(url, timeout=22):
    try:
        req = urllib.request.Request(url, headers={"Accept":"application/json","User-Agent":UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, str(e)[:70]

def probe(args):
    name, host = args
    url = f"https://{host}/api/jobs?keyword=analyst&page=1&limit=2"
    code, body = get(url)
    if code == 200 and body.lstrip().startswith("{"):
        try:
            j = json.loads(body)
            jobs = j.get("jobs") or []
            if jobs and isinstance(jobs[0], dict) and "data" in jobs[0]:
                d = jobs[0]["data"]
                return (name, host, "PHENOM", j.get("count") or j.get("totalCount"), d.get("posted_date"))
        except Exception:
            pass
    return (name, host, f"no({code})", None, None)

tasks = [(n, h) for n, hs in CAND.items() for h in hs]
print(f"probing {len(tasks)} candidate hosts...", file=sys.stderr)
hits = {}
with ThreadPoolExecutor(max_workers=20) as ex:
    for name, host, kind, cnt, pd in ex.map(probe, tasks):
        if kind == "PHENOM" and name not in hits:
            hits[name] = host
            print(f"  HIT {name:32} {host:38} count={cnt} sample_date={pd}", file=sys.stderr)

print(f"\nPHENOM HITS: {len(hits)}", file=sys.stderr)
json.dump(hits, open("phenom_map.json","w"), indent=1)
miss = [n for n in CAND if n not in hits]
print(f"NO PHENOM ({len(miss)}): {miss}", file=sys.stderr)
