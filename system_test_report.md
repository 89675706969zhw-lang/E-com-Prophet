# E-com Prophet System Test Report

## Test Summary

The Streamlit GUI system was tested with the existing dataset `transactions_optimized.csv`.

Dataset:

- Rows: 60,000
- Columns: 45
- Main target for ML: `quantity_sold`

## Fixed Issue

The previous error was caused by `pandas.DataFrame.to_markdown()`, which requires the optional dependency `tabulate`.

Fix:

- Removed dependency on `to_markdown()`.
- Added a custom Markdown table generator.
- The Markdown report can now be generated without `tabulate`.

## Tested Functions

### 1. Demand Forecast

Status: Passed

Output table includes:

- marketplace
- product_sku
- category
- forecast_quantity
- expected_revenue
- expected_profit
- margin_percent

### 2. Supply Planning

Status: Passed

Output table includes:

- forecast_quantity
- recommended_supply_quantity
- expected_profit
- priority_level

The system can generate separate CSV files for marketplaces:

- supply_plan_wildberries.csv
- supply_plan_ozon.csv
- supply_plan_yandex_market.csv

### 3. Advertising and Promo Analysis

Status: Passed

Output table includes:

- advertising_cost
- marketing_roi
- conversion_rate
- profit
- recommendation

Recommendations:

- Promote more
- Monitor
- Stop or reduce

### 4. Price Recommendation

Status: Passed

Output table includes:

- current price
- final price
- cost
- commission
- logistics
- advertising cost
- recommended_price
- price_action

### 5. ML Model and Metrics

Status: Passed

Compared models:

- Linear Regression
- Random Forest
- Gradient Boosting

Metrics from the test sample:

| Model | MAE | RMSE | R2 |
| --- | --- | --- | --- |
| Gradient Boosting | 0.6236 | 0.8419 | 0.7038 |
| Random Forest | 0.7186 | 0.9581 | 0.6164 |
| Linear Regression | 1.0029 | 1.2662 | 0.3300 |

Best model in the test:

- Gradient Boosting

## Export Test

Status: Passed

The system can export:

- CSV tables
- Markdown reports

The ML report includes:

- analysis parameters
- data summary
- model metrics table
- best model
- conclusion

## Forecast period (UI)

The sidebar option **«Период прогноза» / 预测周期** (14 or 30 days) scales forecast quantities in calculations. The GUI now shows:

- an active **horizon metric** on demand forecast, supply planning, and ML forecast screens
- a **bar chart** comparing total predicted volume at **14 vs 30 days** aggregated by marketplace (heuristic forecast; separate chart for ML)
- a **line chart** of the selected horizon’s total forecast split **evenly per day**, with a caption that this is illustrative, not a full time-series day-ahead model

Markdown reports include a short note explaining how the period affects results.

## Current Notes

- The app runs locally with Streamlit.
- The current project is a working prototype suitable for demonstration.
- The ML module uses scikit-learn models for stability.
- CatBoost and XGBoost are not included in the GUI yet to avoid installation issues before the presentation.

## Run Command

```powershell
streamlit run app.py
```

Local URL:

```text
http://localhost:8502
```
