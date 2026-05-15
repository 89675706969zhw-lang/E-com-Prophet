import pandas as pd
import streamlit as st
import altair as alt

import models
from config import TEXT
from schema_utils import availability_summary, normalize_name, schema_summary


MARKETPLACE_COLORS = {
    "OZON": "#2563eb",
    "WildBerries": "#db2777",
    "YandexMarket": "#f59e0b",
}


FEATURE_FIELD_USAGE = {
    "forecast": {
        "core": ["product_sku", "marketplace", "order_date", "quantity_sold", "final_price"],
        "adjustment": [
            "conversion_rate", "product_rating", "is_promo",
            "month", "quarter", "day_of_week", "weekday_type", "is_holiday",
        ],
        "output": [
            "forecast_quantity", "expected_revenue", "expected_profit", "confidence_level",
            "trend_factor", "seasonality_factor", "holiday_factor", "weekday_factor",
        ],
    },
    "supply": {
        "core": ["product_sku", "marketplace", "quantity_sold", "final_price", "profit_per_item", "margin_percent"],
        "adjustment": ["current_stock", "reserved_stock", "safety_stock"],
        "output": ["recommended_supply_quantity", "priority_level", "supply_logic"],
    },
    "promo": {
        "core": ["product_sku", "marketplace", "advertising_cost", "conversion_rate", "profit", "marketing_roi"],
        "adjustment": ["discount_percent", "is_promo", "ad_efficiency"],
        "output": [
            "recommendation", "promo_status", "has_ads", "ad_profitability_status",
            "discount_risk_level", "profit_after_ads", "ad_spend_share",
        ],
    },
    "price": {
        "core": ["product_sku", "marketplace", "final_price", "cost", "commission_rate"],
        "adjustment": ["logistics_cost", "advertising_cost", "margin_percent"],
        "output": [
            "recommended_price", "expected_margin_after_price_change", "price_action",
            "unit_total_cost", "price_delta", "price_delta_percent",
            "current_margin_gap", "target_margin_percent",
        ],
    },
}


def tr(key: str) -> str:
    return TEXT[st.session_state["lang"]][key]


def _available_fields_for_schema(schema_info: dict, feature_key: str) -> set[str]:
    available = set(schema_info.get("column_mapping", {}).values())
    available.update(schema_info.get("derived_columns", []))

    usage = FEATURE_FIELD_USAGE.get(feature_key, {})
    expected_fields = {
        field
        for fields in usage.values()
        for field in fields
    }
    original_normalized = {
        normalize_name(col) for col in schema_info.get("original_columns", [])
    }
    for field in expected_fields:
        if normalize_name(field) in original_normalized:
            available.add(field)
    return available


def show_active_horizon(period: int) -> None:
    st.metric(tr("horizon_label"), f"{period} {tr('days_unit')}")


def show_feature_field_usage(feature_key: str, schema_info: dict, lang: str) -> None:
    usage = FEATURE_FIELD_USAGE.get(feature_key)
    if not usage:
        return

    available = _available_fields_for_schema(schema_info, feature_key)
    availability = schema_info.get("availability", {}).get(feature_key, {})
    missing = availability.get("missing", [])

    title = "Поля, используемые текущей функцией" if lang == "ru" else "当前功能使用字段"
    with st.expander(title, expanded=False):
        labels = {
            "core": "Основные поля" if lang == "ru" else "核心输入字段",
            "adjustment": "Дополнительные поля для уточнения прогноза" if lang == "ru" else "淇/杈呭姪瀛楁",
            "output": "Результаты расчета" if lang == "ru" else "系统计算结果",
        }
        rows = []
        for group, fields in usage.items():
            for field in fields:
                if group == "output":
                    status = "calculated" if lang == "ru" else "绯荤粺璁＄畻"
                elif field in available:
                    status = "available" if lang == "ru" else "鍙敤"
                else:
                    status = "missing/default" if lang == "ru" else "缂哄け/榛樿琛ラ綈"
                rows.append({"group": labels[group], "field": field, "status": status})
        st.dataframe(pd.DataFrame(rows), width="stretch")
        if missing:
            st.warning(
                "Недостающие обязательные поля: " + ", ".join(map(str, missing))
                if lang == "ru"
                else "缺少必需字段: " + ", ".join(map(str, missing))
            )
        else:
            st.success(
                "Обязательные поля для этой функции доступны."
                if lang == "ru"
                else "当前功能所需的必需字段可用。"
            )

        mapped_or_derived = _available_fields_for_schema(schema_info, feature_key)
        defaulted_adjustments = [
            field for field in usage.get("adjustment", [])
            if field not in mapped_or_derived
        ]
        if defaulted_adjustments:
            st.warning(
                "Часть дополнительных полей отсутствует и будет заменена значениями по умолчанию: "
                + ", ".join(defaulted_adjustments)
                + ". Результаты стоит интерпретировать осторожно."
                if lang == "ru"
                else "閮ㄥ垎淇/杈呭姪瀛楁缂哄け锛岀郴缁熶細浣跨敤榛樿鍊硷細"
                + ", ".join(defaulted_adjustments)
                + "。请谨慎解释结果。"
            )


def show_marketplace_overview(filtered: pd.DataFrame, lang: str) -> None:
    if filtered.empty:
        st.warning(
            "Нет строк, соответствующих выбранным фильтрам."
            if lang == "ru"
            else "没有符合当前筛选条件的数据。"
        )
        return

    summary = (
        filtered.groupby("marketplace", as_index=False)
        .agg(rows=("marketplace", "size"), revenue=("revenue", "sum"), profit=("profit", "sum"))
        .sort_values("revenue", ascending=False)
    )
    total_revenue = summary["revenue"].sum()
    summary["revenue_share"] = (summary["revenue"] / total_revenue).fillna(0) if total_revenue else 0
    st.dataframe(summary, width="stretch")

    color_scale = alt.Scale(
        domain=list(MARKETPLACE_COLORS.keys()),
        range=list(MARKETPLACE_COLORS.values()),
    )
    revenue_base = alt.Chart(summary).encode(
        theta=alt.Theta("revenue:Q"),
        color=alt.Color("marketplace:N", scale=color_scale, legend=alt.Legend(title=None)),
    )
    revenue_pie = (
        revenue_base
        .mark_arc(innerRadius=55, outerRadius=120, stroke="white", strokeWidth=2)
        .encode(
            tooltip=[
                alt.Tooltip("marketplace:N", title="Marketplace"),
                alt.Tooltip("revenue:Q", title="Выручка", format=",.0f"),
                alt.Tooltip("revenue_share:Q", title="Доля", format=".1%"),
            ],
        )
        .properties(height=320)
    )
    revenue_chart = revenue_pie
    profit_bar = (
        alt.Chart(summary)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("marketplace:N", sort="-y", title=None),
            y=alt.Y("profit:Q", title=None),
            color=alt.Color("marketplace:N", scale=color_scale, legend=None),
            tooltip=[
                alt.Tooltip("marketplace:N", title="Marketplace"),
                alt.Tooltip("profit:Q", title="Прибыль", format=",.0f"),
            ],
        )
        .properties(height=320)
    )
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Выручка по маркетплейсам" if lang == "ru" else "各平台销售额")
        st.altair_chart(revenue_chart, width="stretch")
    with c2:
        st.caption("Прибыль по маркетплейсам" if lang == "ru" else "各平台利润")
        st.altair_chart(profit_bar, width="stretch")


def show_single_product_data_overview(filtered: pd.DataFrame, lang: str) -> None:
    if filtered.empty:
        st.warning(
            "Нет строк, соответствующих выбранному товару."
            if lang == "ru"
            else "没有符合当前商品筛选的数据。"
        )
        return

    first = filtered.iloc[0]
    product_name = str(first.get("product_name", "Unknown"))
    marketplace = ", ".join(sorted(filtered.get("marketplace", pd.Series(dtype=str)).astype(str).unique()))
    revenue = float(filtered["revenue"].sum()) if "revenue" in filtered.columns else 0
    profit = float(filtered["profit"].sum()) if "profit" in filtered.columns else 0
    ads = float(filtered["advertising_cost"].sum()) if "advertising_cost" in filtered.columns else 0
    quantity = float(filtered["quantity_sold"].sum()) if "quantity_sold" in filtered.columns else 0
    unit_ads = ads / quantity if quantity else 0
    margin = (profit / revenue * 100) if revenue else 0

    st.subheader("Карточка выбранного товара" if lang == "ru" else "所选商品卡片")
    st.caption(product_name)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Marketplace" if lang == "ru" else "平台", marketplace)
    c2.metric("Выручка" if lang == "ru" else "收入", f"{revenue:,.0f}")
    c3.metric("Прибыль" if lang == "ru" else "利润", f"{profit:,.0f}")
    c4.metric("Маржа" if lang == "ru" else "利润率", f"{margin:.2f}%")
    c5.metric("Реклама на единицу" if lang == "ru" else "单件广告费", f"{unit_ads:,.2f}")

    if len(filtered) > 1:
        st.info(
            "По выбранному товару найдено несколько строк; показатели показаны в агрегированном виде."
            if lang == "ru"
            else "当前商品包含多条记录，指标以汇总口径展示。"
        )


def show_forecast_output_note(lang: str) -> None:
    if lang == "ru":
        st.info("Выделенные столбцы рассчитаны системой как результат прогноза.")
    else:
        st.info("高亮列为系统计算得到的预测结果。")


