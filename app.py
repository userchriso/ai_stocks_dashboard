import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# =============================================
# CONFIG & STOCK LIST
# =============================================

st.set_page_config(
    page_title="Top 20 AI Stocks",
    layout="wide",
)

# Your 20 AI stocks
TICKERS = [
    "NVDA", "AVGO", "MU", "AMD", "LRCX", "PLTR", "PATH", "FIVN",
    "QLYS", "TDC", "BB", "HUBS", "MDB", "CALX", "FSLY",
    "NBIS", "APLD", "SOUN", "UBER", "TSM"
]

# Period selector helper
PERIOD_MAP = {
    "1D": "1d",
    "1W": "5d",
    "1M": "1mo",
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
    "YTD": "ytd",
}

# =============================================
# FETCH DATA
# =============================================

@st.cache_data(ttl=300)  # cache 5 minutes
def fetch_data(tickers, period="1y"):
    data = {}
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if len(hist) > 0:
            # store close and normalize
            hist["norm"] = hist["Close"] / hist["Close"].iloc[0] * 100
            data[ticker] = hist
    return data

# Sidebar UI
st.sidebar.title("Top 20 AI‑Stocks Dashboard")
st.sidebar.markdown("Live prices & performance comparison.")

period = st.sidebar.selectbox(
    "Performance period",
    options=["1D", "1W", "1M", "3M", "6M", "1Y", "YTD"],
    index=5,  # default to 1Y
)

timeframe = PERIOD_MAP[period]
stocks = fetch_data(TICKERS, period=timeframe)

if not stocks:
    st.error("No data loaded. Check internet connection or ticker list.")
    st.stop()

# =============================================
# LIVE PRICE TABLE
# =============================================

st.subheader("💵 Live prices (last period close)")
rows = []

for ticker in TICKERS:
    d = stocks.get(ticker)
    if d is None or len(d) < 2:
        continue
    price = d["Close"].iloc[-1]
    prev = d["Close"].iloc[-2]
    chg_abs = price - prev
    chg_pct = (chg_abs / prev) * 100

    # 24h / 1W / 1M performance (if available)
    d_all = fetch_data([ticker], "1y")[ticker]
    close_now = d_all["Close"].iloc[-1]
    if len(d_all) >= 2:
        close_1d = d_all["Close"].iloc[-2]
        chg_1d = (close_now / close_1d - 1) * 100
    else:
        chg_1d = 0.0

    if len(d_all) >= 7:
        close_1w = d_all["Close"].iloc[-7]
        chg_1w = (close_now / close_1w - 1) * 100
    else:
        chg_1w = 0.0

    if len(d_all) >= 30:
        close_1m = d_all["Close"].iloc[-30]
        chg_1m = (close_now / close_1m - 1) * 100
    else:
        chg_1m = 0.0

    rows.append((
        ticker,
        price,
        chg_abs,
        chg_pct,
        chg_1d,
        chg_1w,
        chg_1m,
    ))

df_now = pd.DataFrame(
    rows,
    columns=["Symbol", "Price", "1FX Δ", "1FX %", "1D %", "1W %", "1M %"]
)
df_now = df_now.style.format(
    {
        "Price": "{:.2f}",
        "1FX Δ": "{:.2f}",
        "1FX %": "{:.2f}%",
        "1D %": "{:.2f}%",
        "1W %": "{:.2f}%",
        "1M %": "{:.2f}%",
    }
)
st.dataframe(df_now, use_container_width=True)

# =============================================
# CUMULATIVE PERFORMANCE CHART
# =============================================

st.subheader("📈 Cumulative performance (normalized to 100)")

# build long‑format df for all tickers
dfs = []
for ticker in TICKERS:
    if ticker in stocks:
        d = stocks[ticker][["norm"]].reset_index()
        d["Symbol"] = ticker
        d = d.rename(columns={"norm": "Normalized"})
        dfs.append(d)
df_long = pd.concat(dfs, ignore_index=True)

fig_cum = px.line(
    df_long,
    x="Date",
    y="Normalized",
    color="Symbol",
    title="Normalized performance since period start",
    hover_data={"Normalized": ":.2f", "Symbol": False},
    height=500
)
fig_cum.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig_cum, use_container_width=True)

# =============================================
# SINGLE STOCK DETAIL
# =============================================

st.subheader("🔍 Single‑stock detail")

ticker_input = st.selectbox("Select stock to view detail", TICKERS, index=0)

if ticker_input in stocks:
    hist = stocks[ticker_input]

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    price = hist["Close"].iloc[-1]
    change = price - hist["Close"].iloc[-2]
    change_pct = (change / hist["Close"].iloc[-2]) * 100

    col1.metric("Current price", f"${price:,.2f}")
    col2.metric("1FX Δ", f"${change:,.2f}", f"{change_pct:+.2f}%")

    if len(hist) >= 30:
        close_1m = hist["Close"].iloc[-30]
        chg_1m_single = (price / close_1m - 1) * 100
        col3.metric("1M return", None, f"{chg_1m_single:+.2f}%")

    if len(hist) >= 252:
        close_1y = hist["Close"].iloc[-252]
        chg_1y = (price / close_1y - 1) * 100
        col4.metric("1Y return [approx]", None, f"{chg_1y:+.2f}%")

    # Price chart
    st.markdown(f"### {ticker_input} price chart ({period})")
    fig = go.Figure(
        go.Scatter(
            x=hist.index,
            y=hist["Close"],
            mode="lines",
            name="Close",
            line=dict(width=1.5),
        )
    )
    fig.update_layout(
        title=f"{ticker_input} price ({period})",
        xaxis_title="Date",
        yaxis_title="Price",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Optional: draw 20‑day and 50‑day SMA (if enough data)
    if len(hist) >= 50:
        hist["SMA20"] = hist["Close"].rolling(20).mean()
        hist["SMA50"] = hist["Close"].rolling(50).mean()

        fig_sma = go.Figure()
        fig_sma.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist["Close"],
                mode="lines",
                name="Close",
                line=dict(width=1.2),
            )
        )
        fig_sma.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist["SMA20"],
                mode="lines",
                name="SMA20",
                line=dict(width=1.5, color="orange"),
            )
        )
        fig_sma.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist["SMA50"],
                mode="lines",
                name="SMA50",
                line=dict(width=1.5, color="purple"),
            )
        )
        fig_sma.update_layout(
            title=f"{ticker_input} price + SMA20/SMA50",
            xaxis_title="Date",
            yaxis_title="Price",
            height=400,
        )
        st.plotly_chart(fig_sma, use_container_width=True)

# Footer
st.markdown("---")
st.caption(
    "Data source: Yahoo Finance via `yfinance`. Prices are delayed and not real‑time. "
    "This dashboard is for informational purposes only and not financial advice."
)