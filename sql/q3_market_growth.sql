-- QUESTION: Which country markets served from Dublin grew or shrank the most
-- between 2022 and 2025?
-- WHY IT MATTERS: growth is not even. Markets that add the most passengers need
-- gates, stands and border control capacity first; markets that stall are
-- where airline incentives or route marketing may be needed.
-- Source is the country table (TAA06). Both directions are counted. Only single
-- countries are ranked (the UK is one market; "Other Europe", "America",
-- domestic flights and the four UK nations are left out). The Canary Islands
-- are reported by CSO as a separate market from Spain. 2022 is still a
-- recovery year, so read the percentages as "growth since recovery", and use the
-- 2024 to 2025 column for current momentum. Only markets with at least 100,000
-- passengers in 2022 are ranked, to avoid tiny bases.

WITH m AS (
    SELECT mk.name AS market, f.year, f.passengers_thousand AS pax_k
    FROM fact_market_year f
    JOIN dim_airport a USING (airport_id)
    JOIN dim_market mk USING (market_id)
    WHERE a.name = 'Dublin'
      AND f.direction = 'All directions'
      AND f.flight_type = 'All flights'
      AND mk.kind = 'country'
)
SELECT p25.market,
       p22.pax_k AS pax_2022_k,
       p24.pax_k AS pax_2024_k,
       p25.pax_k AS pax_2025_k,
       ROUND(p25.pax_k - p22.pax_k, 1) AS added_since_2022_k,
       ROUND(100.0 * (p25.pax_k - p22.pax_k) / p22.pax_k, 1) AS pct_since_2022,
       ROUND(100.0 * (p25.pax_k - p24.pax_k) / p24.pax_k, 1) AS pct_2025_vs_2024
FROM m p25
JOIN m p24 ON p24.market = p25.market AND p24.year = 2024
JOIN m p22 ON p22.market = p25.market AND p22.year = 2022
WHERE p25.year = 2025 AND p22.pax_k >= 100
ORDER BY pct_since_2022 DESC;
