"""Download the CSO Ireland aviation tables as raw JSON-stat and log them."""
import json
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
URL = ("https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API."
       "ReadDataset/{code}/JSON-stat/2.0/en")

TABLES = {
    "TAA05": "Passengers by airport, annual, 2005 to 2025",
    "TAM08": "Passengers handled by main airports, monthly, 2019 to 2026",
    "TAA06": "Passengers, freight and flights by airport and country, annual, 2020 to 2025",
}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    log = []
    for code, desc in TABLES.items():
        url = URL.format(code=code)
        with urllib.request.urlopen(url, timeout=120) as r:
            body = r.read()
        data = json.loads(body)  # fail loudly if the response is not JSON
        if "value" not in data or not data["value"]:
            raise SystemExit(f"{code}: no values returned, stopping")
        (RAW / f"{code}.json").write_bytes(body)
        log.append((code, desc, url, data.get("updated", ""), len(body)))
        print(f"{code}: {len(body):,} bytes, updated {data.get('updated')}")
    (RAW / "download_log.json").write_text(json.dumps(
        {"downloaded": today,
         "tables": [dict(code=c, description=d, url=u, cso_updated=up, bytes=n)
                    for c, d, u, up, n in log]}, indent=2))


if __name__ == "__main__":
    main()