def show_forecast_factor_explanation(result: pd.DataFrame, lang: str) -> None:
    title = "Факторы прогноза" if lang == "ru" else "预测因素"
    with st.expander(title, expanded=False):
        if lang == "ru":
            st.write(
                "Прогноз остается эвристическим, но дополнительно учитывает тренд последних 7 дней, "
                "сезонность месяца, праздничный эффект, структуру рабочих/выходных дней, промо, "
                "конверсию и рейтинг."
            )
        else:
            st.write(
                "当前预测仍是启发式业务预测，但已额外考虑最近 7 天趋势、月份季节性、"
                "节假日影响、工作日/周末结构、促销、转化率和评分。"
            )

        factor_labels = {
            "trend_factor": "7-day trend" if lang == "ru" else "最近 7 天趋势",
            "seasonality_factor": "Seasonality" if lang == "ru" else "季节性",
            "holiday_factor": "Holiday effect" if lang == "ru" else "节假日影响",
            "weekday_factor": "Weekday mix" if lang == "ru" else "工作日/周末结构",
        }
        available = [col for col in factor_labels if col in result.columns]
        if result.empty or not available:
            return

        first_row = result.iloc[0]
        chart_rows = []
        for col in available:
            value = pd.to_numeric(pd.Series([first_row.get(col)]), errors="coerce").iloc[0]
            if pd.isna(value):
                continue
            chart_rows.append({
                "factor": factor_labels[col],
                "factor_value": float(value),
                "impact_percent": (float(value) - 1.0) * 100,
                "direction": "Рост" if float(value) >= 1 else "Снижение",
            })

        if not chart_rows:
            return

        chart_df = pd.DataFrame(chart_rows)
        chart_df["impact_label"] = chart_df["impact_percent"].map(lambda v: f"{v:+.2f}%")
        chart_df["factor_value_label"] = chart_df["factor_value"].map(lambda v: f"{v:.4f}")
        source_rows = pd.to_numeric(pd.Series([first_row.get("source_rows")]), errors="coerce").iloc[0]
        confidence_level = str(first_row.get("confidence_level", "")).strip().lower()
        no_factor_impact = chart_df["impact_percent"].abs().max() <= 0.01
        low_data_single_product = (
            no_factor_impact
            and (
                (not pd.isna(source_rows) and source_rows <= 1)
                or confidence_level == "low"
            )
        )
        if low_data_single_product:
            st.warning(
                "Для выбранного товара недостаточно истории, чтобы оценить тренд, сезонность "
                "и календарные факторы. Прогноз рассчитан по доступным продажам, поэтому "
                "уверенность низкая."
                if lang == "ru"
                else "当前商品历史数据不足，无法可靠评估趋势、季节性和日历因素。预测基于现有销售记录计算，因此置信度较低。"
            )
            return

        direction_domain = ["Рост", "Снижение"]
        direction_range = ["#16a34a", "#dc2626"]
        max_abs_impact = max(1.0, float(chart_df["impact_percent"].abs().max()))

        bars = (
            alt.Chart(chart_df)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
            .encode(
                x=alt.X(
                    "impact_percent:Q",
                    title="Impact on forecast, %",
                    scale=alt.Scale(domain=[-max_abs_impact * 1.15, max_abs_impact * 1.15]),
                    axis=alt.Axis(format="+.1f"),
                ),
                y=alt.Y("factor:N", sort="-x", title=None),
                color=alt.Color(
                    "direction:N",
                    scale=alt.Scale(domain=direction_domain, range=direction_range),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("factor:N", title="Factor"),
                    alt.Tooltip("factor_value_label:N", title="Factor value"),
                    alt.Tooltip("impact_label:N", title="Impact"),
                ],
            )
        )
        baseline = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(
            color="#9ca3af",
            strokeDash=[4, 4],
        ).encode(x="x:Q")

        st.altair_chart((bars + baseline).properties(height=220), width="stretch")
        st.caption(
            "Базовый уровень = 1.0. Значения выше 1 увеличивают прогноз, ниже 1 уменьшают прогноз."
            if lang == "ru"
            else "基准值 = 1.0。高于 1 会提高预测，低于 1 会降低预测。"
        )


def show_selected_forecast_summary(result: pd.DataFrame, period: int, lang: str) -> None:
    if result.empty:
        return

    total_quantity = int(result["forecast_quantity"].sum()) if "forecast_quantity" in result.columns else 0
    total_revenue = float(result["expected_revenue"].sum()) if "expected_revenue" in result.columns else 0
    total_profit = float(result["expected_profit"].sum()) if "expected_profit" in result.columns else 0
    forecasted_items = int(result["product_sku"].nunique()) if "product_sku" in result.columns else len(result)
    confidence = "N/A"
    if "confidence_level" in result.columns and not result["confidence_level"].empty:
        confidence = str(result["confidence_level"].mode().iloc[0])

    st.subheader(
        f"Ключевые показатели на {period} дней"
        if lang == "ru"
        else f"{period} 天关键预测指标"
    )
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Прогноз продаж, количество" if lang == "ru" else "预测销量（数量）", f"{total_quantity:,}")
    c2.metric("Товаров в прогнозе" if lang == "ru" else "预测商品数", f"{forecasted_items:,}")
    c3.metric("Ожидаемая выручка" if lang == "ru" else "预计收入", f"{total_revenue:,.0f}")
    c4.metric("Ожидаемая прибыль" if lang == "ru" else "预计利润", f"{total_profit:,.0f}")
    c5.metric("Уверенность" if lang == "ru" else "置信度", confidence)


def show_forecast_charts(
    result: pd.DataFrame,
    filtered: pd.DataFrame,
    period: int,
    lang: str,
    combine_marketplaces: bool = False,
    marketplace_scope: str | None = None,
) -> None:
    if result.empty or "forecast_quantity" not in result.columns:
        st.info(
            "Нет данных для графиков прогноза спроса."
            if lang == "ru"
            else "没有可用于需求预测图表的数据。"
        )
        return

    chart_df = result.copy()
    for col in ["forecast_quantity", "expected_revenue", "expected_profit", "avg_daily_sales"]:
        if col in chart_df.columns:
            chart_df[col] = pd.to_numeric(chart_df[col], errors="coerce").fillna(0)

    confidence_domain = ["High", "Medium", "Low"]
    confidence_range = ["#16a34a", "#f59e0b", "#ef4444"]
    confidence_scale = alt.Scale(domain=confidence_domain, range=confidence_range)

    if {"product_name", "product_sku", "forecast_quantity", "confidence_level"}.issubset(chart_df.columns):
        top_df = chart_df.sort_values("forecast_quantity", ascending=False).head(20).copy()
        top_df["product_label"] = top_df["product_name"].where(
            top_df["product_name"].astype(str).str.lower() != "unknown",
            top_df["product_sku"],
        )
        top_chart = (
            alt.Chart(top_df)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
            .encode(
                x=alt.X("forecast_quantity:Q", title="Прогноз спроса" if lang == "ru" else "预测需求"),
                y=alt.Y("product_label:N", sort="-x", title=None),
                color=alt.Color(
                    "confidence_level:N",
                    scale=confidence_scale,
                    title="Уверенность" if lang == "ru" else "置信度",
                ),
                tooltip=[
                    alt.Tooltip("product_label:N", title="Product"),
                    alt.Tooltip("marketplace:N", title="Marketplace"),
                    alt.Tooltip("category:N", title="Category"),
                    alt.Tooltip("forecast_quantity:Q", title="Прогноз спроса" if lang == "ru" else "预测需求", format=",.0f"),
                    alt.Tooltip("expected_revenue:Q", title="Ожидаемая выручка" if lang == "ru" else "预计收入", format=",.0f"),
                    alt.Tooltip("confidence_level:N", title="Уверенность" if lang == "ru" else "置信度"),
                ],
            )
            .properties(height=max(280, min(620, len(top_df) * 28)))
        )
        st.subheader("Топ товаров по прогнозу спроса" if lang == "ru" else "预测需求最高的商品")
        st.altair_chart(top_chart, width="stretch")

    if {"category", "forecast_quantity", "expected_revenue"}.issubset(chart_df.columns):
        category_df = (
            chart_df.groupby("category", as_index=False)
            .agg(
                forecast_quantity=("forecast_quantity", "sum"),
                expected_revenue=("expected_revenue", "sum"),
            )
            .sort_values("forecast_quantity", ascending=False)
        )
        total_forecast = float(category_df["forecast_quantity"].sum())
        category_df["share"] = category_df["forecast_quantity"] / total_forecast if total_forecast else 0
        category_df["metric"] = "forecast_share"
        contribution = (
            alt.Chart(category_df)
            .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, size=42)
            .encode(
                x=alt.X("share:Q", stack="normalize", title="Доля прогноза" if lang == "ru" else "预测占比", axis=alt.Axis(format="%")),
                y=alt.Y("metric:N", axis=None, title=None),
                color=alt.Color("category:N", title="Категория" if lang == "ru" else "类别"),
                tooltip=[
                    alt.Tooltip("category:N", title="Category"),
                    alt.Tooltip("forecast_quantity:Q", title="Прогноз спроса" if lang == "ru" else "预测需求", format=",.0f"),
                    alt.Tooltip("expected_revenue:Q", title="Ожидаемая выручка" if lang == "ru" else "预计收入", format=",.0f"),
                    alt.Tooltip("share:Q", title="Доля" if lang == "ru" else "占比", format=".1%"),
                ],
            )
            .properties(height=150)
        )
        st.subheader("Вклад категорий в прогноз" if lang == "ru" else "各类别预测贡献")
        st.caption(
            "Полоса показывает, какие категории дают основную долю прогнозируемого спроса."
            if lang == "ru"
            else "该图显示各类别对预测需求的贡献比例。"
        )
        st.altair_chart(contribution, width="stretch")

    if {"avg_daily_sales", "forecast_quantity", "expected_revenue", "confidence_level"}.issubset(chart_df.columns):
        bubble_df = chart_df.head(1000).copy()
        bubble = (
            alt.Chart(bubble_df)
            .mark_circle(opacity=0.72)
            .encode(
                x=alt.X("avg_daily_sales:Q", title="Средние продажи в день" if lang == "ru" else "平均日销量"),
                y=alt.Y("forecast_quantity:Q", title="Прогноз спроса" if lang == "ru" else "预测需求"),
                size=alt.Size(
                    "expected_revenue:Q",
                    title="Ожидаемая выручка" if lang == "ru" else "预计收入",
                    scale=alt.Scale(range=[40, 900]),
                ),
                color=alt.Color(
                    "confidence_level:N",
                    scale=confidence_scale,
                    title="Уверенность" if lang == "ru" else "置信度",
                ),
                tooltip=[
                    alt.Tooltip("product_name:N", title="Product"),
                    alt.Tooltip("marketplace:N", title="Marketplace"),
                    alt.Tooltip("avg_daily_sales:Q", title="Avg daily sales", format=".2f"),
                    alt.Tooltip("forecast_quantity:Q", title="Прогноз спроса" if lang == "ru" else "预测需求", format=",.0f"),
                    alt.Tooltip("expected_revenue:Q", title="Ожидаемая выручка" if lang == "ru" else "预计收入", format=",.0f"),
                    alt.Tooltip("confidence_level:N", title="Уверенность" if lang == "ru" else "置信度"),
                ],
            )
            .properties(height=340)
        )
        st.subheader("Уверенность и масштаб прогноза" if lang == "ru" else "置信度与预测规模")
        st.altair_chart(bubble, width="stretch")


def show_forecast_result_table(result: pd.DataFrame) -> None:
    display_order = [
        "product_name",
        "marketplace",
        "category",
        "brand",
        "historical_quantity_sold",
        "avg_daily_sales",
        "forecast_quantity",
        "expected_revenue",
        "expected_profit",
        "confidence_level",
    ]
    display_cols = [col for col in display_order if col in result.columns]
    extra_cols = [
        col for col in result.columns
        if col not in display_cols and col not in {"product_sku", "marketplace_scope"}
    ]
    display = result[display_cols + extra_cols].head(300).copy()
    forecast_styles = {
        "forecast_quantity": "background-color: #bfdbfe; color: #172554",
        "expected_revenue": "background-color: #bbf7d0; color: #052e16",
        "expected_profit": "background-color: #bbf7d0; color: #052e16",
        "confidence_level": "background-color: #fde68a; color: #451a03",
        "trend_factor": "background-color: #ede9fe; color: #2e1065",
        "seasonality_factor": "background-color: #ede9fe; color: #2e1065",
        "holiday_factor": "background-color: #ede9fe; color: #2e1065",
        "weekday_factor": "background-color: #ede9fe; color: #2e1065",
    }

    def highlight_forecast_columns(_: pd.Series) -> list[str]:
        return [forecast_styles.get(col, "") for col in display.columns]

    st.dataframe(display.style.apply(highlight_forecast_columns, axis=1), width="stretch")


