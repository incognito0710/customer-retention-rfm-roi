"""
Step 1: Load, clean, and push the Online Retail dataset into MySQL.

Dataset: UCI Online Retail II (or Kaggle mirror)
Download from: https://archive.ics.uci.edu/dataset/502/online+retail+ii
Or Kaggle: search "Online Retail II UCI"

Expected columns:
Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country
(Kaggle CSV versions sometimes use InvoiceNo/UnitPrice/CustomerID instead — the
rename step below normalizes both to one schema.)
"""

import pandas as pd
from sqlalchemy import create_engine

# ---------- CONFIG ----------
EXCEL_PATH = r"C:\Users\NIKITAA\Downloads\online+retail+ii\online_retail_II.xlsx"   # raw string (r prefix) # path to your downloaded dataset
EXCEL_SHEETS = ["Year 2009-2010", "Year 2010-2011"]  # both sheets in the UCI file
MYSQL_USER = "root"
MYSQL_PASSWORD = "1234567"
MYSQL_HOST = "localhost"
MYSQL_DB = "retail_rfm"
# -----------------------------

def load_raw(path: str, sheets: list) -> pd.DataFrame:
    # Read both yearly sheets and stack them into one DataFrame
    frames = [pd.read_excel(path, sheet_name=sheet) for sheet in sheets]
    df = pd.concat(frames, ignore_index=True)
    return df


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "InvoiceNo": "Invoice",
        "UnitPrice": "Price",
        "CustomerID": "Customer ID",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # Drop rows with no customer ID — can't attribute them to a segment
    df = df.dropna(subset=["Customer ID"])

    # Drop cancelled orders (Invoice starting with "C")
    df = df[~df["Invoice"].astype(str).str.startswith("C")]

    # Drop non-positive quantity or price (returns, data errors, free items)
    df = df[(df["Quantity"] > 0) & (df["Price"] > 0)]

    # Drop exact duplicate rows
    df = df.drop_duplicates()

    df["Customer ID"] = df["Customer ID"].astype(int)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["TotalPrice"] = df["Quantity"] * df["Price"]

    after = len(df)
    print(f"Cleaned: {before:,} -> {after:,} rows "
          f"({before - after:,} removed, {(before - after) / before:.1%})")
    return df


def load_to_mysql(df: pd.DataFrame):
    engine = create_engine(
        f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    )
    df.to_sql("transactions", engine, if_exists="replace", index=False, chunksize=5000)
    print(f"Loaded {len(df):,} rows into `{MYSQL_DB}.transactions`")


if __name__ == "__main__":
    df = load_raw(EXCEL_PATH, EXCEL_SHEETS)
    df = normalize_columns(df)
    df = clean(df)

    # Optional: save a local cleaned copy for the Python-only RFM steps
    df.to_csv("transactions_clean.csv", index=False)

    load_to_mysql(df)