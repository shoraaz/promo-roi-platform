CREATE OR REPLACE TABLE `promo-roi-platform-2026.promo_roi.promo_features` AS

-- Step 1: Clean raw data
-- Remove closed stores and zero-sales rows
-- Parse date string into actual DATE type
WITH clean_data AS (
  SELECT
    Store,
    PARSE_DATE('%Y-%m-%d', Date) AS Date,
    Sales,
    Promo,
    StateHoliday,
    SchoolHoliday,
    DayOfWeek
  FROM `promo-roi-platform-2026.promo_roi.rossmann_train`
  WHERE Open = 1
    AND Sales > 0
),

-- Step 2: Compute 30-day rolling baseline
-- For each store, average sales on NON-PROMO days in the 30 days before each date
-- This becomes our "what would sales have been without a promo" reference point
baseline AS (
  SELECT
    Store,
    Date,
    Sales,
    Promo,
    StateHoliday,
    SchoolHoliday,
    DayOfWeek,
    -- Rolling 30-day average of non-promo sales
    -- ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING = look back 30 days, exclude today
    AVG(CASE WHEN Promo = 0 THEN Sales END) OVER (
      PARTITION BY Store
      ORDER BY Date
      ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
    ) AS baseline_sales_30d,
    -- Lag features: what were sales 7 and 30 days ago?
    LAG(Sales, 7) OVER (PARTITION BY Store ORDER BY Date) AS lag_7_sales,
    LAG(Sales, 30) OVER (PARTITION BY Store ORDER BY Date) AS lag_30_sales
  FROM clean_data
),

-- Step 3: Compute days since last promotion per store
promo_timing AS (
  SELECT
    Store,
    Date,
    Sales,
    Promo,
    StateHoliday,
    SchoolHoliday,
    DayOfWeek,
    baseline_sales_30d,
    lag_7_sales,
    lag_30_sales,
    DATE_DIFF(
      Date,
      LAST_VALUE(
        CASE WHEN Promo = 1 THEN Date ELSE NULL END IGNORE NULLS
      ) OVER (
        PARTITION BY Store
        ORDER BY Date
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
      ),
      DAY
    ) AS days_since_last_promo
  FROM baseline
),

-- Step 4: Join store metadata
-- Adds store type, assortment, competition distance
with_store_info AS (
  SELECT
    p.*,
    s.StoreType,
    s.Assortment,
    s.CompetitionDistance,
    s.Promo2 AS store_enrolled_in_promo2
  FROM promo_timing p
  LEFT JOIN `promo-roi-platform-2026.promo_roi.rossmann_store` s
    ON p.Store = s.Store
)

-- Final: Compute labels and select only promo rows
-- We only keep rows where Promo=1 because those are the events we're modeling
-- Each row = one promotion event at one store on one day
SELECT
  Store,
  Date,
  DayOfWeek,
  StoreType,
  Assortment,
  COALESCE(CompetitionDistance, 0) AS competition_distance,
  store_enrolled_in_promo2,
  SchoolHoliday AS is_school_holiday,
  CASE WHEN StateHoliday != '0' THEN 1 ELSE 0 END AS is_state_holiday,
  COALESCE(baseline_sales_30d, Sales) AS baseline_sales_30d,
  COALESCE(lag_7_sales, Sales) AS lag_7_sales,
  COALESCE(lag_30_sales, Sales) AS lag_30_sales,
  COALESCE(days_since_last_promo, 999) AS days_since_last_promo,
  Sales AS promo_sales,

  -- Label 1: Sales lift percentage
  SAFE_DIVIDE(
    Sales - COALESCE(baseline_sales_30d, Sales),
    COALESCE(baseline_sales_30d, Sales)
  ) * 100 AS sales_lift_pct,

  -- Label 2: Margin impact in absolute currency
  -- incremental_margin = (promo_sales - baseline) * 0.20
  -- promo_cost = baseline * 0.15
  -- margin_impact = incremental_margin - promo_cost
  (
    (Sales - COALESCE(baseline_sales_30d, Sales)) * 0.20
    - COALESCE(baseline_sales_30d, Sales) * 0.15
  ) AS margin_impact,

  -- Train/test split flag
  CASE
    WHEN Date <= '2015-03-31' THEN 'train'
    ELSE 'validation'
  END AS split

FROM with_store_info
WHERE Promo = 1  -- only keep promotion events
ORDER BY Store, Date;