def show_single_forecast_diagnosis(result: pd.DataFrame, period: int, lang: str) -> None:
    if result.empty:
        return

    row = result.iloc[0]

    def number_value(column: str) -> float:
        if column not in result.columns:
            return 0.0
        value = pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").iloc[0]
        return 0.0 if pd.isna(value) else float(value)

    forecast_quantity = int(round(number_value("forecast_quantity")))
    historical_quantity = int(round(number_value("historical_quantity_sold")))
    avg_daily_sales = number_value("avg_daily_sales")
    expected_revenue = number_value("expected_revenue")
    expected_profit = number_value("expected_profit")
    observed_days = int(round(number_value("observed_days")))
    source_rows = int(round(number_value("source_rows")))
    confidence = str(row.get("confidence_level", "N/A"))
    confidence_key = confidence.strip().lower()
    method_note = str(row.get("forecast_method_note", "")).strip()

    st.subheader(
        "Диагностика прогноза выбранного товара"
        if lang == "ru"
        else "所选商品预测诊断"
    )

    if confidence_key == "high":
        message = (
            f"Прогноз: ожидается {forecast_quantity:,} продаж за {period} дней. Уверенность высокая."
            if lang == "ru"
            else f"预测：未来 {period} 天预计销售 {forecast_quantity:,} 件，置信度较高。"
        )
        st.success(message)
    elif confidence_key == "medium":
        message = (
            f"Прогноз: ожидается {forecast_quantity:,} продаж за {period} дней. Уверенность средняя."
            if lang == "ru"
            else f"预测：未来 {period} 天预计销售 {forecast_quantity:,} 件，置信度中等。"
        )
        st.info(message)
    else:
        message = (
            f"Прогноз: ожидается {forecast_quantity:,} продаж за {period} дней, но уверенность низкая."
            if lang == "ru"
            else f"预测：未来 {period} 天预计销售 {forecast_quantity:,} 件，但置信度较低。"
        )
        st.warning(message)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Прогноз спроса" if lang == "ru" else "预测需求", f"{forecast_quantity:,}")
    c2.metric("Исторические продажи" if lang == "ru" else "历史销量", f"{historical_quantity:,}")
    c3.metric("Средние продажи в день" if lang == "ru" else "平均日销量", f"{avg_daily_sales:.2f}")
    c4.metric("Ожидаемая выручка" if lang == "ru" else "预计收入", f"{expected_revenue:,.0f}")
    c5.metric("Ожидаемая прибыль" if lang == "ru" else "预计利润", f"{expected_profit:,.0f}")
    c6.metric("Уверенность" if lang == "ru" else "置信度", confidence)

    if lang == "ru":
        bullets = [
            f"Горизонт прогноза: {period} дней.",
            f"Расчет основан на {historical_quantity:,} исторических продажах; наблюдаемый период: {observed_days:,} дней, строк данных: {source_rows:,}.",
            f"Средний темп продаж: {avg_daily_sales:.2f} шт. в день.",
        ]
        if method_note:
            bullets.append(f"Использованные факторы: {method_note}.")
        if confidence_key == "low":
            bullets.append("Низкая уверенность означает, что для товара недостаточно истории для устойчивой оценки тренда и сезонности.")
    else:
        bullets = [
            f"预测周期：{period} 天。",
            f"计算基于 {historical_quantity:,} 件历史销量；观察期 {observed_days:,} 天，数据行数 {source_rows:,}。",
            f"平均销售速度：每天 {avg_daily_sales:.2f} 件。",
        ]
        if method_note:
            bullets.append(f"使用因素：{method_note}。")
        if confidence_key == "low":
            bullets.append("低置信度表示该商品历史数据不足，趋势和季节性判断不够稳定。")

    for bullet in bullets:
        st.markdown(f"- {bullet}")


def show_single_forecast_result_table(result: pd.DataFrame, lang: str) -> None:
    if result.empty:
        st.dataframe(result, width="stretch")
        return

    display_order = [
        "marketplace",
        "historical_quantity_sold",
        "avg_daily_sales",
        "forecast_quantity",
        "expected_revenue",
        "expected_profit",
        "confidence_level",
        "observed_days",
        "source_rows",
        "forecast_method_note",
    ]
    display_cols = [col for col in display_order if col in result.columns]
    display = result[display_cols].head(300).copy()

    forecast_styles = {
        "forecast_quantity": "background-color: #bfdbfe; color: #172554; font-weight: 700",
        "expected_revenue": "background-color: #bbf7d0; color: #052e16",
        "expected_profit": "background-color: #bbf7d0; color: #052e16",
        "confidence_level": "background-color: #fde68a; color: #451a03; font-weight: 700",
    }

    def highlight_forecast_columns(_: pd.Series) -> list[str]:
        return [forecast_styles.get(col, "") for col in display.columns]

    st.dataframe(display.style.apply(highlight_forecast_columns, axis=1), width="stretch")


def show_supply_result_table(result: pd.DataFrame) -> None:
    display_order = [
        "product_name",
        "marketplace",
        "category",
        "subcategory",
        "forecast_quantity",
        "recommended_supply_quantity",
        "current_stock",
        "reserved_stock",
        "available_stock",
        "safety_stock",
        "expected_profit",
        "margin_percent",
        "priority_level",
        "supply_logic",
    ]
    display_cols = [col for col in display_order if col in result.columns]
    extra_cols = [
        col for col in result.columns
        if col not in display_cols and col != "product_sku"
    ]
    display = result[display_cols + extra_cols].head(300).copy()
    column_styles = {
        "recommended_supply_quantity": "background-color: #fed7aa; color: #7c2d12; font-weight: 700",
        "forecast_quantity": "background-color: #dbeafe; color: #1e3a8a",
        "margin_percent": "background-color: #fef3c7; color: #78350f",
    }
    priority_styles = {
        "High": "background-color: #bbf7d0; color: #14532d; font-weight: 700",
        "Medium": "background-color: #fde68a; color: #78350f; font-weight: 700",
        "Low": "background-color: #fecaca; color: #7f1d1d; font-weight: 700",
    }

    def highlight_supply_columns(row: pd.Series) -> list[str]:
        styles = []
        for col in display.columns:
            if col == "priority_level":
                styles.append(priority_styles.get(str(row.get(col, "")), ""))
            else:
                styles.append(column_styles.get(col, ""))
        return styles

    st.dataframe(display.style.apply(highlight_supply_columns, axis=1), width="stretch")


def _format_supply_logic(value: str, lang: str) -> str:
    labels = {
        "stock_based": "С учетом остатков" if lang == "ru" else "考虑库存",
        "simplified_no_stock": "Упрощенно, без остатков" if lang == "ru" else "简化模式，无库存",
    }
    return labels.get(str(value), str(value))


def show_single_supply_result_table(result: pd.DataFrame, lang: str) -> None:
    if result.empty:
        st.dataframe(result, width="stretch")
        return

    display_order = [
        "marketplace",
        "forecast_quantity",
        "recommended_supply_quantity",
        "margin_percent",
        "expected_profit",
        "priority_level",
        "supply_logic",
    ]
    display_cols = [col for col in display_order if col in result.columns]
    display = result[display_cols].head(300).copy()

    if "supply_logic" in display.columns:
        display["supply_logic"] = display["supply_logic"].map(lambda value: _format_supply_logic(value, lang))

    display = display.rename(columns={
        "marketplace": "Маркетплейс" if lang == "ru" else "平台",
        "forecast_quantity": "Прогноз спроса" if lang == "ru" else "预测需求",
        "recommended_supply_quantity": "Рекомендовано к поставке" if lang == "ru" else "建议补货量",
        "margin_percent": "Маржа, %" if lang == "ru" else "利润率，%",
        "expected_profit": "Ожидаемая прибыль" if lang == "ru" else "预计利润",
        "priority_level": "Приоритет" if lang == "ru" else "优先级",
        "supply_logic": "Логика расчета" if lang == "ru" else "计算逻辑",
    })

    output_labels = {
        "Прогноз спроса", "Рекомендовано к поставке", "Маржа, %",
        "预测需求", "建议补货量", "利润率，%",
    }
    priority_col = "Приоритет" if lang == "ru" else "优先级"
    output_style = "background-color: #dbeafe; color: #1e3a8a; font-weight: 700"
    supply_style = "background-color: #fed7aa; color: #7c2d12; font-weight: 700"
    margin_style = "background-color: #fef3c7; color: #78350f"
    priority_styles = {
        "High": "background-color: #bbf7d0; color: #14532d; font-weight: 700",
        "Medium": "background-color: #fde68a; color: #78350f; font-weight: 700",
        "Low": "background-color: #fecaca; color: #7f1d1d; font-weight: 700",
    }

    def highlight_single_supply_columns(row: pd.Series) -> list[str]:
        styles = []
        for col in display.columns:
            if col == priority_col:
                styles.append(priority_styles.get(str(row.get(col, "")), ""))
            elif col in {"Рекомендовано к поставке", "建议补货量"}:
                styles.append(supply_style)
            elif col in {"Маржа, %", "利润率，%"}:
                styles.append(margin_style)
            elif col in output_labels:
                styles.append(output_style)
            else:
                styles.append("")
        return styles

    st.dataframe(display.style.apply(highlight_single_supply_columns, axis=1), width="stretch")


def _supply_product_label(row: pd.Series) -> str:
    product_name = str(row.get("product_name", "")).strip()
    if product_name and product_name.lower() != "unknown":
        return product_name
    sku = str(row.get("product_sku", "")).strip()
    return sku or "Unknown"


def show_supply_summary(result: pd.DataFrame, lang: str) -> None:
    if result.empty:
        return

    recommended_qty = pd.to_numeric(
        result.get("recommended_supply_quantity", pd.Series(dtype=float)),
        errors="coerce",
    ).fillna(0)
    expected_profit = pd.to_numeric(
        result.get("expected_profit", pd.Series(dtype=float)),
        errors="coerce",
    ).fillna(0)
    margin = pd.to_numeric(
        result.get("margin_percent", pd.Series(dtype=float)),
        errors="coerce",
    )
    priority = result.get("priority_level", pd.Series(dtype=str)).astype(str)

    total_recommended = int(recommended_qty.sum())
    recommended_items = int((recommended_qty > 0).sum())
    high_priority = int(((recommended_qty > 0) & (priority == "High")).sum())
    total_profit = float(expected_profit[recommended_qty > 0].sum())
    avg_margin = float(margin[recommended_qty > 0].mean()) if (recommended_qty > 0).any() else 0

    st.subheader("Ключевые показатели поставок" if lang == "ru" else "补货关键指标")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("К поставке, шт." if lang == "ru" else "建议补货量", f"{total_recommended:,}")
    c2.metric("Товаров к поставке" if lang == "ru" else "建议补货商品数", f"{recommended_items:,}")
    c3.metric("Высокий приоритет" if lang == "ru" else "高优先级商品", f"{high_priority:,}")
    c4.metric("Ожидаемая прибыль" if lang == "ru" else "预计利润", f"{total_profit:,.0f}")
    c5.metric("Средняя маржа" if lang == "ru" else "平均利润率", f"{avg_margin:.2f}%")
    st.caption(
        "Рекомендация на поставку появляется только у товаров с достаточной маржей и положительной потребностью."
        if lang == "ru"
        else "只有满足利润率阈值且存在补货需求的商品才会得到建议补货量。"
    )


