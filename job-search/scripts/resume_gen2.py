"""Per-JD keyword-matched resumes with a guaranteed-coverage pass and honest gap reporting."""
import json, re, os, collections
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from resume_content import CONTACT, EDUCATION, BBW, BBW_HEADER, GSK, GSK_HEADER
from lexicon import TRUE, GAP, CATEGORIES

# Ahmad's standing stack - always present so a JD that simply doesn't name a tool
# never makes him look like he lacks it. JD-matched terms are surfaced FIRST.
BASE = {
 "Languages & Querying": ["SQL (advanced)","Python (Pandas, NumPy, Scikit-learn)","Excel (advanced)","VBA"],
 "BI & Visualization":   ["Power BI (DAX, Power Query)","Tableau","SSRS","dashboards","KPI design & monitoring"],
 "Data Engineering":     ["ETL pipeline development","Informatica","data modeling","system & data integration"],
 "Enterprise Platforms": ["SAP (SD, MM, CRM, PP, WLM)","SQL Server","Snowflake"],
 "Delivery & Tools":     ["Agile/Scrum","Waterfall","JIRA","Confluence","stakeholder management"],
 "Analytics & Modeling": ["forecasting","statistical analysis","root cause analysis"],
}
CORE_COMPETENCY_FALLBACK = ["SQL & Python analysis","Power BI & Tableau dashboards",
 "KPI design & executive reporting","ETL & data pipeline development","data quality controls",
 "requirements gathering","cross-functional collaboration","stakeholder communication"]

OUT = "resumes"; os.makedirs(OUT, exist_ok=True)
NAVY = RGBColor(0x1F,0x38,0x64); GREY = RGBColor(0x50,0x50,0x50); FONT = "Calibri"

FAMILY_OF = {
 "Business Analysis":"sdlc","Testing & Quality":"sdlc","BI & Visualization":"data",
 "Languages & Querying":"data","Data Engineering":"cloud","Data Governance":"gov",
 "Enterprise Platforms":"tech","Delivery & Tools":"sdlc","Analytics & Modeling":"stats",
 "Domain Expertise":"domain",
}

def match_jd(text):
    t = text or ""
    hits = {}
    for canon,(rx,cat,form) in TRUE.items():
        m = re.search(rx, t, re.I)
        if m:
            n = len(re.findall(rx, t, re.I))
            hits[canon] = {"cat":cat, "form":form, "count":n}
    gaps = [g for g,rx in GAP.items() if re.search(rx, t, re.I)]
    return hits, gaps

def skill_lines(hits):
    """JD-matched forms first within each line; then Ahmad's standing stack. Never drops core skills."""
    matched = collections.defaultdict(list)
    for canon,h in sorted(hits.items(), key=lambda kv:-kv[1]["count"]):
        if h["form"] not in matched[h["cat"]]:
            matched[h["cat"]].append(h["form"])
    cats = set(matched) | set(BASE)
    weight = {c: sum(hits[k]["count"] for k in hits if hits[k]["cat"]==c) for c in cats}
    order = sorted(cats, key=lambda c:(-weight.get(c,0),
                   CATEGORIES.index(c) if c in CATEGORIES else 99))
    out=[]
    for c in order:
        items = list(matched.get(c,[]))
        for b in BASE.get(c,[]):
            if not any(b.split(" (")[0].lower() == x.split(" (")[0].lower() for x in items):
                items.append(b)
        if items: out.append((c, ", ".join(items), bool(matched.get(c))))
    # never let the length cap drop a category that carries a JD-matched term
    keep = [x for x in out if x[2]]
    for x in out:
        if len(keep) >= 7: break
        if x not in keep: keep.append(x)
    keep.sort(key=lambda x: out.index(x))
    return [(c, i) for c, i, _ in keep]

def fam_scores(hits):
    sc = collections.Counter()
    for h in hits.values(): sc[FAMILY_OF.get(h["cat"],"data")] += h["count"]
    return [f for f,_ in sc.most_common()]

