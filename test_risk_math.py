import numpy as np
import pandas as pd

from app import (
    calculate_composite_risk,
    calculate_nupl,
    cycle_framework_signal,
    dynamic_dca_recommendation,
    build_chart,
    format_period_amount,
    normalize_risk,
    period_suffix,
    theme_tokens,
)


def test_normalize_risk_clips_values_between_zero_and_one():
    values = pd.Series([-100, 0, 50, 100, 999], dtype="float64")

    result = normalize_risk(values, lower_quantile=0.20, upper_quantile=0.80)

    assert result.min() >= 0
    assert result.max() <= 1
    assert result.iloc[0] == 0
    assert result.iloc[-1] == 1


def test_nupl_calculation_is_correct():
    result = calculate_nupl(100.0, 70.0)

    assert np.isclose(result, 0.30)


def test_composite_risk_equals_row_wise_mean_of_three_risk_columns():
    frame = pd.DataFrame(
        {
            "price_trend_risk": [0.0, 0.3, 0.9],
            "mvrv_z_risk": [0.3, 0.3, 0.6],
            "nupl_risk": [0.6, 0.3, 0.0],
        }
    )

    result = calculate_composite_risk(frame)
    expected = frame[["price_trend_risk", "mvrv_z_risk", "nupl_risk"]].mean(axis=1)

    pd.testing.assert_series_equal(result, expected, check_names=False)


def test_dynamic_dca_recommendation_increases_amount_at_lower_risk():
    higher_risk = dynamic_dca_recommendation(0.25, max_buy_risk=0.30, base_amount=100)
    lower_risk = dynamic_dca_recommendation(0.15, max_buy_risk=0.30, base_amount=100)

    assert higher_risk["multiplier"] == 1
    assert higher_risk["amount"] == 100
    assert lower_risk["multiplier"] == 2
    assert lower_risk["amount"] == 200


def test_dynamic_dca_recommendation_waits_between_buy_and_scale_out_ranges():
    result = dynamic_dca_recommendation(0.45, max_buy_risk=0.30, base_amount=100)

    assert result["action"] == "No-buy / patience area"
    assert result["amount"] == 0


def test_cycle_framework_signal_labels_dca_zone_and_amount():
    result = cycle_framework_signal(
        0.18,
        previous_risk=0.21,
        max_buy_risk=0.30,
        base_amount=100,
        dca_period="Weekly",
    )

    assert result["zone"] == "DCA zone"
    assert result["signal"] == "Heavier DCA zone"
    assert result["amount"] == 200
    assert result["weight_label"] == "DCA weight: 2x base"
    assert result["amount_label"] == "Framework amount: $200 / week"
    assert result["visual_weight"] == 2


def test_cycle_framework_signal_labels_upside_scale_out_zone():
    result = cycle_framework_signal(0.72, previous_risk=0.65, max_buy_risk=0.30, base_amount=100)

    assert result["zone"] == "Scale-out zone"
    assert result["signal"] == "A little more DCA out"
    assert result["weight_label"] == "DCA-out review weight: 2"
    assert result["visual_weight"] == 2


def test_period_amount_formats_cadence():
    assert period_suffix("Weekly") == "/ week"
    assert period_suffix("Monthly") == "/ month"
    assert format_period_amount(250, "Monthly") == "$250 / month"


def test_build_chart_respects_line_toggles():
    frame = pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=3, freq="D"),
            "PriceUSD": [40000, 41000, 42000],
            "price_trend_risk": [0.1, 0.2, 0.3],
            "mvrv_z_risk": [0.2, 0.3, 0.4],
            "nupl_risk": [0.3, 0.4, 0.5],
            "composite_risk": [0.2, 0.3, 0.4],
        }
    )
    chart_options = {
        "show_price_trend": False,
        "show_mvrv_z": False,
        "show_nupl": False,
        "show_composite": True,
        "show_btc_price": True,
    }

    fig = build_chart(frame, chart_options, True, 0.30, theme_tokens("Light"))
    trace_names = [trace.name for trace in fig.data]

    assert trace_names == ["Composite risk", "BTC price"]
    assert fig.layout.font.color == "#111827"
    assert fig.layout.legend.font.color == "#111827"
    assert fig.layout.yaxis.tickfont.color == "#111827"
    assert fig.layout.yaxis2.title.font.color == "#111827"
    assert fig.data[1].line.color == "#475569"
