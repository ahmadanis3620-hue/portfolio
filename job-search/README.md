# Fortune 100 Analyst Job Openings

Pipeline that pulls **Data Analyst / Senior Data Analyst / Business Analyst** openings at
Fortune 100 companies, US locations only, filtered to postings from the last 24–72 hours.

**Deliverable:** [`Fortune100_Analyst_Openings.xlsx`](Fortune100_Analyst_Openings.xlsx)

Snapshot taken **2026-08-13**. Job postings move fast — re-run before relying on the numbers.

---

## Results in that snapshot

| | |
|---|---|
| Openings within 72h (US) | **45** |
| Companies represented | **23** |
| Backup rows (4–7 days old) | 13 |
| Fortune 100 companies searched | **67 of 100** |

Workbook tabs: `Openings (last 72h)` · `Backup (4-7 days)` · `Coverage (all 100)` · `Method & Caveats`

### The coverage caveat

**33 of the Fortune 100 could not be searched**, so the main sheet is a *floor, not a ceiling*.
A company missing from the results either genuinely has no fresh posting, or was never searchable —
the `Coverage (all 100)` tab says which, company by company.

- **26** have no public JSON endpoint — Radancy, SuccessFactors, Avature and iCIMS career sites
  serve HTML only; IBM and Goldman Sachs run custom single-page apps.
- **7** actively block automated access — Apple, Google, Meta, Tesla, Progressive,
  American Airlines (403 / browser-issued tokens), and Microsoft, whose careers API host failed
  TLS verification through the sandbox egress proxy.

No row in this dataset is estimated or inferred. Companies that could not be searched are left
blank rather than filled with guesses.

---

## How the data is sourced

Every posting is read directly from the employer's own applicant-tracking system over its public
JSON endpoint — not from a job aggregator, and not from a search engine. Five platforms:

| Platform | Companies | Endpoint shape |
|---|---|---|
| Workday | 56 | `POST /wday/cxs/{tenant}/{site}/jobs` |
| Oracle Cloud Recruiting | 6 | `GET /hcmRestApi/.../recruitingCEJobRequisitions?finder=findReqs;siteNumber=CX_n` |
| Phenom | 3 | `GET /api/jobs?keywords=…` |
| amazon.jobs | 1 | `GET /en/search.json?base_query=…` |
| Greenhouse | 1 | `GET boards-api.greenhouse.io/v1/boards/{board}/jobs` |

### Why the dates are trustworthy

For the Workday companies each job's detail record carries an explicit requisition date, which was
cross-checked against the site's own *"Posted Today / N Days Ago"* label. **All 61 matched postings
agreed on both**, which is what makes the `Posted Date` column reliable. Oracle Cloud, Phenom,
Amazon and Greenhouse all return an explicit posting date directly.

---

## Layout

```
job-search/
├── Fortune100_Analyst_Openings.xlsx   # the deliverable
├── scripts/                           # pipeline, in run order
└── data/                              # archived output of the 2026-08-13 run
```

### scripts/

| File | Role |
|---|---|
| `companies.py` | Fortune 100 list + Workday tenant candidates + slug patterns |
| `endpoints.py` | Verified Workday endpoints; careers URLs for unsearchable companies |
| `probe.py` | Round 1 discovery — brute-forces Workday tenant/site slugs |
| `scrape.py` | Round 1 scrape — queries all Workday endpoints |
| `enrich.py` | Resolves full location lists + exact posting dates from job detail records |
| `probe44.py` | Round 2 discovery — tests the Phenom pattern across remaining careers domains |
| `detect2.py` | Round 2 discovery — fingerprints ATS platform from careers-page HTML |
| `round2.py` | Round 2 scrape — Oracle Cloud, Phenom, Amazon, Greenhouse |
| `build2.py` | **Builds the workbook** (merges both rounds) |
| `build_xlsx.py` | *Superseded* — round-1-only builder, kept for reference |

### data/

| File | Contents |
|---|---|
| `jobs_raw.json` | Round 1 raw Workday matches |
| `jobs_enriched.json` | Round 1 with resolved locations + verified dates |
| `jobs_round2.json` | Round 2 matches (Oracle/Phenom/Amazon/Greenhouse) |
| `workday_map.json` | Workday endpoints found by brute-force probing |
| `detect2.json` | ATS fingerprints per careers site |
| `phenom_map.json` | Confirmed Phenom hosts |

---

## Re-running

Requires Python 3 and `openpyxl` (`pip install openpyxl`). No API keys — every source is public.

Scripts read and write **relative to the current working directory**, so run them from `scripts/`:

```bash
cd job-search/scripts
python3 scrape.py      # round 1: Workday   -> jobs_raw.json
python3 enrich.py      # resolve locations + dates -> jobs_enriched.json
python3 round2.py      # round 2: other ATS -> jobs_round2.json
python3 build2.py      # -> Fortune100_Analyst_Openings.xlsx
```

Outputs land in `scripts/`; copy them over `data/` and the workbook up one level to refresh
this folder. `probe.py`, `probe44.py` and `detect2.py` are **discovery** steps — only re-run those
when an employer changes career platforms and an endpoint starts returning nothing.

Set `PULL` at the top of `scrape.py`, `round2.py` and `build2.py` to the current date before a
fresh run — the 72-hour window is computed against it.

### Gotchas worth knowing

- Phenom's filter parameter is **`keywords=`** (plural). `keyword=` singular is silently ignored
  and returns unfiltered results; `sortBy=most_recent` returns HTTP 422.
- Workday's `postedOn` is a coarse label; the precise date lives on the job detail record, which is
  what `enrich.py` fetches.
- The Oracle Cloud `siteNumber` parameter is not validated — any `CX_n` returns the same result set.

### Known limitation in this environment

The workbook's summary cells and `Days Old` column are live formulas written with `openpyxl`,
which does not compute cached values. They evaluate on first open in Excel, Google Sheets or
Numbers. LibreOffice recalculation could not be run in the sandbox that generated this file — its
Calc filter library (`libscfiltlo.so`) is absent, so it cannot open spreadsheets at all. The
formulas were instead verified directly: XML well-formedness, correct ranges, Excel-2007-safe
functions only, and all 45 `Days Old` values cross-checked against source posting dates.
