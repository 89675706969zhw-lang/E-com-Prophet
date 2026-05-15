import re

import numpy as np
import pandas as pd


COLUMN_ALIASES = {
    "product_sku": [
        "product_sku", "sku", "article", "product_id", "item_id", "barcode",
        "артикул", "товар", "商品", "商品编码",
    ],
    "product_name": [
        "product_name", "name", "title", "item_name", "product_title",
        "название", "название_товара", "наименование", "наименование_товара",
        "商品名称", "商品名",
    ],
    "marketplace": [
        "marketplace", "platform", "channel", "market", "site",
        "площадка", "маркетплейс", "平台",
    ],
    "category": ["category", "product_category", "cat", "категория", "类别", "类目"],
    "subcategory": ["subcategory", "sub_category", "подкатегория", "子类目"],
    "brand": ["brand", "manufacturer", "бренд", "品牌"],
    "order_date": ["order_date", "date", "sale_date", "created_at", "дата", "日期"],
    "price": ["price", "original_price", "list_price", "цена", "原价"],
    "final_price": [
        "final_price", "sale_price", "unit_price", "selling_price", "price_after_discount",
        "цена_продажи", "成交价", "售价",
    ],
    "discount_percent": ["discount_percent", "discount", "discount_rate", "скидка", "折扣"],
    "cost": ["cost", "unit_cost", "purchase_price", "cogs", "себестоимость", "成本"],
    "quantity_sold": [
        "quantity_sold", "quantity", "qty", "sales", "sold_units", "units_sold",
        "количество", "продажи", "销量", "销售数量",
    ],
    "revenue": ["revenue", "sales_amount", "turnover", "gmv", "выручка", "销售额"],
    "commission_rate": ["commission_rate", "commission", "platform_fee_rate", "комиссия", "佣金率"],
    "advertising_cost": [
        "advertising_cost", "ad_cost", "ads_cost", "marketing_cost", "реклама", "广告费",
    ],
    "logistics_cost": ["logistics_cost", "shipping_cost", "delivery_cost", "логистика", "物流费"],
    "profit": ["profit", "gross_profit", "net_profit", "прибыль", "利润"],
    "margin_percent": ["margin_percent", "margin", "profit_margin", "маржа", "利润率"],
    "profit_per_item": ["profit_per_item", "unit_profit", "profit_unit", "прибыль_на_единицу", "单件利润"],
    "page_views": ["page_views", "views", "impressions", "visits", "просмотры", "浏览量"],
    "add_to_cart_count": ["add_to_cart_count", "add_to_cart", "cart_adds", "добавления_в_корзину", "加购数"],
    "conversion_rate": ["conversion_rate", "conversion", "cr", "конверсия", "转化率"],
    "is_promo": ["is_promo", "promo", "promotion", "акция", "промо", "促销"],
    "product_rating": ["product_rating", "rating", "score", "рейтинг", "评分"],
    "review_count": ["review_count", "reviews", "feedback_count", "отзывы", "评论数"],
    "marketing_roi": ["marketing_roi", "roi", "ad_roi", "romi", "广告roi"],
    "ad_efficiency": ["ad_efficiency", "ads_efficiency", "广告效率"],
    "current_stock": ["current_stock", "stock", "inventory", "остаток", "库存"],
    "reserved_stock": ["reserved_stock", "reserved", "blocked_stock", "резерв", "预留库存"],
    "safety_stock": ["safety_stock", "buffer_stock", "страховой_запас", "安全库存"],
}


FEATURE_REQUIREMENTS = {
    "forecast": ["product_sku", "marketplace", "quantity_sold", "final_price"],
    "supply": ["product_sku", "marketplace", "quantity_sold", "final_price", "profit_per_item", "margin_percent"],
    "promo": ["product_sku", "marketplace", "advertising_cost", "conversion_rate", "profit", "marketing_roi"],
    "price": ["product_sku", "marketplace", "final_price", "cost", "commission_rate"],
}

TEXT_COLUMNS = {
    "marketplace", "product_sku", "product_name", "category", "subcategory",
    "brand", "region", "city", "price_segment", "weekday_type", "text_features",
}

STANDARD_SAME_NAME_COLUMNS = {
    "month", "week", "day_of_week", "quarter", "is_holiday",
    "weekday_type", "price_segment", "city_tier",
}


def normalize_name(name: str) -> str:
    text = str(name).strip().lower()
    text = text.replace("%", "percent")
    return re.sub(r"[\s\-_.()/]+", "_", text).strip("_")


def _alias_lookup() -> dict[str, str]:
    lookup = {}
    for standard, aliases in COLUMN_ALIASES.items():
        lookup[normalize_name(standard)] = standard
        for alias in aliases:
            lookup[normalize_name(alias)] = standard
    for standard in STANDARD_SAME_NAME_COLUMNS:
        lookup[normalize_name(standard)] = standard
    return lookup


