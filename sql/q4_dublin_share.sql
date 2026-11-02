-- QUESTION: How big is Dublin compared with Cork, Shannon, Knock and Kerry, and
-- has its weight in the Irish system changed?
-- WHY IT MATTERS: a rising Dublin share means the national network leans harder
-- on one hub (capacity and resilience risk, and the case for regional growth).
-- A falling share means the regions are catching up.
-- Share = airport passengers divided by the sum of the five main airports (the
-- same five that CSO reports as "All main airports"). One row per year.

WITH main5 AS (
    SELECT y.year, a.name, y.passengers
    FROM fact_airport_year y
    JOIN dim_airport a USING (airport_id)
    WHERE a.name IN ('Dublin', 'Cork', 'Shannon', 'Knock', 'Kerry')
)
SELECT year,
       SUM(passengers) AS five_airport_total,
       ROUND(100.0 * SUM(CASE WHEN name = 'Dublin'  THEN passengers END) / SUM(passengers), 2) AS dublin_pct,
       ROUND(100.0 * SUM(CASE WHEN name = 'Cork'    THEN passengers END) / SUM(passengers), 2) AS cork_pct,
       ROUND(100.0 * SUM(CASE WHEN name = 'Shannon' THEN passengers END) / SUM(passengers), 2) AS shannon_pct,
       ROUND(100.0 * SUM(CASE WHEN name = 'Knock'   THEN passengers END) / SUM(passengers), 2) AS knock_pct,
       ROUND(100.0 * SUM(CASE WHEN name = 'Kerry'   THEN passengers END) / SUM(passengers), 2) AS kerry_pct
FROM main5
GROUP BY year
ORDER BY year;
