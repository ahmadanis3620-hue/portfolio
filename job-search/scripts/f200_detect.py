import json, re, sys, gzip, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from f200_companies import F200, SLUGS, WD_HOSTS

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
PAY = json.dumps({"appliedFacets":{},"limit":1,"offset":0,"searchText":"analyst"}).encode()

def wd_probe(tenant, host, site, timeout=10):
    url = f"https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    try:
        req = urllib.request.Request(url, data=PAY, method="POST",
              headers={"Content-Type":"application/json","Accept":"application/json","User-Agent":UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0

def get(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":UA,
              "Accept":"text/html,application/xhtml+xml,*/*;q=0.8","Accept-Encoding":"gzip"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding")=="gzip":
                try: raw = gzip.decompress(raw)
                except Exception: pass
            return r.status, raw.decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""

RX_WD     = re.compile(r"([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([A-Za-z0-9_\-]+)")
RX_ORACLE = re.compile(r"([a-z0-9-]+\.fa\.[a-z0-9-]*\.?oraclecloud\.com)", re.I)
RX_CXSITE = re.compile(r"siteNumber[=:\"'\s]+(CX_\d+)", re.I)
RX_GH     = re.compile(r"greenhouse\.io/([a-z0-9]+)", re.I)
RX_8FOLD  = re.compile(r"([a-z0-9-]+)\.eightfold\.ai", re.I)
RX_SR     = re.compile(r"smartrecruiters\.com/([A-Za-z0-9]+)", re.I)
RX_PHENOM = re.compile(r"/api/apply/v2/jobs|ph_widget|phenompeople|/api/jobs\?", re.I)

BAD_SLUG = {"job","jobs","en-US","login","apply","page","details","wday","cxs","introduceYourself"}

def work(item):
    rank, name, tenants, urls = item
    out = {"rank":rank,"name":name}

    # 1) fingerprint careers pages
    for u in urls:
        code, body = get(u)
        if code != 200 or not body:
            continue
        m = RX_WD.search(body)
        if m and m.group(3) not in BAD_SLUG:
            out["workday"] = [m.group(1), m.group(2), m.group(3)]
        mo = RX_ORACLE.search(body)
        if mo:
            out["oracle_host"] = mo.group(1)
            mc = RX_CXSITE.search(body)
            out["oracle_site"] = mc.group(1) if mc else "CX_1"
        mg = RX_GH.search(body)
        if mg: out.setdefault("greenhouse", mg.group(1))
        m8 = RX_8FOLD.search(body)
        if m8: out.setdefault("eightfold", m8.group(1))
        ms = RX_SR.search(body)
        if ms: out.setdefault("smartrecruiters", ms.group(1))
        if RX_PHENOM.search(body):
            out.setdefault("phenom_host", u.split("/")[2])
        if "workday" in out or "oracle_host" in out:
            break

    # 2) if no workday endpoint yet, brute-force tenant+slug
    if "workday" not in out:
        live = []
        for t in tenants:
            for h in WD_HOSTS:
                c = wd_probe(t, h, "External")
                if c == 200:
                    out["workday"] = [t, h, "External"]; break
                if c == 422:
                    live.append((t, h))
            if "workday" in out: break
        if "workday" not in out:
            for t, h in live[:3]:
                for pat in SLUGS:
                    s = pat.replace("{t}", t)
                    if s == "External": continue
                    if wd_probe(t, h, s) == 200:
                        out["workday"] = [t, h, s]; break
                if "workday" in out: break
    return out

print(f"discovering endpoints for {len(F200)} companies (ranks 101-200)...", file=sys.stderr)
res = []
with ThreadPoolExecutor(max_workers=10) as ex:
    for o in ex.map(work, F200):
        res.append(o)
        keys = [k for k in o if k not in ("rank","name")]
        print(f"  {o['rank']:3} {o['name'][:30]:30} {keys if keys else 'NONE'}", file=sys.stderr)

json.dump(res, open("f200_endpoints.json","w"), indent=1)
n_wd = sum(1 for o in res if "workday" in o)
n_or = sum(1 for o in res if "oracle_host" in o)
n_other = sum(1 for o in res if any(k in o for k in ("greenhouse","eightfold","smartrecruiters","phenom_host")))
none = [o["name"] for o in res if len([k for k in o if k not in ("rank","name")]) == 0]
print(f"\nWorkday: {n_wd} | Oracle: {n_or} | other ATS: {n_other} | nothing: {len(none)}", file=sys.stderr)
print("NOTHING:", none, file=sys.stderr)
