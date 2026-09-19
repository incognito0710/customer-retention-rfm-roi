# Customer Segmentation & Retention ROI Analysis

**Business question:** *Which customer segments will give the highest ROI on
retention campaigns, and how should the marketing team allocate budget?*

## Overview
An end-to-end analytics pipeline on the UCI Online Retail II dataset that
goes beyond descriptive RFM segmentation into a decision-oriented output:
a ranked, ROI-driven retention budget allocation across customer segments.

## Dataset
- **Source:** [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) (also mirrored on Kaggle)
- ~1M transaction line items, UK-based online retailer, Dec 2009 – Dec 2011
- Fields: Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country

## Pipeline
| Stage | File | Tool |
|---|---|---|
| 1. Clean & load | `01_data_cleaning.py` | Python (pandas, sqlalchemy) → MySQL |
| 2. RFM base table | `02_rfm_queries.sql` | SQL (MySQL view) |
| 3. RFM scoring & segmentation | `03_rfm_segmentation.py` | Python (pandas) |
| 4. ROI model & budget allocation | `04_roi_budget_allocation.py` | Python (pandas) |
| 5. Dashboard | Power BI, connected live to MySQL | Power BI |

## Methodology

**RFM Segmentation**
Each customer is scored 1–5 (quintiles) on Recency, Frequency, and
Monetary value, then mapped to a segment: Champions, Loyal Customers,
Can't Lose Them, At-Risk, Hibernating (High Value), Lost, etc.

**Retention ROI model**
For each segment:
```
expected_incremental_revenue = avg_customer_value × estimated_retention_uplift
expected_roi_per_customer    = expected_incremental_revenue − campaign_cost_per_customer
```
Budget is then allocated in proportion to each segment's share of total
positive expected ROI, capped to segments where ROI per customer is
positive.

**Assumptions (stated explicitly, not fabricated as fact):**
- Campaign cost: £5/customer/touch (email/SMS/discount)
- Retention uplift % by segment — illustrative estimates based on typical
  CRM/lifecycle-marketing benchmarks (documented in `04_roi_budget_allocation.py`);
  swap in real A/B test data if available
- Total retention budget: £20,000 (adjust to taste)

## Key finding
> Analysis of 5,878 customers (from 779,425 cleaned transactions) found that
> **"Can't Lose Them"** customers — high-value buyers who have gone quiet —
> deliver the highest retention ROI at **£788 per customer**, nearly 4.4x
> higher than the next-best actively-targetable segment. Despite being only
> 3.8% of the customer base, they represent the single best use of
> retention spend.
>
> Champions were deliberately excluded from active retention spend — they
> are already engaged, and modeling initially over-allocated budget to them
> simply because of their size, not their marginal ROI; excluding
> already-retained segments corrected this.
>
> **Recommended allocation:** 37.4% of the retention budget to "Can't Lose
> Them" (VIP outreach), 26.4% to Loyal Customers (loyalty perks), and 18.6%
> to At-Risk customers (win-back email series) — covering the three
> segments responsible for 82% of total expected retention ROI.

## Dashboard (Power BI)
- KPI cards: Total Customers, Total Revenue, Revenue at Risk, Avg Customer Value
- RFM segment treemap
- **Budget allocation bar chart** (segment → £ allocated → customers reachable)
- Segment drill-through table with recommended actions

## How to run
```bash
pip install pandas sqlalchemy mysql-connector-python
python 01_data_cleaning.py          # loads cleaned data into MySQL
mysql -u root -p < 02_rfm_queries.sql   # builds rfm_base view
python 03_rfm_segmentation.py       # scores + labels segments -> rfm_scored.csv
python 04_roi_budget_allocation.py  # -> segment_roi.csv, budget_allocation.csv
```
Connect Power BI to `retail_rfm` in MySQL (or import the CSV outputs) to
build the dashboard.

## Repo structure
```
├── 01_data_cleaning.py
├── 02_rfm_queries.sql
├── 03_rfm_segmentation.py
├── 04_roi_budget_allocation.py
├── README.md
└── dashboard.pbix
```
