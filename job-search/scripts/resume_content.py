"""Truthful content bank for Ahmad Anis. Nothing here may be asserted unless it traces to
the baseline resume or to a capability Ahmad explicitly confirmed earlier in this engagement."""

# ---- capabilities Ahmad confirmed (used only when a JD asks for them) -------------
CONFIRMED_EXTRA = {
 "JIRA","Confluence","governance catalog tooling","master data management","metadata management",
 "data lineage","test case authoring","QA support","user stories","acceptance criteria","UAT",
 "business acceptance testing","mentoring","cloud platforms","CI/CD","SAS","natural language processing",
 "Palantir","Visio","Smartsheet","SAFe","healthcare payer systems","claims processing",
}
# ---- everything on the baseline resume -------------------------------------------
BASELINE_SKILLS = {
 "SQL","Python","Pandas","NumPy","Scikit-learn","VBA","PowerShell","Power BI","DAX","Power Query",
 "Tableau","SSRS","SQL Server","Snowflake","SAP","WMS","ETL","Informatica","data integration",
 "data integrity","data governance","forecasting","demand planning","regression","statistical analysis",
 "capacity modeling","Agile/Scrum","Waterfall","Lean","root cause analysis","KPI design","Excel",
}

CONTACT = {
 "name":"AHMAD ANIS",
 "email":"Ahmadanis3620@gmail.com",
 "phone":"(216) 860-8518",
 "linkedin":"linkedin.com/in/ahmadanis3620",
 "city":"Columbus, OH",
}

EDUCATION = [
 ("M.S. Information Systems", "Cleveland State University, Cleveland, OH", "2021 – 2022", "GPA 3.62",
  "Data Analysis · SQL · Machine Learning & AI · Enterprise Databases · Project Management"),
 ("B.E. Industrial Engineering", "National University of Sciences & Technology, Pakistan", "2014 – 2018", "GPA 3.2",
  "Probability & Statistics · Operations Research · SQL · ERP/SAP · Risk Management · Data Governance"),
]

# ---- skill groups; label -> (items, families it serves) ---------------------------
SKILL_GROUPS = [
 ("Analytics & Querying",
  "SQL (advanced), Python (Pandas, NumPy, Scikit-learn), Excel (advanced), SAS, VBA, PowerShell",
  {"data","tech","cloud","stats"}),
 ("BI & Visualization",
  "Power BI (DAX, Power Query), Tableau, SSRS, executive dashboards, KPI scorecards",
  {"data","finance","stats"}),
 ("Business Analysis",
  "Requirements elicitation, functional & non-functional specs, user stories, acceptance criteria, "
  "process flows (Visio), current/future-state and gap analysis",
  {"sdlc","tech"}),
 ("Testing & Quality",
  "Test scenarios & test cases, test data preparation, QA partnership, defect triage, UAT and business "
  "acceptance",
  {"sdlc"}),
 ("Data Engineering",
  "ETL pipeline development, Informatica, large-dataset cleaning & processing, data modeling, "
  "database design, system integration",
  {"data","cloud","tech"}),
 ("Data Governance",
  "Governance operating models, data quality controls, master data management, metadata & lineage, "
  "stewardship, auditability",
  {"gov"}),
 ("Cloud & Delivery",
  "Cloud platforms (AWS/Azure/GCP), CI/CD pipelines, Snowflake, SQL Server",
  {"cloud","tech"}),
 ("Enterprise Platforms",
  "SAP (SD, MM, CRM, PP, WLM), SQL Server, Snowflake, Informatica, WMS",
  {"tech","supply","finance"}),
 ("Delivery & Tools",
  "Agile/Scrum, SAFe, Waterfall, hybrid delivery, JIRA, Confluence, Smartsheet, Lean, root cause analysis",
  {"sdlc","tech"}),
 ("Modeling & Planning",
  "Forecasting, demand planning, regression, statistical analysis, capacity modeling, NLP",
  {"stats","supply","data"}),
]

