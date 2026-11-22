-- M3 data preparation in DuckDB. Run from the repo root (see notebooks/D01_M3_eda.ipynb).
-- Inputs: data/raw/iex_dam_15min.csv, data/processed/weather_daily.csv, holidays table registered from Python.

-- 1. Typed, flagged block table from 1 Apr 2023 (single Rs 10,000 price-cap regime)
CREATE OR REPLACE TABLE blocks AS
SELECT
    CAST(datetime AS TIMESTAMP)                     AS ts,
    CAST(date AS DATE)                              AS d,
    CAST(block AS INTEGER)                          AS block,
    (CAST(block AS INTEGER) - 1) // 4               AS hour,
    CAST(mcp_rs_mwh AS DOUBLE)                      AS price,
    CAST(purchase_bid_mw AS DOUBLE)                 AS buy_bid_mw,
    CAST(sell_bid_mw AS DOUBLE)                     AS sell_bid_mw,
    CAST(mcv_mw AS DOUBLE)                          AS cleared_mw,
    CAST(final_scheduled_volume_mw AS DOUBLE)       AS scheduled_mw,
    congestion = 'YES'                              AS congested,
    CAST(mcp_rs_mwh AS DOUBLE) >= 10000             AS capped,
    CAST(mcv_mw AS DOUBLE) > LEAST(CAST(purchase_bid_mw AS DOUBLE), CAST(sell_bid_mw AS DOUBLE)) + 1e-6 AS volume_flag
FROM read_csv_auto('data/raw/iex_dam_15min.csv')
WHERE CAST(date AS DATE) >= DATE '2023-04-01';

-- 2. Quality checks: one row per check, expected value in the comment
CREATE OR REPLACE TABLE quality AS
SELECT 'days'               AS check_name, COUNT(DISTINCT d)::DOUBLE AS value FROM blocks              -- 1,331
UNION ALL SELECT 'days_not_96_blocks', COUNT(*) FROM (SELECT d FROM blocks GROUP BY d HAVING COUNT(*) <> 96)  -- 0
UNION ALL SELECT 'duplicate_blocks', COUNT(*) - COUNT(DISTINCT (d, block)) FROM blocks                      -- 0
UNION ALL SELECT 'null_prices', COUNT(*) FILTER (WHERE price IS NULL) FROM blocks                         -- 0
UNION ALL SELECT 'max_price', MAX(price) FROM blocks                                                       -- 10,000
UNION ALL SELECT 'min_price', MIN(price) FROM blocks
UNION ALL SELECT 'capped_share_pct', 100 * AVG(capped::INT) FROM blocks
UNION ALL SELECT 'volume_flag_blocks', SUM(volume_flag::INT) FROM blocks
UNION ALL SELECT 'congested_share_pct', 100 * AVG(congested::INT) FROM blocks;

-- 3. One row per day: price shape, spread and calendar, joined to weather and holidays
CREATE OR REPLACE TABLE days AS
WITH agg AS (
    SELECT d,
        AVG(price)                                                    AS mean_price,
        MIN(price)                                                    AS min_price,
        MAX(price)                                                    AS max_price,
        AVG(price) FILTER (WHERE hour BETWEEN 10 AND 15)              AS midday_price,
        AVG(price) FILTER (WHERE hour BETWEEN 18 AND 23)              AS evening_price,
        AVG(price) FILTER (WHERE hour BETWEEN 5 AND 8)                AS morning_price,
        AVG(price) FILTER (WHERE hour BETWEEN 0 AND 4)                AS night_price,
        SUM(capped::INT)                                              AS capped_blocks,
        AVG(cleared_mw)                                               AS mean_cleared_mw,
        AVG(buy_bid_mw / NULLIF(sell_bid_mw, 0))                      AS bid_ratio
    FROM blocks GROUP BY d
)
SELECT a.*,
    a.max_price - a.min_price                                         AS spread,
    a.evening_price - a.midday_price                                  AS evening_midday_gap,
    a.morning_price - a.midday_price                                  AS morning_midday_gap,
    dayofweek(a.d)                                                    AS dow,          -- 0 = Sunday
    month(a.d)                                                        AS month,
    CASE WHEN month(a.d) IN (3,4,5,6) THEN 'Mar-Jun' WHEN month(a.d) IN (7,8,9) THEN 'Jul-Sep' ELSE 'Oct-Feb' END AS season,
    CASE WHEN a.d >= DATE '2025-11-22' THEN 'test' WHEN a.d >= DATE '2024-11-22' THEN 'validate' ELSE 'train' END AS split,
    h.name IS NOT NULL                                                AS holiday,
    w.solar_midday_wm2, w.cloud_midday_pct, w.temp_max_c, w.temp_evening_c, w.wind_kmh, w.wind_evening_kmh
FROM agg a
LEFT JOIN holidays h ON h.d = a.d
LEFT JOIN read_csv_auto('data/processed/weather_daily.csv') w ON CAST(w.date AS DATE) = a.d
ORDER BY a.d;
