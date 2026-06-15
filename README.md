# BTC Cycle Risk Dashboard

BTC Cycle Risk Dashboard is a local Streamlit dashboard that turns three transparent Bitcoin macro-cycle risk indicators into a quick signal board:

- Price-trend risk from a power-law/log-regression proxy
- MVRV Z-Score risk from Coin Metrics, with a fallback calculation if needed
- NUPL risk from market cap and realized cap

The dashboard calculates an equal-weighted composite risk score, shows a quick
zone readout, and keeps the full chart and CSV download available in the
research details.

It includes an optional transcript-based dynamic DCA guide based on public
cycle-risk discussion around buying more as risk moves lower. The guide is
applied to this dashboard's composite risk approximation, not to any proprietary
model.

The readings are based on Coin Metrics daily data and are shown with an
explicit as-of date. They are not live tick-by-tick BTC prices.

This is an educational framework dashboard. It is not investment advice, not a
buy/sell instruction, and not a proprietary model.

## Views

Quick view is the default. It is meant for fast checks:

- current framework signal
- composite risk
- daily BTC price
- framework DCA amount per selected period
- zone bar with a "you are here" marker
- as-of date

Research view expands the supporting material:

- component risk cards
- full Plotly risk chart
- zone definitions
- source/caveat details
- CSV download

The sidebar includes an Appearance toggle for light or dark mode. Chart options
also let you choose which lines are visible, so the research chart can stay
simple until you want to inspect individual component risks.

The sidebar also lets you set a base DCA amount and DCA period, such as weekly
or monthly. The framework amount scales that base amount by the current risk
zone.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate the virtual environment with:

```bash
.venv\Scripts\activate
```

## Optional Coin Metrics API key

By default, the app uses the Coin Metrics community endpoint:

```text
https://community-api.coinmetrics.io/v4
```

If you have a Coin Metrics API key, set it before running the app:

```bash
export COINMETRICS_API_KEY="your_key_here"
```

When the key is present, the app uses:

```text
https://api.coinmetrics.io/v4
```

## Risk Signals

### Price-trend risk

The app fits a transparent power-law/log-regression proxy:

```text
log10(BTC price) = intercept + slope * log10(days since Bitcoin genesis)
```

It then calculates the residual:

```text
log10(actual BTC price / fitted trend price)
```

That residual is normalized into a 0-1 risk score using the selected quantile calibration.

### MVRV Z-Score risk

The app requests `CapMVRVZ` from Coin Metrics. If that metric is unavailable, it uses this fallback:

```text
(market cap - realized cap) / cumulative standard deviation of market cap
```

The resulting signal is normalized into a 0-1 risk score.

In community mode, Coin Metrics may restrict direct access to `CapMVRVZ` and
`CapRealUSD`. When direct realized cap is unavailable, the app requests the
public `CapMVRVCur` ratio and derives realized cap as:

```text
market cap / MVRV current-supply ratio
```

### NUPL risk

NUPL is calculated as:

```text
(market cap - realized cap) / market cap
```

The resulting signal is normalized into a 0-1 risk score.

### Composite risk

The composite score is the equal-weighted average:

```text
(price_trend_risk + mvrv_z_risk + nupl_risk) / 3
```

## Transcript-Based Dynamic DCA Guide

The dashboard can show an interpretation layer based on the dynamic DCA approach
described in the provided public transcript.

The stricter current-cycle example uses a DCA ceiling of `0.3` risk:

- `0.2-0.3`: framework DCA zone, 1x base DCA amount per period
- `0.1-0.2`: heavier DCA zone, 2x base DCA amount per period
- `0.0-0.1`: heaviest DCA zone, 3x base DCA amount per period
- `0.3-0.6`: pause zone
- `0.6-1.0`: DCA-out review zones

The sidebar also lets you view broader examples with `0.4` or `0.5` DCA
ceilings. Those extend the same logic upward: buy the smallest amount near the
ceiling and increase the amount as risk moves lower.

This is not a recommendation to buy Bitcoin. It is a way to display the
transcript's risk-band logic against this dashboard's transparent approximation.

## Interpretation Notes

Risk bands are labeled as:

- `<0.25`: Low
- `0.25-0.50`: Moderate
- `0.50-0.75`: High
- `>=0.75`: Extreme

The score is relative to available history and calibration choices. Changing the date range, lower quantile, or upper quantile can change the risk level. API data is cached for up to 1 hour during a running Streamlit session.

This is not investment advice. This is not a proprietary model. It is a transparent approximation using similar macro-cycle logic. Past Bitcoin cycle behavior can break.

## Tests

Run the test suite with:

```bash
pytest
```
