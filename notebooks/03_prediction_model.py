"""
03_prediction_model.py
Forecasts future weekly revenue.

Models compared:
  - Baseline: 4-week trailing moving average
  - Linear Regression: trend + lag features (extrapolates growth trend)
  - Random Forest: same features (shown for comparison + limitation discussion)

Note: daily revenue is too sparse/noisy (~30 orders/day) for a stable
signal, so forecasting is done at weekly granularity -- also the more
realistic horizon for actual business planning (staffing, inventory, promos).

Evaluates with MAE and RMSE, and forecasts the next 8 weeks.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

df = pd.read_csv("../data/processed/zomato_sales_cleaned.csv", parse_dates=["order_date"])

# Aggregate to weekly revenue, keeping only complete (7-day) weeks
daily = df.groupby("order_date")["net_revenue"].sum().asfreq("D").fillna(0).reset_index()
daily.columns = ["date", "revenue"]
weekly_agg = daily.resample("W-MON", on="date").agg(revenue=("revenue", "sum"), n_days=("revenue", "count"))
weekly = weekly_agg[weekly_agg["n_days"] == 7].reset_index()[["date", "revenue"]]

# Feature engineering
weekly["week_index"] = np.arange(len(weekly))
weekly["month"] = weekly["date"].dt.month
for lag in [1, 2, 4]:
    weekly[f"lag_{lag}"] = weekly["revenue"].shift(lag)
weekly["rolling_4"] = weekly["revenue"].shift(1).rolling(4).mean()
weekly = weekly.dropna().reset_index(drop=True)

features = ["week_index", "lag_1", "lag_2", "rolling_4"]
X, y = weekly[features], weekly["revenue"]

split = int(len(weekly) * 0.85)
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

# Baseline: 4-week moving average
baseline_pred = weekly["rolling_4"].iloc[split:]
baseline_mae = mean_absolute_error(y_test, baseline_pred)
baseline_rmse = mean_squared_error(y_test, baseline_pred) ** 0.5

# Linear Regression (primary model -- captures linear trend, extrapolates)
lr_model = LinearRegression()
lr_model.fit(X_train, y_train)
lr_pred = lr_model.predict(X_test)
lr_mae = mean_absolute_error(y_test, lr_pred)
lr_rmse = mean_squared_error(y_test, lr_pred) ** 0.5

# Random Forest (comparison only -- tree models can't extrapolate a trend
# beyond the range seen in training, so on strongly growing series they
# tend to underpredict on unseen future periods)
rf_model = RandomForestRegressor(n_estimators=300, max_depth=4, min_samples_leaf=3, random_state=42)
rf_model.fit(X_train, y_train)
rf_pred = rf_model.predict(X_test)
rf_mae = mean_absolute_error(y_test, rf_pred)
rf_rmse = mean_squared_error(y_test, rf_pred) ** 0.5

print("=== MODEL EVALUATION (weekly revenue, holdout test) ===")
print(f"Baseline (4-wk MA)   -> MAE: {baseline_mae:.2f}, RMSE: {baseline_rmse:.2f}")
print(f"Linear Regression    -> MAE: {lr_mae:.2f}, RMSE: {lr_rmse:.2f}")
print(f"Random Forest        -> MAE: {rf_mae:.2f}, RMSE: {rf_rmse:.2f}")
improvement = (baseline_mae - lr_mae) / baseline_mae * 100
print(f"Linear Regression improves on baseline MAE by {improvement:.1f}%")
print("(Random Forest underperforms here because tree models cannot")
print(" extrapolate beyond the value range seen during training -- on a")
print(" steadily growing series, Linear Regression's trend term wins.)")

model = lr_model  # chosen model for forecasting

# Plot actual vs predicted
plt.figure(figsize=(11, 5))
plt.plot(weekly["date"].iloc[split:], y_test.values, label="Actual", color="#333333")
plt.plot(weekly["date"].iloc[split:], lr_pred, label="Linear Regression", color="#e23744")
plt.plot(weekly["date"].iloc[split:], rf_pred, label="Random Forest", color="#2e86ab", linestyle="--")
plt.plot(weekly["date"].iloc[split:], baseline_pred.values, label="Baseline (4wk MA)", linestyle=":", color="#999999")
plt.legend()
plt.title("Actual vs Predicted Weekly Revenue (Test Set)")
plt.ylabel("Net Revenue (\u20b9)")
plt.tight_layout()
plt.savefig("../visuals/08_actual_vs_predicted.png")
plt.close()

# Forecast next 8 weeks with the chosen model (Linear Regression)
last_known = weekly.copy()
future_rows = []
for i in range(8):
    next_date = last_known["date"].iloc[-1] + pd.Timedelta(weeks=1)
    row = {
        "date": next_date,
        "week_index": last_known["week_index"].iloc[-1] + 1,
        "month": next_date.month,
        "lag_1": last_known["revenue"].iloc[-1],
        "lag_2": last_known["revenue"].iloc[-2],
        "lag_4": last_known["revenue"].iloc[-4],
        "rolling_4": last_known["revenue"].iloc[-4:].mean(),
    }
    pred = model.predict(pd.DataFrame([row])[features])[0]
    row["revenue"] = pred
    future_rows.append(row)
    last_known = pd.concat([last_known, pd.DataFrame([row])], ignore_index=True)

forecast_df = pd.DataFrame(future_rows)[["date", "revenue"]]
forecast_df.to_csv("../data/processed/revenue_forecast_next_8_weeks.csv", index=False)

plt.figure(figsize=(11, 5))
plt.plot(weekly["date"].iloc[-26:], weekly["revenue"].iloc[-26:], label="Historical", color="#333333")
plt.plot(forecast_df["date"], forecast_df["revenue"], label="8-Week Forecast", color="#e23744")
plt.axvline(weekly["date"].iloc[-1], linestyle=":", color="gray")
plt.legend()
plt.title("Next 8-Week Revenue Forecast (Linear Regression)")
plt.ylabel("Net Revenue (\u20b9)")
plt.tight_layout()
plt.savefig("../visuals/09_8_week_forecast.png")
plt.close()

print("\nForecast total (next 8 weeks): \u20b9", round(forecast_df["revenue"].sum(), 2))
print(forecast_df.head())
