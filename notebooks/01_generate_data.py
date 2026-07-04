"""Generate a realistic (intentionally messy) Zomato-style sales dataset."""
import numpy as np, pandas as pd
from datetime import datetime, timedelta

rng = np.random.default_rng(42)
N = 45000

cities_regions = {
    "Mumbai": "West", "Pune": "West", "Ahmedabad": "West",
    "Delhi": "North", "Gurgaon": "North", "Lucknow": "North", "Chandigarh": "North",
    "Bangalore": "South", "Hyderabad": "South", "Chennai": "South", "Kochi": "South",
    "Kolkata": "East", "Bhubaneswar": "East", "Patna": "East",
}
cities = list(cities_regions.keys())

categories = ["North Indian", "South Indian", "Chinese", "Fast Food", "Desserts",
              "Beverages", "Italian", "Biryani", "Street Food", "Healthy Food"]

payment_modes = ["UPI", "Credit Card", "Debit Card", "Cash on Delivery", "Wallet"]

restaurants = [f"Restaurant_{i}" for i in range(1, 251)]
rest_city = {r: rng.choice(cities) for r in restaurants}
rest_cat = {r: rng.choice(categories) for r in restaurants}

start_date = datetime(2023, 1, 1)
end_date = datetime(2025, 12, 31)
date_range_days = (end_date - start_date).days

# Build a smooth growth-weighted day-offset distribution (no artificial
# edge decay): business grows steadily over the 3 years, with festive
# season (Oct-Dec) and weekend bumps layered on top.
all_days = np.arange(0, date_range_days + 1)
all_dates = [start_date + timedelta(days=int(d)) for d in all_days]
growth_weight = 1 + 1.4 * (all_days / date_range_days)  # steady ~2.4x growth over 3 yrs
seasonal_weight = np.array([
    1.3 if d.month in (10, 11, 12) else (1.15 if d.month in (1, 8) else 1.0)
    for d in all_dates
])
weekend_weight = np.array([1.25 if d.weekday() >= 5 else 1.0 for d in all_dates])
day_weights = growth_weight * seasonal_weight * weekend_weight
day_weights = day_weights / day_weights.sum()

sampled_offsets = rng.choice(all_days, size=N, p=day_weights)

rows = []
for i in range(N):
    day_offset = int(sampled_offsets[i])
    order_date = start_date + timedelta(days=day_offset)
    month = order_date.month
    seasonal_boost = 1.3 if month in (10, 11, 12) else (1.15 if month in (1, 8) else 1.0)
    weekday_boost = 1.25 if order_date.weekday() >= 5 else 1.0

    restaurant = rng.choice(restaurants)
    city = rest_city[restaurant]
    region = cities_regions[city]
    category = rest_cat[restaurant]

    base_price = {
        "North Indian": 380, "South Indian": 220, "Chinese": 300, "Fast Food": 210,
        "Desserts": 180, "Beverages": 120, "Italian": 420, "Biryani": 340,
        "Street Food": 150, "Healthy Food": 350,
    }[category]

    order_value = max(80, rng.normal(base_price, base_price * 0.35) * seasonal_boost * weekday_boost)
    discount_pct = rng.choice([0, 0, 0, 5, 10, 15, 20, 25], p=[0.35,0.1,0.1,0.15,0.12,0.1,0.05,0.03])
    delivery_fee = rng.choice([0, 20, 29, 39, 49], p=[0.3,0.25,0.2,0.15,0.1])
    rating = round(min(5, max(1, rng.normal(4.1, 0.6))), 1)
    delivery_time = int(max(10, rng.normal(32, 10)))
    quantity = rng.choice([1,1,1,2,2,3], p=[0.35,0.2,0.15,0.15,0.1,0.05])

    payment = rng.choice(payment_modes, p=[0.42,0.18,0.15,0.15,0.10])
    is_new_customer = rng.choice([0,1], p=[0.72,0.28])

    row = {
        "order_id": f"ORD{100000+i}",
        "order_date": order_date.strftime("%Y-%m-%d") if rng.random() > 0.02 else order_date.strftime("%d/%m/%Y"),
        "restaurant_name": restaurant if rng.random() > 0.01 else restaurant.lower(),
        "city": city if rng.random() > 0.03 else city.upper(),
        "region": region,
        "food_category": category,
        "quantity": quantity,
        "order_value": round(order_value, 2),
        "discount_pct": discount_pct,
        "delivery_fee": delivery_fee,
        "payment_mode": payment,
        "rating": rating if rng.random() > 0.05 else np.nan,
        "delivery_time_min": delivery_time,
        "is_new_customer": is_new_customer,
    }
    rows.append(row)

df = pd.DataFrame(rows)

# inject messiness: duplicates, missing values, stray whitespace
dupe_idx = rng.choice(df.index, size=150, replace=False)
df = pd.concat([df, df.loc[dupe_idx]], ignore_index=True)

for col in ["delivery_fee", "payment_mode"]:
    miss_idx = rng.choice(df.index, size=int(len(df)*0.02), replace=False)
    df.loc[miss_idx, col] = np.nan

df["restaurant_name"] = df["restaurant_name"].apply(lambda x: f"  {x}" if rng.random() < 0.02 else x)

df.to_csv("/home/claude/zomato_project/data/zomato_sales_raw.csv", index=False)
print("Raw rows:", len(df))
print(df.head())
