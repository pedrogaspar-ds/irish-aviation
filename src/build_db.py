"""Load the raw CSO JSON-stat files into a clean SQLite star schema."""
import itertools
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "aviation.db"

SCHEMA = """
CREATE TABLE dim_airport (
    airport_id INTEGER PRIMARY KEY,
    icao       TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    is_total   INTEGER NOT NULL DEFAULT 0   -- 1 for the 'All main airports' row
);
CREATE TABLE dim_market (
    market_id INTEGER PRIMARY KEY,
    code      TEXT NOT NULL UNIQUE,
    name      TEXT NOT NULL,
    kind      TEXT NOT NULL CHECK (kind IN
              ('total','domestic','country','uk_nation','group'))
);
CREATE TABLE fact_airport_year (
    year       INTEGER NOT NULL,
    airport_id INTEGER NOT NULL REFERENCES dim_airport(airport_id),
    passengers INTEGER NOT NULL,
    PRIMARY KEY (year, airport_id)
);
CREATE TABLE fact_airport_month (
    month_start TEXT    NOT NULL,            -- ISO date, first day of month
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    airport_id  INTEGER NOT NULL REFERENCES dim_airport(airport_id),
    passengers  INTEGER NOT NULL,
    PRIMARY KEY (month_start, airport_id)
);
CREATE TABLE fact_market_year (
    year        INTEGER NOT NULL,
    airport_id  INTEGER NOT NULL REFERENCES dim_airport(airport_id),
    market_id   INTEGER NOT NULL REFERENCES dim_market(market_id),
    direction   TEXT NOT NULL CHECK (direction IN ('All directions','Arrival','Departure')),
    flight_type TEXT NOT NULL CHECK (flight_type IN ('All flights','Scheduled','Unscheduled')),
    passengers_thousand REAL,
    freight_tonnes_thousand REAL,
    flights_thousand REAL,
    PRIMARY KEY (year, airport_id, market_id, direction, flight_type)
);
CREATE INDEX ix_market_year ON fact_market_year(market_id, year);
"""

UK_NATIONS = {"GB-ENG", "GB-NIR", "GB-SCT", "GB-WLS"}
GROUPS = {"EU27XIE", "GB99", "OTHEUR3", "EUR48", "AM1", "ZZAZR1", "ZZAA8",
          "ZZAA06", "ZZABH", "ZZAB04", "ZZAD01"}


def decode(path):
    """Return (dim_ids, {dim: [(code, label)]}, iterator of (coords, value))."""
    d = json.loads(path.read_text())
    ids = d["id"]
    cats = {}
    for k in ids:
        c = d["dimension"][k]["category"]
        idx = c["index"]
        codes = idx if isinstance(idx, list) else sorted(idx, key=idx.get)
        cats[k] = [(code, c["label"][code]) for code in codes]
    combos = itertools.product(*[range(len(cats[k])) for k in ids])
    return ids, cats, zip(combos, d["value"])


def market_kind(code):
    if code == "-":
        return "total"
    if code == "IE07":
        return "domestic"
    if code in UK_NATIONS:
        return "uk_nation"
    if code in GROUPS:
        return "group"
    return "country"


def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    airports = {}  # icao -> id

    def airport_id(icao, name):
        if icao not in airports:
            airports[icao] = len(airports) + 1
            con.execute("INSERT INTO dim_airport VALUES (?,?,?,?)",
                        (airports[icao], icao, name, int(icao == "EI0M")))
        return airports[icao]

    # Annual passengers by airport (TAA05)
    ids, cats, rows = decode(RAW / "TAA05.json")
    ti, ai = ids.index("TLIST(A1)"), ids.index("C02935V03550")
    for coords, v in rows:
        if v is None:
            continue
        year = int(cats["TLIST(A1)"][coords[ti]][0])
        icao, name = cats["C02935V03550"][coords[ai]]
        con.execute("INSERT INTO fact_airport_year VALUES (?,?,?)",
                    (year, airport_id(icao, name), int(v)))

    # Monthly passengers by airport (TAM08)
    ids, cats, rows = decode(RAW / "TAM08.json")
    ti, ai = ids.index("TLIST(M1)"), ids.index("C02935V03550")
    for coords, v in rows:
        if v is None:
            continue
        code = cats["TLIST(M1)"][coords[ti]][0]  # e.g. 201901
        y, m = int(code[:4]), int(code[4:])
        icao, name = cats["C02935V03550"][coords[ai]]
        con.execute("INSERT INTO fact_airport_month VALUES (?,?,?,?,?)",
                    (f"{y:04d}-{m:02d}-01", y, m, airport_id(icao, name), int(v)))

    # Annual passengers, freight, flights by airport and country (TAA06)
    ids, cats, rows = decode(RAW / "TAA06.json")
    pos = {k: ids.index(k) for k in ids}
    market_ids = {}
    for code, label in cats["C02191V04000"]:
        market_ids[code] = len(market_ids) + 1
        con.execute("INSERT INTO dim_market VALUES (?,?,?,?)",
                    (market_ids[code], code, label.replace("Eygpt", "Egypt"),
                     market_kind(code)))
    stat_names = [lab for _, lab in cats["STATISTIC"]]
    acc = {}
    for coords, v in rows:
        if v is None:
            continue
        year = int(cats["TLIST(A1)"][coords[pos["TLIST(A1)"]]][0])
        icao, aname = cats["C02935V03550"][coords[pos["C02935V03550"]]]
        mcode = cats["C02191V04000"][coords[pos["C02191V04000"]]][0]
        direction = cats["C02354V02832"][coords[pos["C02354V02832"]]][1]
        ftype = cats["C02936V03551"][coords[pos["C02936V03551"]]][1]
        stat = stat_names[coords[pos["STATISTIC"]]]
        key = (year, airport_id(icao, aname), market_ids[mcode], direction, ftype)
        acc.setdefault(key, {})[stat] = v
    for key, s in acc.items():
        con.execute("INSERT INTO fact_market_year VALUES (?,?,?,?,?,?,?,?)",
                    key + (s.get("Passengers"), s.get("Freight"),
                           s.get("Commercial Flights")))
    con.commit()
    for t in ("dim_airport", "dim_market", "fact_airport_year",
              "fact_airport_month", "fact_market_year"):
        print(t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    con.close()


if __name__ == "__main__":
    main()
