"""Run the five SQL questions, draw the PNG charts and write data/results.json."""
import json
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "aviation.db"
SQL = ROOT / "sql"
FIGS = ROOT / "figs"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
BLUE, ORANGE, GREY, RED = "#1f5fa8", "#d9822b", "#8a8f98", "#b23b3b"

plt.rcParams.update({"axes.unicode_minus": False, "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25})


def run(con, name):
    cur = con.execute((SQL / name).read_text())
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIGS / name, dpi=130)
    plt.close(fig)


def main():
    FIGS.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    q1 = run(con, "q1_recovery_vs_2019.sql")
    q2 = run(con, "q2_seasonality.sql")
    q3 = run(con, "q3_market_growth.sql")
    q4 = run(con, "q4_dublin_share.sql")
    q5 = run(con, "q5_concentration.sql")
    for name, rows in zip("q1 q2 q3 q4 q5".split(), (q1, q2, q3, q4, q5)):
        print(f"{name}: {len(rows)} rows")

    # ---- Q1 recovery
    a = [r for r in q1 if r["part"] == "A_full_year"]
    b = {r["period"]: r for r in q1 if r["part"] == "B_jan_jun"}
    fig, ax = plt.subplots(figsize=(8, 4.2))
    cols = [GREY if r["period"] == "2019" else BLUE for r in a]
    ax.bar([r["period"] for r in a], [r["passengers"] / 1e6 for r in a], color=cols)
    for r in a:
        lab = f'{r["pct_vs_2019"]:+.1f}%' if r["period"] != "2019" else "base"
        ax.text(r["period"], r["passengers"] / 1e6 + 0.5, lab, ha="center", fontsize=9)
    ax.set_title("Dublin Airport passengers per year, with change vs 2019")
    ax.set_xlabel("Year")
    ax.set_ylabel("Passengers (millions)")
    ax.set_ylim(0, 42)
    save(fig, "fig1_recovery_vs_2019.png")

    # ---- Q2 seasonality
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for year, colr in ((2019, GREY), (2025, BLUE)):
        rows = [r for r in q2 if r["year"] == year]
        ax.plot(MONTHS, [r["seasonal_index"] for r in rows], marker="o",
                color=colr, label=str(year))
    ax.axhline(100, color="black", lw=0.8, ls=":")
    ax.set_title("Dublin monthly seasonality (100 = average month of the year)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Seasonal index")
    ax.legend(title="Year")
    save(fig, "fig2_seasonality.png")

    # ---- Q3 market growth
    rows = sorted(q3, key=lambda r: r["pct_since_2022"])
    fig, ax = plt.subplots(figsize=(8, 7.5))
    ax.barh([r["market"].replace(" (1)", "") for r in rows],
            [r["pct_since_2022"] for r in rows],
            color=[RED if r["pct_since_2022"] < 0 else BLUE for r in rows])
    ax.set_title("Dublin passenger growth by country market, 2022 to 2025")
    ax.set_xlabel("Change in passengers, 2025 vs 2022 (%)")
    ax.set_ylabel("Destination country")
    ax.tick_params(axis="y", labelsize=8)
    save(fig, "fig3_market_growth.png")

    # ---- Q4 airport share
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot([r["year"] for r in q4], [r["dublin_pct"] for r in q4],
            color=BLUE, marker="o", ms=3, label="Dublin")
    ax.set_ylabel("Dublin share of five main airports (%)")
    ax.set_xlabel("Year")
    ax.set_ylim(70, 92)
    ax2 = ax.twinx()
    ax2.spines["right"].set_visible(True)
    ax2.grid(False)
    ax2.plot([r["year"] for r in q4], [r["cork_pct"] for r in q4],
             color=ORANGE, label="Cork (right axis)")
    ax2.plot([r["year"] for r in q4], [r["shannon_pct"] for r in q4],
             color=GREY, label="Shannon (right axis)")
    ax2.set_ylabel("Cork and Shannon share (%)")
    ax2.set_ylim(0, 14)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3, fontsize=8, frameon=False)
    ax.set_xticks(range(2005, 2026, 4))
    ax.set_title("Share of Irish main airport passengers, 2005 to 2025")
    save(fig, "fig4_airport_share.png")

    # ---- Q5 concentration
    r25 = [r for r in q5 if r["year"] == 2025]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    names = [r["market"].replace(" (1)", "") for r in r25][::-1]
    ax.barh(names, [r["share_pct"] for r in r25][::-1], color=BLUE)
    for i, r in enumerate(r25[::-1]):
        ax.text(r["share_pct"] + 0.3, i, f'{r["share_pct"]:.1f}%  (cum. {r["cumulative_share_pct"]:.1f}%)',
                va="center", fontsize=8)
    ax.set_xlim(0, 40)
    ax.set_title("Top 10 country markets, share of Dublin passengers, 2025")
    ax.set_xlabel("Share of all Dublin passengers (%)")
    ax.set_ylabel("Destination country")
    save(fig, "fig5_market_concentration.png")

    # ---- numbers used in text and dashboard
    a25 = next(r for r in a if r["period"] == "2025")
    a23 = next(r for r in a if r["period"] == "2023")
    s25 = [r for r in q2 if r["year"] == 2025]
    s19 = [r for r in q2 if r["year"] == 2019]
    pk25, tr25 = max(s25, key=lambda r: r["passengers"]), min(s25, key=lambda r: r["passengers"])
    pk19, tr19 = max(s19, key=lambda r: r["passengers"]), min(s19, key=lambda r: r["passengers"])
    top_pct = max(q3, key=lambda r: r["pct_since_2022"])
    top_abs = max(q3, key=lambda r: r["added_since_2022_k"])
    shrink = [r for r in q3 if r["pct_since_2022"] < 0]
    d19 = next(r for r in q4 if r["year"] == 2019)
    d25 = next(r for r in q4 if r["year"] == 2025)
    c25 = r25[-1]
    c22 = [r for r in q5 if r["year"] == 2022][-1]
    uk25 = r25[0]
    h26, h25 = b["2026"], b["2025"]
    yoy = 100.0 * (h26["passengers"] / h25["passengers"] - 1)
    ratio25 = tr25["passengers"] and pk25["passengers"] / tr25["passengers"]
    ratio19 = pk19["passengers"] / tr19["passengers"]
    summary = {
        "kpis": [
            {"value": f'{a25["passengers"] / 1e6:.1f} m', "label": "Dublin passengers in 2025"},
            {"value": f'{h26["pct_vs_2019"]:+.1f}%', "label": "Jan to Jun 2026 vs Jan to Jun 2019"},
            {"value": f"{ratio25:.2f}x", "label": f"{MONTHS[pk25['month']-1]} vs {MONTHS[tr25['month']-1]} 2025 (peak to trough)"},
            {"value": f'{c25["cumulative_share_pct"]:.1f}%', "label": "Share of Dublin traffic in the top 10 markets, 2025"},
        ],
        "captions": {
            "recovery": (f'Dublin carried {a25["passengers"] / 1e6:.1f} million passengers in 2025, '
                         f'{a25["pct_vs_2019"]:.1f}% above 2019. It went past 2019 in 2023 ({a23["pct_vs_2019"]:+.1f}%). '
                         f'January to June 2026 was {h26["passengers"] / 1e6:.1f} million, {h26["pct_vs_2019"]:.1f}% above the same months of 2019 '
                         f'and {yoy:.1f}% above 2025.'),
            "season": (f'In 2025 the busiest month ({MONTHS[pk25["month"]-1]}, {pk25["passengers"] / 1e6:.2f} million) had '
                       f'{ratio25:.2f} times the traffic of the quietest ({MONTHS[tr25["month"]-1]}, {tr25["passengers"] / 1e6:.2f} million). '
                       f'In 2019 the same gap was {ratio19:.2f} times ({MONTHS[pk19["month"]-1]} vs {MONTHS[tr19["month"]-1]}).'),
            "growth": (f'{top_pct["market"].replace(" (1)", "")} grew fastest ({top_pct["pct_since_2022"]:+.1f}%). '
                       f'The UK added the most passengers ({top_abs["added_since_2022_k"] / 1000:.2f} million) and the US added '
                       f'{next(r for r in q3 if r["market"] == "United States")["added_since_2022_k"] / 1000:.2f} million. '
                       f'Only {len(shrink)} of {len(q3)} markets shrank: ' + ", ".join(
                           f'{r["market"]} ({r["pct_since_2022"]:+.1f}%)' for r in sorted(shrink, key=lambda r: r["pct_since_2022"])) + '.'),
            "share": (f'Dublin had {d19["dublin_pct"]:.1f}% of passengers at the five main airports in 2019 and '
                      f'{d25["dublin_pct"]:.1f}% in 2025. Its share was {q4[0]["dublin_pct"]:.1f}% in 2005. '
                      f'Cork rose from {d19["cork_pct"]:.1f}% to {d25["cork_pct"]:.1f}% and Shannon from {d19["shannon_pct"]:.1f}% to {d25["shannon_pct"]:.1f}% since 2019.'),
            "concentration": (f'The top 10 country markets carried {c25["cumulative_share_pct"]:.1f}% of Dublin passengers in 2025 '
                              f'({c22["cumulative_share_pct"]:.1f}% in 2022). The UK alone is {uk25["share_pct"]:.1f}%. '
                              f'Data is by country, not by route.'),
        },
        "airport_share_latest": d25,
    }

    data = {"summary": summary, "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5,
            "months": MONTHS}
    (ROOT / "data" / "results.json").write_text(json.dumps(data, indent=1))
    # dashboard.html is built separately by src/build_dashboard.py
    print(json.dumps(summary["kpis"], indent=1))
    for k, v in summary["captions"].items():
        print(k, ":", v)


if __name__ == "__main__":
    main()
