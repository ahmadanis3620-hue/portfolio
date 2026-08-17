"""JD-term -> resume-term lexicon.

TRUE  : Ahmad can defend it (baseline resume, or confirmed directly in this engagement).
GAP   : appears in job descriptions but Ahmad does NOT have it. Never emitted onto a resume;
        reported in the index so he knows what he'll be asked about.
Each TRUE entry: canonical -> (detect regex, skills-line category, resume surface form)
"""

# category order also controls the order skill lines are printed when equally relevant
CATEGORIES = ["Languages & Querying","BI & Visualization","Business Analysis","Testing & Quality",
              "Data Engineering","Data Governance","Enterprise Platforms","Delivery & Tools",
              "Analytics & Modeling","Domain Expertise"]

TRUE = {
 # --- languages / query
 "SQL":            (r"\bsql\b", "Languages & Querying", "SQL (advanced)"),
 "Python":         (r"\bpython\b", "Languages & Querying", "Python (Pandas, NumPy, Scikit-learn)"),
 "SAS":            (r"\bsas\b", "Languages & Querying", "SAS"),
 "Excel":          (r"\bexcel\b", "Languages & Querying", "Excel (advanced)"),
 "VBA":            (r"\bvba\b", "Languages & Querying", "VBA"),
 "PowerShell":     (r"\bpowershell\b", "Languages & Querying", "PowerShell"),
 # --- BI
 "Power BI":       (r"power\s*bi", "BI & Visualization", "Power BI (DAX, Power Query)"),
 "Tableau":        (r"\btableau\b", "BI & Visualization", "Tableau"),
 "SSRS":           (r"\bssrs\b", "BI & Visualization", "SSRS"),
 "dashboards":     (r"\bdashboard", "BI & Visualization", "dashboards"),
 "data visualization": (r"\bvisuali[sz]", "BI & Visualization", "data visualization"),
 "scorecards":     (r"\bscorecard", "BI & Visualization", "scorecards"),
 "KPIs":           (r"\bkpi", "BI & Visualization", "KPI design & monitoring"),
 "reporting":      (r"\breporting\b", "BI & Visualization", "operational & executive reporting"),
 "ad hoc reporting": (r"ad[- ]hoc", "BI & Visualization", "ad hoc reporting"),
 "self-service":   (r"self[- ]service", "BI & Visualization", "self-service reporting"),
 "business intelligence": (r"business intelligence", "BI & Visualization", "business intelligence"),
 # --- business analysis
 "business requirements": (r"business requirement", "Business Analysis", "business requirements gathering"),
 "functional requirements": (r"functional requirement", "Business Analysis", "functional requirements"),
 "non-functional requirements": (r"non[- ]functional", "Business Analysis", "non-functional requirements"),
 "requirements elicitation": (r"elicit", "Business Analysis", "requirements elicitation"),
 "user stories":   (r"user stor", "Business Analysis", "user stories"),
 "acceptance criteria": (r"acceptance criteria", "Business Analysis", "acceptance criteria"),
 "process flows":  (r"process (flow|map)", "Business Analysis", "process flows & mapping (Visio)"),
 "gap analysis":   (r"gap analysis", "Business Analysis", "fit-gap analysis"),
 "current state":  (r"current[- ]state", "Business Analysis", "current-state analysis"),
 "future state":   (r"future[- ]state", "Business Analysis", "future-state design"),
 "traceability":   (r"traceab", "Business Analysis", "requirements traceability"),
 "documentation":  (r"\bdocumentation\b", "Business Analysis", "solution documentation"),
 "use cases":      (r"use case", "Business Analysis", "use cases"),
 "SDLC":           (r"\bsdlc\b|software development life", "Business Analysis", "full SDLC"),
 # --- testing
 "UAT":            (r"\buat\b|user acceptance", "Testing & Quality", "UAT / user acceptance testing"),
 "test cases":     (r"test case", "Testing & Quality", "test case authoring"),
 "test plans":     (r"test plan", "Testing & Quality", "test planning"),
 "test scripts":   (r"test script", "Testing & Quality", "test scripts"),
 "QA":             (r"\bqa\b|quality assurance", "Testing & Quality", "QA partnership"),
 "defect triage":  (r"\bdefect", "Testing & Quality", "defect triage & root cause"),
 "regression testing": (r"regression testing", "Testing & Quality", "regression testing support"),
 "data validation": (r"data validation|validat", "Testing & Quality", "data validation"),
 # --- data engineering
 "ETL":            (r"\betl\b", "Data Engineering", "ETL pipeline development"),
 "data pipelines": (r"data pipeline", "Data Engineering", "data pipelines"),
 "data modeling":  (r"data model", "Data Engineering", "data modeling"),
 "data warehouse": (r"data warehouse|data mart", "Data Engineering", "data warehouse & mart design"),
 "Informatica":    (r"informatica", "Data Engineering", "Informatica"),
 "automation":     (r"automat", "Data Engineering", "process & reporting automation"),
 "integration":    (r"integrat", "Data Engineering", "system & data integration"),
 "migration":      (r"migrat", "Data Engineering", "platform migration"),
 "CI/CD":          (r"ci/cd|continuous integration", "Data Engineering", "CI/CD pipelines"),
 "cloud":          (r"\bcloud\b|\baws\b|\bazure\b|\bgcp\b", "Data Engineering", "cloud platforms (AWS/Azure/GCP)"),
 # --- governance
 "data governance":(r"data governance", "Data Governance", "data governance"),
 "data quality":   (r"data quality", "Data Governance", "data quality controls"),
 "master data":    (r"master data", "Data Governance", "master data management"),
 "metadata":       (r"metadata", "Data Governance", "metadata management"),
 "data lineage":   (r"lineage", "Data Governance", "data lineage"),
 "data stewardship":(r"steward", "Data Governance", "data stewardship"),
 "data integrity": (r"data integrity", "Data Governance", "data integrity"),
 "compliance":     (r"complian|regulatory", "Data Governance", "regulatory & compliance reporting"),
 "audit":          (r"\baudit", "Data Governance", "auditability & controls"),
 "governance tooling": (r"collibra|alation|data catalog", "Data Governance", "governance catalog tooling"),
 # --- platforms
 "SAP":            (r"\bsap\b|\berp\b", "Enterprise Platforms", "SAP (SD, MM, CRM, PP, WLM)"),
 "SQL Server":     (r"sql server", "Enterprise Platforms", "SQL Server"),
 "Snowflake":      (r"snowflake", "Enterprise Platforms", "Snowflake"),
 "Palantir":       (r"palantir", "Enterprise Platforms", "Palantir"),
 "WMS":            (r"\bwms\b|warehouse management", "Enterprise Platforms", "WMS"),
 # --- delivery
 "Agile":          (r"\bagile\b", "Delivery & Tools", "Agile"),
 "Scrum":          (r"\bscrum\b", "Delivery & Tools", "Scrum"),
 "SAFe":           (r"\bsafe\b(?!ty)", "Delivery & Tools", "SAFe"),
 "Waterfall":      (r"waterfall", "Delivery & Tools", "Waterfall"),
 "JIRA":           (r"\bjira\b", "Delivery & Tools", "JIRA"),
 "Confluence":     (r"confluence", "Delivery & Tools", "Confluence"),
 "Smartsheet":     (r"smartsheet", "Delivery & Tools", "Smartsheet"),
 "Visio":          (r"\bvisio\b", "Delivery & Tools", "Visio"),
 "SharePoint":     (r"sharepoint", "Delivery & Tools", "SharePoint"),
 "PowerPoint":     (r"powerpoint|presentation", "Delivery & Tools", "PowerPoint & executive presentation"),
 "stakeholder management": (r"stakeholder", "Delivery & Tools", "stakeholder management"),
 "cross-functional": (r"cross[- ]functional", "Delivery & Tools", "cross-functional collaboration"),
 "mentoring":      (r"\bmentor|coach", "Delivery & Tools", "mentoring & knowledge transfer"),
 # --- analytics / modeling
 "forecasting":    (r"forecast", "Analytics & Modeling", "forecasting"),
 "predictive modeling": (r"predictive", "Analytics & Modeling", "predictive modeling"),
 "regression":     (r"regression(?! testing)", "Analytics & Modeling", "regression analysis"),
 "statistical analysis": (r"statistic", "Analytics & Modeling", "statistical analysis"),
 "machine learning": (r"machine learning|\bml\b", "Analytics & Modeling",
                      "machine learning (Scikit-learn; MS coursework)"),
 "NLP":            (r"\bnlp\b|natural language", "Analytics & Modeling", "natural language processing"),
 "root cause analysis": (r"root cause", "Analytics & Modeling", "root cause analysis"),
 "capacity modeling": (r"capacity", "Analytics & Modeling", "capacity modeling"),
 "reconciliation": (r"reconcil", "Analytics & Modeling", "reconciliation"),
 "cost-benefit":   (r"cost[- ]benefit|cost analysis", "Analytics & Modeling", "cost-benefit analysis"),
 # --- domain
 "supply chain":   (r"supply chain", "Domain Expertise", "supply chain analytics"),
 "inventory":      (r"inventory", "Domain Expertise", "inventory analytics"),
 "demand planning":(r"demand plan|demand forecast", "Domain Expertise", "demand planning"),
 "logistics":      (r"logistics", "Domain Expertise", "logistics & transportation analysis"),
 "procurement":    (r"procurement|sourcing", "Domain Expertise", "sourcing & procurement data"),
 "pharmaceutical": (r"pharmac", "Domain Expertise", "pharmaceutical operations"),
 "healthcare":     (r"health(care)?\b|patient|clinical", "Domain Expertise", "healthcare data"),
 "claims":         (r"\bclaims\b", "Domain Expertise", "claims data"),
 "payer":          (r"\bpayer\b|medicare|medicaid", "Domain Expertise", "healthcare payer systems"),
 "financial reporting": (r"financial report|financial analysis", "Domain Expertise", "financial reporting"),
}

