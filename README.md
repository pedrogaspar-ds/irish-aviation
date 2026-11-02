# Irish Aviation: Dublin Airport in Numbers

A small analyst project on real public data. It asks five business questions about
Dublin Airport and answers each with a SQL query, a chart and a plain conclusion.

![Dashboard](docs/dashboard.png)

Live: [pedrogaspar-ds.github.io/irish-aviation](https://pedrogaspar-ds.github.io/irish-aviation/)

Or open `dashboard.html` in any browser (double click, no internet needed).

## The question

Is Dublin Airport growing past its pre-pandemic level, how seasonal is it, which
markets drive the growth, and how much risk sits in one hub and a few markets?
These are the questions a capacity planning or commercial data team asks.

## Data

Central Statistics Office (CSO) Ireland, Aviation Statistics, through the public
PxStat API: tables TAA05 (annual passengers by airport), TAM08 (monthly passengers by
airport, to June 2026) and TAA06 (annual passengers by destination country, 2020 to 2025).
Exact URLs, download date and licence notes are in [data/SOURCES.md](data/SOURCES.md).
Source site: https://data.cso.ie

## How it is built

```
src/fetch.py      download raw JSON-stat from the CSO API into data/raw/
src/build_db.py   load into SQLite (data/aviation.db): 2 dimension tables, 3 fact tables
sql/              one SQL file per business question (q1 to q5)
src/analyse.py    run the queries, write figs/*.png and build dashboard.html
```

Schema: `dim_airport`, `dim_market`, `fact_airport_year`, `fact_airport_month`,
`fact_market_year`, with primary keys, foreign keys and check constraints.

## Findings

1. **Recovery.** Dublin handled 36.4 million passengers in 2025, 11.4% above 2019
   (32.7 million). It passed 2019 in 2023 (+1.8%). January to June 2026 was 17.9 million,
   16.2% above the same months of 2019 and 5.8% above 2025.
2. **Seasonality.** In 2025 August (3.78 million) had 1.77 times the traffic of February
   (2.14 million). In 2019 the gap was 1.72 times (July vs February). The winter dip is
   not closing.
3. **Markets.** Between 2022 and 2025, 26 of 28 country markets grew. Turkiye grew fastest
   (+69.8%). The UK added the most passengers (+2.35 million) and the US added 1.06 million.
   Only Lithuania (-8.9%) and Bulgaria (-7.0%) shrank.
4. **Dublin's weight.** Dublin had 83.7% of passengers at the five main Irish airports in
   2025, down from 85.9% in 2019 but up from 72.8% in 2005. Cork rose from 6.8% to 8.0% and
   Shannon from 4.2% to 5.2% since 2019.
5. **Concentration.** The top 10 country markets carried 79.0% of Dublin passengers in 2025
   (80.9% in 2022). The UK alone is 27.8%, so one market is more than a quarter of traffic.

All numbers come from the queries in `sql/` and are printed by `src/analyse.py`
(also saved in `data/results.json`).

## Limitations

- The public tables give passengers by destination **country**, not by route or airline,
  so the question about route concentration is answered at country level.
- 2022 is still a recovery year, so growth since 2022 partly reflects recovery. The
  2025 vs 2024 column in the Q3 output shows current momentum instead.
- Transit passengers are counted twice in the country table. The Canary Islands are a
  separate market from Spain in the CSO data. Figures are subject to revision.
- Cork was closed in October 2021, which explains its dip in the 2021 share.
- This is descriptive analysis. It does not forecast, and it has no airline or capacity
  (seats, runway) data.

## How to run

```
pip install -r requirements.txt
python3 src/fetch.py       # optional, raw data is already in the repo
python3 src/build_db.py
python3 src/analyse.py
```

Python 3.10 or newer. SQLite is part of the standard library. To run a single query:
`sqlite3 -header -column data/aviation.db < sql/q1_recovery_vs_2019.sql`

## Licence

Code: MIT. Data: CSO Ireland, see `data/SOURCES.md`.