def show_supply_top_products_chart(result: pd.DataFrame, lang: str) -> None:
    if result.empty or "recommended_supply_quantity" not in result.columns:
        return

    recommended = result[result["recommended_supply_quantity"] > 0].copy()
    if recommended.empty:
        st.info(tr("supply_no_recommendations"))
        return

    chart_df = recommended.sort_values(
        "recommended_supply_quantity",
        ascending=False,
    ).head(20)
    chart_df["product_label"] = chart_df.apply(_supply_product_label, axis=1)

    priority_scale = alt.Scale(
        domain=["High", "Medium", "Low"],
        range=["#16a34a", "#f59e0b", "#ef4444"],
    )
    supply_title = "Рекомендовано к поставке" if lang == "ru" else "建议补货量"
    forecast_title = "Прогноз спроса" if lang == "ru" else "预测需求"
    priority_title = "Приоритет" if lang == "ru" else "优先级"
    chart = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("recommended_supply_quantity:Q", title=supply_title),
            y=alt.Y("product_label:N", sort="-x", title=None),
            color=alt.Color("priority_level:N", scale=priority_scale, title=priority_title),
            tooltip=[
                alt.Tooltip("product_label:N", title="Product"),
                alt.Tooltip("marketplace:N", title="Marketplace"),
                alt.Tooltip("category:N", title="Category"),
                alt.Tooltip("forecast_quantity:Q", title=forecast_title, format=",.0f"),
                alt.Tooltip("recommended_supply_quantity:Q", title=supply_title, format=",.0f"),
                alt.Tooltip("expected_profit:Q", title="expected_profit", format=",.0f"),
                alt.Tooltip("margin_percent:Q", title="margin_percent", format=".2f"),
            ],
        )
        .properties(height=max(280, min(620, len(chart_df) * 28)))
    )

    st.subheader(tr("supply_top_title"))
    st.caption(
        "Показаны товары с наибольшим рекомендованным количеством к поставке. Цвет показывает приоритет."
        if lang == "ru"
        else "展示建议补货量最高的商品，颜色表示优先级。"
    )
    st.altair_chart(chart, width="stretch")


def show_supply_charts(result: pd.DataFrame, lang: str) -> None:
    if result.empty or "recommended_supply_quantity" not in result.columns:
        st.info(
            "Нет данных для графиков поставок."
            if lang == "ru"
            else "没有可用于补货图表的数据。"
        )
        return

    recommended_qty = pd.to_numeric(result["recommended_supply_quantity"], errors="coerce").fillna(0)
    if recommended_qty.sum() <= 0:
        st.info(tr("supply_no_recommendations"))
        return

    show_supply_top_products_chart(result, lang)

    chart_df = result.copy()
    numeric_cols = [
        "recommended_supply_quantity", "forecast_quantity", "safety_stock",
        "available_stock", "expected_profit", "margin_percent",
    ]
    for col in numeric_cols:
        if col in chart_df.columns:
            chart_df[col] = pd.to_numeric(chart_df[col], errors="coerce").fillna(0)

    if {"marketplace", "priority_level", "recommended_supply_quantity"}.issubset(chart_df.columns):
        heatmap_df = (
            chart_df.groupby(["priority_level", "marketplace"], as_index=False)
            .agg(recommended_supply_quantity=("recommended_supply_quantity", "sum"))
        )
        priority_order = ["High", "Medium", "Low"]
        supply_title = "Рекомендовано к поставке" if lang == "ru" else "建议补货量"
        priority_title = "Приоритет" if lang == "ru" else "优先级"
        heatmap = (
            alt.Chart(heatmap_df)
            .mark_rect(cornerRadius=3)
            .encode(
                x=alt.X("marketplace:N", title=None),
                y=alt.Y("priority_level:N", sort=priority_order, title=priority_title),
                color=alt.Color(
                    "recommended_supply_quantity:Q",
                    title=supply_title,
                    scale=alt.Scale(scheme="oranges"),
                ),
                tooltip=[
                    alt.Tooltip("marketplace:N", title="Marketplace"),
                    alt.Tooltip("priority_level:N", title=priority_title),
                    alt.Tooltip(
                        "recommended_supply_quantity:Q",
                        title=supply_title,
                        format=",.0f",
                    ),
                ],
            )
            .properties(height=260)
        )
        st.subheader(
            "Матрица поставок по маркетплейсам"
            if lang == "ru"
            else "按平台和优先级的补货矩阵"
        )
        st.altair_chart(heatmap, width="stretch")

    has_real_stock = (
        {"forecast_quantity", "safety_stock", "available_stock", "recommended_supply_quantity"}
        .issubset(chart_df.columns)
        and not (
            "supply_logic" in chart_df.columns
            and chart_df["supply_logic"].astype(str).eq("simplified_no_stock").all()
        )
    )
    if has_real_stock:
        decomposition = pd.DataFrame([
            {
                "component": "Прогноз спроса" if lang == "ru" else "预测需求",
                "quantity": float(chart_df["forecast_quantity"].sum()),
            },
            {
                "component": "Safety stock" if lang == "ru" else "安全库存",
                "quantity": float(chart_df["safety_stock"].sum()),
            },
            {
                "component": "Available stock" if lang == "ru" else "可用库存",
                "quantity": -float(chart_df["available_stock"].sum()),
            },
            {
                "component": "К поставке" if lang == "ru" else "建议补货",
                "quantity": float(chart_df["recommended_supply_quantity"].sum()),
            },
        ])
        caption = (
            "Положительные значения увеличивают потребность, доступный запас уменьшает ее."
            if lang == "ru"
            else "正值增加补货需求，可用库存会减少需求。"
        )
    else:
        decomposition = pd.DataFrame([
            {
                "component": "Прогноз спроса" if lang == "ru" else "预测需求",
                "quantity": float(chart_df.get("forecast_quantity", pd.Series(dtype=float)).sum()),
            },
            {
                "component": "15% buffer" if lang == "ru" else "15% 缓冲",
                "quantity": float(chart_df.get("forecast_quantity", pd.Series(dtype=float)).sum()) * 0.15,
            },
            {
                "component": "К поставке" if lang == "ru" else "建议补货",
                "quantity": float(chart_df["recommended_supply_quantity"].sum()),
            },
        ])
        caption = (
            "Упрощенный режим без реальных остатков: рекомендация рассчитывается как прогноз спроса x 1.15."
            if lang == "ru"
            else "无真实库存的简化模式：建议补货量按预测需求 x 1.15 计算。"
        )

    decomposition["direction"] = decomposition["quantity"].map(lambda value: "positive" if value >= 0 else "negative")
    decomposition_chart = (
        alt.Chart(decomposition)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("component:N", title=None),
            y=alt.Y("quantity:Q", title="Quantity"),
            color=alt.Color(
                "direction:N",
                scale=alt.Scale(domain=["positive", "negative"], range=["#2563eb", "#ef4444"]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("component:N", title="Component"),
                alt.Tooltip("quantity:Q", title="Quantity", format=",.0f"),
            ],
        )
        .properties(height=300)
    )
    st.subheader("Структура потребности в поставке" if lang == "ru" else "补货需求结构")
    st.caption(caption)
    st.altair_chart(decomposition_chart, width="stretch")


def show_supply_single_product_summary(result: pd.DataFrame, lang: str) -> None:
    if result.empty:
        return

    if "marketplace" in result.columns:
        summary = (
            result.groupby("marketplace", as_index=False)
            .agg(
                forecast_quantity=("forecast_quantity", "sum"),
                recommended_supply_quantity=("recommended_supply_quantity", "sum"),
                expected_profit=("expected_profit", "sum"),
                margin_percent=("margin_percent", "mean"),
                priority_level=("priority_level", "first"),
                supply_logic=("supply_logic", "first"),
            )
        )
    else:
        summary = result.head(1).copy()

    total_recommended = int(summary["recommended_supply_quantity"].sum())
    total_forecast = int(summary["forecast_quantity"].sum())
    total_profit = float(summary["expected_profit"].sum())
    avg_margin = float(summary["margin_percent"].mean())
    priority = str(summary["priority_level"].iloc[0]) if "priority_level" in summary.columns else "N/A"
    logic = str(summary["supply_logic"].iloc[0]) if "supply_logic" in summary.columns else "N/A"
    logic_label = _format_supply_logic(logic, lang)

    if total_recommended > 0:
        st.success(tr("supply_single_recommended"))
    else:
        st.warning(tr("supply_single_not_recommended"))

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Прогноз спроса" if lang == "ru" else "预测需求", f"{total_forecast:,}")
    c2.metric("К поставке" if lang == "ru" else "建议补货", f"{total_recommended:,}")
    c3.metric("Маржа" if lang == "ru" else "利润率", f"{avg_margin:.2f}%")
    c4.metric("Ожидаемая прибыль" if lang == "ru" else "预计利润", f"{total_profit:,.0f}")
    c5.metric("Приоритет" if lang == "ru" else "优先级", priority)
    c6.metric("Логика расчета" if lang == "ru" else "计算逻辑", logic_label)

    st.caption(
        "В упрощенном режиме без остатков рекомендация рассчитывается как прогноз спроса x 1.15."
        if logic == "simplified_no_stock" and lang == "ru"
        else "无库存字段时，建议补货量按预测需求 x 1.15 计算。"
        if logic == "simplified_no_stock"
        else "Рекомендация учитывает прогноз спроса, доступный остаток и страховой запас."
        if lang == "ru"
        else "建议补货量基于预测需求、可用库存和安全库存计算。"
    )

    if len(summary) > 1:
        st.caption(tr("supply_single_marketplace_breakdown"))
        st.dataframe(summary, width="stretch")