def detect_columns(columns) -> dict[str, str]:
    lookup = _alias_lookup()
    mapping = {}
    used_targets = set()
    for col in columns:
        normalized = normalize_name(col)
        target = lookup.get(normalized)
        if target and target not in used_targets:
            mapping[col] = target
            used_targets.add(target)
    return mapping


def _to_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series
    cleaned = (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace(" ", "", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def standardize_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    original_columns = list(df.columns)
    mapping = detect_columns(original_columns)
    data = df.rename(columns=mapping).copy()

    data = coerce_types(data)
    data, derived_columns = derive_columns(data)
    meaningful_columns = set(data.columns)
    availability = check_availability(data, meaningful_columns)
    data = ensure_runtime_columns(data)

    schema_info = {
        "original_columns": original_columns,
        "column_mapping": mapping,
        "unmapped_columns": [c for c in original_columns if c not in mapping],
        "derived_columns": sorted(derived_columns),
        "availability": availability,
    }
    data.attrs["schema_info"] = schema_info
    return data, schema_info


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    if "order_date" in data.columns:
        data["order_date"] = pd.to_datetime(data["order_date"], errors="coerce")

    for col in data.columns:
        if col in TEXT_COLUMNS or col == "order_date":
            continue
        converted = _to_numeric(data[col])
        if converted.notna().sum() > 0:
            data[col] = converted

    if "is_promo" in data.columns:
        if not pd.api.types.is_bool_dtype(data["is_promo"]):
            promo_text = data["is_promo"].astype(str).str.strip().str.lower()
            data["is_promo"] = promo_text.isin(["1", "true", "yes", "y", "promo", "акция", "да", "是"])

    return data


def derive_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, set[str]]:
    data = df.copy()
    derived = set()

    if "final_price" not in data.columns and "price" in data.columns:
        data["final_price"] = data["price"]
        derived.add("final_price")

    if "price" not in data.columns and "final_price" in data.columns:
        data["price"] = data["final_price"]
        derived.add("price")

    if {"price", "final_price"}.issubset(data.columns) and "discount_percent" not in data.columns:
        price = data["price"].replace(0, np.nan)
        data["discount_percent"] = ((data["price"] - data["final_price"]) / price * 100).fillna(0)
        derived.add("discount_percent")

    if {"final_price", "quantity_sold"}.issubset(data.columns) and "revenue" not in data.columns:
        data["revenue"] = data["final_price"] * data["quantity_sold"]
        derived.add("revenue")

    if {"revenue", "commission_rate"}.issubset(data.columns) and "commission_cost" not in data.columns:
        rate = data["commission_rate"].where(data["commission_rate"] <= 1, data["commission_rate"] / 100)
        data["commission_cost"] = data["revenue"] * rate
        data["commission_rate"] = rate
        derived.add("commission_cost")

    if "quantity_sold" in data.columns:
        qty = data["quantity_sold"].replace(0, np.nan)
        if "logistics_cost" in data.columns and "logistics_cost_total" not in data.columns:
            data["logistics_cost_total"] = data["logistics_cost"]
        if "advertising_cost" in data.columns and "advertising_cost_total" not in data.columns:
            data["advertising_cost_total"] = data["advertising_cost"]
        if "profit" in data.columns and "profit_per_item" not in data.columns:
            data["profit_per_item"] = (data["profit"] / qty).replace([np.inf, -np.inf], np.nan)
            derived.add("profit_per_item")

    if "profit" not in data.columns and {"revenue", "cost", "quantity_sold"}.issubset(data.columns):
        commission = data["commission_cost"] if "commission_cost" in data.columns else 0
        logistics = data["logistics_cost"] if "logistics_cost" in data.columns else 0
        ads = data["advertising_cost"] if "advertising_cost" in data.columns else 0
        data["profit"] = data["revenue"] - data["cost"] * data["quantity_sold"] - commission - logistics - ads
        derived.add("profit")

    if "profit_per_item" not in data.columns and {"profit", "quantity_sold"}.issubset(data.columns):
        qty = data["quantity_sold"].replace(0, np.nan)
        data["profit_per_item"] = (data["profit"] / qty).replace([np.inf, -np.inf], np.nan)
        derived.add("profit_per_item")

    if "margin_percent" not in data.columns and {"profit", "revenue"}.issubset(data.columns):
        revenue = data["revenue"].replace(0, np.nan)
        data["margin_percent"] = (data["profit"] / revenue * 100).replace([np.inf, -np.inf], np.nan)
        derived.add("margin_percent")

    if "conversion_rate" not in data.columns and {"quantity_sold", "page_views"}.issubset(data.columns):
        views = data["page_views"].replace(0, np.nan)
        data["conversion_rate"] = (data["quantity_sold"] / views).replace([np.inf, -np.inf], np.nan)
        derived.add("conversion_rate")

    if "marketing_roi" not in data.columns and {"profit", "advertising_cost"}.issubset(data.columns):
        ads = data["advertising_cost"].replace(0, np.nan)
        data["marketing_roi"] = (data["profit"] / ads).replace([np.inf, -np.inf], np.nan)
        derived.add("marketing_roi")

    if "ad_efficiency" not in data.columns and {"revenue", "advertising_cost"}.issubset(data.columns):
        ads = data["advertising_cost"].replace(0, np.nan)
        data["ad_efficiency"] = (data["revenue"] / ads).replace([np.inf, -np.inf], np.nan)
        derived.add("ad_efficiency")

    if "order_date" in data.columns:
        date = pd.to_datetime(data["order_date"], errors="coerce")
        if "year" not in data.columns:
            data["year"] = date.dt.year
            derived.add("year")
        if "month" not in data.columns:
            data["month"] = date.dt.month
            derived.add("month")
        if "week" not in data.columns:
            data["week"] = date.dt.isocalendar().week.astype("float")
            derived.add("week")
        if "day_of_week" not in data.columns:
            data["day_of_week"] = date.dt.dayofweek
            derived.add("day_of_week")
        if "quarter" not in data.columns:
            data["quarter"] = date.dt.quarter
            derived.add("quarter")
        if "weekday_type" not in data.columns:
            data["weekday_type"] = np.where(date.dt.dayofweek >= 5, "weekend", "weekday")
            derived.add("weekday_type")

    if "price_segment" not in data.columns and "final_price" in data.columns:
        try:
            data["price_segment"] = pd.qcut(
                data["final_price"].rank(method="first"),
                q=min(4, max(1, data["final_price"].notna().sum())),
                labels=False,
                duplicates="drop",
            ).astype("float").map({0: "low", 1: "mid", 2: "high", 3: "premium"}).fillna("unknown")
            derived.add("price_segment")
        except ValueError:
            data["price_segment"] = "unknown"
            derived.add("price_segment")

    return data, derived


def ensure_runtime_columns(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    row_count = len(data)
    defaults = {
        "marketplace": "Uploaded",
        "product_sku": [f"SKU-{i + 1:06d}" for i in range(row_count)],
        "product_name": "Unknown",
        "category": "Unknown",
        "subcategory": "Unknown",
        "brand": "Unknown",
        "price": 0.0,
        "final_price": 0.0,
        "discount_percent": 0.0,
        "cost": 0.0,
        "quantity_sold": 0.0,
        "revenue": 0.0,
        "commission_rate": 0.0,
        "advertising_cost": 0.0,
        "logistics_cost": 0.0,
        "profit": 0.0,
        "margin_percent": 0.0,
        "profit_per_item": 0.0,
        "page_views": 0.0,
        "add_to_cart_count": 0.0,
        "conversion_rate": 0.01,
        "is_promo": False,
        "product_rating": 4.0,
        "review_count": 0.0,
        "marketing_roi": 0.0,
        "ad_efficiency": 0.0,
        "city_tier": 1.0,
        "month": 1.0,
        "week": 1.0,
        "day_of_week": 0.0,
        "quarter": 1.0,
        "is_holiday": False,
        "price_segment": "unknown",
        "weekday_type": "weekday",
    }
    for col, default in defaults.items():
        if col not in data.columns:
            data[col] = default

    numeric_cols = [c for c in data.columns if c not in TEXT_COLUMNS and c != "order_date"]
    for col in numeric_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce")
        if data[col].isna().all():
            data[col] = 0
        else:
            data[col] = data[col].fillna(data[col].median())

    for col in TEXT_COLUMNS:
        if col in data.columns:
            data[col] = data[col].fillna("Unknown").astype(str)

    if "is_promo" in data.columns:
        data["is_promo"] = data["is_promo"].fillna(False).astype(bool)

    return data


def check_availability(df: pd.DataFrame, meaningful_columns: set[str] | None = None) -> dict:
    columns = meaningful_columns or set(df.columns)
    availability = {}
    for feature, required in FEATURE_REQUIREMENTS.items():
        missing = [col for col in required if col not in columns]
        availability[feature] = {
            "available": not missing,
            "missing": missing,
        }
    return availability


def schema_summary(schema_info: dict) -> pd.DataFrame:
    mapping = schema_info.get("column_mapping", {})
    rows = [{"original_column": src, "standard_column": dst} for src, dst in mapping.items()]
    if not rows:
        return pd.DataFrame(columns=["original_column", "standard_column"])
    return pd.DataFrame(rows)


def availability_summary(schema_info: dict) -> pd.DataFrame:
    availability = schema_info.get("availability", {})
    rows = []
    labels = {
        "forecast": "Demand forecast",
        "supply": "Supply planning",
        "promo": "Advertising and promo",
        "price": "Price recommendation",
    }
    for key, info in availability.items():
        rows.append({
            "function": labels.get(key, key),
            "available": "Yes" if info.get("available") else "No",
            "missing_or_reason": ", ".join(info.get("missing", [])),
        })
    return pd.DataFrame(rows)
