"""
最穩上升趨勢 — 入場訊號監控系統
Stable Uptrend Signal Monitor  |  Light Cream UI
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
import hashlib
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
from zoneinfo import ZoneInfo

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="最穩訊號監控",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS  —  cream / light theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #f5f2eb !important;
    color: #2c2c2a !important;
}
.main .block-container {
    background-color: #f5f2eb;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 0.5px solid #ddd8ce !important;
}
section[data-testid="stSidebar"] > div { padding-top: 1rem; }
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    color: #5f5e5a !important;
    font-size: 12px !important;
    font-family: 'Inter', sans-serif !important;
}
section[data-testid="stSidebar"] strong { color: #2c2c2a !important; }

.sig-card {
    background: #ffffff;
    border: 0.5px solid #ddd8ce;
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 12px;
}
.sig-card-strong { border-left: 3px solid #3b6d11; }
.sig-card-warn   { border-left: 3px solid #ba7517; }

.pbox {
    background: #faf8f4;
    border: 0.5px solid #e8e4db;
    border-radius: 7px;
    padding: 9px 11px;
}
.ct-pass {
    background: #eaf3de; border: 0.5px solid #c0dd97; color: #3b6d11;
    border-radius: 4px; padding: 2px 7px; font-size: 11px;
    display: inline-block; margin: 2px 3px 2px 0;
}
.ct-fail {
    background: #fcebeb; border: 0.5px solid #f7c1c1; color: #a32d2d;
    border-radius: 4px; padding: 2px 7px; font-size: 11px;
    display: inline-block; margin: 2px 3px 2px 0;
}
div[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 0.5px solid #ddd8ce !important;
    border-radius: 10px !important;
    padding: 14px 16px !important;
}
div[data-testid="stMetric"] label {
    color: #888780 !important; font-size: 11px !important; font-weight: 400 !important;
}
div[data-testid="stMetricValue"] > div {
    color: #2c2c2a !important; font-size: 22px !important; font-weight: 600 !important;
}
.stButton > button {
    background: #faf8f4 !important; border: 0.5px solid #ddd8ce !important;
    color: #5f5e5a !important; border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important; font-size: 12px !important;
}
.stButton > button:hover {
    background: #eaf3de !important; border-color: #c0dd97 !important; color: #3b6d11 !important;
}
.stTextInput > div > div > input {
    background: #faf8f4 !important; border: 0.5px solid #ddd8ce !important;
    color: #2c2c2a !important; border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 12px !important;
}
input[type=checkbox] { accent-color: #639922 !important; }
.stProgress > div > div > div { background: #639922 !important; }
.stSuccess { background: #eaf3de !important; color: #3b6d11 !important; border-radius: 7px !important; }
.stError   { background: #fcebeb !important; color: #a32d2d !important; border-radius: 7px !important; }
hr { border-color: #e8e4db !important; margin: 0.75rem 0 !important; }
.stCaption, small { color: #b4b2a9 !important; font-size: 11px !important; }
.stCheckbox span { color: #5f5e5a !important; font-size: 13px !important; }

.sb-sec {
    font-size: 10px; font-weight: 600; color: #b4b2a9;
    letter-spacing: 1.5px; text-transform: uppercase;
    border-bottom: 0.5px solid #e8e4db;
    padding-bottom: 5px; margin: 14px 0 8px;
}
.log-row {
    display: flex; gap: 14px; align-items: center;
    padding: 7px 12px; background: #ffffff;
    border: 0.5px solid #e8e4db; border-radius: 7px;
    margin-bottom: 5px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
}
.empty-state {
    border: 0.5px dashed #d3d1c7; border-radius: 10px;
    padding: 40px; text-align: center;
    background: #ffffff; color: #b4b2a9; margin-top: 10px;
}
.scan-footer {
    font-size: 10px; color: #b4b2a9;
    padding-top: 10px; border-top: 0.5px solid #e8e4db; margin-top: 16px;
}
.tf-badge-on {
    background: #eaf3de; border: 0.5px solid #c0dd97; color: #3b6d11;
    border-radius: 4px; padding: 2px 8px; font-size: 11px;
    font-family: 'JetBrains Mono', monospace; display: inline-block; margin-right: 4px;
}
.tf-badge-off {
    background: #faf8f4; border: 0.5px solid #e8e4db; color: #b4b2a9;
    border-radius: 4px; padding: 2px 8px; font-size: 11px;
    font-family: 'JetBrains Mono', monospace; display: inline-block; margin-right: 4px;
}
.mkt-ok  { background:#eaf3de; border:0.5px solid #c0dd97; border-radius:8px; padding:10px 14px; color:#3b6d11; font-size:13px; font-weight:500; }
.mkt-bad { background:#fcebeb; border:0.5px solid #f7c1c1; border-radius:8px; padding:10px 14px; color:#a32d2d; font-size:13px; font-weight:500; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TRADING SESSION DETECTION  (ET-based)
# ─────────────────────────────────────────────
ET = ZoneInfo("America/New_York")

SESSION_CONFIG = {
    "overnight":  {"emoji": "🌙", "label": "隔夜 Overnight",   "color": "#534ab7", "bg": "#eeedfe", "border": "#afa9ec", "warn": True,  "tfs": ["1m","5m"]},
    "premarket":  {"emoji": "🌅", "label": "盤前 Pre-Market",  "color": "#854f0b", "bg": "#faeeda", "border": "#fac775", "warn": True,  "tfs": ["1m","5m"]},
    "regular":    {"emoji": "📈", "label": "盤中 Regular",     "color": "#3b6d11", "bg": "#eaf3de", "border": "#c0dd97", "warn": False, "tfs": ["1m","5m","15m","1h","1d"]},
    "afterhours": {"emoji": "🌆", "label": "盤後 After-Hours", "color": "#185fa5", "bg": "#e6f1fb", "border": "#85b7eb", "warn": True,  "tfs": ["1m","5m"]},
}

def get_session(dt_et: datetime) -> str:
    h = dt_et.hour + dt_et.minute / 60
    if   0   <= h <  4:    return "overnight"
    elif 4   <= h <  9.5:  return "premarket"
    elif 9.5 <= h < 16:    return "regular"
    elif 16  <= h < 20:    return "afterhours"
    else:                  return "overnight"  # 20:00–24:00 → next overnight

def get_allowed_tfs(session: str, user_tfs: list) -> list:
    """Non-regular hours: restrict to 1m/5m only."""
    if session == "regular":
        return user_tfs
    allowed = SESSION_CONFIG[session]["tfs"]
    filtered = [tf for tf in user_tfs if tf in allowed]
    return filtered if filtered else ["5m"]


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in {"signal_log": [], "notified": {}, "signals": []}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def get_telegram_creds(manual_token, manual_chat):
    try:
        token = st.secrets.get("TELEGRAM_BOT_TOKEN", "") or manual_token
        chat  = st.secrets.get("TELEGRAM_CHAT_ID",   "") or manual_chat
    except Exception:
        token, chat = manual_token, manual_chat
    return token.strip(), chat.strip()


def send_telegram_text(token, chat_id, text):
    if not token or not chat_id:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        return r.ok
    except Exception:
        return False


def send_telegram_photo(token, chat_id, img_bytes, caption=""):
    if not token or not chat_id:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"},
            files={"photo": ("chart.png", img_bytes, "image/png")},
            timeout=15,
        )
        return r.ok
    except Exception:
        return False


def build_telegram_message(sig):
    names = ["EMA完美多頭排列", "無連續兩根K跌穿EMA15",
             "K線主體在EMA10之上", "MACD雙線零軸之上", "量能配合上漲"]
    cond_lines = "\n".join(
        f"{'✅' if sig['conditions'][i] else '❌'} {names[i]}"
        for i in range(5) if sig["enabled"][i]
    )
    bar = "🟢" * sig["score"] + "⚫" * (sig["max_score"] - sig["score"])
    sess  = sig.get("session", "regular")
    scfg  = SESSION_CONFIG[sess]
    warn_line = f"\n⚠️ <b>{scfg['label']} — 流動性偏低，訊號僅供參考，慎用大倉</b>" if scfg["warn"] else ""
    return (
        f"{scfg['emoji']} <b>最穩上升趨勢訊號</b> — {sig['ticker']} {sig['timeframe']}"
        f"  [{scfg['label']}]{warn_line}\n\n"
        f"{cond_lines}\n\n"
        f"{bar}  強度 {sig['score']}/{sig['max_score']}\n"
        f"📊 趨勢持續 {sig['duration']} 根K線\n\n"
        f"🟢 <b>入場價：</b>${sig['entry']:.2f}\n"
        f"🎯 <b>目標一：</b>${sig['t1']:.2f}（+{sig['up1']:.1f}%）\n"
        f"🎯 <b>目標二：</b>${sig['t2']:.2f}（+{sig['up2']:.1f}%）\n"
        f"🔴 <b>止損價：</b>${sig['stop']:.2f}（-{sig['risk_pct']:.1f}%）\n"
        f"📐 <b>風險回報：</b>{sig['rrr']}\n\n"
        f"🕐 {sig['time']} ET"
    )


# ─────────────────────────────────────────────
# INDICATORS
# ─────────────────────────────────────────────
def calc_ema(series, n):
    return series.ewm(span=n, adjust=False).mean()

def calc_macd(close, fast=12, slow=26, signal=9):
    dif = calc_ema(close, fast) - calc_ema(close, slow)
    dea = calc_ema(dif, signal)
    return dif, dea, (dif - dea) * 2

def calc_indicators(df):
    c, v = df["Close"], df["Volume"]
    for n in [5, 10, 15, 20, 50, 120, 200]:
        df[f"ema{n}"] = calc_ema(c, n)
    df["dif"], df["dea"], df["macd_hist"] = calc_macd(c)
    df["vol_ma5"] = v.rolling(5).mean()
    return df


# ─────────────────────────────────────────────
# DATA FETCH  —  4-Layer Extended Hours Strategy
# ─────────────────────────────────────────────
# Layer 1: yfinance fast_info        (pre_market_price / post_market_price)
# Layer 2: yfinance history prepost  (最新1d K線含盤前/盤後)
# Layer 3: Yahoo JSON API            (query1 / query2)
# Layer 4: Yahoo HTML fallback       (fin-streamer tag parse)
# K線數據永遠用 yfinance history，只有「入場價」用最新即時報價覆蓋

TF_MAP = {
    "1m":  ("7d",   "1m"),
    "5m":  ("60d",  "5m"),
    "15m": ("60d",  "15m"),
    "1h":  ("730d", "1h"),
    "1d":  ("5y",   "1d"),
}

def _safe_float(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None

@st.cache_data(ttl=20, show_spinner=False)
def get_realtime_price(ticker: str) -> dict:
    """
    4-layer strategy to get the most current price including extended hours.
    Returns: {price, regular_price, pre_price, post_price, source, staleness_sec}
    """
    result = {
        "price": None, "regular_price": None,
        "pre_price": None, "post_price": None,
        "source": "unknown", "staleness_sec": None,
    }

    # ── Layer 1: fast_info (no extra HTTP, internal yfinance session) ──
    try:
        tk = yf.Ticker(ticker)
        fi = tk.fast_info
        reg  = _safe_float(getattr(fi, "previous_close",    None)) or \
               _safe_float(getattr(fi, "last_price",         None))
        pre  = _safe_float(getattr(fi, "pre_market_price",  None))
        post = _safe_float(getattr(fi, "post_market_price", None))
        if reg and reg > 0:
            result["regular_price"] = reg
            anchor = reg
            if pre  and (anchor * 0.70 <= pre  <= anchor * 1.30):
                result["pre_price"]  = pre
            if post and (anchor * 0.70 <= post <= anchor * 1.30):
                result["post_price"] = post
            result["price"]  = (result["pre_price"] or
                                result["post_price"] or reg)
            result["source"] = "fast_info"
            if result["pre_price"] or result["post_price"]:
                return result          # 有即時延伸時段價，直接返回
    except Exception:
        pass

    # ── Layer 2: history prepost=True (pull latest 1-day 1m bar) ──
    try:
        tk  = yf.Ticker(ticker)
        df2 = tk.history(period="1d", interval="1m", prepost=True)
        if not df2.empty:
            if isinstance(df2.columns, pd.MultiIndex):
                df2.columns = df2.columns.get_level_values(0)
            last_row  = df2.iloc[-1]
            last_price = _safe_float(last_row.get("Close"))
            reg = result.get("regular_price") or _safe_float(
                df2[df2.index.time < __import__("datetime").time(9, 30)]["Close"].iloc[-1]
                if len(df2) > 1 else None
            )
            if last_price and last_price > 0:
                if reg and (reg * 0.70 <= last_price <= reg * 1.30):
                    result["price"]  = last_price
                    result["source"] = "history_prepost"
                    # staleness = seconds since last bar
                    try:
                        import datetime as _dt
                        last_ts = df2.index[-1]
                        if hasattr(last_ts, "tzinfo") and last_ts.tzinfo:
                            now_ts = _dt.datetime.now(last_ts.tzinfo)
                        else:
                            now_ts = _dt.datetime.now()
                        result["staleness_sec"] = int((now_ts - last_ts).total_seconds())
                    except Exception:
                        pass
                    return result
    except Exception:
        pass

    # ── Layer 3: Yahoo Finance JSON API ──
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d&includePrePost=true"
        r   = requests.get(url, headers=headers, timeout=8)
        if r.ok:
            data = r.json()
            meta = data["chart"]["result"][0]["meta"]
            price = _safe_float(meta.get("regularMarketPrice"))
            pre   = _safe_float(meta.get("preMarketPrice"))
            post  = _safe_float(meta.get("postMarketPrice"))
            reg   = _safe_float(meta.get("previousClose")) or price
            if reg and reg > 0:
                result["regular_price"] = reg
                if pre  and (reg * 0.70 <= pre  <= reg * 1.30):
                    result["pre_price"]  = pre
                if post and (reg * 0.70 <= post <= reg * 1.30):
                    result["post_price"] = post
                result["price"]  = (result["pre_price"] or
                                    result["post_price"] or price or reg)
                result["source"] = "yahoo_json"
                return result
    except Exception:
        pass

    # ── Layer 4: Yahoo HTML fallback ──
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(f"https://finance.yahoo.com/quote/{ticker}",
                         headers=headers, timeout=10)
        if r.ok:
            import re
            prices = re.findall(
                r'data-field="regularMarketPrice"[^>]*data-value="([0-9.]+)"', r.text
            )
            pre_prices = re.findall(
                r'data-field="preMarketPrice"[^>]*data-value="([0-9.]+)"', r.text
            )
            if prices:
                reg = _safe_float(prices[0])
                pre = _safe_float(pre_prices[0]) if pre_prices else None
                if reg and reg > 0:
                    result["regular_price"] = reg
                    if pre and (reg * 0.70 <= pre <= reg * 1.30):
                        result["pre_price"] = pre
                    result["price"]  = result["pre_price"] or reg
                    result["source"] = "yahoo_html"
                    return result
    except Exception:
        pass

    return result


@st.cache_data(ttl=25, show_spinner=False)
def fetch_data(ticker, timeframe):
    """Fetch OHLCV + indicators. Entry price is overridden by get_realtime_price()."""
    period, interval = TF_MAP[timeframe]
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False, prepost=True)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
        return calc_indicators(df)
    except Exception:
        return None


# ─────────────────────────────────────────────
# SIGNAL EVALUATION
# ─────────────────────────────────────────────
def check_signals(df, enabled_conditions, dynamic_stop, market_ok):
    if df is None or len(df) < 210:
        return None

    last, prev = df.iloc[-1], df.iloc[-2]
    raw = [
        bool(last["ema5"] > last["ema10"] > last["ema15"] > last["ema20"]
             > last["ema50"] > last["ema120"] > last["ema200"]),
        bool(last["Close"] >= last["ema15"] and prev["Close"] >= prev["ema15"]),
        bool(last["Close"] > last["ema10"]),
        bool(last["dif"] > 0 and last["dea"] > 0),
        bool(pd.notna(last["vol_ma5"]) and last["Volume"] > last["vol_ma5"]),
    ]
    active = [raw[i] if enabled_conditions[i] else True for i in range(5)]
    if not all(active) or not market_ok:
        return None

    enabled_idx = [i for i in range(5) if enabled_conditions[i]]
    score     = sum(raw[i] for i in enabled_idx)
    max_score = len(enabled_idx) or 1

    duration = 0
    for i in range(len(df) - 1, -1, -1):
        r = df.iloc[i]
        if (r["ema5"] > r["ema10"] > r["ema15"] > r["ema20"]
                > r["ema50"] > r["ema120"] > r["ema200"]):
            duration += 1
        else:
            break

    entry = float(last["Close"])
    stop  = float(last["ema20"]) if dynamic_stop else entry * 0.995
    risk  = max(entry - stop, entry * 0.005)
    t1    = entry + risk * 2.5
    t2    = entry + risk * 4.0

    return {
        "conditions":  raw,
        "enabled":     enabled_conditions[:],
        "score":       score,
        "max_score":   max_score,
        "duration":    duration,
        "entry":       entry,       # will be overridden by realtime price in main loop
        "t1":          t1,
        "t2":          t2,
        "stop":        stop,
        "up1":         (t1 - entry) / entry * 100,
        "up2":         (t2 - entry) / entry * 100,
        "risk_pct":    (entry - stop) / entry * 100,
        "rrr":         f"1 : {(t1 - entry) / risk:.1f}",
        "time":        datetime.now(ET).strftime("%H:%M:%S"),
        "session":     get_session(datetime.now(ET)),
        "price_source": "yfinance_kline",
        "staleness":   None,
        "df":          df,
    }


# ─────────────────────────────────────────────
# CHART (Telegram)
# ─────────────────────────────────────────────
def make_chart_bytes(df, ticker, timeframe, sig):
    try:
        plot_df = df.tail(80).copy()
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7),
                                        gridspec_kw={"height_ratios": [3, 1]},
                                        facecolor="#f5f2eb")
        ax1.set_facecolor("#ffffff")
        ax2.set_facecolor("#ffffff")
        x = range(len(plot_df))

        for i, (_, row) in enumerate(plot_df.iterrows()):
            col = "#3b6d11" if row["Close"] >= row["Open"] else "#a32d2d"
            ax1.plot([i, i], [row["Low"], row["High"]], color=col, linewidth=0.8)
            ax1.bar(i, abs(row["Close"] - row["Open"]),
                    bottom=min(row["Open"], row["Close"]),
                    color=col, width=0.6, alpha=0.9)

        for ema, col, lw in [
            ("ema5","#97c459",1.2), ("ema10","#ba7517",1.2),
            ("ema15","#d85a30",1.0), ("ema20","#a32d2d",1.0),
            ("ema50","#7f77dd",0.8), ("ema200","#185fa5",0.8),
        ]:
            ax1.plot(x, plot_df[ema].values, color=col, linewidth=lw, alpha=0.9, label=ema.upper())

        ax1.axhline(sig["entry"], color="#185fa5", linewidth=1.2, linestyle="--", alpha=0.8)
        ax1.axhline(sig["t1"],    color="#3b6d11", linewidth=1.2, linestyle="--", alpha=0.8)
        ax1.axhline(sig["stop"],  color="#a32d2d", linewidth=1.2, linestyle="--", alpha=0.8)
        ax1.legend(fontsize=7, loc="upper left", framealpha=0.6)
        ax1.set_title(f"{ticker} {timeframe}  —  最穩上升趨勢訊號",
                      color="#2c2c2a", fontsize=12, pad=8)
        ax1.tick_params(colors="#888780")
        for spine in ax1.spines.values():
            spine.set_color("#e8e4db")

        cv = ["#3b6d11" if r["Close"] >= r["Open"] else "#a32d2d"
              for _, r in plot_df.iterrows()]
        ax2.bar(x, plot_df["Volume"].values, color=cv, alpha=0.7, width=0.6)
        ax2.tick_params(colors="#888780")
        for spine in ax2.spines.values():
            spine.set_color("#e8e4db")

        plt.tight_layout(pad=1.5)
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=120, facecolor="#f5f2eb")
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    except Exception:
        return None


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def dedup_key(ticker, timeframe):
    return hashlib.md5(f"{ticker}-{timeframe}".encode()).hexdigest()

@st.cache_data(ttl=60, show_spinner=False)
def get_market_ok(vix_threshold, spy_drop_threshold):
    try:
        vix = yf.download("^VIX", period="2d", interval="1d", progress=False)
        spy = yf.download("SPY",  period="2d", interval="1d", progress=False)
        for d in [vix, spy]:
            if isinstance(d.columns, pd.MultiIndex):
                d.columns = d.columns.get_level_values(0)
        vix_val = float(vix["Close"].iloc[-1])
        spy_chg = float((spy["Close"].iloc[-1] - spy["Close"].iloc[-2])
                        / spy["Close"].iloc[-2] * 100)
        return (vix_val <= vix_threshold and spy_chg >= -spy_drop_threshold,
                vix_val, spy_chg)
    except Exception:
        return True, None, None


# ─────────────────────────────────────────────
# RENDER SIGNAL CARD
# ─────────────────────────────────────────────
COND_SHORT = ["EMA排列", "不跌EMA15", "EMA10上", "MACD零軸", "量能配合"]
MONO = "font-family:'JetBrains Mono',monospace"

def render_signal_card(ticker, timeframe, sig):
    score, max_s = sig["score"], sig["max_score"]
    strength     = score / max_s if max_s else 0
    border_cls   = "sig-card-strong" if strength >= 1.0 else "sig-card-warn"
    score_dots   = "🟢" * score + "⚫" * (max_s - score)

    tf_color  = "#3b6d11" if strength >= 1.0 else "#854f0b"
    tf_bg     = "#eaf3de" if strength >= 1.0 else "#faeeda"
    tf_border = "#c0dd97" if strength >= 1.0 else "#fac775"
    live_col  = "#639922" if strength >= 1.0 else "#ba7517"

    # session badge
    sess     = sig.get("session", "regular")
    scfg     = SESSION_CONFIG[sess]
    sess_html = (
        f'<span style="font-size:11px;background:{scfg["bg"]};'
        f'border:0.5px solid {scfg["border"]};color:{scfg["color"]};'
        f'border-radius:4px;padding:2px 7px;margin-left:6px">'
        f'{scfg["emoji"]} {scfg["label"]}</span>'
    )
    warn_html = ""
    if scfg["warn"]:
        warn_html = (
            f'<div style="margin-top:6px;font-size:11px;background:#faeeda;'
            f'border:0.5px solid #fac775;border-radius:5px;padding:4px 10px;'
            f'color:#633806;display:inline-block">'
            f'⚠️ {scfg["label"]} — 流動性偏低，訊號僅供參考，慎用大倉</div>'
        )

    cond_html = "".join(
        f'<span class="ct-{"pass" if sig["conditions"][i] else "fail"}">'
        f'{"✓" if sig["conditions"][i] else "✗"} {COND_SHORT[i]}</span>'
        for i in range(5) if sig["enabled"][i]
    )

    st.markdown(f"""
    <div class="sig-card {border_cls}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
        <div>
          <div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px">
            <span style="font-size:20px;font-weight:600;color:#2c2c2a;{MONO}">{ticker}</span>
            <span style="font-size:11px;background:{tf_bg};border:0.5px solid {tf_border};
                         color:{tf_color};border-radius:4px;padding:2px 8px;{MONO}">{timeframe}</span>
            <span style="font-size:10px;color:{live_col}">● LIVE</span>
            {sess_html}
          </div>
          <div style="font-size:11px;color:#b4b2a9;margin-top:5px">
            訊號時間 <span style="{MONO}">{sig['time']} ET</span>
            &nbsp;·&nbsp; 趨勢持續
            <span style="color:#854f0b;font-weight:500">{sig['duration']}</span> 根K線
            &nbsp;·&nbsp; 報價來源：<span style="color:#639922;font-weight:500">{sig.get('price_source','—')}</span>
            {f'&nbsp;·&nbsp; <span style="color:#a32d2d">延遲 {sig["staleness"]}s</span>' if sig.get('staleness') and sig['staleness'] > 30 else ''}
          </div>
          {warn_html}
        </div>
        <div style="text-align:right;flex-shrink:0;margin-left:12px">
          <div style="font-size:15px;letter-spacing:1px">{score_dots}</div>
          <div style="font-size:10px;color:#b4b2a9;margin-top:3px">強度 {score}/{max_s}</div>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;margin-bottom:12px">
        <div class="pbox">
          <div style="font-size:9px;color:#b4b2a9;margin-bottom:3px">入場價</div>
          <div style="font-size:14px;font-weight:500;color:#185fa5;{MONO}">${sig['entry']:.2f}</div>
        </div>
        <div class="pbox">
          <div style="font-size:9px;color:#b4b2a9;margin-bottom:3px">目標一</div>
          <div style="font-size:14px;font-weight:500;color:#3b6d11;{MONO}">${sig['t1']:.2f}</div>
          <div style="font-size:10px;color:#639922;margin-top:1px">+{sig['up1']:.1f}%</div>
        </div>
        <div class="pbox">
          <div style="font-size:9px;color:#b4b2a9;margin-bottom:3px">目標二</div>
          <div style="font-size:14px;font-weight:500;color:#639922;{MONO}">${sig['t2']:.2f}</div>
          <div style="font-size:10px;color:#97c459;margin-top:1px">+{sig['up2']:.1f}%</div>
        </div>
        <div class="pbox">
          <div style="font-size:9px;color:#b4b2a9;margin-bottom:3px">止損</div>
          <div style="font-size:14px;font-weight:500;color:#a32d2d;{MONO}">${sig['stop']:.2f}</div>
          <div style="font-size:10px;color:#d85a30;margin-top:1px">-{sig['risk_pct']:.1f}%</div>
        </div>
      </div>

      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">
        <div>{cond_html}</div>
        <div style="font-size:11px;font-weight:500;color:#633806;background:#faeeda;
                    border:0.5px solid #fac775;border-radius:5px;padding:4px 10px;
                    {MONO};white-space:nowrap;flex-shrink:0">
          RRR {sig['rrr']}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ═════════════════════════════════════════════
