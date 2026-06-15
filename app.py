import hashlib
import os
from datetime import date, timedelta
from html import escape
from typing import Optional
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import requests


GENESIS_DATE = pd.Timestamp("2009-01-03")
COMMUNITY_BASE_URL = "https://community-api.coinmetrics.io/v4"
PRO_BASE_URL = "https://api.coinmetrics.io/v4"
REQUESTED_METRICS = "PriceUSD,CapMrktCurUSD,CapRealUSD,CapMVRVZ"
FALLBACK_METRICS = "PriceUSD,CapMrktCurUSD,CapMVRVCur"
RISK_COLUMNS = ["price_trend_risk", "mvrv_z_risk", "nupl_risk"]
SCALE_OUT_START = 0.60
ZONE_COLORS = {
    "starter_buy": "#22c55e",
    "deep_buy": "#0f7a3b",
    "buy": "#16a34a",
    "pause": "#6b7280",
    "scale": "#c2410c",
    "high_scale": "#991b1b",
    "unavailable": "#6b7280",
}


def theme_tokens(mode):
    if mode == "Dark":
        return {
            "mode": "dark",
            "app_bg": "#0f1419",
            "sidebar_bg": "#111820",
            "panel_bg": "#151b22",
            "panel_border": "#2f3844",
            "button_bg": "#151b22",
            "field_bg": "#0f1419",
            "primary_text": "#f3f4f6",
            "secondary_text": "#cbd5e1",
            "muted_text": "#94a3b8",
            "accent": "#f7931a",
            "accent_soft": "rgba(247, 147, 26, 0.14)",
            "bar_bg": "#10151c",
            "bar_border": "#3f4a59",
            "marker": "#f8fafc",
            "pause": "#4b5563",
            "chart_template": "plotly_dark",
            "chart_grid": "rgba(148, 163, 184, 0.18)",
            "chart_paper": "#0f1419",
            "chart_plot": "#111827",
            "composite_line": "#f8fafc",
            "btc_price_line": "#cbd5e1",
        }

    return {
        "mode": "light",
        "app_bg": "#ffffff",
        "sidebar_bg": "#f8fafc",
        "panel_bg": "#ffffff",
        "panel_border": "#e5e7eb",
        "button_bg": "#ffffff",
        "field_bg": "#ffffff",
        "primary_text": "#111827",
        "secondary_text": "#374151",
        "muted_text": "#6b7280",
        "accent": "#f7931a",
        "accent_soft": "rgba(247, 147, 26, 0.14)",
        "bar_bg": "#f9fafb",
        "bar_border": "#e5e7eb",
        "marker": "#111827",
        "pause": "#d1d5db",
        "chart_template": "plotly_white",
        "chart_grid": "rgba(107, 114, 128, 0.18)",
        "chart_paper": "#ffffff",
        "chart_plot": "#ffffff",
        "composite_line": "#111111",
        "btc_price_line": "#475569",
    }


