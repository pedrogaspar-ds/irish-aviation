# Data sources

All data comes from the Central Statistics Office (CSO) Ireland, Aviation Statistics,
through the public PxStat API (JSON-stat 2.0). Raw files are in `data/raw/`.
Downloaded on 2026-11-02 by `src/fetch.py`.

| Table | Content | Exact URL | CSO last update |
|-------|---------|-----------|-----------------|
| TAA05 | Passengers by airport, annual, 2005 to 2025 | https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/TAA05/JSON-stat/2.0/en | 2026-08-05 |
| TAM08 | Passengers handled by main airports, monthly, Jan 2019 to Jun 2026 | https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/TAM08/JSON-stat/2.0/en | 2026-08-19 |
| TAA06 | Passengers, freight and commercial flights by airport, country, direction and flight type, annual, 2020 to 2025 | https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/TAA06/JSON-stat/2.0/en | 2026-04-16 |

Catalogue and landing page: https://data.cso.ie and
https://www.cso.ie/en/statistics/transport/aviationstatistics/

Licence: CSO open data. The CSO publishes its statistics for free reuse with
attribution (Creative Commons Attribution 4.0 is the licence named in the CSO open
data policy). The JSON files themselves only carry the line "Central Statistics Office,
Ireland" as copyright holder, and I could not re-confirm the licence text by script on
the download date, so check https://www.cso.ie/en/aboutus/lgdp/csodatapolicy/ before
reusing the data commercially. Attribution: "Source: CSO Ireland, Aviation Statistics."

Notes from CSO (in the raw files):
- TAM08: commercial passengers only; data subject to revision.
- TAA06: transit passengers are counted twice (arriving and departing); the country
  table is by destination or origin country, not by route.
- TAA05 and TAM08 agree: Dublin 2019 is 32,676,251 passengers in both.
