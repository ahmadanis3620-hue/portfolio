import json, re, datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from companies import FORTUNE100
from endpoints import ENDPOINTS, CAREERS_URL
from f200_companies import F200
from f300_companies import F300

PULL = datetime.date(2026, 8, 17)

us = json.load(open("jobs_all_300.json"))
for r in us:
    r["loc_str"] = r["location"]



def match_type(t):
    tl = t.lower()
    sr = re.search(r"\b(senior|sr\.?|lead|principal|staff)\b", tl)
    if sr and "data analyst" in tl: return "Senior Data Analyst"
    if sr and "business analyst" in tl: return "Senior Business Analyst"
    if "data analyst" in tl: return "Data Analyst"
    if "business analyst" in tl: return "Business Analyst"
    return "Analyst"

for r in us:
    r["match"] = match_type(r["title"])
    r["pdate"] = datetime.date.fromisoformat(r["start_date"])
    r["tier"] = ("Fortune 1-100" if r["rank"] <= 100 else
                 "Fortune 101-200" if r["rank"] <= 200 else "Fortune 201-300")

main   = sorted([r for r in us if r["age"] <= 1], key=lambda r: (r["age"], r["rank"]))
backup = sorted([r for r in us if 1 < r["age"] <= 7], key=lambda r: (r["age"], r["rank"]))

# ---------------- coverage -------------------------------------------------
SRC2 = {
 "Amazon":("Searched (live API)","amazon.jobs search API","https://www.amazon.jobs/en/"),
 "JPMorgan Chase":("Searched (live API)","Oracle Cloud recruiting API (jpmc)","https://careers.jpmorgan.com/us/en/jobs"),
 "Oracle":("Searched (live API)","Oracle Cloud recruiting API (eeho)","https://careers.oracle.com/jobs"),
 "Kroger":("Searched (live API)","Oracle Cloud recruiting API (eluq)","https://jobs.kroger.com/"),
 "Albertsons":("Searched (live API)","Oracle Cloud recruiting API (eofd)","https://careers.albertsons.com/"),
 "American Express":("Searched (live API)","Oracle Cloud recruiting API (egug)","https://www.americanexpress.com/en-us/careers/"),
 "Uber Technologies":("Searched (live API)","Oracle Cloud recruiting API (iaziqy)","https://www.uber.com/us/en/careers/list/"),
 "Costco Wholesale":("Searched (live API)","Phenom jobs API (careers.costco.com)","https://careers.costco.com/"),
 "State Farm Insurance":("Searched (live API)","Phenom jobs API (jobs.statefarm.com)","https://jobs.statefarm.com/"),
 "PepsiCo":("Searched (live API)","Phenom jobs API (pepsicojobs.com)","https://www.pepsicojobs.com/"),
 "Galaxy Digital":("Searched (live API)","Greenhouse boards API","https://www.galaxy.com/careers/"),
}
BLOCKED = {
 "Microsoft":"TLS/egress policy blocked the careers API host",
 "Tesla":"Careers API blocked by bot protection (Akamai)",
 "Progressive":"Careers site returns 403 to non-browser clients",
 "American Airlines Group":"Careers site returns 403 to non-browser clients",
 "Apple":"Search API requires browser-issued token",
 "Alphabet (Google)":"Public search API retired; no open endpoint",
 "Meta Platforms":"GraphQL endpoint requires signed doc_id",
}
PLATFORM = {
 "UnitedHealth Group":"Radancy (HTML only)","Ford Motor":"Radancy (HTML only)",
 "Charter Communications":"Radancy (HTML only)","AT&T":"Radancy / Workday (no open site slug)",
 "Exxon Mobil":"SuccessFactors (auth required)","Phillips 66":"SuccessFactors (auth required)",
 "New York Life Insurance":"SuccessFactors (auth required)",
 "Bank of America":"Avature / Workday (no open site slug)","MetLife":"Avature (no public API)",
 "Lockheed Martin":"Avature (no public API)","Delta Air Lines":"Avature (no public API)",
 "Liberty Mutual Insurance Group":"iCIMS (no public search API)",
 "IBM":"Custom SPA (no open endpoint)","Goldman Sachs Group":"Custom SPA (no open endpoint)",
 "Berkshire Hathaway":"Holding company - hiring sits with subsidiaries",
}
STATUS_ALL = json.load(open("status_all_300.json"))
URLS = {}
for rk, n, _t, urls in F200: URLS[n] = urls[-1] if urls else ""
for rk, n, _t, urls in F300: URLS[n] = urls[-1] if urls else ""
URLS.update(CAREERS_URL)