def show_forecast_horizon_summary(
    filtered: pd.DataFrame,
    lang: str,
    combine_marketplaces: bool = False,
    marketplace_scope: str | None = None,
) -> None:
    if filtered.empty:
        return
    r14 = models.estimate_sku_forecast(
        filtered,
        14,
        combine_marketplaces=combine_marketplaces,
        marketplace_scope=marketplace_scope,
    )
    r30 = models.estimate_sku_forecast(
        filtered,
        30,
        combine_marketplaces=combine_marketplaces,
        marketplace_scope=marketplace_scope,
    )
    if r14.empty or r30.empty:
        return

    total_14 = int(r14["forecast_quantity"].sum())
    total_30 = int(r30["forecast_quantity"].sum())
    increment = total_30 - total_14
    growth = (increment / total_14 * 100) if total_14 else 0

    title = "Сравнение 14 и 30 дней" if lang == "ru" else "14 天与 30 天对比"
    with st.expander(title, expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("14 дней, количество" if lang == "ru" else "14 天数量", f"{total_14:,}")
        c2.metric("30 дней, количество" if lang == "ru" else "30 天数量", f"{total_30:,}")
        c3.metric("+16 дней, количество" if lang == "ru" else "+16 天数量", f"{increment:,}")
        c4.metric("Рост" if lang == "ru" else "增长", f"{growth:.1f}%")
        st.caption(
            "Если выбраны все маркетплейсы, прогноз рассчитан по объединенным данным."
            if lang == "ru"
            else "如果选择全部平台，预测基于所有平台合并后的数据。"
        )


def show_uniform_daily_line(result: pd.DataFrame, period: int, quantity_col: str) -> None:
    if result.empty or period <= 0 or quantity_col not in result.columns:
        return
    total = float(result[quantity_col].sum())
    if total <= 0:
        return
    per_day = total / period
    daily_df = pd.DataFrame(
        {"forecast_per_day": [per_day] * period},
        index=pd.RangeIndex(1, period + 1, name="day"),
    )
    st.subheader(tr("daily_chart_title"))
    st.caption(tr("daily_chart_caption"))
    st.line_chart(daily_df)


def show_promo_summary(result: pd.DataFrame, lang: str) -> None:
    if result.empty:
        return

    if "has_ads" in result.columns:
        ads_mask = result["has_ads"].astype(bool)
    elif "advertising_cost" in result.columns:
        ads_mask = result["advertising_cost"] > 0
    else:
        ads_mask = pd.Series(False, index=result.index)

    advertised = result[ads_mask]
    total_ads = float(advertised["advertising_cost"].sum()) if "advertising_cost" in advertised.columns else 0
    total_profit = float(advertised["profit_after_ads"].sum()) if "profit_after_ads" in advertised.columns else 0
    overall_roi = total_profit / total_ads if total_ads > 0 else 0
    loss_count = int((advertised.get("ad_profitability_status", pd.Series(dtype=str)) == "Loss-making").sum())
    promote_count = int((result.get("recommendation", pd.Series(dtype=str)) == "Promote more").sum())
    organic_count = int((result.get("recommendation", pd.Series(dtype=str)) == "Organic opportunity").sum())

    st.subheader("Ключевые показатели рекламы" if lang == "ru" else "广告关键指标")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Расходы на рекламу" if lang == "ru" else "广告花费", f"{total_ads:,.0f}")
    c2.metric("ROI рекламы" if lang == "ru" else "广告 ROI", f"{overall_roi:.2f}")
    c3.metric("Убыточных кампаний" if lang == "ru" else "亏损活动数", f"{loss_count:,}")
    c4.metric("Продвигать дальше" if lang == "ru" else "建议继续推广", f"{promote_count:,}")
    c5.metric("Органические возможности" if lang == "ru" else "自然销售机会", f"{organic_count:,}")
    st.caption(
        "ROI рекламы и убыточные кампании считаются только по товарам с advertising_cost > 0."
        if lang == "ru"
        else "广告 ROI 和亏损活动只基于 advertising_cost > 0 的商品计算。"
    )


def show_promo_charts(result: pd.DataFrame, lang: str) -> None:
    if result.empty:
        return

    if "recommendation" in result.columns:
        rec_df = (
            result.groupby("recommendation", as_index=False)
            .size()
            .rename(columns={"size": "count"})
            .sort_values("count", ascending=False)
        )
        rec_chart = (
            alt.Chart(rec_df)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("recommendation:N", sort="-y", title=None),
                y=alt.Y("count:Q", title=None),
                color=alt.Color("recommendation:N", legend=None),
                tooltip=[
                    alt.Tooltip("recommendation:N", title="Recommendation"),
                    alt.Tooltip("count:Q", title="Count", format=",.0f"),
                ],
            )
            .properties(height=260)
        )
        st.caption("Структура рекомендаций" if lang == "ru" else "建议分布")
        st.altair_chart(rec_chart, width="stretch")

    if "has_ads" in result.columns:
        advertised = result[result["has_ads"].astype(bool)].copy()
    elif "advertising_cost" in result.columns:
        advertised = result[result["advertising_cost"] > 0].copy()
    else:
        advertised = pd.DataFrame()

    if advertised.empty:
        st.info(
            "В выбранном срезе нет рекламных расходов. Система может показать только органические возможности."
            if lang == "ru"
            else "当前筛选范围没有广告花费，系统只能识别自然销售机会。"
        )
        return

    if {"marketing_roi", "profit_after_ads", "recommendation"}.issubset(advertised.columns):
        scatter = (
            alt.Chart(advertised.head(1000))
            .mark_circle(size=70, opacity=0.75)
            .encode(
                x=alt.X("marketing_roi:Q", title="Marketing ROI"),
                y=alt.Y("profit_after_ads:Q", title="Profit after ads"),
                color=alt.Color("recommendation:N", title=None),
                tooltip=[
                    alt.Tooltip("product_name:N", title="Product"),
                    alt.Tooltip("marketplace:N", title="Marketplace"),
                    alt.Tooltip("marketing_roi:Q", title="ROI", format=".2f"),
                    alt.Tooltip("profit_after_ads:Q", title="Profit", format=",.0f"),
                    alt.Tooltip("recommendation:N", title="Recommendation"),
                ],
            )
            .properties(height=320)
        )
        st.caption("ROI рекламы и прибыль после рекламы" if lang == "ru" else "广告 ROI 与广告后利润")
        st.altair_chart(scatter, width="stretch")

    if {"advertising_cost", "product_name", "product_sku"}.issubset(advertised.columns):
        top_ads = advertised.sort_values("advertising_cost", ascending=False).head(15).copy()
        top_ads["product_label"] = top_ads["product_name"].where(
            top_ads["product_name"].astype(str).str.lower() != "unknown",
            top_ads["product_sku"],
        )
        spend_chart = (
            alt.Chart(top_ads)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
            .encode(
                x=alt.X("advertising_cost:Q", title=None),
                y=alt.Y("product_label:N", sort="-x", title=None),
                color=alt.Color("recommendation:N", title=None),
                tooltip=[
                    alt.Tooltip("product_label:N", title="Product"),
                    alt.Tooltip("advertising_cost:Q", title="Ad spend", format=",.0f"),
                    alt.Tooltip("marketing_roi:Q", title="ROI", format=".2f"),
                    alt.Tooltip("recommendation:N", title="Recommendation"),
                ],
            )
            .properties(height=360)
        )
        st.caption("Товары с наибольшими расходами на рекламу" if lang == "ru" else "广告花费最高的商品")
        st.altair_chart(spend_chart, width="stretch")


def _single_promo_decision_row(result: pd.DataFrame) -> pd.Series:
    if len(result) == 1:
        return result.iloc[0]

    advertised = result[result.get("has_ads", pd.Series(False, index=result.index)).astype(bool)]
    source = advertised if not advertised.empty else result
    revenue = float(source["revenue"].sum()) if "revenue" in source.columns else 0
    profit = float(source["profit_after_ads"].sum()) if "profit_after_ads" in source.columns else 0
    ads = float(source["advertising_cost"].sum()) if "advertising_cost" in source.columns else 0
    row = source.iloc[0].copy()
    row["revenue"] = revenue
    row["profit_after_ads"] = profit
    row["advertising_cost"] = ads
    row["marketing_roi"] = profit / ads if ads > 0 else 0
    row["ad_efficiency"] = revenue / ads if ads > 0 else 0
    row["ad_spend_share"] = ads / revenue * 100 if revenue > 0 else 0
    row["margin_percent"] = profit / revenue * 100 if revenue > 0 else 0
    return row


def show_single_promo_diagnosis(
    result: pd.DataFrame,
    roi_threshold: float,
    min_margin_after_ads: float,
    lang: str,
) -> None:
    if result.empty:
        return

    row = _single_promo_decision_row(result)
    recommendation = str(row.get("recommendation", "No ad action"))
    has_ads = bool(row.get("has_ads", False))
    roi = float(row.get("marketing_roi", 0) or 0)
    margin = float(row.get("margin_percent", 0) or 0)
    ad_share = float(row.get("ad_spend_share", 0) or 0)
    discount = float(row.get("discount_percent", 0) or 0)
    profit = float(row.get("profit_after_ads", 0) or 0)
    ads = float(row.get("advertising_cost", 0) or 0)
    promo_status = str(row.get("promo_status", "No promo"))
    ad_status = str(row.get("ad_profitability_status", "No ads"))
    discount_risk = str(row.get("discount_risk_level", "Low"))

    status_styles = {
        "Promote more": ("success", "Решение: продолжать продвижение" if lang == "ru" else "决策：继续推广"),
        "Stop or reduce ads": ("error", "Решение: остановить или снизить рекламу" if lang == "ru" else "决策：停止或减少广告"),
        "Reduce discount": ("warning", "Решение: снизить скидку" if lang == "ru" else "决策：降低折扣"),
        "Keep, monitor discount": ("warning", "Решение: оставить и контролировать скидку" if lang == "ru" else "决策：保留并监控折扣"),
        "Organic opportunity": ("info", "Решение: органическая возможность" if lang == "ru" else "决策：自然销售机会"),
        "No ad action": ("info", "Решение: действий по рекламе не требуется" if lang == "ru" else "决策：无需广告动作"),
    }
    level, title = status_styles.get(recommendation, ("info", recommendation))

    st.subheader("Диагностика выбранного товара" if lang == "ru" else "单商品诊断")
    getattr(st, level)(title)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("ROI рекламы" if lang == "ru" else "广告 ROI", f"{roi:.2f}")
    c2.metric("Порог ROI" if lang == "ru" else "ROI 阈值", f"{roi_threshold:.2f}")
    c3.metric("Маржа после рекламы" if lang == "ru" else "广告后利润率", f"{margin:.2f}%")
    c4.metric("Доля рекламы" if lang == "ru" else "广告占收入", f"{ad_share:.2f}%")
    c5.metric("Прибыль после рекламы" if lang == "ru" else "广告后利润", f"{profit:,.0f}")

    facts = [
        (
            "Есть рекламные расходы" if has_ads and lang == "ru" else
            "Нет рекламных расходов" if lang == "ru" else
            "有广告投放" if has_ads else "没有广告投放"
        ),
        (
            f"promo_status = {promo_status}: это статус скидки/промо, не факт рекламы."
            if lang == "ru"
            else f"promo_status = {promo_status}：这是折扣/促销状态，不等于是否有广告。"
        ),
        (
            f"ROI {roi:.2f} {'>=' if roi >= roi_threshold else '<'} порога {roi_threshold:.2f}."
            if lang == "ru"
            else f"ROI {roi:.2f} {'>=' if roi >= roi_threshold else '<'} 阈值 {roi_threshold:.2f}。"
        ),
        (
            f"Маржа {margin:.2f}% {'>=' if margin >= min_margin_after_ads else '<'} минимума {min_margin_after_ads:.2f}%."
            if lang == "ru"
            else f"利润率 {margin:.2f}% {'>=' if margin >= min_margin_after_ads else '<'} 最低要求 {min_margin_after_ads:.2f}%。"
        ),
        (
            f"Расходы на рекламу: {ads:,.0f}; скидка: {discount:.2f}%; риск скидки: {discount_risk}; статус окупаемости: {ad_status}."
            if lang == "ru"
            else f"广告费：{ads:,.0f}；折扣：{discount:.2f}%；折扣风险：{discount_risk}；广告回本状态：{ad_status}。"
        ),
    ]
    for fact in facts:
        st.write("- " + fact)

    if len(result) == 1:
        st.caption(
            "Вывод основан на одной строке данных; это текущий срез, а не долгосрочный тренд."
            if lang == "ru"
            else "该结论基于单条数据，是当前切片表现，不代表长期趋势。"
        )
    else:
        st.caption(
            "По товару найдено несколько строк; ключевые метрики агрегированы, а решение взято по наиболее приоритетному случаю."
            if lang == "ru"
            else "该商品包含多条记录，关键指标已汇总，决策取最优先处理的情况。"
        )

    if has_ads:
        compare_df = pd.DataFrame(
            [
                {"metric": "ROI", "value": roi, "threshold": roi_threshold},
                {"metric": "Margin, %", "value": margin, "threshold": min_margin_after_ads},
            ]
        )
        bars = (
            alt.Chart(compare_df)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("metric:N", title=None),
                y=alt.Y("value:Q", title=None),
                color=alt.Color("metric:N", legend=None),
                tooltip=[
                    alt.Tooltip("metric:N", title="Metric"),
                    alt.Tooltip("value:Q", title="Value", format=".2f"),
                    alt.Tooltip("threshold:Q", title="Threshold", format=".2f"),
                ],
            )
        )
        rules = (
            alt.Chart(compare_df)
            .mark_tick(color="#ef4444", thickness=3, size=50)
            .encode(x="metric:N", y="threshold:Q")
        )
        st.caption("Сравнение с порогами" if lang == "ru" else "与阈值对比")
        st.altair_chart((bars + rules).properties(height=260), width="stretch")
    else:
        st.info(
            "У товара нет рекламных расходов, поэтому он не участвует в расчете рекламного ROI. Если прибыль и маржа хорошие, это кандидат для тестовой рекламы."
            if lang == "ru"
            else "该商品没有广告费，因此不参与广告 ROI 计算。如果利润和利润率表现好，可作为测试投放候选。"
        )