# In JDs but NOT Ahmad's - never emitted; surfaced as interview-prep gaps.
GAP = {
 "Java":       r"\bjava\b(?!script)", "R": r"(?<![A-Za-z])R(?![A-Za-z])(?=\s*(,|/|and|programming))",
 "Salesforce": r"salesforce", "Alteryx": r"alteryx", "Looker": r"\blooker\b", "Qlik": r"\bqlik",
 "Databricks": r"databricks", "Hadoop": r"hadoop", "Spark": r"\bspark\b", "ServiceNow": r"servicenow",
 "Oracle EPM/Hyperion": r"hyperion|oracle epm", "Essbase": r"essbase", "Anaplan": r"anaplan",
 "Snowpark": r"snowpark", "dbt": r"\bdbt\b", "Airflow": r"airflow", "Kafka": r"kafka",
 "Scala": r"\bscala\b", "C#": r"c#|\.net", "Power Automate": r"power automate",
 "Adobe Analytics": r"adobe analytics", "Google Analytics": r"google analytics",
 "Teradata": r"teradata", "Cognos": r"cognos", "MicroStrategy": r"microstrategy",
 "SPSS": r"\bspss\b", "Minitab": r"minitab", "Six Sigma": r"six sigma|black belt",
 "Security clearance": r"security clearance|ts/sci|top secret|polygraph",
}
