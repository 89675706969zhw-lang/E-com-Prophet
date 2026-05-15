import pandas as pd
import streamlit as st

from config import DATA_PATH, TEXT
from schema_utils import standardize_dataframe


def _short_label(value: str, max_length: int = 42) -> str:
    text = str(value).strip()
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def tr(key: str) -> str:
    return TEXT[st.session_state["lang"]][key]


@st.cache_data
def load_data(uploaded_file=None) -> pd.DataFrame:
    """Read a built-in or uploaded CSV and normalize it to the app schema."""
    source = uploaded_file if uploaded_file is not None else DATA_PATH
    try:
        raw = pd.read_csv(source)
    except UnicodeDecodeError:
        raw = pd.read_csv(source, encoding="utf-8-sig")

    df, schema_info = standardize_dataframe(raw)
    df.attrs["schema_info"] = schema_info
    df.attrs["source_name"] = getattr(uploaded_file, "name", DATA_PATH)
    return df


def filter_data(df: pd.DataFrame, marketplace: str, category: str, sku: str) -> pd.DataFrame:
    result = df.copy()
    all_label = tr("all")
    if marketplace != all_label:
        result = result[result["marketplace"].astype(str) == str(marketplace)]
    if category != all_label:
        result = result[result["category"].astype(str) == str(category)]
    if sku != all_label:
        result = result[result["product_sku"].astype(str) == str(sku)]
    result.attrs.update(df.attrs)
    return result


def filter_options(df: pd.DataFrame):
    all_label = tr("all")
    marketplaces = [all_label] + sorted(
        df.get("marketplace", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()
    )
    categories = [all_label] + sorted(
        df.get("category", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()
    )

    sku_labels = {}
    if {"product_sku", "quantity_sold"}.issubset(df.columns):
        top_sku = (
            df.groupby("product_sku")["quantity_sold"]
            .sum()
            .sort_values(ascending=False)
            .head(1500)
            .index
            .astype(str)
            .tolist()
        )
        if "product_name" in df.columns:
            label_source = (
                df[["product_sku", "product_name"]]
                .dropna(subset=["product_sku"])
                .drop_duplicates(subset=["product_sku"])
            )
            for _, row in label_source.iterrows():
                sku_value = str(row["product_sku"])
                name_value = str(row.get("product_name", "")).strip()
                if name_value and name_value.lower() != "unknown":
                    sku_labels[sku_value] = _short_label(name_value)
    else:
        top_sku = []
    skus = [all_label] + sorted(top_sku)
    sku_labels[all_label] = all_label

    return marketplaces, categories, skus, sku_labels