def show_promo_result_table(result: pd.DataFrame, derived_columns: list[str] | set[str] | None = None) -> None:
    if result.empty:
        st.dataframe(result, width="stretch")
        return

    display_order = [
        "product_name",
        "marketplace",
        "category",
        "brand",
        "promo_status",
        "has_ads",
        "advertising_cost",
        "discount_percent",
        "marketing_roi",
        "ad_efficiency",
        "ad_spend_share",
        "profit_after_ads",
        "margin_percent",
        "ad_profitability_status",
        "discount_risk_level",
        "recommendation",
    ]
    display_cols = [col for col in display_order if col in result.columns]
    extra_cols = [
        col for col in result.columns
        if col not in display_cols and col != "product_sku"
    ]
    display = result[display_cols + extra_cols].head(300).copy()
    derived = set(derived_columns or [])
    promo_analysis_cols = {
        "ad_profitability_status", "discount_risk_level",
        "profit_after_ads", "ad_spend_share",
    }
    derived_style = "background-color: #ede9fe; color: #2e1065"
    analysis_style = "background-color: #dbeafe; color: #1e3a8a"
    recommendation_styles = {
        "Promote more": "background-color: #bbf7d0; color: #14532d; font-weight: 700",
        "Keep, monitor discount": "background-color: #fde68a; color: #78350f; font-weight: 700",
        "Reduce discount": "background-color: #fed7aa; color: #7c2d12; font-weight: 700",
        "Stop or reduce ads": "background-color: #fecaca; color: #7f1d1d; font-weight: 700",
        "Monitor": "background-color: #e5e7eb; color: #111827; font-weight: 700",
        "Organic opportunity": "background-color: #99f6e4; color: #134e4a; font-weight: 700",
        "No ad action": "background-color: #e5e7eb; color: #111827; font-weight: 700",
    }

    def highlight_promo_columns(row: pd.Series) -> list[str]:
        styles = []
        for col in display.columns:
            if col == "recommendation":
                styles.append(recommendation_styles.get(str(row.get(col, "")), ""))
            elif col in promo_analysis_cols:
                styles.append(analysis_style)
            elif col in derived:
                styles.append(derived_style)
            else:
                styles.append("")
        return styles

    st.dataframe(display.style.apply(highlight_promo_columns, axis=1), width="stretch")


def show_price_result_table(result: pd.DataFrame, compact: bool = False) -> None:
    if result.empty:
        st.dataframe(result, width="stretch")
        return

    if compact:
        display_order = [
            "marketplace",
            "final_price",
            "recommended_price",
            "price_delta",
            "price_delta_percent",
            "margin_percent",
            "expected_margin_after_price_change",
            "price_action",
        ]
    else:
        display_order = [
            "product_name",
            "marketplace",
            "category",
            "brand",
            "final_price",
            "recommended_price",
            "price_delta",
            "price_delta_percent",
            "target_margin_percent",
            "margin_percent",
            "current_margin_gap",
            "expected_margin_after_price_change",
            "cost",
            "unit_logistics_cost",
            "unit_advertising_cost",
            "unit_total_cost",
            "commission_rate",
            "commission_amount_at_recommended_price",
            "target_margin_amount",
            "price_action",
        ]
    display_cols = [col for col in display_order if col in result.columns]
    extra_cols = [
        col for col in result.columns
        if not compact and col not in display_cols and col != "product_sku"
    ]
    display = result[display_cols + extra_cols].head(300).copy()

    action_labels = {
        "Increase price": "Цена ниже минимальной" if st.session_state.get("lang") == "ru" else "当前价格低于最低价",
        "Price can be reduced": "Цена выше минимальной" if st.session_state.get("lang") == "ru" else "当前价格高于最低价",
        "Keep price": "Цена близка к минимальной" if st.session_state.get("lang") == "ru" else "当前价格接近最低价",
    }
    if "price_action" in display.columns:
        display["price_action"] = display["price_action"].map(action_labels).fillna(display["price_action"])
    display = display.rename(columns={
        "recommended_price": "minimum_acceptable_price",
        "price_delta": "delta_to_minimum_price",
        "price_delta_percent": "delta_to_minimum_price_percent",
        "expected_margin_after_price_change": "margin_at_minimum_price",
        "price_action": "price_status",
    })

    output_cols = {
        "minimum_acceptable_price", "delta_to_minimum_price", "delta_to_minimum_price_percent",
        "margin_at_minimum_price", "price_status",
    }
    support_cols = {
        "unit_total_cost", "current_margin_gap", "target_margin_percent",
        "commission_amount_at_recommended_price", "target_margin_amount",
    }
    output_style = "background-color: #dbeafe; color: #1e3a8a; font-weight: 700"
    support_style = "background-color: #ede9fe; color: #2e1065"
    action_styles = {
        "Increase price": "background-color: #fecaca; color: #7f1d1d; font-weight: 700",
        "Price can be reduced": "background-color: #bbf7d0; color: #14532d; font-weight: 700",
        "Keep price": "background-color: #e5e7eb; color: #111827; font-weight: 700",
        "Цена ниже минимальной": "background-color: #fecaca; color: #7f1d1d; font-weight: 700",
        "Цена выше минимальной": "background-color: #bbf7d0; color: #14532d; font-weight: 700",
        "Цена близка к минимальной": "background-color: #e5e7eb; color: #111827; font-weight: 700",
        "当前价格低于最低价": "background-color: #fecaca; color: #7f1d1d; font-weight: 700",
        "当前价格高于最低价": "background-color: #bbf7d0; color: #14532d; font-weight: 700",
        "当前价格接近最低价": "background-color: #e5e7eb; color: #111827; font-weight: 700",
    }

    def highlight_price_columns(row: pd.Series) -> list[str]:
        styles = []
        for col in display.columns:
            if col == "price_status":
                styles.append(action_styles.get(str(row.get(col, "")), output_style))
            elif col in output_cols:
                styles.append(output_style)
            elif col in support_cols:
                styles.append(support_style)
            else:
                styles.append("")
        return styles

    st.dataframe(display.style.apply(highlight_price_columns, axis=1), width="stretch")


def show_single_price_result_table(result: pd.DataFrame, lang: str) -> None:
    if result.empty:
        st.dataframe(result, width="stretch")
        return

    display_order = [
        "marketplace",
        "final_price",
        "recommended_price",
        "price_delta",
        "price_delta_percent",
        "margin_percent",
        "expected_margin_after_price_change",
        "price_action",
    ]
    display_cols = [col for col in display_order if col in result.columns]
    display = result[display_cols].head(300).copy()

    action_labels = {
        "Increase price": "Цена ниже минимальной" if lang == "ru" else "当前价格低于最低价",
        "Price can be reduced": "Цена выше минимальной" if lang == "ru" else "当前价格高于最低价",
        "Keep price": "Цена близка к минимальной" if lang == "ru" else "当前价格接近最低价",
    }
    if "price_action" in display.columns:
        display["price_action"] = display["price_action"].map(action_labels).fillna(display["price_action"])

    display = display.rename(columns={
        "marketplace": "Маркетплейс" if lang == "ru" else "平台",
        "final_price": "Текущая цена" if lang == "ru" else "当前价格",
        "recommended_price": "Минимально допустимая цена" if lang == "ru" else "最低可接受价格",
        "price_delta": "Разница с минимумом" if lang == "ru" else "与最低价差额",
        "price_delta_percent": "Разница, %" if lang == "ru" else "差额，%",
        "margin_percent": "Текущая маржа, %" if lang == "ru" else "当前利润率，%",
        "expected_margin_after_price_change": "Маржа при минимальной цене, %" if lang == "ru" else "最低价格下利润率，%",
        "price_action": "Статус цены" if lang == "ru" else "价格状态",
    })

    output_labels = {
        "Минимально допустимая цена", "Разница с минимумом", "Разница, %",
        "Маржа при минимальной цене, %", "Статус цены",
        "最低可接受价格", "与最低价差额", "差额，%", "最低价格下利润率，%", "价格状态",
    }
    status_col = "Статус цены" if lang == "ru" else "价格状态"
    status_styles = {
        "Цена ниже минимальной": "background-color: #fecaca; color: #7f1d1d; font-weight: 700",
        "Цена выше минимальной": "background-color: #bbf7d0; color: #14532d; font-weight: 700",
        "Цена близка к минимальной": "background-color: #e5e7eb; color: #111827; font-weight: 700",
        "当前价格低于最低价": "background-color: #fecaca; color: #7f1d1d; font-weight: 700",
        "当前价格高于最低价": "background-color: #bbf7d0; color: #14532d; font-weight: 700",
        "当前价格接近最低价": "background-color: #e5e7eb; color: #111827; font-weight: 700",
    }
    output_style = "background-color: #dbeafe; color: #1e3a8a; font-weight: 700"

    def highlight_single_price_columns(row: pd.Series) -> list[str]:
        styles = []
        for col in display.columns:
            if col == status_col:
                styles.append(status_styles.get(str(row.get(col, "")), output_style))
            elif col in output_labels:
                styles.append(output_style)
            else:
                styles.append("")
        return styles

    st.dataframe(display.style.apply(highlight_single_price_columns, axis=1), width="stretch")


