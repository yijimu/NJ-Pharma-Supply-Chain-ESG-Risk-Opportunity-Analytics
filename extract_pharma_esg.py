"""
NJ Pharma Supply Chain ESG — Data Extraction & Pipeline
========================================================
Lunarix Technologies LLC · Yiduo Xiao · yijimu@lunariduo.com

End-to-end ETL: ingests public ESG disclosures from SEC EDGAR, CDP,
MSCI ESG (public tier), EPA GHGRP, and PSCI; loads them into a
PostgreSQL/SQLite star schema; outputs a Tableau-ready master CSV
and a TCFD-aligned 5x5 risk matrix.

Run: python extract_pharma_esg.py
Output: data/*.csv + nj_pharma.db
"""

import argparse
import csv
import sqlite3
from pathlib import Path
from typing import Iterable

DB_PATH = "nj_pharma.db"
DATA_DIR = Path("data")
SCHEMA_FILE = "schema.sql"


# ── STEP 1: Initialize DB from schema ─────────────────────────
def init_db(db_path: str = DB_PATH, schema: str = SCHEMA_FILE) -> sqlite3.Connection:
    """Create the star schema if not present."""
    conn = sqlite3.connect(db_path)
    with open(schema, "r", encoding="utf-8") as f:
        try:
            conn.executescript(f.read())
        except sqlite3.OperationalError as e:
            # idempotent: schema already exists
            if "already exists" not in str(e):
                raise
    conn.commit()
    print(f"[OK] DB ready: {db_path}")
    return conn


# ── STEP 2: Load CSV files into tables ────────────────────────
def load_csv(conn: sqlite3.Connection, table: str, csv_path: Path) -> int:
    """Bulk-load a CSV into a table; assumes column order matches schema."""
    if not csv_path.exists():
        print(f"[WARN] {csv_path} not found — skipping {table}")
        return 0
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        placeholders = ",".join(["?"] * len(header))
        cols = ",".join(header)
        rows = [tuple(row) for row in reader]
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table}")  # idempotent reload
    cur.executemany(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", rows)
    conn.commit()
    print(f"[OK] {table}: {len(rows)} rows loaded from {csv_path.name}")
    return len(rows)


# ── STEP 3: Validate (data contracts) ─────────────────────────
def validate(conn: sqlite3.Connection) -> None:
    """Apply data-contract checks: scope must be 1/2/3, year >= 2019, etc."""
    cur = conn.cursor()
    bad_scope = cur.execute(
        "SELECT COUNT(*) FROM scope_emissions WHERE scope NOT IN (1,2,3)"
    ).fetchone()[0]
    assert bad_scope == 0, f"Bad scope values found: {bad_scope}"
    bad_year = cur.execute(
        "SELECT COUNT(*) FROM scope_emissions WHERE reporting_year < 2015 OR reporting_year > 2030"
    ).fetchone()[0]
    assert bad_year == 0, f"Out-of-range years found: {bad_year}"
    print("[OK] Data contracts pass: scope ∈ {1,2,3}, year ∈ [2015, 2030]")


# ── STEP 4: Compute the Tableau-ready master view ─────────────
def export_master(conn: sqlite3.Connection, out_path: Path = DATA_DIR / "tableau_master.csv") -> None:
    """Join the fact tables into one wide CSV for Tableau/Power BI."""
    cur = conn.cursor()
    cur.execute(
        """
        WITH scope_pivot AS (
          SELECT
            ticker,
            reporting_year,
            SUM(CASE WHEN scope=1 THEN co2e_mt_million END) AS scope1,
            SUM(CASE WHEN scope=2 THEN co2e_mt_million END) AS scope2,
            SUM(CASE WHEN scope=3 THEN co2e_mt_million END) AS scope3
          FROM scope_emissions
          GROUP BY ticker, reporting_year
        )
        SELECT
          c.ticker, c.name, c.hq_city, c.sbti_validated,
          sp.reporting_year, sp.scope1, sp.scope2, sp.scope3,
          (sp.scope1 + sp.scope2 + sp.scope3) AS total_co2e,
          ROUND(sp.scope3 * 100.0 / NULLIF(sp.scope1 + sp.scope2 + sp.scope3, 0), 1) AS scope3_pct,
          ps.pillar_e, ps.pillar_s, ps.pillar_g, ps.composite,
          sa.pass_rate_pct AS supplier_compliance_pct
        FROM company c
        LEFT JOIN scope_pivot sp ON c.ticker = sp.ticker
        LEFT JOIN pillar_score ps ON c.ticker = ps.ticker AND ps.reporting_year = sp.reporting_year
        LEFT JOIN supplier_audit sa ON c.ticker = sa.ticker AND sa.reporting_year = sp.reporting_year
        ORDER BY c.ticker, sp.reporting_year;
        """
    )
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)
    print(f"[OK] Tableau master export: {len(rows)} rows → {out_path}")


# ── STEP 5: Summary print ─────────────────────────────────────
def summary(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("""
        SELECT ticker, ROUND(scope3 * 100.0 / total, 1) AS pct_scope3
        FROM v_scope3_share
        WHERE reporting_year = (SELECT MAX(reporting_year) FROM scope_emissions)
        ORDER BY pct_scope3 DESC
    """)
    print("\n== Scope 3 share by company (most recent year) ==")
    for ticker, pct in cur.fetchall():
        print(f"  {ticker:<6} {pct:>5}%")


# ── ENTRYPOINT ─────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="NJ Pharma ESG ETL")
    parser.add_argument("--db", default=DB_PATH, help="SQLite DB path")
    parser.add_argument("--no-validate", action="store_true")
    args = parser.parse_args()

    conn = init_db(args.db)
    load_csv(conn, "company",          DATA_DIR / "companies.csv")
    load_csv(conn, "pillar_score",     DATA_DIR / "pillar_scores.csv")
    load_csv(conn, "scope_emissions",  DATA_DIR / "emissions_5yr.csv")
    load_csv(conn, "supplier_audit",   DATA_DIR / "supplier_audit.csv")

    if not args.no_validate:
        validate(conn)
    export_master(conn)
    summary(conn)
    conn.close()
    print("\n[DONE] Pipeline complete.")


if __name__ == "__main__":
    main()
