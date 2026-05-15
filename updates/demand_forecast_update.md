# Demand Forecast Update

Date: 2026-05-14

## Scope

This update focuses on the first feature: `Прогнозирование спроса` / demand forecasting.

The goal was to make the flow clearer for users and reduce misleading output in the forecast screen.

## Updated User Flow

1. Load the default `transactions_optimized.csv` or upload a CSV file.
2. Standardize and validate the CSV fields.
3. Select the demand forecast feature.
4. Select analysis mode:
   - all products
   - one product
5. Select marketplace.
6. Select category.
7. Select SKU only when one-product mode is active.
8. Select forecast horizon:
   - 14 days
   - 30 days
9. Run the analysis.
10. Review SKU-level forecast results and download CSV or Markdown output.

## Main Changes

### 1. Forecast Output Is Now SKU-Level

Before this update, the demand forecast table was based on transaction-level rows. That made the output harder to use because marketplace sellers usually make decisions at the SKU level.

The forecast now aggregates data by:

- `marketplace`
- `product_sku`
- `category`
- `subcategory`
- `brand`

The output now includes decision-oriented fields such as:

- `historical_quantity_sold`
- `avg_daily_sales`
- `forecast_quantity`
- `expected_revenue`
- `expected_profit`
- `confidence_level`

### 2. Demand Forecast Uses Recent Sales Pace

The new demand forecast function uses the latest 30-day window when `order_date` is available.

The basic logic is:

```text
recent historical quantity
    / observed days in the recent window
    * selected forecast horizon
    * conversion/rating/promo adjustment
```

This is still a heuristic forecast, not a full time-series model. It is more realistic than the previous transaction-row forecast, but it should still be presented as an operational estimate.

### 3. Irrelevant Sidebar Controls Are Hidden

For the demand forecast feature, these controls are now hidden:

- target margin
- training sample size

Reason:

- target margin belongs to supply planning and price recommendation
- training sample size belongs to ML model training

This makes the demand forecast flow easier to understand and avoids implying that those controls affect the demand forecast.

### 4. Daily Uniform Split Chart Removed From Demand Forecast

The demand forecast screen no longer shows the uniform daily split line chart.

Reason:

That chart divided the total forecast evenly across days. It was useful as an illustration, but it could be misunderstood as a real daily time-series forecast.

The chart remains available in other places where the app still uses it as an illustrative helper, but the main demand forecast screen now avoids this ambiguity.

## Current Limitations

The demand forecast is still not a full statistical forecasting model.

Known limitations:

- It does not model seasonality deeply.
- It does not forecast day-by-day demand.
- It does not separate organic demand from promo-driven demand.
- SKU confidence is often low when each SKU appears only a few times in the source data.
- The result quality depends heavily on whether uploaded CSV files include reliable `order_date`, `quantity_sold`, `final_price`, and `profit_per_item` fields.

## Recommended Next Step

The next major improvement should be a proper time-aware validation and forecasting layer:

- aggregate sales by SKU and date
- train on earlier dates
- validate on later dates
- compare heuristic forecast against ML/time-series baselines
- show forecast error metrics to the user