def coverage(name, rank):
    st = STATUS_ALL.get(name)
    if st and st[0] == "ok":
        return ("Searched (live API)", st[1], URLS.get(name, ""))
    if st and st[0] == "failed":
        return ("Not searched - endpoint failed", st[1], URLS.get(name, ""))
    if name in BLOCKED:
        return ("Not searched - blocked", BLOCKED[name], URLS.get(name, ""))
    return ("Not searched - no API", PLATFORM.get(name, "No public JSON endpoint found during discovery"),
            URLS.get(name, ""))

ARIAL="Arial"
HDR_FILL=PatternFill("solid",fgColor="1F3864"); HDR_FONT=Font(name=ARIAL,bold=True,color="FFFFFF",size=10)
TTL=Font(name=ARIAL,bold=True,size=14,color="1F3864"); SUB=Font(name=ARIAL,size=9,italic=True,color="595959")
CELL=Font(name=ARIAL,size=10); LINK=Font(name=ARIAL,size=10,color="0563C1",underline="single")
BOLD=Font(name=ARIAL,size=10,bold=True); THIN=Side(style="thin",color="D0D0D0")
BORDER=Border(left=THIN,right=THIN,top=THIN,bottom=THIN); BAND=PatternFill("solid",fgColor="F2F5FA")
YELLOW=PatternFill("solid",fgColor="FFFF00")

wb=Workbook(); ws=wb.active; ws.title="Openings (last 48h)"
COLS=[("Fortune Rank",11),("Tier",14),("Company",24),("Job Title",50),("Role Type",21),
      ("Location(s) - US",38),("Posted Date",13),("Days Old",10),("Source",20),("Req ID",14),("Apply Link",38)]
HDR=5

def header(sh, title, sub, cols):
    sh["A1"]=title; sh["A1"].font=TTL
    sh["A2"]=sub;   sh["A2"].font=SUB
    last=get_column_letter(len(cols))
    sh.merge_cells(f"A1:{last}1"); sh.merge_cells(f"A2:{last}2")
    sh["A3"]="Pull date ->"; sh["A3"].font=BOLD
    sh["B3"]=PULL; sh["B3"].number_format="yyyy-mm-dd"; sh["B3"].font=BOLD; sh["B3"].fill=YELLOW
    sh["C3"]="Change this date and Days Old recalculates."; sh["C3"].font=SUB
    for i,(h,w) in enumerate(cols,start=1):
        c=sh.cell(HDR,i,h); c.font=HDR_FONT; c.fill=HDR_FILL
        c.alignment=Alignment(horizontal="center",vertical="center",wrap_text=True)
        sh.column_dimensions[get_column_letter(i)].width=w
    sh.row_dimensions[HDR].height=30

def write_rows(sh,data,start):
    for n,r in enumerate(data):
        rr=start+n
        vals=[r["rank"],r["tier"],r["company"],r["title"],r["match"],r["loc_str"],r["pdate"],None,
              r.get("source","Workday"),r.get("req_id") or r.get("req") or "-","Open posting"]
        for i,v in enumerate(vals,start=1):
            c=sh.cell(rr,i,v); c.font=CELL; c.border=BORDER
            if n%2: c.fill=BAND
            c.alignment=Alignment(vertical="top",wrap_text=(i in (4,6)))
        sh.cell(rr,7).number_format="yyyy-mm-dd"
        sh.cell(rr,8).value=f"=$B$3-G{rr}"; sh.cell(rr,8).number_format="0"
        sh.cell(rr,8).alignment=Alignment(horizontal="center",vertical="top")
        sh.cell(rr,1).alignment=Alignment(horizontal="center",vertical="top")
        lc=sh.cell(rr,11); lc.value="Open posting"; lc.font=LINK; lc.hyperlink=r["url"]
    return start+len(data)

n100 = len(set(r['company'] for r in main if r['rank']<=100))
n200 = len(set(r['company'] for r in main if r['rank']>100))
header(ws,"US Analyst Openings at Fortune 300 Companies - Posted Within 48 Hours",
  f"Data pulled {PULL:%B %d, %Y} direct from employer applicant-tracking systems across six platforms. "
  f"{len(main)} openings. NOTE: {PULL:%A %d %B %Y} is a Monday, so this 48-hour window covers Monday and Sunday - "
  "and employers post almost nothing at weekends, making it effectively ONE business day. "
  "See the 'Prior business days' tab for the preceding week.",COLS)