OPENERS = {
 "sdlc":"Business analyst with 6+ years acting as the bridge between business partners and technical teams, "
        "translating business need into requirements that hold through design, build, testing and release.",
 "data":"Data analyst with 6+ years turning complex, high-volume enterprise datasets into decisions, owning "
        "the work end to end from extraction and modeling through dashboards and executive reporting.",
 "gov": "Data professional with 6+ years operationalising data governance — standards, quality controls, "
        "master data and metadata — keeping enterprise reporting trusted and auditable.",
 "tech":"Technical business analyst with 6+ years leading systems analysis across enterprise platforms, "
        "translating business need into technical requirements and integration-aware design.",
 "cloud":"Analytics engineer with 6+ years building ETL pipelines and automated reporting on cloud "
         "infrastructure, replacing manual process with governed data products.",
 "stats":"Analyst with 6+ years applying forecasting, regression and statistical modeling to large "
         "operational datasets, with measurable and repeatable accuracy gains.",
 "domain":"Analyst with 6+ years across supply chain, pharmaceutical and retail operations, pairing deep "
          "domain grounding with advanced SQL, Python and BI delivery.",
}
PROOF = {
 "sdlc":"Writes user stories and acceptance criteria, authors test cases, partners with QA through defect "
        "triage, and drives UAT and business acceptance to formal sign-off.",
 "data":"Advanced SQL and Python with Power BI and Tableau — dashboards that cut reporting time 30% and KPI "
        "frameworks presented monthly to senior leadership.",
 "gov": "Delivered a full SAP migration at 100% data integrity with a 40% drop in data entry errors, under "
        "documented quality controls and auditable, lineage-traceable data flows.",
 "tech":"Works across SAP, SQL Server, Snowflake and Informatica, running impact and scope analysis over "
        "integrated systems before build.",
 "cloud":"Python and SQL pipelines released through CI/CD practices, plus Informatica ETL standards that keep "
         "data flows consistent and auditable.",
 "stats":"Forecast accuracy improved 25% at Bath & Body Works and 20% at GSK through statistical modeling and "
         "structured performance review.",
 "domain":"Managed 1,000+ pharmaceutical SKUs across East and West Africa and drove a $50M logistics cost "
          "reduction through cost-benefit and root cause analysis.",
}

def summary(fams, hits):
    lead = fams[0] if fams else "data"
    parts = [OPENERS.get(lead, OPENERS["data"]), PROOF.get(lead, PROOF["data"])]
    for f in fams[1:3]:
        p = PROOF.get(f)
        if p and p not in parts: parts.append(p)
    parts.append("M.S. Information Systems; B.E. Industrial Engineering.")
    return " ".join(parts[:4])

def pick_bullets(bank, fams, hits, want):
    famset = set(fams[:3])
    ranked = []
    for txt, bf, w in bank:
        low = txt.lower()
        kw = sum(1 for c,h in hits.items() if c.lower().split()[0] in low)
        ranked.append((w*2 + len(bf & famset)*3 + kw, txt))
    ranked.sort(key=lambda x:-x[0])
    return [t for _,t in ranked[:want]]

# ---------- docx helpers
def rule(p, color="BFBFBF", size=6):
    pPr=p._p.get_or_add_pPr(); b=OxmlElement('w:pBdr'); bt=OxmlElement('w:bottom')
    bt.set(qn('w:val'),'single'); bt.set(qn('w:sz'),str(size)); bt.set(qn('w:space'),'2'); bt.set(qn('w:color'),color)
    b.append(bt); pPr.append(b)

def para(doc,text="",size=10.5,bold=False,color=None,sa=2,sb=0,align=None,italic=False):
    p=doc.add_paragraph(); pf=p.paragraph_format
    pf.space_after=Pt(sa); pf.space_before=Pt(sb); pf.line_spacing=1.0
    if align: p.alignment=align
    if text:
        r=p.add_run(text); r.bold=bold; r.italic=italic; r.font.size=Pt(size); r.font.name=FONT
        if color is not None: r.font.color.rgb=color
    return p

def heading(doc,text):
    p=para(doc,text,size=10.5,bold=True,color=NAVY,sb=7,sa=3)
    for r in p.runs:
        rPr=r._r.get_or_add_rPr(); sp=OxmlElement('w:spacing'); sp.set(qn('w:val'),'30'); rPr.append(sp)
    rule(p); return p

def bullet(doc,text,size=10):
    p=doc.add_paragraph(style="List Bullet"); pf=p.paragraph_format
    pf.space_after=Pt(2); pf.space_before=Pt(0); pf.line_spacing=1.0
    pf.left_indent=Inches(0.18); pf.first_line_indent=Inches(-0.13)
    r=p.add_run(text); r.font.size=Pt(size); r.font.name=FONT
    return p