def show_price_summary(result: pd.DataFrame, lang: str) -> None:
    if result.empty:
        return

    actions = result.get("price_action", pd.Series(dtype=str)).astype(str)
    increase_count = int((actions == "Increase price").sum())
    above_min_count = int((actions == "Price can be reduced").sum())
    near_min_count = int((actions == "Keep price").sum())
    avg_delta = float(pd.to_numeric(result.get("price_delta", pd.Series(dtype=float)), errors="coerce").mean())
    avg_delta_percent = float(
        pd.to_numeric(result.get("price_delta_percent", pd.Series(dtype=float)), errors="coerce").mean()
    )
    avg_margin_at_minimum = float(
        pd.to_numeric(
            result.get("expected_margin_after_price_change", pd.Series(dtype=float)),
            errors="coerce",
        ).mean()
    )

    st.subheader("Ключевые показатели цены" if lang == "ru" else "价格关键指标")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Ниже минимума" if lang == "ru" else "低于最低价", f"{increase_count:,}")
    c2.metric("Выше минимума" if lang == "ru" else "高于最低价", f"{above_min_count:,}")
    c3.metric("Близко к минимуму" if lang == "ru" else "接近最低价", f"{near_min_count:,}")
    c4.metric("Средняя разница" if lang == "ru" else "平均差额", f"{avg_delta:,.0f}", f"{avg_delta_percent:+.1f}%")
    c5.metric(
        "Маржа при мин. цене" if lang == "ru" else "最低价利润率",
        f"{avg_margin_at_minimum:.2f}%",
    )
    st.caption(
        "Минимальная цена рассчитана так, чтобы после расходов сохранить выбранную целевую маржу."
        if lang == "ru"
        else "最低价用于在扣除费用后保持所选目标利润率。"
    )


def show_price_charts(result: pd.DataFrame, lang: str) -> None:
    if result.empty:
        st.info(
            "Нет данных для построения графиков цены."
            if lang == "ru"
            else "没有可用于价格图表的数据。"
        )
        return

    chart_df = result.copy()
    for col in [
        "final_price", "recommended_price", "price_delta_percent",
        "cost", "unit_logistics_cost", "unit_advertising_cost",
        "commission_amount_at_recommended_price", "target_margin_amount",
    ]:
        if col in chart_df.columns:
            chart_df[col] = pd.to_numeric(chart_df[col], errors="coerce").fillna(0)

    action_domain = ["Increase price", "Keep price", "Price can be reduced"]
    action_labels = {
        "Increase price": "Цена ниже минимальной" if lang == "ru" else "当前价格低于最低价",
        "Keep price": "Цена близка к минимальной" if lang == "ru" else "当前价格接近最低价",
        "Price can be reduced": "Цена выше минимальной" if lang == "ru" else "当前价格高于最低价",
    }
    action_range = ["#ef4444", "#6b7280", "#16a34a"]
    action_scale = alt.Scale(domain=action_domain, range=action_range)

    if {"price_delta_percent", "price_action"}.issubset(chart_df.columns):
        histogram_source = chart_df.copy()
        histogram_source["price_status"] = histogram_source["price_action"].map(action_labels).fillna(
            histogram_source["price_action"]
        )
        histogram = (
            alt.Chart(histogram_source)
            .mark_bar(opacity=0.85)
            .encode(
                x=alt.X(
                    "price_delta_percent:Q",
                    bin=alt.Bin(maxbins=30),
                    title="Delta to minimum acceptable price, %",
                ),
                y=alt.Y("count():Q", title=None),
                color=alt.Color("price_action:N", scale=action_scale, title=None),
                tooltip=[
                    alt.Tooltip("price_delta_percent:Q", bin=True, title="Delta to minimum, %"),
                    alt.Tooltip("count():Q", title="Count", format=",.0f"),
                    alt.Tooltip("price_status:N", title="Price status"),
                ],
            )
            .properties(height=280)
        )
        st.subheader(
            "Распределение изменения цены"
            if lang == "ru"
            else "价格调整幅度分布"
        )
        st.altair_chart(histogram, width="stretch")

    if {"final_price", "recommended_price", "price_action"}.issubset(chart_df.columns):
        scatter_source = chart_df.head(1000).copy()
        max_price = float(scatter_source[["final_price", "recommended_price"]].max().max())
        line_df = pd.DataFrame({"price": [0, max_price]})
        scatter_source["price_status"] = scatter_source["price_action"].map(action_labels).fillna(
            scatter_source["price_action"]
        )
        scatter = (
            alt.Chart(scatter_source)
            .mark_circle(size=65, opacity=0.7)
            .encode(
                x=alt.X("final_price:Q", title="Current final price"),
                y=alt.Y("recommended_price:Q", title="Minimum acceptable price"),
                color=alt.Color("price_action:N", scale=action_scale, title=None),
                tooltip=[
                    alt.Tooltip("product_name:N", title="Product"),
                    alt.Tooltip("marketplace:N", title="Marketplace"),
                    alt.Tooltip("final_price:Q", title="Current price", format=",.2f"),
                    alt.Tooltip("recommended_price:Q", title="Minimum acceptable price", format=",.2f"),
                    alt.Tooltip("price_delta_percent:Q", title="Change, %", format=".2f"),
                    alt.Tooltip("price_status:N", title="Price status"),
                ],
            )
        )
        reference = (
            alt.Chart(line_df)
            .mark_line(color="#9ca3af", strokeDash=[5, 5])
            .encode(x="price:Q", y="price:Q")
        )
        st.subheader(
            "Текущая цена и минимально допустимая цена"
            if lang == "ru"
            else "当前价格与最低可接受价格"
        )
        st.altair_chart((scatter + reference).properties(height=340), width="stretch")

    cost_cols = [
        "cost", "unit_logistics_cost", "unit_advertising_cost",
        "commission_amount_at_recommended_price", "target_margin_amount",
    ]
    if {"marketplace", *cost_cols}.issubset(chart_df.columns):
        cost_summary = (
            chart_df.groupby("marketplace", as_index=False)[cost_cols]
            .mean()
            .rename(columns={
                "cost": "Cost",
                "unit_logistics_cost": "Logistics per unit",
                "unit_advertising_cost": "Ads per unit",
                "commission_amount_at_recommended_price": "Commission",
                "target_margin_amount": "Target margin",
            })
        )
        folded = cost_summary.melt(
            id_vars="marketplace",
            var_name="component",
            value_name="amount",
        )
        structure = (
            alt.Chart(folded)
            .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X("marketplace:N", title=None),
                y=alt.Y("amount:Q", title="Average amount per unit"),
                color=alt.Color("component:N", title=None),
                tooltip=[
                    alt.Tooltip("marketplace:N", title="Marketplace"),
                    alt.Tooltip("component:N", title="Component"),
                    alt.Tooltip("amount:Q", title="Amount", format=",.2f"),
                ],
            )
            .properties(height=320)
        )
        st.subheader(
            "Структура цены по маркетплейсам"
            if lang == "ru"
            else "各平台价格结构"
        )
        st.altair_chart(structure, width="stretch")


def _single_price_decision_row(result: pd.DataFrame, target_margin: float) -> pd.Series:
    if len(result) == 1:
        return result.iloc[0]

    numeric_cols = [
        "final_price", "recommended_price", "margin_percent",
        "expected_margin_after_price_change", "current_margin_gap",
        "unit_total_cost", "cost", "unit_logistics_cost", "unit_advertising_cost",
        "commission_rate", "price_delta", "price_delta_percent",
    ]
    row = result.iloc[0].copy()
    for col in numeric_cols:
        if col in result.columns:
            row[col] = pd.to_numeric(result[col], errors="coerce").mean()
    final_price = float(row.get("final_price", 0) or 0)
    recommended_price = float(row.get("recommended_price", 0) or 0)
    row["price_delta"] = recommended_price - final_price
    row["price_delta_percent"] = row["price_delta"] / final_price * 100 if final_price else 0
    row["target_margin_percent"] = target_margin
    row["current_margin_gap"] = target_margin - float(row.get("margin_percent", 0) or 0)
    if recommended_price > final_price * 1.05:
        row["price_action"] = "Increase price"
    elif recommended_price < final_price * 0.95:
        row["price_action"] = "Price can be reduced"
    else:
        row["price_action"] = "Keep price"
    return row