end=write_rows(ws,main,HDR+1)
ws.freeze_panes=f"A{HDR+1}"; ws.auto_filter.ref=f"A{HDR}:K{end-1}"
s=end+1
ws.cell(s,1,"Summary").font=Font(name=ARIAL,bold=True,size=11,color="1F3864")
for n,(lbl,f) in enumerate([
 ("Total openings",f"=COUNTA(D{HDR+1}:D{end-1})"),
 ("Distinct companies",f"=SUMPRODUCT(1/COUNTIF(C{HDR+1}:C{end-1},C{HDR+1}:C{end-1}))"),
 ("From Fortune 1-100",f'=COUNTIF(B{HDR+1}:B{end-1},"Fortune 1-100")'),
 ("From Fortune 101-200",f'=COUNTIF(B{HDR+1}:B{end-1},"Fortune 101-200")'),
 ("From Fortune 201-300",f'=COUNTIF(B{HDR+1}:B{end-1},"Fortune 201-300")'),
 ("Posted today",f"=COUNTIF(H{HDR+1}:H{end-1},0)"),
 ("Posted yesterday",f"=COUNTIF(H{HDR+1}:H{end-1},1)"),
 ("Data Analyst",f'=COUNTIF(E{HDR+1}:E{end-1},"Data Analyst")'),
 ("Senior Data Analyst",f'=COUNTIF(E{HDR+1}:E{end-1},"Senior Data Analyst")'),
 ("Business Analyst",f'=COUNTIF(E{HDR+1}:E{end-1},"Business Analyst")'),
 ("Senior Business Analyst",f'=COUNTIF(E{HDR+1}:E{end-1},"Senior Business Analyst")'),
],start=1):
    ws.cell(s+n,1,lbl).font=CELL
    c=ws.cell(s+n,2,f); c.font=BOLD; c.number_format="0"

w2=wb.create_sheet("Prior business days")
header(w2,"US Analyst Openings Posted 2 to 7 Days Ago (prior business days)",
 "Outside your 48-hour window. Because the pull date is a Monday, ages 1 and 2 fall on Sunday and Saturday and are "
 "empty - the rows here start at Friday. This tab is where the week's actual volume sits.",COLS)
e2=write_rows(w2,backup,HDR+1); w2.freeze_panes=f"A{HDR+1}"
if e2>HDR+1: w2.auto_filter.ref=f"A{HDR}:K{e2-1}"

# ---------------- coverage sheet ------------------------------------------
ALL = ([(rk,n) for rk,n,_ in FORTUNE100] + [(rk,n) for rk,n,_,_ in F200]
       + [(rk,n) for rk,n,_,_ in F300])
w3=wb.create_sheet("Coverage (all 300)")
w3["A1"]="Search Coverage - All 300 Fortune Companies"; w3["A1"].font=TTL
w3["A2"]=("Which companies were searched via a live API and which were not, with the reason. For any company "
          "not searched, a blank means UNKNOWN - not 'no openings'. Use the careers link to check those by hand.")
w3["A2"].font=SUB
w3.merge_cells("A1:G1"); w3.merge_cells("A2:G2")
C3=[("Rank",7),("Tier",14),("Company",30),("Search Status",26),("Matches (<=7d, US)",17),("Source / Reason",50),("Careers Site",24)]
for i,(h,w) in enumerate(C3,start=1):
    c=w3.cell(4,i,h); c.font=HDR_FONT; c.fill=HDR_FILL
    c.alignment=Alignment(horizontal="center",vertical="center",wrap_text=True)
    w3.column_dimensions[get_column_letter(i)].width=w
w3.row_dimensions[4].height=30
counts={}
for r in us: counts[r["company"]]=counts.get(r["company"],0)+1
GRN=PatternFill("solid",fgColor="E2EFDA"); RED=PatternFill("solid",fgColor="FCE4E4"); AMB=PatternFill("solid",fgColor="FFF2CC")
for n,(rank,name) in enumerate(ALL):
    rr=5+n; status,src,url=coverage(name,rank)
    searched=status.startswith("Searched")
    found=counts.get(name,0) if searched else "not searched"
    tier="Fortune 1-100" if rank<=100 else ("Fortune 101-200" if rank<=200 else "Fortune 201-300")
    for i,v in enumerate([rank,tier,name,status,found,src,""],start=1):
        c=w3.cell(rr,i,v); c.font=CELL; c.border=BORDER
        c.alignment=Alignment(vertical="center",wrap_text=(i==6))
        if i==4: c.fill=GRN if searched else (RED if "blocked" in status else AMB)
    w3.cell(rr,1).alignment=Alignment(horizontal="center")
    w3.cell(rr,5).alignment=Alignment(horizontal="center")
    if url:
        lc=w3.cell(rr,7); lc.value="Careers site"; lc.font=LINK; lc.hyperlink=url
