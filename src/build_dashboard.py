"""Build dashboard.html from aviation.db.

Reads every figure straight out of the database, assembles one JSON payload and
drops it into src/dashboard_template.html. The output is a single file with no
external requests, so it works offline by double click and on GitHub Pages.

    python src/build_dashboard.py
"""
import json
import re
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "aviation.db"
TEMPLATE = Path(__file__).resolve().parent / "dashboard_template.html"
OUT = ROOT / "dashboard.html"

MAIN = ["Dublin", "Cork", "Shannon", "Knock", "Kerry", "Donegal"]
MARKET_FILTER = """
      a.is_total = 1
  AND f.direction = 'All directions'
  AND f.flight_type = 'All flights'
"""


def rows(con, sql, args=()):
    cur = con.execute(sql, args)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


# ---------------------------------------------------------------- panels

def annual(con):
    """Total passengers per year, 2005 to 2025, plus the per airport split."""
    total = rows(con, """
        SELECT f.year, SUM(f.passengers) AS passengers
          FROM fact_airport_year f
          JOIN dim_airport a USING (airport_id)
         WHERE a.is_total = 0
         GROUP BY f.year
         ORDER BY f.year
    """)
    per = rows(con, """
        SELECT f.year, a.name, f.passengers
          FROM fact_airport_year f
          JOIN dim_airport a USING (airport_id)
         WHERE a.is_total = 0 AND a.name IN ('Dublin','Cork','Shannon','Knock','Kerry','Donegal')
         ORDER BY f.year
    """)
    split = {}
    for r in per:
        split.setdefault(r["name"], {})[r["year"]] = r["passengers"]
    return total, split


def monthly(con):
    """Monthly passengers, 2019-01 to 2026-06, all airports and the five reported."""
    out = {}
    for r in rows(con, """
        SELECT f.month_start, a.name, f.passengers
          FROM fact_airport_month f
          JOIN dim_airport a USING (airport_id)
         ORDER BY f.month_start
    """):
        key = "All" if r["name"] == "All main airports" else r["name"]
        out.setdefault(key, {})[r["month_start"][:7]] = r["passengers"]
    months = sorted(out["All"])
    series = {k: [v.get(m) for m in months] for k, v in out.items()}
    return months, series


def markets(con):
    """Country level passengers, 2025 against 2022, ranked with a cumulative share."""
    data = rows(con, f"""
        SELECT m.name,
               MAX(CASE WHEN f.year = 2025 THEN f.passengers_thousand END) AS p25,
               MAX(CASE WHEN f.year = 2022 THEN f.passengers_thousand END) AS p22
          FROM fact_market_year f
          JOIN dim_airport a USING (airport_id)
          JOIN dim_market  m USING (market_id)
         WHERE {MARKET_FILTER} AND m.kind IN ('country','domestic')
         GROUP BY m.name
        HAVING p25 IS NOT NULL AND p25 > 0
         ORDER BY p25 DESC
    """)
    for d in data:
        # CSO footnote markers, e.g. "United Kingdom (1)"
        d["name"] = re.sub(r"\s*\(\d+\)$", "", d["name"]).replace("(domestic)", "domestic")
    total = sum(d["p25"] for d in data)
    cum = 0.0
    for d in data:
        cum += d["p25"]
        d["share"] = round(d["p25"] / total * 100, 2)
        d["cum"] = round(cum / total * 100, 2)
        d["growth"] = round((d["p25"] / d["p22"] - 1) * 100, 1) if d["p22"] else None
        d["p25"] = round(d["p25"], 1)
        d["p22"] = round(d["p22"], 1) if d["p22"] else None
    return data, round(total, 1)


def operations(con):
    """Passengers, freight and flights per year, and the passengers per flight ratio."""
    data = rows(con, f"""
        SELECT f.year,
               SUM(f.passengers_thousand)      AS pax,
               SUM(f.freight_tonnes_thousand)  AS freight,
               SUM(f.flights_thousand)         AS flights
          FROM fact_market_year f
          JOIN dim_airport a USING (airport_id)
          JOIN dim_market  m USING (market_id)
         WHERE {MARKET_FILTER} AND m.kind = 'total'
         GROUP BY f.year
         ORDER BY f.year
    """)
    for d in data:
        d["ppf"] = round(d["pax"] / d["flights"], 1)
        for k in ("pax", "freight", "flights"):
            d[k] = round(d[k], 1)
    return data