#  SIDEBAR
# ═════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:4px 0 12px">
      <div style="font-size:17px;font-weight:600;color:#2c2c2a;letter-spacing:-0.3px">最穩訊號</div>
      <div style="font-size:9px;color:#b4b2a9;letter-spacing:2.5px">SIGNAL MONITOR</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # stocks
    st.markdown('<div class="sb-sec">監控股票</div>', unsafe_allow_html=True)
    stocks_raw = st.text_input(
        "stocks", value="TSLA,NVDA,AAPL",
        placeholder="TSLA,AMZN,AAPL,MSFT,…",
        label_visibility="collapsed",
    )
    stocks = [s.strip().upper() for s in stocks_raw.split(",") if s.strip()]
    st.caption(f"共 {len(stocks)} 隻：{', '.join(stocks)}")

    # timeframes
    st.markdown('<div class="sb-sec">週期選擇</div>', unsafe_allow_html=True)
    tf_options  = ["1m", "5m", "15m", "1h", "1d"]
    tf_defaults = {"1m": False, "5m": True, "15m": True, "1h": False, "1d": False}
    selected_tfs = []
    cols_tf = st.columns(5)
    for i, tf in enumerate(tf_options):
        if cols_tf[i].checkbox(tf, value=tf_defaults[tf], key=f"tf_{tf}"):
            selected_tfs.append(tf)
    if not selected_tfs:
        selected_tfs = ["5m"]
        st.caption("⚠️ 最少選一個週期，預設 5m")

    # refresh
    st.markdown('<div class="sb-sec">刷新間隔</div>', unsafe_allow_html=True)
    refresh_sec = st.slider("秒", 10, 300, 30, 10, label_visibility="collapsed")
    st.caption(f"每 {refresh_sec} 秒自動刷新")

    # core conditions
    st.markdown('<div class="sb-sec">核心條件（個別開關）</div>', unsafe_allow_html=True)
    core_labels = [
        "C1：EMA完美多頭排列",
        "C2：無連續兩根K跌穿EMA15",
        "C3：K線主體在EMA10之上",
        "C4：MACD雙線零軸之上",
        "C5：量能配合上漲",
    ]
    enabled_conditions = [
        st.checkbox(lbl, value=True, key=f"cc_{i}")
        for i, lbl in enumerate(core_labels)
    ]
    active_count = sum(enabled_conditions)
    st.caption(f"已啟用 {active_count}/5 個條件")

    # enhancements
    st.markdown('<div class="sb-sec">增強功能</div>', unsafe_allow_html=True)
    use_score_filter = st.checkbox("訊號強度過濾", value=True)
    if use_score_filter:
        min_score_pct = st.slider("最低通過比例", 50, 100, 80, 10, format="%d%%")
    else:
        min_score_pct = 0

    dynamic_stop = st.checkbox("止損用 EMA20（動態）", value=True)
    if not dynamic_stop:
        st.caption("止損改用固定 0.5%")

    use_market_filter = st.checkbox("VIX / SPY 大市過濾", value=False)
    if use_market_filter:
        vix_threshold   = st.slider("VIX 上限", 15, 40, 25)
        spy_drop_thresh = st.slider("SPY 單日跌幅上限 (%)", 0.5, 3.0, 1.5, step=0.5)
    else:
        vix_threshold, spy_drop_thresh = 999, 999

    send_chart = st.checkbox("Telegram 附帶K線截圖", value=False)

    # telegram
    st.markdown('<div class="sb-sec">Telegram 通知</div>', unsafe_allow_html=True)
    tg_enabled = st.checkbox("啟用 Telegram 通知", value=True)

    try:
        secret_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
        secret_chat  = st.secrets.get("TELEGRAM_CHAT_ID",   "")
        has_secrets  = bool(secret_token and secret_chat)
    except Exception:
        secret_token, secret_chat, has_secrets = "", "", False

    if has_secrets:
        st.success("🔐 已從 Streamlit Secrets 讀取 Token")
        manual_token, manual_chat = "", ""
    else:
        st.caption("未偵測到 Secrets，請手動輸入：")
        manual_token = st.text_input("Bot Token", type="password",
                                     placeholder="110201543:AAHdq…")
        manual_chat  = st.text_input("Chat ID", placeholder="-1001234567890")

    tg_token, tg_chat = get_telegram_creds(manual_token, manual_chat)

    if tg_enabled:
        cooldown_min       = st.slider("通知冷卻（分鐘）", 1, 60, 15)
        tg_overnight       = st.checkbox("🌙 隔夜時段發送通知", value=False)
        tg_premarket       = st.checkbox("🌅 盤前時段發送通知", value=True)
        tg_afterhours      = st.checkbox("🌆 盤後時段發送通知", value=True)
    else:
        cooldown_min  = 15
        tg_overnight  = False
        tg_premarket  = True
        tg_afterhours = True

    if st.button("📤 測試 Telegram"):
        ok = send_telegram_text(tg_token, tg_chat,
                                "✅ 最穩訊號系統 — Telegram 連線測試成功！")
        if ok:
            st.success("發送成功 ✓")
        else:
            st.error("發送失敗，請檢查 Token / Chat ID")

    st.divider()
    if st.button("🗑 清除今日記錄"):
        st.session_state.signal_log = []
        st.session_state.notified   = {}
        st.rerun()


