"""
01_data_cleaning.py
Cleans the raw Zomato sales dataset:
- removes duplicates
- standardizes text fields
- fixes inconsistent date formats
- handles missing values
- treats outliers in order_value
- creates derived columns (net_revenue, month, weekday, is_weekend)
"""
import pandas as pd
import numpy as np

RAW_PATH = "../data/raw/zomato_sales_raw.csv"
OUT_PATH = "../data/processed/zomato_sales_cleaned.csv"

df = pd.read_csv(RAW_PATH)
print(f"Raw shape: {df.shape}")

# 1. Remove duplicate orders
before = len(df)
df = df.drop_duplicates(subset="order_id", keep="first")
print(f"Removed {before - len(df)} duplicate orders")

# 2. Standardize text fields
df["restaurant_name"] = df["restaurant_name"].str.strip().str.lower().str.title()
df["city"] = df["city"].str.strip().str.title()
df["food_category"] = df["food_category"].str.strip().str.title()
df["payment_mode"] = df["payment_mode"].str.strip().str.title()

# 3. Fix inconsistent date formats (mix of YYYY-MM-DD and DD/MM/YYYY)
def parse_date(x):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return pd.to_datetime(x, format=fmt)
        except (ValueError, TypeError):
            continue
    return pd.NaT

df["order_date"] = df["order_date"].apply(parse_date)
print(f"Unparseable dates: {df['order_date'].isna().sum()}")
df = df.dropna(subset=["order_date"])

# 4. Handle missing values
# rating: impute with category-level median (ratings are subjective per cuisine)
df["rating"] = df.groupby("food_category")["rating"].transform(lambda s: s.fillna(s.median()))
# delivery_fee: missing likely means free delivery promo -> impute with 0
df["delivery_fee"] = df["delivery_fee"].fillna(0)
# payment_mode: impute with mode (most common payment method)
df["payment_mode"] = df["payment_mode"].fillna(df["payment_mode"].mode()[0])

# 5. Outlier treatment on order_value (cap at 1st/99th percentile rather than drop)
low, high = df["order_value"].quantile([0.01, 0.99])
df["order_value"] = df["order_value"].clip(lower=low, upper=high)

# 6. Derived columns
df["gross_amount"] = df["order_value"] * df["quantity"]
df["discount_amount"] = df["gross_amount"] * df["discount_pct"] / 100
df["net_revenue"] = df["gross_amount"] - df["discount_amount"] + df["delivery_fee"]
df["month"] = df["order_date"].dt.to_period("M").astype(str)
df["year"] = df["order_date"].dt.year
df["weekday"] = df["order_date"].dt.day_name()
df["is_weekend"] = df["order_date"].dt.weekday >= 5

df = df.sort_values("order_date").reset_index(drop=True)

df.to_csv(OUT_PATH, index=False)
print(f"Cleaned shape: {df.shape}")
print(df.isna().sum())
print(df.head())
