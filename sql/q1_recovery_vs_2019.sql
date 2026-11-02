-- QUESTION: How is Dublin airport passenger traffic doing against 2019, the last
-- normal year before the pandemic?
-- WHY IT MATTERS: if traffic is already well above 2019, capacity planning is
-- about managing growth and congestion, not about winning back lost demand.
-- Part A is full years (index, 2019 = 100). Part B compares January to June of
-- 2026, 2025 and 2019, which is the latest data available.

-- Part A: full years
WITH dub AS (
    SELECT y.year, y.passengers
    FROM fact_airport_year y
    JOIN dim_airport a USING (airport_id)
    WHERE a.name = 'Dublin' AND y.year BETWEEN 2019 AND 2025
),
base AS (SELECT passengers AS p2019 FROM dub WHERE year = 2019)
SELECT 'A_full_year' AS part,
       CAST(dub.year AS TEXT) AS period,
       dub.passengers,
       ROUND(100.0 * dub.passengers / base.p2019, 1) AS index_2019_eq_100,
       ROUND(100.0 * (dub.passengers - base.p2019) / base.p2019, 1) AS pct_vs_2019
FROM dub, base

UNION ALL

-- Part B: January to June in each year
SELECT 'B_jan_jun',
       CAST(m.year AS TEXT),
       SUM(m.passengers),
       ROUND(100.0 * SUM(m.passengers) / (
           SELECT SUM(m2.passengers) FROM fact_airport_month m2
           JOIN dim_airport a2 USING (airport_id)
           WHERE a2.name = 'Dublin' AND m2.year = 2019 AND m2.month <= 6), 1),
       ROUND(100.0 * (SUM(m.passengers) - (
           SELECT SUM(m2.passengers) FROM fact_airport_month m2
           JOIN dim_airport a2 USING (airport_id)
           WHERE a2.name = 'Dublin' AND m2.year = 2019 AND m2.month <= 6))
           / (SELECT SUM(m2.passengers) FROM fact_airport_month m2
              JOIN dim_airport a2 USING (airport_id)
              WHERE a2.name = 'Dublin' AND m2.year = 2019 AND m2.month <= 6), 1)
FROM fact_airport_month m
JOIN dim_airport a USING (airport_id)
WHERE a.name = 'Dublin' AND m.month <= 6 AND m.year IN (2019, 2025, 2026)
GROUP BY m.year
ORDER BY part, period;