# ═════════════════════════════════════════════
#  MAIN
# ═════════════════════════════════════════════
london_now = datetime.now(ZoneInfo("Europe/London"))
et_now     = datetime.now(ET)
cur_session = get_session(et_now)
scfg        = SESSION_CONFIG[cur_session]

# ── auto-restrict timeframes for non-regular hours ──
effective_tfs = get_allowed_tfs(cur_session, selected_tfs)
tfs_restricted = (cur_session != "regular" and effective_tfs != selected_tfs)

# header
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(
        '<h2 style="color:#2c2c2a;font-weight:600;margin:0;font-size:22px">'
        '最穩上升趨勢 入場訊號系統</h2>',
        unsafe_allow_html=True,
    )
    tf_html = "".join(
        f'<span class="tf-badge-{"on" if tf in effective_tfs else "off"}">{tf}</span>'
        for tf in ["1m","5m","15m","1h","1d"]
    )
    st.markdown(
        f'<div style="margin-top:6px;font-size:12px;color:#888780">'
        f'監控：<span style="color:#2c2c2a;font-weight:500">{", ".join(stocks)}</span>'
        f'&nbsp;&nbsp;週期：{tf_html}'
        f'&nbsp;&nbsp;刷新：<span style="color:#639922;{MONO}">{refresh_sec}s</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
with col_h2:
    st.markdown(
        f'<div style="text-align:right">'
        f'<div style="font-size:20px;font-weight:600;color:#2c2c2a;{MONO}">'
        f'{et_now.strftime("%H:%M:%S")}</div>'
        f'<div style="font-size:10px;color:#b4b2a9;margin-top:1px">ET &nbsp;|&nbsp; '
        f'{london_now.strftime("%H:%M")} LON</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.divider()

# ── session banner ──
warn_extra = " — 流動性偏低，訊號僅供參考，慎用大倉" if scfg["warn"] else " — 正常交易時段"
tf_note    = f"　·　已自動限制週期為 {', '.join(effective_tfs)}" if tfs_restricted else ""
st.markdown(
    f'<div style="background:{scfg["bg"]};border:0.5px solid {scfg["border"]};'
    f'border-radius:8px;padding:10px 16px;margin-bottom:4px;'
    f'font-size:13px;color:{scfg["color"]};font-weight:500">'
    f'{scfg["emoji"]} {scfg["label"]}{warn_extra}{tf_note}'
    f'</div>',
    unsafe_allow_html=True,
)
st.divider()

# market filter
if use_market_filter:
    mkt_ok, vix_val, spy_chg = get_market_ok(vix_threshold, spy_drop_thresh)
    cm1, cm2, cm3 = st.columns(3)
    cls = "mkt-ok" if mkt_ok else "mkt-bad"
    lbl = "✅ 大市允許入場" if mkt_ok else "🚫 大市過濾中，暫停通知"
    cm1.markdown(f'<div class="{cls}">{lbl}</div>', unsafe_allow_html=True)
    if vix_val:
        cm2.metric("VIX", f"{vix_val:.1f}", delta=f"上限 {vix_threshold}")
    if spy_chg is not None:
        cm3.metric("SPY 今日", f"{spy_chg:+.2f}%", delta=f"下限 -{spy_drop_thresh}%")
    st.divider()
else:
    mkt_ok = True

# scan
scan_pairs   = [(t, tf) for t in stocks for tf in effective_tfs]
total_pairs  = len(scan_pairs)
live_signals = []

prog = st.progress(0, text="🔍 掃描中…")
for idx, (ticker, tf) in enumerate(scan_pairs):
    prog.progress((idx + 1) / total_pairs, text=f"🔍 掃描 {ticker} {tf}…")
    df  = fetch_data(ticker, tf)
    sig = check_signals(df, enabled_conditions, dynamic_stop, mkt_ok)
    if sig is None:
        continue
    if use_score_filter and sig["max_score"] > 0:
        if sig["score"] / sig["max_score"] * 100 < min_score_pct:
            continue

    sig["ticker"]    = ticker
    sig["timeframe"] = tf

    # ── 用即時報價覆蓋入場價（4層策略）──
    rt = get_realtime_price(ticker)
    if rt["price"] and rt["price"] > 0:
        new_entry = rt["price"]
        stop      = sig["stop"]  # EMA20 止損不變
        risk      = max(new_entry - stop, new_entry * 0.005)
        sig["entry"]        = new_entry
        sig["t1"]           = new_entry + risk * 2.5
        sig["t2"]           = new_entry + risk * 4.0
        sig["up1"]          = (sig["t1"] - new_entry) / new_entry * 100
        sig["up2"]          = (sig["t2"] - new_entry) / new_entry * 100
        sig["risk_pct"]     = (new_entry - stop) / new_entry * 100
        sig["rrr"]          = f"1 : {(sig['t1'] - new_entry) / risk:.1f}"
        sig["price_source"] = rt["source"]
        sig["staleness"]    = rt.get("staleness_sec")

    # session-aware Telegram gate
    sess = sig.get("session", "regular")
    tg_session_ok = {
        "overnight":  tg_overnight,
        "premarket":  tg_premarket,
        "regular":    True,
        "afterhours": tg_afterhours,
    }.get(sess, True)

    if tg_enabled and tg_session_ok:
        key       = dedup_key(ticker, tf)
        last_sent = st.session_state.notified.get(key, 0)
        now_ts    = time.time()
        if now_ts - last_sent > cooldown_min * 60:
            msg = build_telegram_message(sig)
            if send_chart:
                cb = make_chart_bytes(df, ticker, tf, sig)
                if cb:
                    send_telegram_photo(tg_token, tg_chat, cb, msg[:1000])
                else:
                    send_telegram_text(tg_token, tg_chat, msg)
            else:
                send_telegram_text(tg_token, tg_chat, msg)
            st.session_state.notified[key] = now_ts
            st.session_state.signal_log.insert(0, {
                "time":      sig["time"],
                "ticker":    ticker,
                "tf":        tf,
                "score":     sig["score"],
                "max_score": sig["max_score"],
                "entry":     sig["entry"],
                "session":   sess,
            })

    live_signals.append(sig)

prog.empty()

# stat row
today_count = len(st.session_state.signal_log)
c1, c2, c3, c4 = st.columns(4)
c1.metric("即時訊號",  len(live_signals))
c2.metric("今日累計",  today_count)
c3.metric("監控組合",  total_pairs)
c4.metric("啟用條件",  f"{active_count}/5")

st.divider()

# signal cards
if live_signals:
    st.markdown(
        f'<div style="font-size:10px;color:#b4b2a9;letter-spacing:1.5px;'
        f'text-transform:uppercase;margin-bottom:12px">'
        f'即時訊號 — {len(live_signals)} 個</div>',
        unsafe_allow_html=True,
    )
    for sig in live_signals:
        render_signal_card(sig["ticker"], sig["timeframe"], sig)
else:
    st.markdown("""
    <div class="empty-state">
      <div style="font-size:30px;margin-bottom:10px">◎</div>
      <div style="font-size:13px;font-weight:500">暫無訊號 — 系統持續監控中</div>
      <div style="font-size:11px;margin-top:6px;color:#d3d1c7">條件未全數成立，等待最佳入場時機</div>
    </div>
    """, unsafe_allow_html=True)

# activity log
if st.session_state.signal_log:
    st.divider()
    st.markdown(
        '<div style="font-size:10px;color:#b4b2a9;letter-spacing:1.5px;'
        'text-transform:uppercase;margin-bottom:8px">今日訊號記錄</div>',
        unsafe_allow_html=True,
    )
    for entry in st.session_state.signal_log[:10]:
        dots      = "🟢" * entry["score"] + "⚫" * (entry.get("max_score", 5) - entry["score"])
        sess_emoji = SESSION_CONFIG.get(entry.get("session","regular"), {}).get("emoji","📈")
        st.markdown(f"""
        <div class="log-row">
          <span style="color:#b4b2a9;min-width:56px">{entry['time']}</span>
          <span style="min-width:18px">{sess_emoji}</span>
          <span style="color:#3b6d11;font-weight:500;min-width:44px">{entry['ticker']}</span>
          <span style="color:#854f0b;min-width:30px">{entry['tf']}</span>
          <span style="color:#5f5e5a">入場 ${entry['entry']:.2f}</span>
          <span style="margin-left:auto">{dots}</span>
        </div>
        """, unsafe_allow_html=True)

# footer
st.markdown(
    f'<div class="scan-footer">'
    f'最後掃描：{et_now.strftime("%Y-%m-%d %H:%M:%S")} ET'
    f'&nbsp;·&nbsp;{london_now.strftime("%H:%M")} LON'
    f'&nbsp;·&nbsp; 下次刷新 {refresh_sec}s 後'
    f'</div>',
    unsafe_allow_html=True,
)

time.sleep(refresh_sec)
st.rerun()