def closed_markets(con):
    """Markets that carried passengers early in the series and none in 2024 or 2025.

    The threshold keeps out the charter noise: a market has to have moved at least
    5,000 passengers in 2020 or 2021 to count as having been a market at all.
    """
    data = rows(con, f"""
        SELECT m.name,
               MAX(CASE WHEN f.year IN (2020,2021) THEN f.passengers_thousand END) AS early,
               MAX(CASE WHEN f.year IN (2024,2025) THEN f.passengers_thousand END) AS late
          FROM fact_market_year f
          JOIN dim_airport a USING (airport_id)
          JOIN dim_market  m USING (market_id)
         WHERE {MARKET_FILTER} AND m.kind = 'country'
         GROUP BY m.name
        HAVING early >= 5 AND late = 0
         ORDER BY early DESC
    """)
    return [re.sub(r"\s*\(\d+\)$", "", d["name"]) for d in data]


def build(con):
    years, split = annual(con)
    months, mseries = monthly(con)
    mkts, mkt_total = markets(con)
    ops = operations(con)

    by_year = {r["year"]: r["passengers"] for r in years}
    peak_pre = max((y for y in by_year if y <= 2008), key=lambda y: by_year[y])
    regained = min((y for y in by_year if y > peak_pre and by_year[y] > by_year[peak_pre]),
                   default=None)
    trough = min((y for y in by_year if 2008 < y < 2015), key=lambda y: by_year[y])

    all_m = mseries["All"]
    floor_i = min(range(len(all_m)), key=lambda i: all_m[i])
    peak_i = max(range(len(all_m)), key=lambda i: all_m[i])

    h1_26 = sum(v for m, v in zip(months, all_m) if m.startswith("2026") and m[5:7] <= "06")
    h1_25 = sum(v for m, v in zip(months, all_m) if m.startswith("2025") and m[5:7] <= "06")

    airports = []
    for name in MAIN:
        s = split[name]
        airports.append({
            "name": name,
            "series": [s.get(y) for y in sorted(s)],
            "y2019": s[2019],
            "y2025": s[2025],
            "delta": round((s[2025] / s[2019] - 1) * 100, 1),
        })
    airports.sort(key=lambda a: -a["y2025"])

    top10 = mkts[9]["cum"]
    both = [m for m in mkts if m["p22"]]
    grew = [m for m in both if m["growth"] > 0]
    gone = closed_markets(con)
    movers = [m for m in both if m["p25"] > 200 and m["p22"] > 200]
    movers.sort(key=lambda m: -m["growth"])

    return {
        "built": date.today().isoformat(),
        "annualYears": [r["year"] for r in years],
        "annual": [r["passengers"] for r in years],
        "months": months,
        "monthly": mseries,
        "airports": airports,
        "markets": mkts,
        "marketTotal": mkt_total,
        "ops": ops,
        "facts": {
            "y2025": by_year[2025],
            "y2019": by_year[2019],
            "vs2019": round((by_year[2025] / by_year[2019] - 1) * 100, 1),
            "peakPreYear": peak_pre,
            "peakPre": by_year[peak_pre],
            "vsPeakPre": round((by_year[2025] / by_year[peak_pre] - 1) * 100, 1),
            "troughYear": trough,
            "troughDrop": round((by_year[trough] / by_year[peak_pre] - 1) * 100, 1),
            "regainedYear": regained,
            "regainedAfter": regained - peak_pre,
            "covidDrop": round((by_year[2020] / by_year[2019] - 1) * 100, 1),
            "floorMonth": months[floor_i],
            "floorValue": all_m[floor_i],
            "floorDrop": round((all_m[floor_i] / all_m[floor_i - 12] - 1) * 100, 1),
            "mar2020": round(
                all_m[months.index("2020-03")] / all_m[months.index("2019-03")] * 100, 1),
            "peakMonth": months[peak_i],
            "peakValue": all_m[peak_i],
            "h1Growth": round((h1_26 / h1_25 - 1) * 100, 1),
            "lastMonth": months[-1],
            "ppfFirst": ops[0]["ppf"],
            "ppfLast": ops[-1]["ppf"],
            "ppfGain": round((ops[-1]["ppf"] / ops[0]["ppf"] - 1) * 100, 1),
            "freightGain": round((ops[-1]["freight"] / ops[0]["freight"] - 1) * 100, 1),
            "topMarket": mkts[0]["name"],
            "topShare": mkts[0]["share"],
            "top10": top10,
            "countries": len(mkts),
            "bothYears": len(both),
            "grewCount": len(grew),
            "gone": gone,
            "moverFloor": 200,
            "fastest": movers[0]["name"],
            "fastestGrowth": movers[0]["growth"],
            "slowest": movers[-1]["name"],
            "slowestGrowth": movers[-1]["growth"],
        },
    }


def main():
    con = sqlite3.connect(DB)
    data = build(con)
    con.close()
    html = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    if "__DATA__" not in html:
        raise SystemExit("template is missing the __DATA__ placeholder")
    OUT.write_text(html.replace("__DATA__", payload), encoding="utf-8")
    print(f"dashboard.html written, {OUT.stat().st_size / 1024:.0f} KB")
    for k, v in data["facts"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
