import re
NAMES = """Diamondback Energy|EchoStar|Textron|Expedia Group|W.R. Berkley|Xcel Energy|FirstEnergy|
Erie Insurance Group|First Citizens BancShares|Blackstone|Fidelity National Financial|Otis Worldwide|
Amentum Holdings|Regeneron Pharmaceuticals|Estee Lauder|BorgWarner|Northern Trust|Viatris|MasTec|Reliance|
Western & Southern Financial Group|Alaska Air Group|BrightSpring Health Services|CSX|LKQ|Labcorp Holdings|
Arthur J. Gallagher|Venture Global|DoorDash|Sempra|DaVita|Eversource Energy|ServiceNow|M&T Bank|Henry Schein|
GXO Logistics|Ball|Unum Group|Las Vegas Sands|Entergy|Fifth Third Bancorp|Graybar Electric|DXC Technology|
Alcoa|Assurant|Ryder System|Intercontinental Exchange|Cincinnati Financial|Chewy|Community Health Systems|
Huntington Bancshares|Huntington Ingalls Industries|Wayfair|Lumen Technologies|Ulta Beauty|Crown Holdings|
Airbnb|AES|Norfolk Southern|Public Service Enterprise Group|KLA|Expand Energy|Hormel Foods|Darden Restaurants|
Citizens Financial Group|Mosaic|Hilton Worldwide Holdings|Air Products & Chemicals|Jacobs Solutions|
Vertex Pharmaceuticals|J.B. Hunt Transport Services|Booz Allen Hamilton|Williams|Chipotle Mexican Grill|
Yum China Holdings|Oscar Health|Hershey|Motorola Solutions|Equitable Holdings|Avis Budget Group|
Conagra Brands|Baxter International|Burlington Stores|Caesars Entertainment|Owens Corning|KeyCorp|
Thrivent Financial|Westlake|Westinghouse Air Brake|Molson Coors Beverage|Lululemon athletica|FM|Ebay|
Expeditors International|Quest Diagnostics|Analog Devices|Andersons|Gold.com|Toll Brothers|
International Flavors & Fragrances|Welltower|Jefferies Financial Group|Autoliv|Mohawk Industries|
Delek US Holdings|Fidelity National Information Services|Accendra Health|American Tower|NVR|
Interactive Brokers Group|Oshkosh|Cintas|Campbells|Vertiv Holdings|Global Payments|Constellation Brands|
AGCO|Intuitive Surgical|Ace Hardware|Dana|Biogen|News Corp|Concentrix|WEC Energy Group|VF|Seaboard|
Icahn Enterprises|Regions Financial|Thor Industries|Workday|Celanese|Western Digital|QVC Group|Zoetis|
CenterPoint Energy|Equinix|Palo Alto Networks|APA|Old Republic International|Comfort Systems USA|
JetBlue Airways|PPL|Xylem|Arista Networks|Packaging Corp of America|PVH|Ovintiv|Avery Dennison|
TransDigm Group|Sprouts Farmers Market|Prologis|Franklin Resources|Eastman Chemical|ABM Industries|NOV|
J.M. Smucker|Securian Financial Group|EQT|CACI International|Graphic Packaging Holding|Advance Auto Parts|
Optimum Communications|Sirius XM Holdings|CMS Energy|Hertz Global Holdings|Ameren|Rockwell Automation|
Solventum|Monster Beverage|Nasdaq|Howmet Aerospace|Insight Enterprises|Zimmer Biomet Holdings|Yum Brands|
Fastenal|Marvell Technology|Voya Financial|American Financial Group|Post Holdings|XPO|DuPont|Sanmina|
Taylor Morrison Home|Dover|Vulcan Materials|APi Group|Roper Technologies|KBR|Sonoco Products|
Williams-Sonoma|Commercial Metals|Moodys|Continental Resources|Ingersoll Rand|Core & Main|Coterra Energy|
Primoris Services|Masco|Somnigroup International|Resideo Technologies"""
names=[n.strip() for n in NAMES.replace("\n","").split("|") if n.strip()]
SUFFIX=re.compile(r"\b(holdings?|group|international|inc|corp(oration)?|company|co|plc|systems?|"
                  r"technologies|technology|services|financial|energy|brands|stores|enterprises|"
                  r"pharmaceuticals|restaurants|worldwide|industries|products)\b", re.I)
def slug(n):
    b=SUFFIX.sub("", n)
    b=re.sub(r"[^A-Za-z0-9]+","",b).lower()
    return b or re.sub(r"[^A-Za-z0-9]+","",n).lower()
out=[]
for i,n in enumerate(names, start=301):
    s=slug(n); full=re.sub(r"[^A-Za-z0-9]+","",n).lower()
    tenants=list(dict.fromkeys([s, full]))[:2]
    urls=[f"https://careers.{s}.com/", f"https://jobs.{s}.com/", f"https://www.{s}.com/careers"]
    out.append((i,n,tenants,urls))
with open("f500_companies.py","w") as f:
    f.write("# Fortune 301-500 (demandsage listing); tenant/url guesses auto-derived\nF500 = [\n")
    for i,n,t,u in out:
        f.write(f" ({i},{n!r},{t!r},{u!r}),\n")
    f.write("]\n")
print("companies:",len(out),"first:",out[0][:2],"last:",out[-1][:2])