def apply_app_theme(st, appearance):
    tokens = theme_tokens(appearance)

    st.markdown(
        f"""
        <style>
            :root {{
                color-scheme: {tokens['mode']};
            }}
            .stApp {{
                background: {tokens['app_bg']};
                color: {tokens['primary_text']};
            }}
            .stApp header[data-testid="stHeader"] {{
                background: {tokens['app_bg']} !important;
                color: {tokens['primary_text']} !important;
                box-shadow: none !important;
            }}
            .stApp [data-testid="stToolbar"] {{
                background: transparent !important;
                color: {tokens['primary_text']} !important;
            }}
            .stApp,
            .stApp p,
            .stApp label,
            .stApp span,
            .stApp div,
            .stApp li {{
                color: {tokens['primary_text']};
            }}
            [data-testid="stSidebar"] {{
                background: {tokens['sidebar_bg']};
                color: {tokens['primary_text']} !important;
            }}
            [data-testid="stSidebar"] *,
            .stApp [data-testid="stWidgetLabel"] *,
            .stApp [data-testid="stRadio"] *,
            .stApp [data-testid="stCheckbox"] *,
            .stApp [data-testid="stNumberInput"] *,
            .stApp [data-testid="stDateInput"] * {{
                color: {tokens['primary_text']} !important;
            }}
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] span,
            [data-testid="stSidebar"] div {{
                color: {tokens['primary_text']} !important;
            }}
            .stApp button {{
                background-color: {tokens['button_bg']} !important;
                color: {tokens['primary_text']} !important;
                border-color: {tokens['panel_border']} !important;
            }}
            .stApp button p,
            .stApp button span,
            .stApp button div {{
                color: {tokens['primary_text']} !important;
            }}
            .stApp button svg,
            [data-testid="stSidebar"] svg {{
                color: {tokens['primary_text']} !important;
                fill: currentColor !important;
            }}
            .stApp input,
            .stApp textarea,
            .stApp [data-baseweb="select"] > div {{
                background-color: {tokens['field_bg']} !important;
                color: {tokens['primary_text']} !important;
                border-color: {tokens['panel_border']} !important;
            }}
            .stApp input::placeholder,
            .stApp textarea::placeholder {{
                color: {tokens['muted_text']} !important;
                opacity: 1;
            }}
            .stApp [data-baseweb="select"] * {{
                color: {tokens['primary_text']} !important;
            }}
            .stApp [data-baseweb="slider"] * {{
                color: {tokens['primary_text']} !important;
            }}
            .stApp [data-testid="stAlert"] {{
                background-color: {tokens['panel_bg']} !important;
                border: 1px solid {tokens['panel_border']} !important;
                border-left: 4px solid {tokens['accent']} !important;
                color: {tokens['primary_text']} !important;
            }}
            .stApp [data-testid="stAlert"] * {{
                color: {tokens['primary_text']} !important;
            }}
            .stApp [data-testid="stAlert"] svg {{
                color: {tokens['primary_text']} !important;
                fill: currentColor !important;
            }}
            [data-testid="stMetric"],
            [data-testid="stDataFrame"],
            div[data-testid="stExpander"] {{
                color: {tokens['primary_text']};
            }}
            .stApp details {{
                background: transparent !important;
                border-color: {tokens['panel_border']} !important;
                color: {tokens['primary_text']} !important;
            }}
            .stApp details > summary {{
                background-color: {tokens['panel_bg']} !important;
                border-color: {tokens['panel_border']} !important;
                color: {tokens['primary_text']} !important;
            }}
            .stApp details[open] > summary {{
                background-color: {tokens['panel_bg']} !important;
                border-color: {tokens['panel_border']} !important;
                color: {tokens['primary_text']} !important;
            }}
            .stApp details > summary:hover {{
                background-color: {tokens['accent_soft']} !important;
            }}
            .stApp details > summary *,
            .stApp details > summary svg,
            .stApp details[open] > summary *,
            .stApp details[open] > summary svg {{
                color: {tokens['primary_text']} !important;
                fill: currentColor !important;
            }}
            .section-heading-row {{
                align-items: center;
                display: flex;
                gap: 10px;
                justify-content: flex-start;
                margin: 0.7rem 0 0.35rem;
            }}
            .section-heading-row h3 {{
                color: {tokens['primary_text']} !important;
                font-size: 1.75rem;
                font-weight: 750;
                letter-spacing: 0;
                line-height: 1.2;
                margin: 0;
            }}
            .stApp h1 a[href^="#"],
            .stApp h2 a[href^="#"],
            .stApp h3 a[href^="#"],
            .stApp [data-testid="stHeading"] a[href^="#"],
            .stApp .stHeading a[href^="#"],
            .stApp a.anchor-link {{
                display: none !important;
                pointer-events: none !important;
                visibility: hidden !important;
            }}
            .info-popover {{
                background: transparent !important;
                border: 0 !important;
                color: {tokens['primary_text']} !important;
                display: inline-flex !important;
                flex: 0 0 auto;
                line-height: 1;
                margin: 0;
                padding: 0;
                position: relative;
                width: max-content;
            }}
            .info-popover > summary {{
                align-items: center;
                background: {tokens['panel_bg']} !important;
                border: 1px solid {tokens['panel_border']} !important;
                border-radius: 999px;
                color: {tokens['primary_text']} !important;
                cursor: pointer;
                display: inline-flex;
                font-size: 0.78rem;
                font-weight: 800;
                height: 30px;
                justify-content: center;
                line-height: 1;
                list-style: none;
                padding: 0;
                user-select: none;
                width: 30px;
            }}
            .info-popover > summary::-webkit-details-marker {{
                display: none;
            }}
            .info-popover[open] > summary,
            .info-popover > summary:hover {{
                background: {tokens['accent_soft']} !important;
                border-color: {tokens['accent']} !important;
            }}
            .info-popover-body {{
                background: {tokens['panel_bg']};
                border: 1px solid {tokens['panel_border']};
                border-radius: 8px;
                box-shadow: 0 16px 40px rgba(0, 0, 0, 0.22);
                color: {tokens['primary_text']} !important;
                font-size: 0.88rem;
                font-weight: 500;
                line-height: 1.45;
                max-width: min(320px, calc(100vw - 48px));
                min-width: 240px;
                padding: 12px 14px;
                position: absolute;
                right: 0;
                text-align: left;
                top: 36px;
                z-index: 100;
            }}
            .info-popover-body p {{
                color: {tokens['secondary_text']} !important;
                margin: 0;
            }}
            .component-risk-card {{
                margin-bottom: 8px;
            }}
            .component-risk-label-row {{
                align-items: center;
                display: inline-flex;
                gap: 6px;
                margin-bottom: 4px;
            }}
            .component-risk-label {{
                color: {tokens['primary_text']} !important;
                font-size: 0.9rem;
                font-weight: 650;
                line-height: 1.2;
            }}
            .component-risk-label-row .info-popover > summary {{
                font-size: 0.68rem;
                height: 22px;
                width: 22px;
            }}
            .component-risk-label-row .info-popover-body {{
                left: 0;
                right: auto;
                top: 28px;
            }}
            .component-risk-value {{
                color: {tokens['primary_text']} !important;
                font-size: 2rem;
                font-weight: 500;
                letter-spacing: 0;
                line-height: 1.15;
                margin-bottom: 6px;
            }}
            .component-risk-band {{
                align-items: center;
                border-radius: 999px;
                display: inline-flex;
                font-size: 0.8rem;
                font-weight: 650;
                line-height: 1;
                padding: 5px 8px;
            }}
            .stApp [data-testid="stMetric"] *,
            .stApp [data-testid="stCaptionContainer"] *,
            .stApp div[data-testid="stExpander"] summary *,
            .stApp div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] * {{
                color: {tokens['primary_text']} !important;
            }}
            h1, h2, h3, h4, p, label, span {{
                color: inherit;
            }}
            .stApp .js-plotly-plot .main-svg text,
            .stApp .js-plotly-plot .legendtext,
            .stApp .js-plotly-plot .xtick text,
            .stApp .js-plotly-plot .ytick text,
            .stApp .js-plotly-plot .ytitle,
            .stApp .js-plotly-plot .y2title,
            .stApp .js-plotly-plot .annotation-text {{
                fill: {tokens['primary_text']} !important;
                color: {tokens['primary_text']} !important;
            }}
            .stApp .js-plotly-plot .modebar-btn svg path {{
                fill: {tokens['primary_text']} !important;
            }}
            .btc-header {{
                display: flex;
                align-items: center;
                gap: 14px;
                margin: 2px 0 10px;
                padding: 4px 0 2px;
            }}
            .btc-logo {{
                align-items: center;
                background: radial-gradient(circle at 34% 28%, #ffc46b, {tokens['accent']} 56%, #c76c00 100%);
                border: 1px solid rgba(255, 255, 255, 0.34);
                border-radius: 999px;
                box-shadow: 0 10px 24px rgba(247, 147, 26, 0.28);
                color: #ffffff !important;
                display: inline-flex;
                flex: 0 0 auto;
                font-size: 2rem;
                font-weight: 850;
                height: 52px;
                justify-content: center;
                line-height: 1;
                width: 52px;
            }}
            .btc-header-title {{
                color: {tokens['primary_text']} !important;
                font-size: 2.25rem;
                font-weight: 800;
                letter-spacing: 0;
                line-height: 1.06;
            }}
            .btc-header-subtitle {{
                color: {tokens['secondary_text']} !important;
                font-size: 1rem;
                line-height: 1.4;
                margin-top: 5px;
            }}
            .btc-context-line {{
                color: {tokens['secondary_text']} !important;
                display: flex;
                flex-wrap: wrap;
                gap: 6px 10px;
                font-size: 0.88rem;
                font-weight: 650;
                line-height: 1.35;
                margin: 4px 0 18px;
            }}
            .btc-context-line span {{
                color: {tokens['secondary_text']} !important;
            }}
            .btc-context-line .dot {{
                color: {tokens['muted_text']} !important;
                font-weight: 700;
            }}
            @media (max-width: 640px) {{
                .btc-header {{
                    align-items: flex-start;
                    gap: 10px;
                }}
                .btc-logo {{
                    font-size: 1.55rem;
                    height: 42px;
                    width: 42px;
                }}
                .btc-header-title {{
                    font-size: 1.65rem;
                }}
                .btc-header-subtitle {{
                    font-size: 0.92rem;
                }}
                .btc-context-line {{
                    font-size: 0.8rem;
                    margin: 2px 0 14px;
                }}
                .section-heading-row h3 {{
                    font-size: 1.55rem;
                }}
                .info-popover > summary {{
                    height: 30px;
                    width: 30px;
                }}
                .section-heading-row .info-popover-body {{
                    left: auto;
                    right: 0;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    return tokens


def normalize_risk(values, lower_quantile=0.05, upper_quantile=0.95):
    """Normalize a numeric signal to 0-1 by quantile clipping."""
    series = pd.Series(values, dtype="float64")

    if not 0 <= lower_quantile < upper_quantile <= 1:
        raise ValueError("Quantiles must satisfy 0 <= lower < upper <= 1.")

    lower = series.quantile(lower_quantile)
    upper = series.quantile(upper_quantile)

    if not np.isfinite(lower) or not np.isfinite(upper):
        return pd.Series(np.nan, index=series.index, dtype="float64")

    if np.isclose(upper, lower):
        result = pd.Series(np.nan, index=series.index, dtype="float64")
        result.loc[series.notna()] = 0.5
        return result

    return ((series - lower) / (upper - lower)).clip(0, 1)


def calculate_nupl(market_cap, realized_cap):
    market = pd.Series(market_cap, dtype="float64")
    realized = pd.Series(realized_cap, dtype="float64")
    nupl = (market - realized) / market.replace(0, np.nan)

    if np.isscalar(market_cap) and np.isscalar(realized_cap):
        return float(nupl.iloc[0])
    return nupl


def calculate_mvrv_z_fallback(market_cap, realized_cap, min_periods=30):
    market = pd.Series(market_cap, dtype="float64")
    realized = pd.Series(realized_cap, dtype="float64")
    cumulative_std = market.expanding(min_periods=min_periods).std().replace(0, np.nan)
    return (market - realized) / cumulative_std


def calculate_composite_risk(frame):
    return frame[RISK_COLUMNS].sum(axis=1, min_count=len(RISK_COLUMNS)) / len(RISK_COLUMNS)


def dynamic_dca_plan(max_buy_risk=0.30, base_amount=100.0):
    """Build transcript-inspired dynamic DCA bands from low to max buy risk."""
    band_count = int(round(max_buy_risk * 10))
    rows = []

    for band_index in reversed(range(band_count)):
        lower = band_index / 10
        upper = (band_index + 1) / 10
        multiplier = band_count - band_index
        rows.append(
            {
                "risk_band": f"{lower:.1f}-{upper:.1f}",
                "multiplier": multiplier,
                "illustrative_amount": float(base_amount) * multiplier,
            }
        )

    return rows


def dynamic_dca_recommendation(risk, max_buy_risk=0.30, base_amount=100.0):
    """Map a 0-1 risk value to the transcript's dynamic DCA style."""
    if pd.isna(risk):
        return {
            "zone": "Unavailable",
            "action": "Risk score unavailable",
            "multiplier": np.nan,
            "amount": np.nan,
        }

    risk = float(np.clip(risk, 0, 1))
    band_count = int(round(max_buy_risk * 10))

    if risk < max_buy_risk:
        band_index = min(int(risk * 10), band_count - 1)
        lower = band_index / 10
        upper = (band_index + 1) / 10
        multiplier = band_count - band_index
        return {
            "zone": f"{lower:.1f}-{upper:.1f} risk",
            "action": "Dynamic DCA area",
            "multiplier": multiplier,
            "amount": float(base_amount) * multiplier,
        }

    if risk < SCALE_OUT_START:
        return {
            "zone": f"{max_buy_risk:.1f}-{SCALE_OUT_START:.1f} risk",
            "action": "No-buy / patience area",
            "multiplier": 0,
            "amount": 0.0,
        }

    return {
        "zone": f">={SCALE_OUT_START:.1f} risk",
        "action": "Scale-out review area",
        "multiplier": 0,
        "amount": 0.0,
    }


def add_dynamic_dca_columns(frame, max_buy_risk=0.30, base_amount=100.0):
    working = frame.copy()
    recommendations = working["composite_risk"].apply(
        lambda risk: dynamic_dca_recommendation(risk, max_buy_risk, base_amount)
    )
    working["dynamic_dca_zone"] = recommendations.apply(lambda item: item["zone"])
    working["dynamic_dca_action"] = recommendations.apply(lambda item: item["action"])
    working["dynamic_dca_multiplier"] = recommendations.apply(lambda item: item["multiplier"])
    working["dynamic_dca_amount"] = recommendations.apply(lambda item: item["amount"])
    return working


def calculate_price_trend_metrics(frame):
    working = frame.copy()
    working["days_since_genesis"] = (
        pd.to_datetime(working["time"]).dt.tz_localize(None) - GENESIS_DATE
    ).dt.days

    valid = (working["PriceUSD"] > 0) & (working["days_since_genesis"] > 0)
    valid = valid & working["PriceUSD"].notna()

    working["trend_price"] = np.nan
    working["price_trend_residual"] = np.nan

    if valid.sum() < 2:
        return working, np.nan, np.nan

    log_days = np.log10(working.loc[valid, "days_since_genesis"])
    log_prices = np.log10(working.loc[valid, "PriceUSD"])
    slope, intercept = np.polyfit(log_days, log_prices, 1)

    fitted_log_price = intercept + slope * np.log10(working.loc[valid, "days_since_genesis"])
    working.loc[valid, "trend_price"] = np.power(10, fitted_log_price)
    working.loc[valid, "price_trend_residual"] = np.log10(
        working.loc[valid, "PriceUSD"] / working.loc[valid, "trend_price"]
    )

    return working, intercept, slope


def calculate_risk_dataset(raw_data, lower_quantile=0.05, upper_quantile=0.95):
    frame = raw_data.copy()
    frame["time"] = pd.to_datetime(frame["time"], utc=True)

    for column in ["PriceUSD", "CapMrktCurUSD", "CapRealUSD", "CapMVRVZ", "CapMVRVCur"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.sort_values("time").reset_index(drop=True)

    if "CapRealUSD" in frame.columns and frame["CapRealUSD"].notna().any():
        realized_cap_source = "Coin Metrics CapRealUSD"
        if "CapMVRVCur" in frame.columns and frame["CapMVRVCur"].notna().any():
            derived_realized_cap = frame["CapMrktCurUSD"] / frame["CapMVRVCur"].replace(0, np.nan)
            frame["CapRealUSD"] = frame["CapRealUSD"].fillna(derived_realized_cap)
    elif "CapMVRVCur" in frame.columns and frame["CapMVRVCur"].notna().any():
        frame["CapRealUSD"] = frame["CapMrktCurUSD"] / frame["CapMVRVCur"].replace(0, np.nan)
        realized_cap_source = "Derived from Coin Metrics CapMVRVCur"
    else:
        raise ValueError(
            "Realized cap is unavailable. Set COINMETRICS_API_KEY or use a date range "
            "where CapRealUSD or CapMVRVCur is available."
        )

    frame, intercept, slope = calculate_price_trend_metrics(frame)
    frame["price_trend_risk"] = normalize_risk(
        frame["price_trend_residual"], lower_quantile, upper_quantile
    )

    fallback_mvrv_z = calculate_mvrv_z_fallback(frame["CapMrktCurUSD"], frame["CapRealUSD"])
    if "CapMVRVZ" in frame.columns and frame["CapMVRVZ"].notna().any():
        frame["mvrv_z_raw"] = frame["CapMVRVZ"].fillna(fallback_mvrv_z)
        if frame["CapMVRVZ"].isna().any():
            mvrv_source = "Coin Metrics CapMVRVZ, with fallback for missing rows"
        else:
            mvrv_source = "Coin Metrics CapMVRVZ"
    else:
        frame["mvrv_z_raw"] = fallback_mvrv_z
        mvrv_source = "Fallback calculation"

    frame["mvrv_z_risk"] = normalize_risk(frame["mvrv_z_raw"], lower_quantile, upper_quantile)
    frame["nupl_raw"] = calculate_nupl(frame["CapMrktCurUSD"], frame["CapRealUSD"])
    frame["nupl_risk"] = normalize_risk(frame["nupl_raw"], lower_quantile, upper_quantile)
    frame["composite_risk"] = calculate_composite_risk(frame)

    metadata = {
        "power_law_intercept": intercept,
        "power_law_slope": slope,
        "mvrv_source": mvrv_source,
        "realized_cap_source": realized_cap_source,
    }
    return frame, metadata


def coinmetrics_base_url(api_key: Optional[str]) -> str:
    return PRO_BASE_URL if api_key else COMMUNITY_BASE_URL


def api_key_fingerprint(api_key: Optional[str]) -> str:
    if not api_key:
        return "community"
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def is_coinmetrics_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.netloc in {
        "community-api.coinmetrics.io",
        "api.coinmetrics.io",
    }


def fetch_coinmetrics_pages(start_date, end_date, metrics, api_key):
    endpoint = f"{coinmetrics_base_url(api_key)}/timeseries/asset-metrics"
    params = {
        "assets": "btc",
        "frequency": "1d",
        "metrics": metrics,
        "page_size": 10000,
        "start_time": str(start_date),
        "end_time": str(end_date),
    }
    if api_key:
        params["api_key"] = api_key

    rows = []
    next_url = endpoint
    request_params = params

    while next_url:
        if not is_coinmetrics_url(next_url):
            raise ValueError(f"Unexpected pagination URL from Coin Metrics: {next_url}")

        response = requests.get(next_url, params=request_params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        rows.extend(payload.get("data", []))
        next_url = payload.get("next_page_url")
        request_params = {"api_key": api_key} if api_key and next_url else None

    if not rows:
        raise ValueError("Coin Metrics returned no rows for the selected date range.")

    return pd.DataFrame(rows)


def fetch_coinmetrics_data(start_date, end_date):
    api_key = os.getenv("COINMETRICS_API_KEY")

    try:
        return fetch_coinmetrics_pages(start_date, end_date, REQUESTED_METRICS, api_key)
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code not in {400, 403, 404}:
            raise

        # Some Coin Metrics plans do not expose CapMVRVZ. The app can still run
        # from market cap and realized cap, then use the documented fallback.
        return fetch_coinmetrics_pages(start_date, end_date, FALLBACK_METRICS, api_key)


def risk_band(value):
    if pd.isna(value):
        return "Unavailable"
    if value < 0.25:
        return "Low"
    if value < 0.50:
        return "Moderate"
    if value < 0.75:
        return "High"
    return "Extreme"


def risk_band_color(value):
    band = risk_band(value)
    return {
        "Low": "#16a34a",
        "Moderate": "#ca8a04",
        "High": "#c2410c",
        "Extreme": "#b91c1c",
        "Unavailable": "#6b7280",
    }[band]


def format_risk(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:.3f}"


def format_as_of_date(value):
    if pd.isna(value):
        return "latest available date"
    parsed = pd.to_datetime(value).date()
    return f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"


def format_usd(value):
    if pd.isna(value):
        return "N/A"
    return f"${float(value):,.0f}"


def period_suffix(period):
    if period == "Weekly":
        return "/ week"
    if period == "Monthly":
        return "/ month"
    if period == "Custom period":
        return "/ custom period"
    return ""


def format_period_amount(value, period):
    return f"{format_usd(value)} {period_suffix(period)}".strip()


def risk_direction(current_risk, previous_risk, tolerance=0.005):
    if pd.isna(current_risk) or pd.isna(previous_risk):
        return "flat"
    if current_risk > previous_risk + tolerance:
        return "rising"
    if current_risk < previous_risk - tolerance:
        return "falling"
    return "flat"


def cycle_framework_signal(
    risk,
    previous_risk=np.nan,
    max_buy_risk=0.30,
    base_amount=100.0,
    dca_period="Weekly",
):
    """Translate risk into a simple transcript-inspired zone signal."""
    if pd.isna(risk):
        return {
            "zone": "Unavailable",
            "signal": "No current signal",
            "detail": "A current composite risk score is not available.",
            "amount": np.nan,
            "multiplier": np.nan,
            "color": ZONE_COLORS["unavailable"],
            "direction": "flat",
            "weight_label": "No weight",
            "visual_weight": 1,
        }

    risk = float(np.clip(risk, 0, 1))
    direction = risk_direction(risk, previous_risk)
    band_count = int(round(max_buy_risk * 10))

    if risk < max_buy_risk:
        band_index = min(int(risk * 10), band_count - 1)
        lower = band_index / 10
        upper = (band_index + 1) / 10
        multiplier = band_count - band_index

        if multiplier >= 3:
            signal = "Heaviest DCA zone"
            zone = "Deep DCA zone"
            color = ZONE_COLORS["deep_buy"]
        elif multiplier == 2:
            signal = "Heavier DCA zone"
            zone = "DCA zone"
            color = ZONE_COLORS["buy"]
        else:
            signal = "Framework DCA zone"
            zone = "DCA zone"
            color = ZONE_COLORS["starter_buy"]

        if direction == "rising" and upper >= max_buy_risk:
            signal = "Still DCA zone, nearing pause"

        return {
            "zone": zone,
            "signal": signal,
            "detail": (
                f"Composite risk is in the {lower:.1f}-{upper:.1f} band. "
                "The framework increases DCA size as risk moves lower."
            ),
            "amount": float(base_amount) * multiplier,
            "multiplier": multiplier,
            "color": color,
            "direction": direction,
            "weight_label": f"DCA weight: {multiplier}x base",
            "amount_label": f"Framework amount: {format_period_amount(float(base_amount) * multiplier, dca_period)}",
            "visual_weight": multiplier,
        }

    if risk < SCALE_OUT_START:
        crossed_up = not pd.isna(previous_risk) and previous_risk < max_buy_risk <= risk
        return {
            "zone": "Pause zone",
            "signal": "Time to pause" if crossed_up or risk < 0.40 else "Patience zone",
            "detail": (
                "Risk is above the selected buy ceiling but below the scale-out area. "
                "In the transcript framework, this is the middle zone where you stop "
                "forcing buys and wait."
            ),
            "amount": 0.0,
            "multiplier": 0,
            "color": ZONE_COLORS["pause"],
            "direction": direction,
            "weight_label": "Pause weight: 0x",
            "amount_label": "Framework amount: pause",
            "visual_weight": 1,
        }

    if risk < 0.70:
        signal = "Maybe DCA out"
        zone = "Early scale-out zone"
        color = ZONE_COLORS["scale"]
        visual_weight = 1
    elif risk < 0.80:
        signal = "A little more DCA out"
        zone = "Scale-out zone"
        color = ZONE_COLORS["scale"]
        visual_weight = 2
    elif risk < 0.90:
        signal = "More DCA out"
        zone = "High scale-out zone"
        color = ZONE_COLORS["high_scale"]
        visual_weight = 3
    else:
        signal = "Heaviest DCA out"
        zone = "Extreme scale-out zone"
        color = ZONE_COLORS["high_scale"]
        visual_weight = 4

    return {
        "zone": zone,
        "signal": signal,
        "detail": (
            "Risk is in the upside area. The transcript describes scaling out gradually "
            "rather than trying to sell one exact top."
        ),
        "amount": 0.0,
        "multiplier": 0,
        "color": color,
        "direction": direction,
        "weight_label": f"DCA-out review weight: {visual_weight}",
        "amount_label": "Framework amount: DCA-out review",
        "visual_weight": visual_weight,
    }


def framework_zone_table(max_buy_risk=0.30, base_amount=100.0, dca_period="Weekly"):
    rows = []
    band_count = int(round(max_buy_risk * 10))

    for band_index in reversed(range(band_count)):
        lower = band_index / 10
        upper = (band_index + 1) / 10
        multiplier = band_count - band_index
        if multiplier >= 3:
            signal = "Heaviest DCA zone"
        elif multiplier == 2:
            signal = "Heavier DCA zone"
        else:
            signal = "Framework DCA zone"
        rows.append(
            {
                "Zone": f"{lower:.1f}-{upper:.1f}",
                "Readout": signal,
                "Action": f"{multiplier}x base DCA ({format_period_amount(float(base_amount) * multiplier, dca_period)})",
            }
        )

    rows.extend(
        [
            {"Zone": f"{max_buy_risk:.1f}-0.6", "Readout": "Time to pause", "Action": "No forced buy"},
            {"Zone": "0.6-0.7", "Readout": "Maybe DCA out", "Action": "Small scale-out review"},
            {"Zone": "0.7-0.8", "Readout": "A little more DCA out", "Action": "Increase scale-out review"},
            {"Zone": "0.8-0.9", "Readout": "More DCA out", "Action": "Larger scale-out review"},
            {"Zone": "0.9-1.0", "Readout": "Heaviest DCA out", "Action": "Most aggressive scale-out review"},
        ]
    )
    return rows


def info_popover_html(help_text):
    text = " ".join(line.strip() for line in help_text.splitlines() if line.strip())
    return (
        '<details class="info-popover">'
        '<summary aria-label="More information">?</summary>'
        f'<div class="info-popover-body"><p>{escape(text)}</p></div>'
        "</details>"
    )


def section_header(title, help_text):
    import streamlit as st

    st.markdown(
        f"""
        <div class="section-heading-row">
            <h3>{escape(title)}</h3>
            {info_popover_html(help_text)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_app_header():
    import streamlit as st

    st.markdown(
        """
        <div class="btc-header">
            <div class="btc-logo" role="img" aria-label="Bitcoin">₿</div>
            <div>
                <div class="btc-header-title">BTC Cycle Risk Dashboard</div>
                <div class="btc-header-subtitle">
                    Bitcoin cycle risk, simplified into one current signal.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_context_line(as_of_label):
    import streamlit as st

    st.markdown(
        f"""
        <div class="btc-context-line">
            <span>As of {as_of_label}</span>
            <span class="dot">•</span>
            <span>Daily Coin Metrics data</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_disclosure_expander(as_of_label, api_mode, metadata):
    import streamlit as st

    with st.expander("Educational framework and data notes", expanded=False):
        st.markdown(
            f"""
            This dashboard is not investment advice, not a buy/sell instruction,
            and not a proprietary risk model.

            Risk readings are calculated from daily Coin Metrics data as of
            **{as_of_label}**. The app is refreshed from daily macro data, not
            live tick-by-tick BTC pricing.

            Data source: **Coin Metrics {api_mode}**. MVRV Z source:
            **{metadata['mvrv_source']}**. Realized cap source:
            **{metadata['realized_cap_source']}**.
            """
        )


def render_signal_card(signal, risk, as_of_label, tokens):
    import streamlit as st

    visual_weight = int(signal.get("visual_weight") or 1)
    border_width = min(14, 6 + (visual_weight * 2))
    badge_bg = f"{signal['color']}22"
    amount_label = signal.get("amount_label") or signal.get("zone", "Current zone")

    st.markdown(
        f"""
        <div style="
            border: 1px solid {tokens['panel_border']};
            border-left: {border_width}px solid {signal['color']};
            border-radius: 8px;
            padding: 18px 20px;
            background: {tokens['panel_bg']};
            margin-bottom: 12px;
        ">
            <div style="font-size: 0.82rem; color: {tokens['muted_text']}; font-weight: 600; text-transform: uppercase;">
                Current zone as of {as_of_label}
            </div>
            <div style="font-size: 2rem; line-height: 1.15; font-weight: 750; margin-top: 4px; color: {tokens['primary_text']};">
                {signal['signal']}
            </div>
            <div style="font-size: 1.05rem; color: {tokens['secondary_text']}; margin-top: 4px;">
                {signal['zone']} | Composite risk {format_risk(risk)}
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px;">
                <span style="
                    display: inline-flex;
                    align-items: center;
                    border: 1px solid {signal['color']};
                    background: {badge_bg};
                    color: {tokens['primary_text']};
                    border-radius: 999px;
                    padding: 4px 10px;
                    font-size: 0.82rem;
                    font-weight: 750;
                ">{signal.get('weight_label', 'Current weight')}</span>
                <span style="
                    display: inline-flex;
                    align-items: center;
                    border: 1px solid {tokens['panel_border']};
                    color: {tokens['secondary_text']};
                    border-radius: 999px;
                    padding: 4px 10px;
                    font-size: 0.82rem;
                    font-weight: 650;
                ">{amount_label}</span>
            </div>
            <div style="font-size: 0.95rem; color: {tokens['secondary_text']}; margin-top: 10px;">
                {signal['detail']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_zone_bar(risk, max_buy_risk=0.30, tokens=None, signal=None):
    import streamlit as st

    tokens = tokens or theme_tokens("Light")
    marker = 0 if pd.isna(risk) else max(0, min(100, float(risk) * 100))
    signal = signal or {}
    visual_weight = int(signal.get("visual_weight") or 1)
    marker_width = min(9, 3 + (visual_weight * 2))
    marker_height = min(48, 30 + (visual_weight * 4))
    marker_top = -((marker_height - 20) / 2)
    marker_shadow = f"0 0 0 2px {tokens['panel_bg']}, 0 0 0 {visual_weight + 1}px {signal.get('color', tokens['marker'])}55"
    buy_width = max_buy_risk * 100
    pause_width = max(0, (SCALE_OUT_START - max_buy_risk) * 100)
    scale_width = (1 - SCALE_OUT_START) * 100

    st.markdown(
        f"""
        <div style="margin: 8px 0 22px;">
            <div style="position: relative; height: 58px;">
                <div style="
                    display: flex;
                    height: 20px;
                    border-radius: 999px;
                    overflow: hidden;
                    border: 1px solid {tokens['bar_border']};
                    background: {tokens['bar_bg']};
                ">
                    <div style="width: {buy_width}%; background: linear-gradient(90deg, #0f7a3b, #22c55e);"></div>
                    <div style="width: {pause_width}%; background: {tokens['pause']};"></div>
                    <div style="width: {scale_width}%; background: linear-gradient(90deg, #f97316, #991b1b);"></div>
                </div>
                <div style="
                    position: absolute;
                    left: calc({marker}% - {marker_width / 2}px);
                    top: {marker_top}px;
                    height: {marker_height}px;
                    width: {marker_width}px;
                    background: {tokens['marker']};
                    border-radius: 2px;
                    box-shadow: {marker_shadow};
                "></div>
                <div style="
                    position: absolute;
                    left: calc({marker}% - 42px);
                    top: 30px;
                    width: 84px;
                    text-align: center;
                    font-size: 0.78rem;
                    color: {tokens['primary_text']};
                    font-weight: 700;
                ">You are here</div>
            </div>
            <div style="
                display: grid;
                grid-template-columns: {buy_width}% {pause_width}% {scale_width}%;
                column-gap: 0;
                font-size: 0.8rem;
                color: {tokens['secondary_text']};
                font-weight: 650;
            ">
                <div>DCA zone<br><span style="font-weight: 500;">0.0-{max_buy_risk:.1f}</span></div>
                <div style="text-align: center;">Pause<br><span style="font-weight: 500;">{max_buy_risk:.1f}-0.6</span></div>
                <div style="text-align: right;">DCA out review<br><span style="font-weight: 500;">0.6-1.0</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_compact_zone_reference(risk, max_buy_risk=0.30, tokens=None, signal=None):
    import streamlit as st

    tokens = tokens or theme_tokens("Light")
    marker = 0 if pd.isna(risk) else max(0, min(100, float(risk) * 100))
    signal = signal or {}
    visual_weight = int(signal.get("visual_weight") or 1)
    marker_width = min(7, 3 + visual_weight)
    buy_width = max_buy_risk * 100
    pause_width = max(0, (SCALE_OUT_START - max_buy_risk) * 100)
    scale_width = (1 - SCALE_OUT_START) * 100
    label = f"Current composite risk: {format_risk(risk)}"

    st.markdown(
        f"""
        <div style="
            border: 1px solid {tokens['panel_border']};
            background: {tokens['panel_bg']};
            border-radius: 8px;
            padding: 10px 12px 8px;
            margin: 4px 0 12px;
        ">
            <div style="
                display: flex;
                justify-content: space-between;
                gap: 12px;
                align-items: baseline;
                color: {tokens['secondary_text']};
                font-size: 0.82rem;
                font-weight: 700;
                margin-bottom: 8px;
            ">
                <span>Chart zone reference</span>
                <span>{label}</span>
            </div>
            <div style="position: relative; height: 28px;">
                <div style="
                    display: flex;
                    height: 14px;
                    border-radius: 999px;
                    overflow: hidden;
                    border: 1px solid {tokens['bar_border']};
                    background: {tokens['bar_bg']};
                ">
                    <div title="DCA zone" style="width: {buy_width}%; background: linear-gradient(90deg, #0f7a3b, #22c55e);"></div>
                    <div title="Pause" style="width: {pause_width}%; background: {tokens['pause']};"></div>
                    <div title="DCA out review" style="width: {scale_width}%; background: linear-gradient(90deg, #f97316, #991b1b);"></div>
                </div>
                <div style="
                    position: absolute;
                    left: calc({marker}% - {marker_width / 2}px);
                    top: -5px;
                    height: 24px;
                    width: {marker_width}px;
                    background: {tokens['marker']};
                    border-radius: 2px;
                    box-shadow: 0 0 0 2px {tokens['panel_bg']}, 0 0 0 3px {signal.get('color', tokens['marker'])}66;
                "></div>
            </div>
            <div style="
                display: grid;
                grid-template-columns: {buy_width}% {pause_width}% {scale_width}%;
                font-size: 0.74rem;
                color: {tokens['muted_text']};
                font-weight: 650;
                line-height: 1.25;
            ">
                <div>DCA</div>
                <div style="text-align: center;">Pause</div>
                <div style="text-align: right;">DCA out</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_component_risks(current, tokens):
    import streamlit as st

    component_columns = st.columns(3)
    component_specs = [
        (
            "Price-trend",
            current.get("price_trend_risk"),
            "Compares BTC price to a fitted long-term power-law trend. Higher means price is farther above trend.",
        ),
        (
            "MVRV Z",
            current.get("mvrv_z_risk"),
            "Compares market value to realized value. Higher means market cap is stretched versus realized cap.",
        ),
        (
            "NUPL",
            current.get("nupl_risk"),
            "Measures unrealized profit/loss across holders. Higher means more aggregate holder profit.",
        ),
    ]
    for column, (label, value, help_text) in zip(component_columns, component_specs):
        band = risk_band(value)
        band_color = risk_band_color(value)
        with column:
            st.markdown(
                f"""
                <div class="component-risk-card">
                    <div class="component-risk-label-row">
                        <span class="component-risk-label">{escape(label)}</span>
                        {info_popover_html(help_text)}
                    </div>
                    <div class="component-risk-value">{format_risk(value)}</div>
                    <span
                        class="component-risk-band"
                        style="
                            background: {band_color}18;
                            border: 1px solid {band_color}55;
                            color: {tokens['primary_text']} !important;
                        "
                    >
                        {escape(band)}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_risk_chart(
    frame,
    chart_options,
    show_dca_guide,
    dca_ceiling,
    tokens,
    current=None,
    current_signal=None,
):
    import streamlit as st

    if show_dca_guide and current is not None:
        render_compact_zone_reference(
            current.get("composite_risk"),
            dca_ceiling,
            tokens,
            current_signal,
        )

    st.plotly_chart(
        build_chart(frame, chart_options, show_dca_guide, dca_ceiling, tokens),
        use_container_width=True,
    )


def build_chart(frame, chart_options=None, show_dca_zones=False, max_buy_risk=0.30, tokens=None):
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    tokens = tokens or theme_tokens("Light")
    axis_font = {"color": tokens["primary_text"], "size": 12}
    title_font = {"color": tokens["primary_text"], "size": 13}
    chart_options = chart_options or {
        "show_price_trend": False,
        "show_mvrv_z": False,
        "show_nupl": False,
        "show_composite": True,
        "show_btc_price": True,
    }
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    traces = [
        ("Price-trend risk", "price_trend_risk", "#2d7dd2", 1.8),
        ("MVRV Z risk", "mvrv_z_risk", "#f45d01", 1.8),
        ("NUPL risk", "nupl_risk", "#33a02c", 1.8),
        ("Composite risk", "composite_risk", tokens["composite_line"], 3.0),
    ]
    trace_keys = {
        "price_trend_risk": "show_price_trend",
        "mvrv_z_risk": "show_mvrv_z",
        "nupl_risk": "show_nupl",
        "composite_risk": "show_composite",
    }

    for name, column, color, width in traces:
        if not chart_options.get(trace_keys[column], True):
            continue
        fig.add_trace(
            go.Scatter(
                x=frame["time"],
                y=frame[column],
                mode="lines",
                name=name,
                line={"color": color, "width": width},
            ),
            secondary_y=False,
        )

    if chart_options.get("show_btc_price", True):
        price_frame = frame[frame["PriceUSD"] > 0]
        fig.add_trace(
            go.Scatter(
                x=price_frame["time"],
                y=price_frame["PriceUSD"],
                mode="lines",
                name="BTC price",
                line={"color": tokens["btc_price_line"], "width": 1.6, "dash": "dot"},
                opacity=0.95,
            ),
            secondary_y=True,
        )
        fig.update_yaxes(
            title_text="BTC price (USD, log scale)",
            title_font=title_font,
            tickfont=axis_font,
            color=tokens["primary_text"],
            linecolor=tokens["panel_border"],
            zerolinecolor=tokens["panel_border"],
            type="log",
            secondary_y=True,
        )
    else:
        fig.update_yaxes(visible=False, secondary_y=True)

    if show_dca_zones:
        band_shapes = [
            (0, 0.10, "rgba(15, 122, 59, 0.18)"),
            (0.10, 0.20, "rgba(31, 157, 85, 0.14)"),
            (0.20, max_buy_risk, "rgba(34, 197, 94, 0.10)"),
            (max_buy_risk, SCALE_OUT_START, "rgba(107, 114, 128, 0.08)"),
            (SCALE_OUT_START, 0.70, "rgba(249, 115, 22, 0.10)"),
            (0.70, 0.80, "rgba(234, 88, 12, 0.12)"),
            (0.80, 0.90, "rgba(220, 38, 38, 0.12)"),
            (0.90, 1.0, "rgba(153, 27, 27, 0.14)"),
        ]
    else:
        band_shapes = [
            (0, 0.25, "rgba(76, 175, 80, 0.08)"),
            (0.25, 0.50, "rgba(255, 193, 7, 0.08)"),
            (0.50, 0.75, "rgba(255, 152, 0, 0.08)"),
            (0.75, 1.0, "rgba(244, 67, 54, 0.08)"),
        ]
    for y0, y1, color in band_shapes:
        fig.add_hrect(y0=y0, y1=y1, fillcolor=color, line_width=0, secondary_y=False)

    if show_dca_zones:
        fig.add_hline(
            y=max_buy_risk,
            line_dash="dash",
            line_color="#0f8b4c",
            annotation_text=f"Dynamic DCA ceiling {max_buy_risk:.1f}",
            annotation_position="bottom left",
        )
        fig.add_hline(
            y=SCALE_OUT_START,
            line_dash="dash",
            line_color="#9c2f2f",
            annotation_text=f"Scale-out review {SCALE_OUT_START:.1f}",
            annotation_position="top left",
        )

    fig.update_annotations(font={"color": tokens["primary_text"]})
    fig.update_xaxes(
        gridcolor=tokens["chart_grid"],
        tickfont=axis_font,
        title_font=title_font,
        color=tokens["primary_text"],
        linecolor=tokens["panel_border"],
        zerolinecolor=tokens["panel_border"],
    )
    fig.update_yaxes(
        title_text="Risk score",
        title_font=title_font,
        tickfont=axis_font,
        color=tokens["primary_text"],
        gridcolor=tokens["chart_grid"],
        linecolor=tokens["panel_border"],
        zerolinecolor=tokens["panel_border"],
        range=[0, 1],
        secondary_y=False,
    )
    fig.update_yaxes(
        title_font=title_font,
        tickfont=axis_font,
        color=tokens["primary_text"],
        gridcolor=tokens["chart_grid"],
        linecolor=tokens["panel_border"],
        zerolinecolor=tokens["panel_border"],
        secondary_y=True,
    )
    fig.update_layout(
        height=680,
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "x": 0,
            "font": {"color": tokens["primary_text"], "size": 12},
            "bgcolor": tokens["chart_paper"],
        },
        margin={"l": 24, "r": 24, "t": 44, "b": 24},
        template=tokens["chart_template"],
        paper_bgcolor=tokens["chart_paper"],
        plot_bgcolor=tokens["chart_plot"],
        font={"color": tokens["primary_text"], "size": 12},
        hoverlabel={
            "bgcolor": tokens["panel_bg"],
            "bordercolor": tokens["panel_border"],
            "font": {"color": tokens["primary_text"]},
        },
    )
    return fig


def main():
    import streamlit as st

    st.set_page_config(
        page_title="BTC Cycle Risk Dashboard",
        page_icon="₿",
        layout="wide",
    )

    @st.cache_data(ttl=3600, show_spinner=False)
    def cached_fetch_coinmetrics_data(start_date, end_date, _api_key_marker):
        return fetch_coinmetrics_data(start_date, end_date)

    today = date.today()
    default_start = date(2010, 7, 17)
    default_end = today - timedelta(days=1)

    with st.sidebar:
        st.header("Controls")
        st.caption("Use the top controls for the quick readout. Calibration is tucked under Advanced.")
        appearance = st.radio(
            "Appearance",
            options=["Light", "Dark"],
            index=1,
            horizontal=True,
        )
        view_mode = st.radio(
            "View",
            options=["Quick view", "Research view"],
            horizontal=False,
        )
        start_date = st.date_input(
            "Start date",
            value=default_start,
            min_value=GENESIS_DATE.date(),
            max_value=today,
        )
        end_date = st.date_input(
            "End date",
            value=default_end,
            min_value=GENESIS_DATE.date(),
            max_value=today,
        )
        show_dca_guide = st.checkbox(
            "Show zone bar",
            value=True,
        )
        dca_ceiling = st.selectbox(
            "Max DCA risk",
            options=[0.30, 0.40, 0.50],
            index=0,
            format_func=lambda value: {
                0.30: "0.3 - stricter current-cycle example",
                0.40: "0.4 - less conservative",
                0.50: "0.5 - older broader example",
            }[value],
        )
        base_dca_amount = st.number_input(
            "Base DCA per period",
            min_value=0.0,
            value=100.0,
            step=25.0,
        )
        dca_period = st.selectbox(
            "DCA period",
            options=["Weekly", "Monthly", "Custom period"],
            index=0,
        )
        with st.expander("Chart options", expanded=view_mode == "Research view"):
            show_composite = st.checkbox("Composite risk", value=True)
            show_btc_price = st.checkbox(
                "BTC price overlay",
                value=True,
            )
            show_price_trend = st.checkbox("Price-trend risk", value=False)
            show_mvrv_z = st.checkbox("MVRV Z risk", value=False)
            show_nupl = st.checkbox("NUPL risk", value=False)
        with st.expander("Advanced calibration", expanded=False):
            lower_quantile = st.slider(
                "Lower quantile for low-risk calibration",
                min_value=0.00,
                max_value=0.45,
                value=0.05,
                step=0.01,
            )
            upper_quantile = st.slider(
                "Upper quantile for high-risk calibration",
                min_value=0.55,
                max_value=1.00,
                value=0.95,
                step=0.01,
            )

    tokens = apply_app_theme(st, appearance)
    chart_options = {
        "show_price_trend": show_price_trend,
        "show_mvrv_z": show_mvrv_z,
        "show_nupl": show_nupl,
        "show_composite": show_composite,
        "show_btc_price": show_btc_price,
    }

    render_app_header()

    if start_date >= end_date:
        st.error("Start date must be before end date.")
        st.stop()

    api_key = os.getenv("COINMETRICS_API_KEY")
    api_mode = "Pro/API key endpoint" if api_key else "Community endpoint"

    try:
        with st.spinner("Loading Coin Metrics data..."):
            raw = cached_fetch_coinmetrics_data(
                start_date.isoformat(),
                end_date.isoformat(),
                api_key_fingerprint(api_key),
            )
        frame, metadata = calculate_risk_dataset(raw, lower_quantile, upper_quantile)
        frame = add_dynamic_dca_columns(frame, dca_ceiling, base_dca_amount)
    except Exception as exc:
        st.error(f"Could not load or calculate the dataset: {exc}")
        st.stop()

    current_rows = frame.dropna(subset=RISK_COLUMNS + ["composite_risk"])
    current = current_rows.iloc[-1] if not current_rows.empty else frame.iloc[-1]
    previous = current_rows.iloc[-2] if len(current_rows) > 1 else None
    previous_risk = previous.get("composite_risk") if previous is not None else np.nan
    latest_date = pd.to_datetime(current["time"]).date()
    as_of_label = format_as_of_date(latest_date)
    current_signal = cycle_framework_signal(
        current.get("composite_risk"),
        previous_risk,
        dca_ceiling,
        base_dca_amount,
        dca_period,
    )

    render_context_line(as_of_label)

    section_header(
        "Current Signal",
        """
        This is the plain-English readout. It maps the dashboard's composite risk
        score to the dynamic DCA zones described in the transcript. It is a guide
        for interpreting the chart, not financial advice.
        """,
    )
    render_signal_card(current_signal, current.get("composite_risk"), as_of_label, tokens)

    summary_columns = st.columns(4)
    summary_columns[0].metric("Composite risk", format_risk(current.get("composite_risk")), risk_band(current.get("composite_risk")))
    summary_columns[1].metric("BTC price", format_usd(current.get("PriceUSD")), "daily PriceUSD")
    if current_signal["multiplier"]:
        summary_columns[2].metric(
            "Framework DCA",
            format_period_amount(current_signal["amount"], dca_period),
            f"{current_signal['multiplier']:.0f}x base",
        )
    elif current.get("composite_risk") >= SCALE_OUT_START:
        summary_columns[2].metric("Upside action", "DCA out review", current_signal["signal"])
    else:
        summary_columns[2].metric("Buy action", "No forced buy", current_signal["signal"])
    summary_columns[3].metric(
        "Daily direction",
        current_signal["direction"].title(),
        "vs previous point",
    )
    render_disclosure_expander(as_of_label, api_mode, metadata)

    if show_dca_guide:
        section_header(
            "Zone Bar",
            """
            The zone bar is the simplified framework: DCA zones on the left,
            pause in the middle, and DCA-out review zones on the right. The marker
            shows where the current composite risk sits.
            """,
        )
        render_zone_bar(current.get("composite_risk"), dca_ceiling, tokens, current_signal)
        with st.expander("Zone definitions", expanded=view_mode == "Research view"):
            zone_table = pd.DataFrame(framework_zone_table(dca_ceiling, base_dca_amount, dca_period))
            st.table(zone_table)
            st.caption(
                "These labels are a decision aid for the dashboard, not a command to buy or sell."
            )

    if view_mode == "Quick view":
        with st.expander("Why this signal?", expanded=False):
            st.caption(
                "The composite score is the equal-weighted average of these three inputs."
            )
            render_component_risks(current, tokens)
        with st.expander("Research chart", expanded=False):
            render_risk_chart(
                frame,
                chart_options,
                show_dca_guide,
                dca_ceiling,
                tokens,
                current,
                current_signal,
            )
    else:
        section_header(
            "Component Risks",
            """
            These are the three inputs behind the composite score. The composite is an
            equal-weighted average of price-trend risk, MVRV Z risk, and NUPL risk.
            """,
        )
        render_component_risks(current, tokens)

        section_header(
            "Risk Chart",
            """
            The black line is the composite risk score. The colored background marks the
            DCA, pause, and DCA-out review zones. The gray dotted line is BTC price when
            the overlay is enabled.
            """,
        )
        render_risk_chart(
            frame,
            chart_options,
            show_dca_guide,
            dca_ceiling,
            tokens,
            current,
            current_signal,
        )

    with st.expander("Data, Sources, and Caveats", expanded=False):
        st.write(
            f"As-of date: **{as_of_label}**. "
            f"Data source: **Coin Metrics {api_mode}**. "
            f"MVRV Z source: **{metadata['mvrv_source']}**. "
            f"Realized cap source: **{metadata['realized_cap_source']}**."
        )
        st.write(
            "API data is cached for up to **1 hour** during a running Streamlit session. "
            "The risk model uses daily Coin Metrics data, not live intraday pricing."
        )

        download_frame = frame.copy()
        download_frame["time"] = download_frame["time"].dt.strftime("%Y-%m-%d")
        st.download_button(
            "Download calculated CSV",
            data=download_frame.to_csv(index=False).encode("utf-8"),
            file_name="btc_cycle_risk_dataset.csv",
            mime="text/csv",
        )

        st.markdown(
            """
            This dashboard is not investment advice.

            This is not a proprietary Risk metric. It is a transparent
            approximation using similar macro-cycle logic: price deviation from a
            power-law trend, MVRV Z-Score, and NUPL.

            If you share this dashboard, keep the interpretation framed as an
            educational risk framework. The labels are not instructions to buy, sell,
            hold, or size a position for any specific person.

            The transcript-based dynamic DCA guide is an interpretation layer. The
            framework describes buying more as risk moves lower, with a stricter
            current-cycle example focused on DCA below 0.3 risk. It also describes
            doing nothing through a middle range and reviewing scale-outs above about
            0.6 risk. This app applies that framework to the composite score shown
            here, not to any private model.

            The transcript also mentions Monday as historically favorable for routine
            DCA in his own tooling. This dashboard does not independently test weekday
            performance.

            Scores are relative to the available history and the quantile calibration
            choices in the sidebar. Changing the date range or calibration settings can
            change the level of each risk score.

            Past Bitcoin cycle behavior can break. Structural changes in market
            behavior, liquidity, regulation, or data quality can make historical cycle
            relationships less useful.
            """
        )


if __name__ == "__main__":
    main()
