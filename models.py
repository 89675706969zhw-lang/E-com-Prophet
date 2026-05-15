import numpy as np
import pandas as pd

from schema_utils import (
    ensure_runtime_columns,
    normalize_name,
)


def _safe_output(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    available = [col for col in columns if col in data.columns]
    return data[available].copy()


def _safe_ratio(numerator: float, denominator: float, default: float = 1.0) -> float:
    if pd.isna(numerator) or pd.isna(denominator) or denominator <= 0:
        return default
    return float(numerator / denominator)


def _clipped_factor(value: float, lower: float = 0.75, upper: float = 1.25) -> float:
    if pd.isna(value) or not np.isfinite(value):
        return 1.0
    return float(np.clip(value, lower, upper))


def _real_columns_from_schema(df: pd.DataFrame) -> set[str]:
    schema_info = df.attrs.get("schema_info", {})
    real_columns = set(schema_info.get("column_mapping", {}).values())
    real_columns.update(schema_info.get("derived_columns", []))

    standard_fields = {
        "order_date", "quantity_sold", "final_price",
        "conversion_rate", "product_rating", "is_promo",
        "month", "quarter", "day_of_week", "weekday_type", "is_holiday",
    }
    original_normalized = {
        normalize_name(col) for col in schema_info.get("original_columns", [])
    }
    for field in standard_fields:
        if normalize_name(field) in original_normalized:
            real_columns.add(field)

    if not real_columns:
        real_columns = set(df.columns)
    return real_columns


def _forecast_context_factors(
    data: pd.DataFrame,
    recent: pd.DataFrame,
    real_columns: set[str],
) -> tuple[dict[str, float], str]:
    factors = {
        "trend_factor": 1.0,
        "seasonality_factor": 1.0,
        "holiday_factor": 1.0,
        "weekday_factor": 1.0,
    }
    used = ["recent sales pace"]

    if "order_date" in real_columns and "order_date" in data.columns and data["order_date"].notna().any():
        max_date = data["order_date"].max()
        last_7 = data[data["order_date"] >= max_date - pd.Timedelta(days=6)]
        recent_days = max(1, int(recent["order_date"].dt.normalize().nunique())) if not recent.empty else 1
        last_7_days = max(1, int(last_7["order_date"].dt.normalize().nunique())) if not last_7.empty else 1
        recent_daily = recent["quantity_sold"].sum() / recent_days if not recent.empty else 0
        last_7_daily = last_7["quantity_sold"].sum() / last_7_days if not last_7.empty else 0
        factors["trend_factor"] = _clipped_factor(_safe_ratio(last_7_daily, recent_daily), 0.7, 1.3)
        used.append("7-day trend")

        if "month" in real_columns and "month" in data.columns and data["month"].notna().any():
            current_month = int(max_date.month)
            month_avg = data[data["month"] == current_month]["quantity_sold"].mean()
            overall_avg = data["quantity_sold"].mean()
            factors["seasonality_factor"] = _clipped_factor(_safe_ratio(month_avg, overall_avg), 0.85, 1.15)
            used.append("month seasonality")
        elif "quarter" in real_columns and "quarter" in data.columns and data["quarter"].notna().any():
            current_quarter = int(max_date.quarter)
            quarter_avg = data[data["quarter"] == current_quarter]["quantity_sold"].mean()
            overall_avg = data["quantity_sold"].mean()
            factors["seasonality_factor"] = _clipped_factor(_safe_ratio(quarter_avg, overall_avg), 0.9, 1.1)
            used.append("quarter seasonality")

    if "is_holiday" in real_columns and "is_holiday" in data.columns and data["is_holiday"].notna().any():
        holiday_sales = data[data["is_holiday"].astype(bool)]["quantity_sold"].mean()
        normal_sales = data[~data["is_holiday"].astype(bool)]["quantity_sold"].mean()
        factors["holiday_factor"] = _clipped_factor(_safe_ratio(holiday_sales, normal_sales), 0.9, 1.1)
        used.append("holiday effect")

    if "weekday_type" in real_columns and "weekday_type" in data.columns and data["weekday_type"].notna().any():
        recent_weekend_share = recent["weekday_type"].astype(str).str.lower().eq("weekend").mean()
        all_weekend_share = data["weekday_type"].astype(str).str.lower().eq("weekend").mean()
        factors["weekday_factor"] = _clipped_factor(1 + (recent_weekend_share - all_weekend_share) * 0.2, 0.95, 1.05)
        used.append("weekday/weekend mix")
    elif "day_of_week" in real_columns and "day_of_week" in data.columns and data["day_of_week"].notna().any():
        recent_weekend_share = recent["day_of_week"].isin([5, 6]).mean()
        all_weekend_share = data["day_of_week"].isin([5, 6]).mean()
        factors["weekday_factor"] = _clipped_factor(1 + (recent_weekend_share - all_weekend_share) * 0.2, 0.95, 1.05)
        used.append("weekday/weekend mix")

    return factors, ", ".join(used)


def estimate_sku_forecast(
    df: pd.DataFrame,
    horizon: int,
    combine_marketplaces: bool = False,
    marketplace_scope: str | None = None,
) -> pd.DataFrame:
    """Return demand forecast at the SKU decision level."""
    if df.empty:
        return pd.DataFrame()

    real_columns = _real_columns_from_schema(df)
    data = ensure_runtime_columns(df)
    if "order_date" in data.columns:
        data["order_date"] = pd.to_datetime(data["order_date"], errors="coerce")

    avg_conversion = data["conversion_rate"].replace(0, np.nan).mean()
    if pd.isna(avg_conversion) or avg_conversion <= 0:
        avg_conversion = 0.01
    avg_rating = data["product_rating"].replace(0, np.nan).mean()
    if pd.isna(avg_rating) or avg_rating <= 0:
        avg_rating = 4.0

    if combine_marketplaces:
        group_cols = ["product_sku", "product_name", "category", "subcategory", "brand"]
    else:
        group_cols = ["marketplace", "product_sku", "product_name", "category", "subcategory", "brand"]
    if "order_date" in data.columns and data["order_date"].notna().any():
        max_date = data["order_date"].max()
        recent = data[data["order_date"] >= max_date - pd.Timedelta(days=29)].copy()
        if recent.empty:
            recent = data.copy()
        observed_days = max(1, min(30, int(recent["order_date"].dt.normalize().nunique())))
    else:
        recent = data.copy()
        observed_days = 30

    context_factors, forecast_method_note = _forecast_context_factors(data, recent, real_columns)
    base = recent.groupby(group_cols, as_index=False).agg(
        historical_quantity_sold=("quantity_sold", "sum"),
        historical_revenue=("revenue", "sum"),
        historical_profit=("profit", "sum"),
        avg_final_price=("final_price", "mean"),
        avg_profit_per_item=("profit_per_item", "mean"),
        avg_margin_percent=("margin_percent", "mean"),
        avg_conversion_rate=("conversion_rate", "mean"),
        avg_product_rating=("product_rating", "mean"),
        promo_share=("is_promo", "mean"),
        source_rows=("quantity_sold", "size"),
    )
    base["marketplace_scope"] = marketplace_scope or ("All marketplaces" if combine_marketplaces else "Selected marketplace")
    if combine_marketplaces:
        base["marketplace"] = base["marketplace_scope"]
    base["observed_days"] = observed_days

    base["observed_days"] = base["observed_days"].fillna(1).clip(lower=1)
    base["avg_daily_sales"] = base["historical_quantity_sold"] / base["observed_days"]
    for factor_name, factor_value in context_factors.items():
        base[factor_name] = factor_value
    base["forecast_method_note"] = forecast_method_note

    conversion_factor = (base["avg_conversion_rate"] / avg_conversion).replace([np.inf, -np.inf], 1)
    rating_factor = (base["avg_product_rating"] / avg_rating).replace([np.inf, -np.inf], 1)
    promo_factor = 1 + base["promo_share"].fillna(0).clip(0, 1) * 0.08

    raw_forecast = (
        base["avg_daily_sales"]
        * horizon
        * np.clip(conversion_factor.fillna(1), 0.5, 2.0)
        * np.clip(rating_factor.fillna(1), 0.7, 1.3)
        * promo_factor
        * base["trend_factor"]
        * base["seasonality_factor"]
        * base["holiday_factor"]
        * base["weekday_factor"]
    )
    base["forecast_quantity"] = np.floor(raw_forecast.clip(lower=0) + 0.5).astype(int)
    base["expected_revenue"] = base["forecast_quantity"] * base["avg_final_price"]
    base["expected_profit"] = base["forecast_quantity"] * base["avg_profit_per_item"]

    confidence_conditions = [
        (base["observed_days"] >= 21) & (base["source_rows"] >= 10),
        (base["observed_days"] >= 7) & (base["source_rows"] >= 3),
    ]
    base["confidence_level"] = np.select(confidence_conditions, ["High", "Medium"], default="Low")

    columns = [
        "marketplace", "marketplace_scope", "product_sku", "product_name", "category", "subcategory", "brand",
        "historical_quantity_sold", "avg_daily_sales", "forecast_quantity",
        "expected_revenue", "expected_profit", "avg_margin_percent",
        "avg_conversion_rate", "avg_product_rating", "promo_share",
        "trend_factor", "seasonality_factor", "holiday_factor", "weekday_factor",
        "observed_days", "source_rows", "confidence_level", "forecast_method_note",
    ]
    return _safe_output(base, columns).sort_values(
        ["expected_profit", "forecast_quantity"], ascending=False
    )


def build_supply_plan(df: pd.DataFrame, horizon: int, target_margin: int) -> pd.DataFrame:
    forecast = estimate_sku_forecast(df, horizon, combine_marketplaces=False)
    if forecast.empty:
        return forecast

    forecast = forecast.rename(columns={"avg_margin_percent": "margin_percent"})
    has_stock = {"current_stock", "reserved_stock"}.issubset(df.columns)
    profitable = (forecast["expected_profit"] > 0) & (forecast["margin_percent"] >= target_margin)

    if has_stock:
        stock_source = ensure_runtime_columns(df)
        stock = (
            stock_source.groupby(["marketplace", "product_sku"], as_index=False)
            .agg(
                current_stock=("current_stock", "max"),
                reserved_stock=("reserved_stock", "max"),
            )
        )
        if "safety_stock" in df.columns:
            safety_stock = (
                stock_source.groupby(["marketplace", "product_sku"], as_index=False)
                .agg(safety_stock=("safety_stock", "max"))
            )
            stock = stock.merge(safety_stock, on=["marketplace", "product_sku"], how="left")
        forecast = forecast.merge(stock, on=["marketplace", "product_sku"], how="left")
        forecast["current_stock"] = forecast["current_stock"].fillna(0)
        forecast["reserved_stock"] = forecast["reserved_stock"].fillna(0)
        forecast["available_stock"] = (forecast["current_stock"] - forecast["reserved_stock"]).clip(lower=0)
        if "safety_stock" not in forecast.columns:
            forecast["safety_stock"] = np.ceil(forecast["forecast_quantity"] * 0.15)
        else:
            forecast["safety_stock"] = forecast["safety_stock"].fillna(
                np.ceil(forecast["forecast_quantity"] * 0.15)
            )
        recommended = forecast["forecast_quantity"] + forecast["safety_stock"] - forecast["available_stock"]
        forecast["recommended_supply_quantity"] = np.where(
            profitable, np.ceil(recommended).clip(lower=0), 0
        ).astype(int)
        forecast["supply_logic"] = "stock_based"
    else:
        forecast["recommended_supply_quantity"] = np.where(
            profitable,
            np.ceil(forecast["forecast_quantity"] * 1.15),
            0,
        ).astype(int)
        forecast["supply_logic"] = "simplified_no_stock"

    conditions = [
        profitable & (forecast["margin_percent"] >= target_margin + 10),
        profitable,
    ]
    forecast["priority_level"] = np.select(conditions, ["High", "Medium"], default="Low")
    priority_map = {"High": 1, "Medium": 2, "Low": 3}
    forecast["priority_rank"] = forecast["priority_level"].map(priority_map)

    columns = [
        "marketplace", "product_sku", "product_name", "category", "subcategory",
        "forecast_quantity", "current_stock", "reserved_stock", "available_stock",
        "safety_stock", "recommended_supply_quantity",
        "expected_revenue", "expected_profit", "margin_percent",
        "priority_level", "supply_logic", "priority_rank",
    ]
    result = _safe_output(forecast, columns).sort_values(
        ["priority_rank", "expected_profit"], ascending=[True, False]
    )
    return result.drop(columns=["priority_rank"], errors="ignore")


def analyze_promo(
    df: pd.DataFrame,
    roi_threshold: float = 1.0,
    min_margin_after_ads: float = 10.0,
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    result = ensure_runtime_columns(df)
    median_conversion = result["conversion_rate"].median()
    if pd.isna(median_conversion):
        median_conversion = 0

    ads = result["advertising_cost"].clip(lower=0)
    revenue = result["revenue"].replace(0, np.nan)
    result["profit_after_ads"] = result["profit"]
    result["ad_spend_share"] = (ads / revenue * 100).replace([np.inf, -np.inf], np.nan).fillna(0)
    result["marketing_roi"] = (result["profit_after_ads"] / ads.replace(0, np.nan)).replace(
        [np.inf, -np.inf],
        np.nan,
    ).fillna(0)
    result["ad_efficiency"] = (result["revenue"] / ads.replace(0, np.nan)).replace(
        [np.inf, -np.inf],
        np.nan,
    ).fillna(0)
    result["promo_status"] = np.where(result["is_promo"].astype(bool), "Promo", "No promo")

    has_ads = ads > 0
    result["has_ads"] = has_ads
    result["ad_profitability_status"] = np.select(
        [
            ~has_ads,
            has_ads
            & (result["marketing_roi"] >= roi_threshold)
            & (result["profit_after_ads"] > 0)
            & (result["margin_percent"] >= min_margin_after_ads),
            has_ads & (result["marketing_roi"] >= 0) & (result["profit_after_ads"] >= 0),
        ],
        ["No ads", "Profitable", "Break-even"],
        default="Loss-making",
    )

    result["discount_risk_level"] = np.select(
        [
            (result["discount_percent"] >= 30) | (result["margin_percent"] < min_margin_after_ads),
            (result["discount_percent"] >= 15) | (result["margin_percent"] < min_margin_after_ads + 5),
        ],
        ["High", "Medium"],
        default="Low",
    )

    cond_stop = (
        has_ads
        & (
            (result["profit_after_ads"] < 0)
        | (has_ads & (result["marketing_roi"] < roi_threshold) & (result["ad_profitability_status"] != "Break-even"))
        )
    )
    cond_promote = (
        has_ads
        & (result["profit_after_ads"] > 0)
        & (result["marketing_roi"] >= roi_threshold)
        & (result["conversion_rate"] >= median_conversion)
        & (result["margin_percent"] >= min_margin_after_ads)
        & (result["discount_risk_level"] != "High")
    )
    cond_reduce_discount = (
        has_ads
        & (result["profit_after_ads"] > 0)
        & (result["discount_risk_level"] == "High")
    )
    cond_monitor = (
        has_ads
        & (result["profit_after_ads"] >= 0)
        & (
            (result["ad_profitability_status"] == "Break-even")
            | (result["discount_risk_level"] == "Medium")
            | (has_ads & (result["marketing_roi"] >= 0))
        )
    )
    cond_organic_opportunity = (
        ~has_ads
        & (result["profit_after_ads"] > 0)
        & (result["margin_percent"] >= min_margin_after_ads)
    )
    result["recommendation"] = np.select(
        [cond_stop, cond_reduce_discount, cond_promote, cond_monitor, cond_organic_opportunity],
        [
            "Stop or reduce ads",
            "Reduce discount",
            "Promote more",
            "Keep, monitor discount",
            "Organic opportunity",
        ],
        default="No ad action",
    )
    priority_map = {
        "Stop or reduce ads": 1,
        "Reduce discount": 2,
        "Promote more": 3,
        "Keep, monitor discount": 4,
        "Monitor": 5,
        "Organic opportunity": 6,
        "No ad action": 7,
    }
    result["promo_priority_rank"] = result["recommendation"].map(priority_map).fillna(8)

    columns = [
        "marketplace", "product_sku", "product_name", "category", "brand",
        "promo_status", "has_ads", "discount_percent", "advertising_cost",
        "marketing_roi", "ad_efficiency", "ad_spend_share",
        "conversion_rate", "revenue", "profit", "profit_after_ads",
        "margin_percent", "ad_profitability_status", "discount_risk_level",
        "recommendation", "promo_priority_rank",
    ]
    output = _safe_output(result, columns).sort_values(
        ["promo_priority_rank", "advertising_cost", "profit_after_ads"],
        ascending=[True, False, False],
    )
    return output.drop(columns=["promo_priority_rank"], errors="ignore")


def recommend_prices(df: pd.DataFrame, target_margin: int) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    result = ensure_runtime_columns(df)
    qty = result["quantity_sold"].replace(0, 1)
    unit_logistics = result["logistics_cost"] / qty
    unit_ads = result["advertising_cost"] / qty
    unit_cost = result["cost"] + unit_logistics + unit_ads

    commission = result["commission_rate"].where(result["commission_rate"] <= 1, result["commission_rate"] / 100)
    denominator = (1 - commission - target_margin / 100).clip(lower=0.05)
    result["unit_logistics_cost"] = unit_logistics
    result["unit_advertising_cost"] = unit_ads
    result["unit_total_cost"] = unit_cost
    result["target_margin_percent"] = float(target_margin)
    result["recommended_price"] = np.ceil(unit_cost / denominator).astype(int)
    result["price_delta"] = result["recommended_price"] - result["final_price"]
    result["price_delta_percent"] = (
        result["price_delta"] / result["final_price"].replace(0, np.nan) * 100
    ).replace([np.inf, -np.inf], np.nan).fillna(0)
    result["current_margin_gap"] = (target_margin - result["margin_percent"]).fillna(0)
    result["commission_amount_at_recommended_price"] = result["recommended_price"] * commission
    result["target_margin_amount"] = result["recommended_price"] * target_margin / 100
    result["expected_margin_after_price_change"] = (
        (result["recommended_price"] - unit_cost - result["recommended_price"] * commission)
        / result["recommended_price"].replace(0, np.nan)
        * 100
    ).fillna(0)

    result["price_action"] = np.select(
        [
            result["recommended_price"] > result["final_price"] * 1.05,
            result["recommended_price"] < result["final_price"] * 0.95,
        ],
        ["Increase price", "Price can be reduced"],
        default="Keep price",
    )

    columns = [
        "marketplace", "product_sku", "product_name", "category", "brand",
        "price", "final_price", "cost", "commission_rate",
        "logistics_cost", "advertising_cost", "unit_logistics_cost",
        "unit_advertising_cost", "unit_total_cost", "margin_percent",
        "target_margin_percent", "current_margin_gap",
        "recommended_price", "price_delta", "price_delta_percent",
        "expected_margin_after_price_change",
        "commission_amount_at_recommended_price", "target_margin_amount",
        "price_action",
    ]
    return _safe_output(result, columns).sort_values(["margin_percent", "recommended_price"], ascending=[True, False])
