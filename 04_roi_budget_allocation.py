"""
Step 4: Retention ROI estimation and budget allocation.

This is the layer that directly answers the business question:
"Which customer segments will give the highest ROI on retention
campaigns, and how should the marketing team allocate budget?"

Everything here is a transparent, documented model — not fabricated
fact. State your assumptions in the README/report so it reads as a
modeling exercise, which is exactly what a BA/DA role expects.
"""

import pandas as pd

INPUT_CSV = "rfm_scored.csv"

# ---------- ASSUMPTIONS (state these explicitly in your write-up) ----------
CAMPAIGN_COST_PER_CUSTOMER = 5.0     # e.g. cost of an email/SMS/discount touch, in £
TOTAL_RETENTION_BUDGET = 20000.0     # total budget available to allocate

# Estimated retention uplift by segment: how much more likely a customer
# in this segment is to make another purchase IF targeted with a
# retention campaign, vs. left alone. These are illustrative assumptions
# based on typical CRM benchmarks — swap in real experiment data if you
# have it.
UPLIFT_BY_SEGMENT = {
    "Champions": 0.02,                  # already retained, campaigns add little
    "Loyal Customers": 0.05,
    "New / Recent Customers": 0.08,
    "Can't Lose Them": 0.18,            # high value + slipping away = best target
    "At-Risk": 0.15,
    "Hibernating (High Value)": 0.10,
    "Lost": 0.03,                       # cheap to reach, but low win-back rate
    "Needs Attention": 0.07,
}

# Priority weighting for segments a marketing team should NOT actively
# target even if ROI math is nonzero (kept for transparency in the model)
EXCLUDE_FROM_ACTIVE_SPEND = {"Champions"}  # already retained — don't compete for retention budget
# -----------------------------------------------------------------------


def compute_segment_roi(df: pd.DataFrame) -> pd.DataFrame:
    seg = df.groupby("Segment").agg(
        customers=("customer_id", "count"),
        avg_monetary=("monetary", "mean"),
        total_monetary=("monetary", "sum"),
    ).reset_index()

    seg["uplift"] = seg["Segment"].map(UPLIFT_BY_SEGMENT).fillna(0.05)

    # Expected incremental revenue per customer if targeted
    seg["expected_incremental_revenue"] = seg["avg_monetary"] * seg["uplift"]

    # ROI per customer = incremental revenue - campaign cost
    seg["expected_roi_per_customer"] = (
        seg["expected_incremental_revenue"] - CAMPAIGN_COST_PER_CUSTOMER
    )

    # Total expected ROI for the segment if fully targeted
    seg["total_expected_roi"] = seg["expected_roi_per_customer"] * seg["customers"]

    return seg.sort_values("expected_roi_per_customer", ascending=False)


def allocate_budget(seg: pd.DataFrame) -> pd.DataFrame:
    seg = seg.copy()

    # Only allocate to segments with positive expected ROI per customer
    eligible = seg[
        (seg["expected_roi_per_customer"] > 0)
        & (~seg["Segment"].isin(EXCLUDE_FROM_ACTIVE_SPEND))
    ].copy()

    # Weight allocation by each segment's share of total positive ROI
    eligible["roi_weight"] = eligible["total_expected_roi"].clip(lower=0)
    total_weight = eligible["roi_weight"].sum()
    eligible["budget_share_pct"] = (eligible["roi_weight"] / total_weight * 100).round(1)
    eligible["allocated_budget"] = (
        eligible["budget_share_pct"] / 100 * TOTAL_RETENTION_BUDGET
    ).round(2)
    eligible["customers_reachable"] = (
        eligible["allocated_budget"] / CAMPAIGN_COST_PER_CUSTOMER
    ).round(0).astype(int)

    cols = [
        "Segment", "customers", "avg_monetary", "expected_roi_per_customer",
        "budget_share_pct", "allocated_budget", "customers_reachable",
    ]
    return eligible[cols].sort_values("budget_share_pct", ascending=False)


ACTION_MAP = {
    "Can't Lose Them": "VIP outreach / account-manager call + exclusive offer",
    "At-Risk": "Win-back email series + personalized discount",
    "Hibernating (High Value)": "Re-engagement campaign, remind of past purchases",
    "New / Recent Customers": "Onboarding nurture sequence, second-purchase incentive",
    "Loyal Customers": "Loyalty program perks, referral incentives",
    "Needs Attention": "Light-touch email, monitor for further decline",
    "Champions": "Low spend — reward/advocacy program, not retention",
    "Lost": "Low-cost automated win-back email only",
}


if __name__ == "__main__":
    df = pd.read_csv(INPUT_CSV)

    seg_roi = compute_segment_roi(df)
    print("=== Segment ROI ranking ===")
    print(seg_roi[["Segment", "customers", "avg_monetary",
                    "expected_roi_per_customer", "total_expected_roi"]]
          .round(2).to_string(index=False))

    budget = allocate_budget(seg_roi)
    budget["recommended_action"] = budget["Segment"].map(ACTION_MAP)

    print("\n=== Recommended budget allocation ===")
    print(budget.to_string(index=False))

    budget.to_csv("budget_allocation.csv", index=False)
    seg_roi.to_csv("segment_roi.csv", index=False)
    print("\nSaved segment_roi.csv and budget_allocation.csv — wire these into Power BI")
