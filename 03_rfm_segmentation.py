"""
Step 3: RFM scoring and segment labeling.

Pulls rfm_base from MySQL (created in 02_rfm_queries.sql), scores each
customer 1-5 on R, F, M, and assigns a human-readable segment.
"""

import pandas as pd
from sqlalchemy import create_engine

MYSQL_USER = "root"
MYSQL_PASSWORD = "1234567"
MYSQL_HOST = "localhost"
MYSQL_DB = "retail_rfm"


def load_rfm() -> pd.DataFrame:
    engine = create_engine(
        f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    )
    return pd.read_sql("SELECT * FROM rfm_base", engine)


def score_rfm(df: pd.DataFrame) -> pd.DataFrame:
    # Recency: lower is better -> reverse the quintile labels
    df["R_score"] = pd.qcut(df["recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    # Frequency/Monetary: higher is better
    df["F_score"] = pd.qcut(df["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    df["M_score"] = pd.qcut(df["monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)

    df["RFM_score"] = df["R_score"].astype(str) + df["F_score"].astype(str) + df["M_score"].astype(str)
    df["RFM_total"] = df["R_score"] + df["F_score"] + df["M_score"]
    return df


def assign_segment(row) -> str:
    r, f, m = row["R_score"], row["F_score"], row["M_score"]

    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3 and m >= 3:
        return "Loyal Customers"
    if r >= 4 and f <= 2:
        return "New / Recent Customers"
    if r <= 2 and f >= 4 and m >= 4:
        return "Can't Lose Them"
    if r <= 2 and f >= 3:
        return "At-Risk"
    if r <= 2 and f <= 2 and m >= 3:
        return "Hibernating (High Value)"
    if r <= 2 and f <= 2 and m <= 2:
        return "Lost"
    return "Needs Attention"


def label_segments(df: pd.DataFrame) -> pd.DataFrame:
    df["Segment"] = df.apply(assign_segment, axis=1)
    return df


if __name__ == "__main__":
    df = load_rfm()
    df = score_rfm(df)
    df = label_segments(df)

    print(df["Segment"].value_counts())
    print("\nAvg monetary value by segment:")
    print(df.groupby("Segment")["monetary"].mean().sort_values(ascending=False).round(2))

    df.to_csv("rfm_scored.csv", index=False)
    print("\nSaved rfm_scored.csv — feed this into 04_roi_budget_allocation.py")