last=4+len(ALL)
w3.freeze_panes="A5"; w3.auto_filter.ref=f"A4:G{last}"
sr=last+2
w3.cell(sr,1,"Coverage summary").font=Font(name=ARIAL,bold=True,size=11,color="1F3864")
for n,(lbl,f) in enumerate([
 ("Searched via live API",f'=COUNTIF(D5:D{last},"Searched (live API)")'),
 ("Not searched - no public API",f'=COUNTIF(D5:D{last},"Not searched - no API")'),
 ("Not searched - endpoint failed",f'=COUNTIF(D5:D{last},"Not searched - endpoint failed")'),
 ("Not searched - blocked",f'=COUNTIF(D5:D{last},"Not searched - blocked")'),
 ("Total companies",f"=COUNTA(C5:C{last})"),
],start=1):
    w3.cell(sr+n,1,lbl).font=CELL
    c=w3.cell(sr+n,2,f); c.font=BOLD; c.number_format="0"

w4=wb.create_sheet("Method & Caveats")
w4.column_dimensions["A"].width=118
w4["A1"]="How this file was built - and what it does not cover"; w4["A1"].font=TTL
searched_total = sum(1 for rk,n in ALL if coverage(n,rk)[0].startswith("Searched"))
NOTES=[
 ("H","What you asked for"),
 ("T","Data Analyst / Senior Data Analyst / Business Analyst roles (plus close title variants) at Fortune 300 "
      "companies, US locations only, posted within the last 48 hours. Scraped fresh on the pull date."),
 ("B",""),
 ("H","READ THIS FIRST - the 48-hour window landed on a weekend"),
 ("T","The pull date, 17 August 2026, is a Monday. A 48-hour window therefore covers Monday and Sunday. Employers "
      "post almost nothing at weekends: this scrape found 5 postings on Monday, ZERO on Sunday and ZERO on Saturday, "
      "against 5 on Friday, 8 on Thursday and 12 on Wednesday."),
 ("T","So the main sheet is effectively a single business day of hiring, not two days. That is a calendar artifact, "
      "not a signal that hiring has stopped. If you want two working days of coverage, run this on a Wednesday-to-"
      "Friday, or widen the window to 4 days on a Monday. The 'Prior business days' tab holds the rest of the week."),
 ("B",""),
 ("H","Where the data comes from"),
 ("T","Every posting was read directly from the employer's own applicant-tracking system over its public JSON "
      "endpoint - not from a job aggregator and not from a search engine. Six platforms: Workday, Oracle Cloud "
      "Recruiting, Phenom, Eightfold, Amazon's own jobs API, and Greenhouse."),
 ("T","The pull date itself was verified against live data rather than assumed: jobs labelled 'Posted Today' were "
      "opened and their requisition start dates read back, returning 2026-08-17. For every Workday match the "
      "site's 'Posted Today / N Days Ago' label was then cross-checked against that requisition date - all agreed, "
      "with zero mismatches."),
 ("B",""),
 ("H","Coverage falls as you go down the Fortune list"),
 ("T","Endpoint discovery found usable APIs for progressively fewer companies in each tier: strongest in the "
      "Fortune 1-100, weaker in 101-200, weakest in 201-300, where most companies run custom or mid-market career "
      "sites that expose nothing machine-readable. The Coverage tab records the exact reason per company."),
 ("T","The main sheet is a floor, not a ceiling. It is complete and accurate for the companies actually searched. "
      "A company absent from the results either genuinely has no fresh posting, or could not be searched."),
 ("B",""),
 ("H","How US-only was enforced"),
 ("T","Postings were resolved to their full location list, including locations hidden behind a '3 Locations' "
      "label, then filtered to US states, US territories and US-based remote roles. Non-US matches were dropped."),
 ("B",""),
 ("H","Freshness"),
 ("T","This is a snapshot as of the pull date. Postings are filled or pulled within days. Re-run before relying "
      "on it later in the week."),
 ("B",""),
 ("H","Fortune ranking sources"),
 ("T","Ranks 1-200 from the us500.com Fortune 500 listing; ranks 201-300 from the demandsage Fortune 500 listing, "
      "chosen because a competing source duplicated ~20 companies already ranked in 101-200. Rankings vary "
      "slightly between publishers; treat rank as approximate and company membership as the reliable part."),
]
r=3
for kind,text in NOTES:
    c=w4.cell(r,1,text)
    if kind=="H": c.font=Font(name=ARIAL,bold=True,size=11,color="1F3864")
    else:
        c.font=Font(name=ARIAL,size=10); c.alignment=Alignment(wrap_text=True,vertical="top")
        w4.row_dimensions[r].height=max(15,13*(len(text)//105+1))
    r+=1

wb.save("Fortune300_Analyst_Openings_48h.xlsx")
print("main:",len(main),"| backup:",len(backup),
      "| companies in main:",len(set(r['company'] for r in main)),
      "| searched:",searched_total,"of",len(ALL))
