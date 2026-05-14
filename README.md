[README.md](https://github.com/user-attachments/files/27745052/README.md)
# NJ Pharma Supply Chain ESG — Risk & Opportunity Analytics

> A data-driven scoring platform for the supply-chain ESG performance of six New Jersey-headquartered pharmaceutical manufacturers — covering Scope 1–3 emissions, supplier governance, and TCFD-aligned risk classification.

**Live dashboard:** [lunariduo.com/nj_pharma_supply_chain_esg.html](https://lunariduo.com/nj_pharma_supply_chain_esg.html)
**Author:** Yiduo Xiao · Lunarix Technologies LLC · [yijimu@lunariduo.com](mailto:yijimu@lunariduo.com)
**Frameworks:** TCFD · SASB Pharmaceutical Standard · PSCI · SBTi · MSCI ESG

---

## Problem

The New Jersey pharma cluster (J&J, Merck, BMS, Bayer, Sanofi, Becton Dickinson) outperforms global pharma and S&P 500 averages on ESG — but **82% of its carbon footprint sits with upstream suppliers**. Most strategy conversation centers on Scope 1 and 2; the leverage is in Scope 3. Sustainability leads and supply-chain analysts need:

1. A unified view of where supply-chain ESG risk concentrates.
2. Quantified opportunities — not just risks — for board-level conversation.
3. A defensible methodology with traceable sources.

## Approach

End-to-end analytics pipeline:

1. **Ingestion** — Python ETL pulls 5-year ESG disclosures from SEC EDGAR, CDP, MSCI ESG (public tier), EPA GHGRP, and PSCI supplier-membership data.
2. **Schema** — PostgreSQL star schema: `company` (dim) · `year` (dim) · `pillar_score` (fact) · `scope_emissions` (fact) · `supplier_audit` (fact). Data contracts enforce unit normalization (MT CO₂e), assurance-level tagging, and PSCI risk-category taxonomy.
3. **Risk scoring** — TCFD-aligned 5×5 likelihood × impact matrix applied across 6 supply-chain stages × 5 risk types. Composite ESG score weighted per SASB pharma materiality: `0.40·E + 0.35·S + 0.25·G`.
4. **Visualization** — Chart.js interactive dashboard with company / risk-level filters. Tableau-ready master CSV for drill-down.

## Findings & Outcome

- **Three hotspots account for ~half the cluster's residual supply-chain risk** — all in API sourcing / API manufacturing.
- **API sourcing from Asia compounds three risks** into a single touchpoint: environmental compliance, geopolitical exposure, and Scope 3 emissions.
- Three quantified opportunities:
  - SBTi-aligned supplier engagement: projected **−14% Scope 3** by 2030.
  - IoT cold-chain telemetry: **−22% spoilage** (J&J pilot data).
  - Nearshoring with IRA Section 60101 credits: **$40–60M working-capital release**.
- Five of six companies have SBTi-validated 1.5°C targets; only Bayer is pending.

---

## Tech stack

| Layer | Tool |
|---|---|
| Database | PostgreSQL / SQLite |
| ETL | Python 3.10+ (`pandas`, `sqlalchemy`, `requests`) |
| Visualization | Chart.js 4.4 (embedded HTML) |
| Notebooks | Jupyter (analysis + methodology) |
| Reporting | Tableau-ready CSV export |

## Project structure

```
project_02_nj_pharma_supply_chain_esg/
├── README.md                     # this file
├── LICENSE                       # MIT
├── .gitignore
├── requirements.txt
├── index.html                    # live Chart.js dashboard
├── schema.sql                    # PostgreSQL DDL + materiality weights
├── extract_pharma_esg.py         # ETL pipeline
├── notebooks/
│   └── risk_scoring.ipynb        # 5×5 risk matrix methodology
└── data/
    ├── companies.csv             # 6 NJ pharma master
    ├── emissions_5yr.csv         # Scope 1-3 5-year trajectory
    ├── pillar_scores.csv         # E/S/G composite scoring
    └── supplier_audit.csv        # PSCI compliance trend
```

## Quick start

```bash
# 1. Clone
git clone https://github.com/yiduo194/project_02_nj_pharma_supply_chain_esg.git
cd project_02_nj_pharma_supply_chain_esg

# 2. Install deps
pip install -r requirements.txt

# 3. Set up DB
sqlite3 nj_pharma.db < schema.sql

# 4. Run the ETL pipeline
python extract_pharma_esg.py
# → populates DB and writes data/*.csv exports

# 5. Open the dashboard
open index.html
```

## Data sources (all public)

- [SEC EDGAR](https://www.sec.gov/edgar) — annual 10-K / proxy statements
- [CDP Climate Change](https://www.cdp.net) — voluntary corporate climate disclosure
- [MSCI ESG](https://www.msci.com/our-solutions/esg-investing) — public-tier signals
- [EPA GHG Reporting Tool](https://www.epa.gov/ghgreporting) — facility-level NAICS 3254
- [PSCI](https://pscinitiative.org) — Pharmaceutical Supply Chain Initiative
- [SBTi](https://sciencebasedtargets.org) — Science Based Targets initiative

## Limitations

- ESG composite scores are **my synthesis** of public signals — they will not match any single rating provider exactly.
- True supplier-by-supplier granularity is not publicly disclosed; data is reported in cluster aggregate.
- Cost estimates ($80–140M carbon exposure, $40–60M working-capital release) are scenario projections built on published industry benchmarks — treat as order-of-magnitude.

## License

MIT — see [LICENSE](LICENSE).
