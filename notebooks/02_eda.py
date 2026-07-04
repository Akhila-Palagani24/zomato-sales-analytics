"""
02_eda.py
Exploratory Data Analysis on cleaned Zomato sales data.
Generates charts into ../visuals/
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 120

df = pd.read_csv("../data/processed/zomato_sales_cleaned.csv", parse_dates=["order_date"])
VIS = "../visuals/"

# 1. Monthly revenue trend
monthly = df.groupby("month")["net_revenue"].sum().reset_index()
plt.figure(figsize=(10, 5))
plt.plot(monthly["month"], monthly["net_revenue"], marker="o", color="#e23744")
plt.xticks(rotation=60, fontsize=7)
plt.title("Monthly Net Revenue Trend")
plt.ylabel("Net Revenue (₹)")
plt.tight_layout()
plt.savefig(VIS + "01_monthly_revenue_trend.png")
plt.close()

# 2. Revenue by city
city_rev = df.groupby("city")["net_revenue"].sum().sort_values(ascending=False)
plt.figure(figsize=(10, 5))
sns.barplot(x=city_rev.values, y=city_rev.index, color="#e23744")
plt.title("Total Revenue by City")
plt.xlabel("Net Revenue (₹)")
plt.tight_layout()
plt.savefig(VIS + "02_revenue_by_city.png")
plt.close()

# 3. Revenue by region
region_rev = df.groupby("region")["net_revenue"].sum().sort_values(ascending=False)
plt.figure(figsize=(7, 5))
sns.barplot(x=region_rev.index, y=region_rev.values, color="#cb202d")
plt.title("Total Revenue by Region")
plt.ylabel("Net Revenue (₹)")
plt.tight_layout()
plt.savefig(VIS + "03_revenue_by_region.png")
plt.close()

# 4. Top food categories by revenue
cat_rev = df.groupby("food_category")["net_revenue"].sum().sort_values(ascending=False)
plt.figure(figsize=(10, 5))
sns.barplot(x=cat_rev.values, y=cat_rev.index, color="#ff6b35")
plt.title("Revenue by Food Category")
plt.xlabel("Net Revenue (₹)")
plt.tight_layout()
plt.savefig(VIS + "04_revenue_by_category.png")
plt.close()

# 5. Order value distribution
plt.figure(figsize=(8, 5))
sns.histplot(df["order_value"], bins=40, color="#e23744", kde=True)
plt.title("Order Value Distribution (after outlier capping)")
plt.xlabel("Order Value (₹)")
plt.tight_layout()
plt.savefig(VIS + "05_order_value_distribution.png")
plt.close()

# 6. Weekday vs weekend order volume
weekday_orders = df.groupby("weekday")["order_id"].count().reindex(
    ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
plt.figure(figsize=(9, 5))
sns.barplot(x=weekday_orders.index, y=weekday_orders.values, color="#2e86ab")
plt.title("Order Volume by Day of Week")
plt.ylabel("Number of Orders")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig(VIS + "06_orders_by_weekday.png")
plt.close()

# 7. Discount % vs average order count (does discount drive volume?)
disc_orders = df.groupby("discount_pct")["order_id"].count()
plt.figure(figsize=(8, 5))
sns.barplot(x=disc_orders.index, y=disc_orders.values, color="#f4a261")
plt.title("Order Count by Discount %")
plt.xlabel("Discount %")
plt.ylabel("Number of Orders")
plt.tight_layout()
plt.savefig(VIS + "07_discount_vs_orders.png")
plt.close()

# ---- Print key summary stats for README ----
print("=== KEY INSIGHTS ===")
print("Total net revenue:", round(df["net_revenue"].sum(), 2))
print("Total orders:", len(df))
print("Avg order value:", round(df["order_value"].mean(), 2))
print("\nTop 3 cities by revenue:\n", city_rev.head(3))
print("\nTop 3 categories by revenue:\n", cat_rev.head(3))
print("\nRevenue by region:\n", region_rev)
weekend_share = df[df["is_weekend"]]["net_revenue"].sum() / df["net_revenue"].sum() * 100
print(f"\nWeekend revenue share: {weekend_share:.1f}%")
yoy = df.groupby("year")["net_revenue"].sum()
print("\nYearly revenue:\n", yoy)