def show_single_price_diagnosis(result: pd.DataFrame, target_margin: float, lang: str) -> None:
    if result.empty:
        return

    row = _single_price_decision_row(result, target_margin)
    action = str(row.get("price_action", "Keep price"))
    final_price = float(row.get("final_price", 0) or 0)
    recommended_price = float(row.get("recommended_price", 0) or 0)
    price_delta = float(row.get("price_delta", recommended_price - final_price) or 0)
    price_delta_percent = float(row.get("price_delta_percent", 0) or 0)
    margin = float(row.get("margin_percent", 0) or 0)
    expected_margin = float(row.get("expected_margin_after_price_change", 0) or 0)
    margin_buffer = margin - target_margin
    margin_metric_label = (
        "Запас маржи" if margin_buffer >= 0 and lang == "ru" else
        "Дефицит маржи" if lang == "ru" else
        "利润率安全空间" if margin_buffer >= 0 else "利润率缺口"
    )
    margin_metric_value = (
        f"+{margin_buffer:.2f} п.п."
        if margin_buffer >= 0 and lang == "ru" else
        f"{abs(margin_buffer):.2f} п.п."
        if lang == "ru" else
        f"+{margin_buffer:.2f} 个百分点"
        if margin_buffer >= 0 else
        f"{abs(margin_buffer):.2f} 个百分点"
    )
    unit_cost = float(row.get("unit_total_cost", 0) or 0)

    status_styles = {
        "Increase price": ("warning", "Решение: повысить цену" if lang == "ru" else "决策：提高价格"),
        "Price can be reduced": (
            "success",
            "Минимально допустимая цена рассчитана"
            if lang == "ru"
            else "已计算最低可接受价格",
        ),
        "Keep price": ("info", "Решение: оставить цену" if lang == "ru" else "决策：保持价格"),
    }
    level, title = status_styles.get(action, ("info", action))

    st.subheader("Диагностика цены выбранного товара" if lang == "ru" else "单商品价格诊断")
    getattr(st, level)(title)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Текущая цена" if lang == "ru" else "当前价格", f"{final_price:,.2f}")
    c2.metric("Минимально допустимая цена" if lang == "ru" else "最低可接受价格", f"{recommended_price:,.2f}")
    c3.metric("Разница" if lang == "ru" else "价格差额", f"{price_delta:,.2f}", f"{price_delta_percent:+.2f}%")
    c4.metric("Целевая маржа" if lang == "ru" else "目标利润率", f"{target_margin:.2f}%")
    c5.metric("Маржа при минимальной цене" if lang == "ru" else "最低价格下利润率", f"{expected_margin:.2f}%")
    c6.metric(margin_metric_label, margin_metric_value)

    if action == "Price can be reduced":
        price_explanation = (
            f"Минимально допустимая цена для сохранения целевой маржи {target_margin:.2f}%: {recommended_price:,.2f}."
            if lang == "ru"
            else f"为保持 {target_margin:.2f}% 的目标利润率，最低可接受价格为 {recommended_price:,.2f}。"
        )
    elif action == "Increase price":
        price_explanation = (
            f"Чтобы сохранить целевую маржу {target_margin:.2f}%, цену нужно поднять минимум до {recommended_price:,.2f}."
            if lang == "ru"
            else f"为了保持 {target_margin:.2f}% 的目标利润率，价格至少需要提高到 {recommended_price:,.2f}。"
        )
    else:
        price_explanation = (
            f"Текущая цена близка к минимально допустимой цене {recommended_price:,.2f}; изменение не требуется."
            if lang == "ru"
            else f"当前价格接近最低可接受价格 {recommended_price:,.2f}，无需调整。"
        )

    facts = [
        (
            f"Расчет учитывает себестоимость, комиссию, логистику и рекламу; полная стоимость на единицу: {unit_cost:,.2f}."
            if lang == "ru"
            else f"计算已考虑成本、平台佣金、物流和广告；单件总成本为 {unit_cost:,.2f}。"
        ),
        (
            f"Текущая маржа {margin:.2f}% {'ниже' if margin < target_margin else 'не ниже'} цели {target_margin:.2f}%."
            if lang == "ru"
            else f"当前利润率 {margin:.2f}% {'低于' if margin < target_margin else '不低于'}目标 {target_margin:.2f}%。"
        ),
        (
            price_explanation
        ),
    ]
    for fact in facts:
        st.write("- " + fact)

    if len(result) > 1:
        st.caption(
            "По выбранному товару найдено несколько строк; ключевые метрики показаны в агрегированном виде."
            if lang == "ru"
            else "当前商品包含多条记录，关键指标以汇总口径展示。"
        )

    if "marketplace" in result.columns and result["marketplace"].nunique(dropna=True) > 1:
        breakdown = (
            result.groupby("marketplace", as_index=False)
            .agg(
                final_price=("final_price", "mean"),
                recommended_price=("recommended_price", "mean"),
                price_delta=("price_delta", "mean"),
                price_delta_percent=("price_delta_percent", "mean"),
                margin_percent=("margin_percent", "mean"),
                expected_margin_after_price_change=("expected_margin_after_price_change", "mean"),
            )
        )
        breakdown["price_action"] = "Keep price"
        breakdown.loc[
            breakdown["recommended_price"] > breakdown["final_price"] * 1.05,
            "price_action",
        ] = "Increase price"
        breakdown.loc[
            breakdown["recommended_price"] < breakdown["final_price"] * 0.95,
            "price_action",
        ] = "Price can be reduced"
        st.caption(
            "Разбивка по маркетплейсам"
            if lang == "ru"
            else "按平台拆分"
        )
        st.dataframe(breakdown, width="stretch")


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df is None or df.empty:
        return ""
    display = df.head(max_rows).copy()
    for col in display.select_dtypes(include=["float"]).columns:
        display[col] = display[col].map(lambda v: f"{v:.4f}")
    headers = [str(c) for c in display.columns]
    rows = display.astype(str).values.tolist()
    table = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    table.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(table)


def _schema_markdown(schema_info: dict) -> str:
    if not schema_info:
        return ""
    mapping = schema_summary(schema_info)
    availability = availability_summary(schema_info)
    derived = schema_info.get("derived_columns", [])
    sections = ["## CSV schema recognition"]
    if not mapping.empty:
        sections.append(dataframe_to_markdown(mapping, max_rows=50))
    else:
        sections.append("No known business fields were mapped.")
    if derived:
        sections.append("\nDerived columns: " + ", ".join(derived))
    sections.append("\n## Function availability")
    sections.append(dataframe_to_markdown(availability, max_rows=20))
    return "\n\n".join(sections)


def _business_top_section(title: str, result_df: pd.DataFrame) -> str:
    if result_df is None or result_df.empty:
        return ""
    important_cols = [
        "marketplace", "product_name", "product_sku", "category", "forecast_quantity",
        "recommended_supply_quantity", "expected_profit",
        "margin_percent", "priority_level", "recommendation", "recommended_price",
        "price_delta", "price_delta_percent", "expected_margin_after_price_change",
        "price_action", "advertising_cost", "marketing_roi", "ad_efficiency",
        "has_ads", "profit_after_ads", "ad_profitability_status", "discount_risk_level",
    ]
    cols = [col for col in important_cols if col in result_df.columns]
    if not cols:
        cols = result_df.columns[: min(8, len(result_df.columns))].tolist()
    return f"## {title}\n\n{dataframe_to_markdown(result_df[cols], max_rows=10)}"


def make_report(
    title: str,
    source_df: pd.DataFrame,
    result_df: pd.DataFrame,
    filters: dict,
    lang: str,
    schema_info=None,
) -> str:
    if lang == "ru":
        report_title = "Аналитический отчет"
        params = "Параметры анализа"
        summary = "Краткая сводка"
        conclusion_text = (
            "Система сформировала практические рекомендации для продавца на маркетплейсах. "
            "CSV-файл можно использовать как основу для операционных решений."
        )
    else:
        report_title = "鍒嗘瀽鎶ュ憡"
        params = "鍒嗘瀽鍙傛暟"
        summary = "汇总信息"
        conclusion_text = "系统已经生成可执行的电商业务建议，CSV 文件可用于后续运营决策。"

    param_lines = [
        f"- Marketplace: {filters.get('marketplace')}",
        f"- Category: {filters.get('category')}",
        f"- SKU: {filters.get('sku')}",
        f"- Mode: {filters.get('mode', '')}",
    ]
    if filters.get("period") is not None:
        param_lines.insert(3, f"- Period: {filters.get('period')} days")
    if filters.get("roi_threshold") is not None:
        param_lines.append(f"- Advertising ROI threshold: {filters.get('roi_threshold')}")
    if filters.get("min_margin_after_ads") is not None:
        param_lines.append(f"- Minimum margin after ads: {filters.get('min_margin_after_ads')}%")

    report = f"""# {report_title}: {title}

## {params}

{chr(10).join(param_lines)}

## {summary}

- Rows: {len(source_df)}
- Revenue: {source_df["revenue"].sum():,.2f}
- Profit: {source_df["profit"].sum():,.2f}
- Average margin: {source_df["margin_percent"].mean():.2f}%
"""

    report += "\n\n" + _schema_markdown(schema_info or source_df.attrs.get("schema_info", {}))
    report += "\n\n" + _business_top_section("Top recommendations", result_df)

    forecast_cols = {"forecast_quantity", "expected_revenue", "expected_profit", "confidence_level"}
    if forecast_cols.intersection(set(result_df.columns)):
        if lang == "ru":
            report += """

## Поля результата прогноза

- forecast_quantity: прогнозируемое количество продаж, рассчитанное системой.
- expected_revenue: ожидаемая выручка на основе прогноза и средней цены.
- expected_profit: ожидаемая прибыль на основе прогноза и средней прибыли на единицу.
- confidence_level: уровень доверия на основе доступной истории по SKU.
"""
        else:
            report += """

## 棰勬祴缁撴灉瀛楁璇存槑

- forecast_quantity锛氱郴缁熻绠楀緱鍒扮殑棰勬祴閿€閲忋€?- expected_revenue锛氭牴鎹娴嬮攢閲忓拰骞冲潎鎴愪氦浠疯绠楃殑棰勮鏀跺叆銆?- expected_profit锛氭牴鎹娴嬮攢閲忓拰骞冲潎鍗曚欢鍒╂鼎璁＄畻鐨勯璁″埄娑︺€?- confidence_level锛氬熀浜庡綋鍓?SKU 鍙敤鍘嗗彶鏁版嵁閲忚绠楃殑缃俊搴︾瓑绾с€?"""

    promo_cols = {"ad_profitability_status", "discount_risk_level", "profit_after_ads", "ad_spend_share"}
    if promo_cols.intersection(set(result_df.columns)):
        if lang == "ru":
            report += """

## Поля анализа рекламы и промо

- marketing_roi: прибыль после рекламы, деленная на расходы на рекламу.
- ad_efficiency: выручка, деленная на расходы на рекламу.
- profit_after_ads: прибыль в текущей бизнес-логике после учета рекламных расходов.
- ad_spend_share: доля рекламных расходов в выручке, %.
- ad_profitability_status: оценка окупаемости рекламы.
- discount_risk_level: риск того, что скидка съедает маржу.
- recommendation: практическое действие для продавца.

ROI рекламы в сводке считается только по строкам с advertising_cost > 0. Organic opportunity означает, что товар сейчас продается без рекламы и показывает хорошую прибыльность; это возможность для тестовой рекламы, а не уже успешная рекламная кампания.
"""
            if filters.get("single_product"):
                report += """

## Пояснение для одного товара

Решение по товару основано на текущих значениях рекламных расходов, прибыли после рекламы, ROI, маржи и риска скидки. Если в выбранном срезе только одна строка, результат отражает текущую запись и не является долгосрочным трендом.
"""
        else:
            report += """

## 广告与促销分析字段

- marketing_roi：广告后利润 / 广告费用。
- ad_efficiency：收入 / 广告费用。
- profit_after_ads：当前业务口径下扣除广告后的利润。
- ad_spend_share：广告费用占收入比例。
- ad_profitability_status：广告回本状态。
- discount_risk_level：折扣侵蚀利润的风险。
- recommendation：给卖家的操作建议。

汇总中的广告 ROI 只基于 advertising_cost > 0 的商品计算。Organic opportunity 表示商品当前没有广告但利润表现较好，适合测试投放；它不等于广告已经成功。
"""
            if filters.get("single_product"):
                report += """

## 单商品说明

该商品决策基于当前筛选范围内的广告费、广告后利润、ROI、利润率和折扣风险。如果当前只有一条记录，结果表示当前切片表现，不代表长期趋势。
"""

    report += f"""

## Conclusion

{conclusion_text}
"""
    return report


def download_buttons(result: pd.DataFrame, report: str, filename: str):
    st.download_button(
        tr("download_csv"),
        result.to_csv(index=False).encode("utf-8-sig"),
        f"{filename}.csv",
        "text/csv",
    )
    st.download_button(
        tr("download_md"),
        report,
        f"{filename}_report.md",
        "text/markdown",
    )