def build(job):
    hits, gaps = match_jd(job["jd_text"])
    fams = fam_scores(hits) or ["data"]
    jd_title = (job.get("jd_title") or job["title"]).strip()

    doc=Document(); st=doc.styles["Normal"]; st.font.name=FONT; st.font.size=Pt(10.5)
    st.element.rPr.rFonts.set(qn('w:eastAsia'),FONT)
    s=doc.sections[0]; s.page_width,s.page_height=Inches(8.5),Inches(11)
    s.top_margin=s.bottom_margin=Inches(0.5); s.left_margin=s.right_margin=Inches(0.6)

    p=para(doc,CONTACT["name"],size=20,bold=True,color=NAVY,align=WD_ALIGN_PARAGRAPH.CENTER,sa=0)
    for r in p.runs:
        rPr=r._r.get_or_add_rPr(); sp=OxmlElement('w:spacing'); sp.set(qn('w:val'),'60'); rPr.append(sp)
    para(doc,jd_title,size=11.5,color=GREY,align=WD_ALIGN_PARAGRAPH.CENTER,sa=1)
    cp=para(doc,f'{CONTACT["email"]}  |  {CONTACT["phone"]}  |  {CONTACT["linkedin"]}  |  {CONTACT["city"]}',
            size=9.5,color=GREY,align=WD_ALIGN_PARAGRAPH.CENTER,sa=4)
    rule(cp,color="1F3864",size=8)

    heading(doc,"PROFESSIONAL SUMMARY")
    para(doc,summary(fams,hits),size=10,sa=3)

    # Core competencies = the JD's own top concepts, verbatim resume forms
    heading(doc,"CORE COMPETENCIES")
    top = [h["form"] for _,h in sorted(hits.items(), key=lambda kv:-kv[1]["count"])][:14]
    for c in CORE_COMPETENCY_FALLBACK:
        if len(top) >= 12: break
        if not any(c.split()[0].lower() in t.lower() for t in top): top.append(c)
    para(doc,"  ·  ".join(top),size=9.5,sa=3)

    heading(doc,"TECHNICAL SKILLS")
    lines = skill_lines(hits)
    for label,items in lines:
        p=doc.add_paragraph(); pf=p.paragraph_format
        pf.space_after=Pt(1); pf.space_before=Pt(0); pf.line_spacing=1.0
        r1=p.add_run(f"{label}: "); r1.bold=True; r1.font.size=Pt(10); r1.font.name=FONT
        r2=p.add_run(items); r2.font.size=Pt(10); r2.font.name=FONT

    heading(doc,"PROFESSIONAL EXPERIENCE")
    for (org,loc,dates),bank,want in ((BBW_HEADER,BBW,8),(GSK_HEADER,GSK,7)):
        role = "Senior Data Analyst / Business Analyst" if org.startswith("Bath") else "Data Analyst & Reporting Engineer"
        p=doc.add_paragraph(); pf=p.paragraph_format
        pf.space_before=Pt(5); pf.space_after=Pt(0); pf.line_spacing=1.0
        r=p.add_run(f"{role}  |  {org}"); r.bold=True; r.font.size=Pt(10.5); r.font.name=FONT
        para(doc,f"{loc}  ·  {dates}",size=9.5,color=GREY,italic=True,sa=2)
        for b in pick_bullets(bank,fams,hits,want): bullet(doc,b)

    heading(doc,"EDUCATION")
    for deg,school,yrs,gpa,course in EDUCATION:
        p=doc.add_paragraph(); pf=p.paragraph_format
        pf.space_before=Pt(3); pf.space_after=Pt(0); pf.line_spacing=1.0
        r=p.add_run(f"{deg}  |  {school}"); r.bold=True; r.font.size=Pt(10); r.font.name=FONT
        para(doc,f"{yrs}  ·  {gpa}  ·  {course}",size=9.5,color=GREY,sa=2)

    return doc, hits, gaps, fams

def slug(s,n=52):
    return re.sub(r"[^A-Za-z0-9]+","_",s).strip("_")[:n].rstrip("_")

jobs=json.load(open("jds.json")); index=[]
for j in jobs:
    doc,hits,gaps,fams = build(j)
    fn=f"{j['idx']:02d}_{slug(j['company'],22)}_{slug(j['title'],46)}.docx"
    path=os.path.join(OUT,fn); doc.save(path)
    # ---- verify every TRUE-matched keyword actually landed in the document
    txt=" ".join(p.text for p in Document(path).paragraphs).lower()
    missing=[c for c,h in hits.items() if h["form"].split(" (")[0].lower() not in txt
             and c.lower() not in txt]
    index.append({"file":fn,**{k:j[k] for k in ("company","title","location","start_date","url","source","rank")},
                  "families":fams[:3],"matched":sorted(hits),"n_matched":len(hits),
                  "gaps":gaps,"missing_in_doc":missing})
json.dump(index,open("resume_index.json","w"),indent=1)

tot=sum(i["n_matched"] for i in index); miss=sum(len(i["missing_in_doc"]) for i in index)
print(f"generated {len(index)} resumes")
print(f"JD keywords matched (truthful): {tot} across 35 -> mean {tot/len(index):.1f} per resume")
print(f"matched keywords NOT present in the document: {miss}  (target 0)")
print("mean gaps per JD:", round(sum(len(i['gaps']) for i in index)/len(index),1))