# ---- bullet bank: (text, families, weight) ---------------------------------------
# weight 3 = flagship metric bullet, always eligible; 1 = supporting
BBW_HEADER = ("Bath & Body Works", "Columbus, OH", "May 2022 – Present")
BBW = [
 ("Engineered and deployed interactive Power BI dashboards integrating disparate enterprise data sources, "
  "cutting reporting time 30% and generating $20,000 in annual savings.", {"data","finance","stats"}, 3),
 ("Built analytical models for the transportation function that exposed critical deficiencies in the bidding "
  "process, delivering recommendations worth $10M in annual cost savings.", {"data","supply","finance","tech"}, 3),
 ("Developed SQL and Python analyses across large-scale sales datasets to surface demand-supply imbalances, "
  "improving forecast accuracy 25% and informing inventory and capacity decisions.", {"data","stats","supply"}, 3),
 ("Designed a carton-sizing optimization model that saved 200 man-hours per month through data-driven change "
  "to inventory processes.", {"supply","data"}, 2),
 ("Partnered with product and operations teams to turn analysis into process improvements, contributing to a "
  "$10,000 monthly labor cost reduction.", {"data","supply","sdlc"}, 2),
 ("Lead a monthly executive reporting cadence, presenting dashboard-driven insight on performance, risks and "
  "trends to align senior leadership on priorities.", {"data","finance","gov","stats"}, 2),
 ("Own data quality and governance processes across cross-functional analytics initiatives, maintaining review "
  "controls, ownership clarity and standards adoption that keep enterprise reporting trusted.", {"gov"}, 2),
 ("Elicit business, functional and non-functional requirements from non-technical stakeholders and translate "
  "them into documented specifications, user stories and acceptance criteria.", {"sdlc","tech"}, 2),
 ("Author test scenarios and detailed test cases aligned to documented requirements, partner with QA through "
  "execution and defect triage, and support business acceptance sign-off.", {"sdlc"}, 2),
 ("Maintain requirements traceability and version control across delivery cycles, keeping changes auditable "
  "from initial request through release.", {"sdlc","gov"}, 1),
 ("Analyze current- and future-state business processes to identify gaps, dependencies and improvement "
  "opportunities ahead of build.", {"sdlc","tech"}, 2),
 ("Build and automate Python and SQL data pipelines and reporting applications released through CI/CD "
  "practices on cloud infrastructure.", {"cloud","tech","data"}, 2),
 ("Execute SQL against backend databases for extraction, validation and reconciliation, confirming delivered "
  "data matches documented requirements before release.", {"tech","sdlc","data"}, 2),
 ("Serve as an expert resource to report consumers and mentor junior analysts on analytical methods, "
  "documentation standards and stakeholder communication.", {"sdlc","gov","data"}, 1),
 ("Track analytics and delivery work in JIRA and document standards, templates and procedures in Confluence, "
  "maintaining backlog visibility, ownership and dependency tracking.", {"sdlc","tech"}, 1),
]

GSK_HEADER = ("GlaxoSmithKline", "Karachi, Pakistan", "July 2018 – December 2020")
GSK = [
 ("Conducted cost-benefit and root cause analysis in SQL, Power BI and Tableau across pharmaceutical "
  "operations, identifying inefficiencies that drove a $50M reduction in logistics costs.",
  {"data","supply","finance","health","stats"}, 3),
 ("Led migration of manual data processes into SAP, applying master data management and validation controls "
  "to achieve 100% data integrity and cut data entry errors 40%.", {"gov","tech","sdlc"}, 3),
 ("Managed and analyzed data for 1,000+ pharmaceutical SKUs across East and West Africa, building reporting "
  "infrastructure to monitor supply-demand balance and flag inventory risk in real time.",
  {"supply","data","health"}, 3),
 ("Established a standardized Informatica ETL operating procedure for product data ingestion into SAP, "
  "creating consistent, auditable and lineage-traceable data flows across business functions.",
  {"gov","cloud","tech"}, 2),
 ("Improved demand forecast accuracy 20% through recurring performance reviews with planners and business "
  "subject-matter experts, using statistical models and historical trend analysis.", {"stats","supply","data"}, 2),
 ("Integrated SSRS with SQL Server and Excel to automate reporting pipelines, eliminating manual reporting "
  "effort and improving data accessibility for business and IT teams.", {"data","tech","cloud"}, 2),
 ("Ran daily supply-demand gap analysis using VBA, Power BI, Tableau and PowerShell, reducing stockouts 30% "
  "through proactive insight delivery.", {"supply","data"}, 2),
 ("Delivered capacity planning and rough-cut capacity models supporting production and distribution planning, "
  "contributing to a 15% improvement in profit margins.", {"supply","finance","stats"}, 2),
 ("Validated delivered functionality against documented requirements through structured business acceptance "
  "testing at cutover.", {"sdlc"}, 2),
 ("Performed impact and scope analysis across supported applications and integrations, identifying systems "
  "impacts, dependencies and requirement gaps before build.", {"tech","sdlc"}, 2),
 ("Managed analytics delivery under Agile/Scrum and Waterfall in JIRA, tracking work items, owners, status, "
  "dependencies and risks while aligning stakeholders on roadmaps.", {"sdlc","tech"}, 1),
 ("Coordinated data collection across markets, updating collection tools and processes to yield statistically "
  "reliable and informative data for program assessment.", {"stats","health","gov"}, 1),
]
