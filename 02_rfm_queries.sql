-- =========================================================
-- Step 2: RFM base table in MySQL
-- Run after 01_data_cleaning.py has loaded `transactions`
-- =========================================================

USE retail_rfm;

-- NOTE: MySQL views cannot reference user variables (@snapshot_date),
-- so the snapshot-date calculation is done as a subquery inline below
-- instead of with SET @snapshot_date = ...

-- Core RFM table: one row per customer
CREATE OR REPLACE VIEW rfm_base AS
SELECT
    `Customer ID`                                                          AS customer_id,
    DATEDIFF(
        (SELECT DATE_ADD(MAX(InvoiceDate), INTERVAL 1 DAY) FROM transactions),
        MAX(InvoiceDate)
    )                                                                       AS recency,
    COUNT(DISTINCT Invoice)                                                 AS frequency,
    ROUND(SUM(TotalPrice), 2)                                               AS monetary
FROM transactions
GROUP BY `Customer ID`;

-- Sanity check
SELECT COUNT(*) AS total_customers FROM rfm_base;
SELECT * FROM rfm_base ORDER BY monetary DESC LIMIT 10;

-- =========================================================
-- Handy summary queries you can reuse for the Power BI model
-- =========================================================

-- Revenue and order count by country (for a geography visual)
SELECT
    Country,
    COUNT(DISTINCT Invoice)   AS orders,
    ROUND(SUM(TotalPrice), 2) AS revenue
FROM transactions
GROUP BY Country
ORDER BY revenue DESC;

-- Monthly revenue trend
SELECT
    DATE_FORMAT(InvoiceDate, '%Y-%m') AS month,
    ROUND(SUM(TotalPrice), 2)         AS revenue
FROM transactions
GROUP BY month
ORDER BY month;
