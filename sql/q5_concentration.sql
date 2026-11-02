-- QUESTION: Is Dublin traffic concentrated in a handful of markets, and is that
-- concentration rising or falling?
-- WHY IT MATTERS: if a few markets carry most passengers, a shock in one of them
-- (a policy change, an airline failure, a travel restriction) hits the airport
-- hard. Diversification is a risk-management argument for route development.
-- IMPORTANT: the public tables give passengers by destination country, not by
-- individual route, so "market" means country (the UK counts as one market).
-- Share is of all Dublin passengers (domestic and "other region" groups included
-- in the denominator). Ranked markets are single countries only.

WITH pax AS (
    SELECT mk.name AS market, mk.kind, f.year, f.passengers_thousand AS pax_k
    FROM fact_market_year f
    JOIN dim_airport a USING (airport_id)
    JOIN dim_market mk USING (market_id)
    WHERE a.name = 'Dublin'
      AND f.direction = 'All directions'
      AND f.flight_type = 'All flights'
      AND f.year IN (2022, 2025)
),
tot AS (SELECT year, pax_k AS total_k FROM pax WHERE kind = 'total'),
ranked AS (
    SELECT p.year, p.market, p.pax_k,
           RANK() OVER (PARTITION BY p.year ORDER BY p.pax_k DESC) AS rnk
    FROM pax p
    WHERE p.kind = 'country'
)
SELECT r.year,
       r.rnk,
       r.market,
       r.pax_k,
       ROUND(100.0 * r.pax_k / t.total_k, 1) AS share_pct,
       ROUND(100.0 * SUM(r.pax_k) OVER (PARTITION BY r.year ORDER BY r.rnk)
             / t.total_k, 1) AS cumulative_share_pct
FROM ranked r
JOIN tot t USING (year)
WHERE r.rnk <= 10
ORDER BY r.year, r.rnk;
