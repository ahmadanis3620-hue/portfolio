import json, re, sys, time, html, urllib.request, urllib.parse, gzip
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

def http(url, data=None, timeout=35, tries=3):
    for a in range(tries):
        try:
            h={"User-Agent":UA,"Accept":"application/json","Accept-Encoding":"gzip"}
            if data is not None: h["Content-Type"]="application/json"
            req=urllib.request.Request(url,data=data,headers=h,method="POST" if data is not None else "GET")
            with urllib.request.urlopen(req,timeout=timeout) as r:
                raw=r.read()
                if r.headers.get("Content-Encoding")=="gzip":
                    try: raw=gzip.decompress(raw)
                    except Exception: pass
                return json.loads(raw.decode("utf-8","replace"))
        except Exception:
            if a==tries-1: return None
            time.sleep(1.2*(a+1))
    return None

def strip_html(s):
    if not s: return ""
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S|re.I)
    s = re.sub(r"<li[^>]*>", "\n- ", s, flags=re.I)
    s = re.sub(r"</(p|div|li|ul|ol|h[1-6]|tr)>", "\n", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\xa0]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()

def wd_jd(url):
    m = re.match(r"https://([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/([^/]+)(/.*)$", url)
    if not m: return None
    t,h,site,path = m.groups()
    d = http(f"https://{t}.{h}.myworkdayjobs.com/wday/cxs/{t}/{site}{path}")
    jpi = (d or {}).get("jobPostingInfo") or {}
    return {"text": strip_html(jpi.get("jobDescription")),
            "title": jpi.get("title"), "location": jpi.get("location"),
            "posted": jpi.get("startDate"), "req": jpi.get("jobReqId"),
            "timeType": jpi.get("timeType"), "remote": jpi.get("remoteType")}

def get_html(url, timeout=35, tries=3):
    for a in range(tries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,
                "Accept":"text/html,application/xhtml+xml","Accept-Encoding":"gzip"})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                raw=r.read()
                if r.headers.get("Content-Encoding")=="gzip":
                    try: raw=gzip.decompress(raw)
                    except Exception: pass
                return raw.decode("utf-8","replace")
        except Exception:
            if a==tries-1: return ""
            time.sleep(1.2*(a+1))
    return ""

def amazon_jd(url):
    """amazon.jobs .json 302->406; the rendered page carries the JD in section blocks."""
    s = get_html(url)
    if not s: return None
    blocks = re.findall(r'<div class="section (description|qualifications)">(.*?)'
                        r'(?=<div class="section |<footer|</main)', s, re.S|re.I)
    txt = "\n".join(strip_html(b[1]) for b in blocks)
    ttl = re.search(r'<h1[^>]*class="title"[^>]*>(.*?)</h1>', s, re.S|re.I)
    return {"text": txt, "title": strip_html(ttl.group(1)) if ttl else None,
            "location": None, "posted": None, "req": None}

ORACLE_HOSTS = {
 "GuideWell Mutual Holding": "fa-etum-saasfaprod1.fa.ocs.oraclecloud.com",
 "Albertsons": "eofd.fa.us6.oraclecloud.com",
 "Waste Management": "emcm.fa.us2.oraclecloud.com",
 "JPMorgan Chase": "jpmc.fa.oraclecloud.com",
}
def oracle_jd(company, req):
    host = ORACLE_HOSTS.get(company)
    if not host or not req: return None
    for sn in ("CX_1","CX_2","CX_1001","CX_2001","CX_4001","CX_3001"):
        j = http(f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails"
                 f"?expand=all&onlyData=true&finder=ById;Id=%22{req}%22,siteNumber={sn}")
        it = (j or {}).get("items") or []
        if it and it[0].get("ExternalDescriptionStr"):
            d = it[0]
            body = " ".join(x for x in (d.get("ExternalDescriptionStr"), d.get("ExternalQualificationsStr"),
                                        d.get("ExternalResponsibilitiesStr")) if x)
            return {"text": strip_html(body), "title": d.get("Title"),
                    "location": d.get("PrimaryLocation"), "posted": d.get("PostedDate"), "req": req}
    return None

rows = [x for x in json.load(open("jobs_all_300.json")) if 1 < x["age"] <= 7]
rows.sort(key=lambda z:(z["age"], z["rank"]))

def work(i_r):
    i, r = i_r
    jd = None
    try:
        if r["source"] == "Workday":      jd = wd_jd(r["url"])
        elif r["source"] == "amazon.jobs":jd = amazon_jd(r["url"])
        elif r["source"] == "Oracle Cloud":jd = oracle_jd(r["company"], r["req_id"])
    except Exception as e:
        jd = None
    out = dict(r); out["idx"] = i
    out["jd_text"] = (jd or {}).get("text") or ""
    out["jd_title"] = (jd or {}).get("title") or r["title"]
    out["jd_ok"] = bool(out["jd_text"] and len(out["jd_text"]) > 200)
    return out

print(f"fetching {len(rows)} job descriptions...", file=sys.stderr)
with ThreadPoolExecutor(max_workers=8) as ex:
    got = list(ex.map(work, enumerate(rows, 1)))

json.dump(got, open("jds.json","w"), indent=1)
ok = sum(1 for g in got if g["jd_ok"])
print(f"JD text retrieved: {ok}/{len(got)}", file=sys.stderr)
for g in got:
    if not g["jd_ok"]:
        print(f"  MISS {g['company']} | {g['title'][:44]} | {g['source']}", file=sys.stderr)
print(f"\nmean JD length: {sum(len(g['jd_text']) for g in got)//max(1,len(got))} chars", file=sys.stderr)
