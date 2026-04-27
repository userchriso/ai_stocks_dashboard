import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta

# =============================================
# CONFIG & TICKERS
# =============================================

st.set_page_config(
    page_title="AI Stocks Mobile",
    layout="centered",  # better for phones
)

TICKERS = [
    "NVDA", "AVGO", "MU", "AMD", "LRCX", "PLTR", "PATH", "FIVN",
    "QLYS", "TDC", "BB", "HUBS", "MDB", "CALX", "FSLY",
    "NBIS", "APLD", "SOUN", "UBER", "TSM",
]

PERIOD_MAP = {
    "1D": "1d",
    "1W": "5d",
    "2W": "10d",
    "1M": "1mo",
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
}

@st.cache_data(ttl=300)
def fetch_data(tickers, period="1y"):
    data = {}
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if len(hist) > 0:
            hist["norm"] = hist["Close"] / hist["Close"].iloc[0] * 100
            data[ticker] = hist
    return data


# =============================================
# SIDEBAR: minimal controls
# =============================================

st.sidebar.title("📱 AI Stocks Mobile")
st.sidebar.markdown("Top 20 AI‑focused stocks.")

period = st.sidebar.selectbox(
    "Look‑back",
    options=["1D", "1W", "1M", "3M", "6M", "1Y"],
    index=2,  # default to 1M
)

timeframe = PERIOD_MAP[period]
stocks = fetch_data(TICKERS, period=timeframe)

if not stocks:
    st.error("No data. Check connection or tickers.")
    st.stop()


# =============================================
# TOP: 3 BIGGEST MOVERS (MOBILE FOCUS)
# =============================================

st.subheader("🚀 Top movers (1FX %)")

rows = []
for ticker in TICKERS:
    d = stocks.get(ticker)
    if d is None or len(d) < 2:
        continue
    price = d["Close"].iloc[-1]
    prev = d["Close"].iloc[-2]
    chg_pct = (price - prev) / prev * 100
    rows.append((ticker, price, chg_pct))

df_chg = pd.DataFrame(rows, columns=["Symbol", "Price", "Chg %"])
df_chg = df_chg.sort_values("Chg %", key=abs, ascending=False)

n_top = 6  # top 3 up + down (on mobile)
top_rows = df_chg.head(n_top)

st.markdown("**Biggest movers (today’s move)**")
for _, row in top_rows.iterrows():
    color = "🟢" if row["Chg %"] > 0 else "🔴"
    st.markdown(
        f"{color} **{row['Symbol']}** = ${row['Price']:.2f} ({row['Chg %']:+.2f}%)")


# =============================================
# COMPACT TABLE FOR ALL 20 (MOBILE‑SCROLLING)
# =============================================

st.subheader("📊 All 20 at a glance")

rows_all = []
for ticker in TICKERS:
    d = stocks.get(ticker)
    if d is None or len(d) < 2:
        continue
    price = d["Close"].iloc[-1]
    prev = d["Close"].iloc[-2]
    chg_pct = (price - prev) / prev * 100

    # 1W & 1M if available
    d_all = fetch_data([ticker], "1y")[ticker]
    close_now = d_all["Close"].iloc[-1]
    chg_1w, chg_1m = 0.0, 0.0
    if len(d_all) >= 7:
        close_1w = d_all["Close"].iloc[-7]
        chg_1w = (close_now / close_1w - 1) * 100
    if len(d_all) >= 30:
        close_1m = d_all["Close"].iloc[-30]
        chg_1m = (close_now / close_1m - 1) * 100

    rows_all.append((ticker, price, chg_pct, chg_1w, chg_1m))

df_all = pd.DataFrame(
    rows_all,
    columns=["Symbol", "Price", "1FX %", "1W %", "1M %"]
).sort_values("1FX %", key=abs, ascending=False)

# Show compact table (no styling for mobile clarity)
st.dataframe(
    df_all.round(2),
    use_container_width=True,
    hide_index=True,
)

# =============================================
# SINGLE STOCK QUICK VIEW (ONE CHART)
# =============================================

st.subheader("🔍 Quick stock view")

ticker = st.selectbox(
    "Pick one to see price",
    options=TICKERS,
    index=0,
    label_visibility="collapsed",
)

if ticker in stocks:
    d = stocks[ticker]
    price = d["Close"].iloc[-1]
    chg_1fx = (price - d["Close"].iloc[-2]) / d["Close"].iloc[-2] * 100

    st.markdown(f"**{ticker} = ${price:.2f} ({chg_1fx:+.2f}%)**")

    # Simple plot for mobile
    fig = go.Figure(
        go.Scatter(
            x=d.index,
            y=d["Close"],
            mode="lines",
            line=dict(width=1.5),
        )
    )
    fig.update_layout(
        title=f"{ticker} price ({period})",
        xaxis_title="Date",
        yaxis_title="Price",
        height=300,
        margin=dict(l=40, r=20, t=40, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


# =============================================
# FOOTER
# =============================================

st.markdown("---")
st.caption(
    "Data: Yahoo Finance via `yfinance` (delayed). Not real‑time. "
    "Not financial advice."
)