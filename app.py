import math

import pandas as pd
import streamlit as st

import models
from config import MARKETPLACE_FILES
from data_utils import filter_data, filter_options, load_data
from schema_utils import availability_summary, schema_summary
from ui import (
    download_buttons,
    make_report,
    show_active_horizon,
    show_feature_field_usage,
    show_forecast_charts,
    show_forecast_factor_explanation,
    show_forecast_horizon_summary,
    show_forecast_output_note,
    show_forecast_result_table,
    show_marketplace_overview,
    show_promo_charts,
    show_promo_result_table,
    show_promo_summary,
    show_price_charts,
    show_price_result_table,
    show_price_summary,
    show_selected_forecast_summary,
    show_single_forecast_diagnosis,
    show_single_forecast_result_table,
    show_single_price_diagnosis,
    show_single_price_result_table,
    show_single_product_data_overview,
    show_single_promo_diagnosis,
    show_single_supply_result_table,
    show_supply_charts,
    show_supply_result_table,
    show_supply_single_product_summary,
    show_supply_summary,
    show_supply_top_products_chart,
    tr,
)


def _feature_options() -> list[tuple[str, str]]:
    return [
        (tr("forecast"), "forecast"),
        (tr("supply"), "supply"),
        (tr("promo"), "promo"),
        (tr("price"), "price"),
    ]


def _show_system_purpose(lang: str) -> None:
    with st.expander(tr("system_description_title"), expanded=False):
        if lang == "ru":
            st.info(
                "E-com Prophet помогает продавцу на маркетплейсах принимать операционные решения: "
                "прогнозировать спрос, понимать потребность в поставке, распределять товар по площадкам "
                "и оценивать экономику SKU."
            )
        else:
            st.info(
                "E-com Prophet 帮助 marketplace 卖家预测需求、制定供货计划、按平台分配商品，"
                "并评估 SKU 的经营表现。"
            )


def _show_schema_panel(schema_info: dict) -> None:
    with st.expander(tr("schema_panel_title"), expanded=False):
        mapping_df = schema_summary(schema_info)
        availability_df = availability_summary(schema_info)
        if mapping_df.empty:
            st.warning(tr("schema_empty_warning"))
        else:
            st.dataframe(mapping_df, width="stretch")

        derived = schema_info.get("derived_columns", [])
        if derived:
            st.caption(tr("derived_columns") + ", ".join(derived))

        unmapped = schema_info.get("unmapped_columns", [])
        if unmapped:
            st.caption(tr("unmapped_columns") + ", ".join(map(str, unmapped[:30])))

        st.subheader(tr("function_availability"))
        st.dataframe(availability_df, width="stretch")


def _availability_for(schema_info: dict, key: str) -> dict:
    return schema_info.get("availability", {}).get(key, {"available": True, "missing": []})


def _supply_margin_slider_max(df: pd.DataFrame) -> int:
    if "margin_percent" not in df.columns:
        return 40

    margins = pd.to_numeric(df["margin_percent"], errors="coerce").dropna()
    if margins.empty:
        return 40

    p99 = margins.quantile(0.99)
    if pd.isna(p99):
        return 40

    return int(min(100, max(5, math.ceil(float(p99)))))


