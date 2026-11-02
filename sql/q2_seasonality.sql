-- QUESTION: How seasonal is Dublin traffic, and how far apart are the busiest and
-- quietest months?
-- WHY IT MATTERS: terminals, security lanes and stands are sized for the peak,
-- and staff rosters follow the curve. A wide peak to trough gap means a lot of
-- capacity sits idle in winter, so shifting demand into the shoulder months is
-- worth real money.
-- Index = month passengers divided by the average month of that year (100 = average).
-- Years: 2019 (last normal year) and 2025 (last full year).

WITH monthly AS (
    SELECT m.year, m.month, m.passengers
    FROM fact_airport_month m
    JOIN dim_airport a USING (airport_id)
    WHERE a.name = 'Dublin' AND m.year IN (2019, 2025)
),
avg_month AS (
    SELECT year, AVG(passengers) AS avg_pax FROM monthly GROUP BY year
)
SELECT m.year,
       m.month,
       m.passengers,
       ROUND(100.0 * m.passengers / a.avg_pax, 1) AS seasonal_index,
       ROUND(1.0 * m.passengers / MIN(m.passengers) OVER (PARTITION BY m.year), 2)
           AS multiple_of_quietest_month,
       RANK() OVER (PARTITION BY m.year ORDER BY m.passengers DESC) AS busiest_rank
FROM monthly m
JOIN avg_month a USING (year)
ORDER BY m.year, m.month;
