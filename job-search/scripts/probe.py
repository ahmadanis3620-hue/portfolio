import json, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from companies import FORTUNE100, CONFIRMED, SITE_CANDIDATES, WD_HOSTS

PAY = json.dumps({"appliedFacets":{},"limit":1,"offset":0,"searchText":"analyst"}).encode()

def hit(tenant, host, site, timeout=12):
    url = f"https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    req = urllib.request.Request(url, data=PAY, method="POST",
        headers={"Content-Type":"application/json","Accept":"application/json",
                 "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None

# ---- Stage 1: which tenant+host exist? (422 = tenant live, wrong site) ----
def stage1(args):
    name, tenant, host = args
    code, _ = hit(tenant, host, "External")
    return (name, tenant, host, code)

tasks = []
for rank, name, tenants in FORTUNE100:
    if name in CONFIRMED:
        continue
    for t in tenants:
        for h in WD_HOSTS:
            tasks.append((name, t, h))

print(f"stage1: {len(tasks)} probes", file=sys.stderr)
live = {}
with ThreadPoolExecutor(max_workers=60) as ex:
    for name, tenant, host, code in ex.map(stage1, tasks):
        if code in (200, 422):
            live.setdefault(name, []).append((tenant, host, code))

found = {}
for name, lst in live.items():
    for tenant, host, code in lst:
        if code == 200:
            found[name] = (tenant, host, "External")
print(f"stage1 done: {len(live)} companies with live tenants, {len(found)} solved outright", file=sys.stderr)

# ---- Stage 2: brute force site slugs for live-but-unsolved ----
def stage2(args):
    name, tenant, host, site = args
    code, _ = hit(tenant, host, site)
    return (name, tenant, host, site, code)

t2 = []
for name, lst in live.items():
    if name in found:
        continue
    for tenant, host, code in lst:
        if code != 422:
            continue
        for pat in SITE_CANDIDATES:
            site = pat.replace("{t}", tenant)
            if site == "External":
                continue
            t2.append((name, tenant, host, site))

print(f"stage2: {len(t2)} probes", file=sys.stderr)
with ThreadPoolExecutor(max_workers=60) as ex:
    for name, tenant, host, site, code in ex.map(stage2, t2):
        if code == 200 and name not in found:
            found[name] = (tenant, host, site)

out = {**{k: list(v) for k, v in CONFIRMED.items()}, **{k: list(v) for k, v in found.items()}}
json.dump(out, open("workday_map.json","w"), indent=1)
print(f"TOTAL SOLVED: {len(out)}", file=sys.stderr)
for k in sorted(out):
    print("  ", k, out[k], file=sys.stderr)
missing = [n for _, n, _ in FORTUNE100 if n not in out]
print(f"\nUNSOLVED ({len(missing)}): {missing}", file=sys.stderr)