def main():
    st.set_page_config(page_title="E-com Prophet", layout="wide")

    if "lang" not in st.session_state:
        st.session_state["lang"] = "ru"

    with st.sidebar:
        language = st.selectbox("Language / Язык / 语言", ["Русский", "中文"])
        st.session_state["lang"] = "ru" if language == "Русский" else "zh"
        lang = st.session_state["lang"]

        st.header(tr("data"))
        data_source = st.radio(
            tr("data"),
            [tr("default_data"), tr("upload_data")],
            label_visibility="collapsed",
        )
        uploaded = (
            st.file_uploader(
                tr("upload_label"),
                type=["csv"],
                help=tr("upload_help"),
            )
            if data_source == tr("upload_data")
            else None
        )
        if data_source == tr("upload_data") and uploaded is None:
            st.info(tr("upload_missing"))

    try:
        df = load_data(uploaded)
    except Exception as exc:
        st.error(f"CSV could not be loaded: {exc}")
        return

    schema_info = df.attrs.get("schema_info", {})

    st.title(tr("title"))
    st.caption(tr("subtitle"))
    _show_system_purpose(st.session_state["lang"])
    _show_schema_panel(schema_info)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(tr("rows"), f"{len(df):,}")
    c2.metric(tr("revenue"), f"{df['revenue'].sum():,.0f}")
    c3.metric(tr("profit"), f"{df['profit'].sum():,.0f}")
    c4.metric(tr("margin"), f"{df['margin_percent'].mean():.2f}%")

    marketplaces, categories, skus, sku_labels = filter_options(df)

    with st.sidebar:
        st.header(tr("function"))
        feature_labels = [label for label, _ in _feature_options()]
        feature_label = st.selectbox(tr("function"), feature_labels)
        feature_key = dict(_feature_options())[feature_label]

        mode = st.radio(tr("mode"), [tr("mode_all"), tr("mode_one")])

        marketplace = st.selectbox(tr("marketplace"), marketplaces)
        category = st.selectbox(tr("category"), categories)

        all_label = tr("all")
        if mode == tr("mode_all"):
            sku = all_label
            st.caption(tr("batch_mode_caption"))
        else:
            sku_choices = [s for s in skus if s != all_label]
            if not sku_choices:
                st.warning("No SKU values are available.")
                sku = all_label
            else:
                sku = st.selectbox(
                    tr("sku"),
                    sku_choices,
                    format_func=lambda value: sku_labels.get(value, value),
                )

        period = None
        target_margin = 20
        promo_roi_threshold = 1.0
        promo_min_margin_after_ads = 10
        if feature_key in {"forecast", "supply"}:
            period = st.radio(tr("period"), [14, 30], horizontal=True)
        if feature_key == "promo":
            if lang == "ru":
                st.caption("Здесь оценивается окупаемость рекламы и скидок, а не прогноз продаж.")
                roi_label = "Порог окупаемости рекламы (ROI)"
                margin_label = "Минимальная маржа после рекламы, %"
            else:
                st.caption("这里评估广告和折扣是否回本，不做销量预测。")
                roi_label = "广告回本阈值（ROI）"
                margin_label = "广告后最低利润率，%"
            promo_roi_threshold = st.number_input(
                roi_label,
                min_value=0.0,
                max_value=10.0,
                value=1.0,
                step=0.1,
            )
            promo_min_margin_after_ads = st.slider(
                margin_label,
                0,
                80,
                10,
            )
        if feature_key == "supply":
            supply_margin_max = _supply_margin_slider_max(df)
            target_margin = st.slider(
                tr("supply_min_margin"),
                5,
                supply_margin_max,
                min(20, supply_margin_max),
            )
            st.caption(tr("supply_min_margin_note"))
        if feature_key == "price":
            target_margin = st.slider(tr("target_margin"), 5, 40, 20)
        run = st.button(tr("run"), type="primary")

    selected_availability = _availability_for(schema_info, feature_key)
    show_feature_field_usage(feature_key, schema_info, st.session_state["lang"])
    if not selected_availability.get("available", True):
        reason = ", ".join(selected_availability.get("missing", []))
        st.warning(tr("feature_unavailable").format(reason=reason))

    filtered = filter_data(df, marketplace, category, sku)
    single_promo_mode = feature_key == "promo" and mode == tr("mode_one")
    single_product_mode = mode == tr("mode_one")
    st.subheader(tr("dashboard"))
    st.metric(tr("filtered_rows"), f"{len(filtered):,}")
    if single_product_mode:
        show_single_product_data_overview(filtered, st.session_state["lang"])
    else:
        show_marketplace_overview(filtered, st.session_state["lang"])
    if len(filtered) > 1:
        with st.expander(tr("filtered_preview"), expanded=False):
            st.dataframe(filtered.head(50), width="stretch")

    if not run:
        return
    if filtered.empty:
        st.error(tr("empty_selection"))
        return
    if not selected_availability.get("available", True):
        st.error(tr("analysis_stopped"))
        return

    filters = {
        "marketplace": marketplace,
        "category": category,
        "sku": sku,
        "mode": mode,
    }
    if period is not None:
        filters["period"] = period
    lang = st.session_state["lang"]

    if feature_key == "forecast":
        st.subheader(tr("forecast_result"))
        show_active_horizon(period)
        combine_marketplaces = marketplace == tr("all")
        marketplace_scope = tr("all_marketplaces") if combine_marketplaces else marketplace
        result = models.estimate_sku_forecast(
            filtered,
            period,
            combine_marketplaces=combine_marketplaces,
            marketplace_scope=marketplace_scope,
        )
        show_selected_forecast_summary(result, period, lang)
        if mode == tr("mode_all"):
            show_forecast_charts(
                result,
                filtered,
                period,
                lang,
                combine_marketplaces=combine_marketplaces,
                marketplace_scope=marketplace_scope,
            )
        else:
            show_single_forecast_diagnosis(result, period, lang)
        show_forecast_factor_explanation(result, lang)
        show_forecast_output_note(lang)
        if mode == tr("mode_all"):
            show_forecast_result_table(result)
        else:
            show_single_forecast_result_table(result, lang)
        show_forecast_horizon_summary(
            filtered,
            lang,
            combine_marketplaces=combine_marketplaces,
            marketplace_scope=marketplace_scope,
        )
        report = make_report(tr("forecast"), filtered, result, filters, lang, schema_info=schema_info)
        download_buttons(result, report, "demand_forecast")

    elif feature_key == "supply":
        st.subheader(tr("supply_result"))
        show_active_horizon(period)
        result = models.build_supply_plan(filtered, period, target_margin)
        if mode == tr("mode_all"):
            show_supply_summary(result, lang)
            show_supply_charts(result, lang)
            show_supply_result_table(result)
        else:
            show_supply_single_product_summary(result, lang)
            show_single_supply_result_table(result, lang)

        filename = "supply_plan_all_marketplaces"
        if marketplace in MARKETPLACE_FILES:
            filename = MARKETPLACE_FILES[marketplace].replace(".csv", "")
        report = make_report(tr("supply"), filtered, result, filters, lang, schema_info=schema_info)
        download_buttons(result, report, filename)

        if mode == tr("mode_all") and marketplace == tr("all"):
            st.write(tr("marketplace_csv_files"))
            for mkt, fname in MARKETPLACE_FILES.items():
                mkt_result = result[result["marketplace"] == mkt]
                if not mkt_result.empty:
                    st.download_button(
                        fname,
                        mkt_result.to_csv(index=False).encode("utf-8-sig"),
                        fname,
                        "text/csv",
                    )

    elif feature_key == "promo":
        st.subheader(tr("promo_result"))
        result = models.analyze_promo(
            filtered,
            roi_threshold=promo_roi_threshold,
            min_margin_after_ads=promo_min_margin_after_ads,
        )
        if single_promo_mode:
            show_single_promo_diagnosis(
                result,
                promo_roi_threshold,
                promo_min_margin_after_ads,
                lang,
            )
        else:
            show_promo_summary(result, lang)
            show_promo_charts(result, lang)
        show_promo_result_table(result, schema_info.get("derived_columns", []))
        filters["roi_threshold"] = promo_roi_threshold
        filters["min_margin_after_ads"] = promo_min_margin_after_ads
        filters["single_product"] = single_promo_mode
        report = make_report(tr("promo"), filtered, result, filters, lang, schema_info=schema_info)
        download_buttons(result, report, "promo_advertising_analysis")

    elif feature_key == "price":
        st.subheader(tr("price_result"))
        result = models.recommend_prices(filtered, target_margin)
        if mode == tr("mode_all"):
            show_price_summary(result, lang)
            show_price_charts(result, lang)
            show_price_result_table(result)
        else:
            show_single_price_diagnosis(result, target_margin, lang)
            show_single_price_result_table(result, lang)
        report = make_report(tr("price"), filtered, result, filters, lang, schema_info=schema_info)
        download_buttons(result, report, "price_recommendations")


if __name__ == "__main__":
    main()
