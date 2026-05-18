"""
最穩上升趨勢 — 入場訊號監控系統
Stable Uptrend Signal Monitor
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
import matplotlib.patches as mpatches
from datetime import datetime, timezone
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
# CUSTOM CSS  — light cream theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #f5f2eb;
    color: #2c2c2a;
}
.main .block-container {
    background-color: #f5f2eb;
    padding-top: 1.5rem;
}

/* ── sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 0.5px solid #ddd8ce !important;
}
section[data-testid="stSidebar"] * {
    font-family: 'Inter', sans-serif !important;
    color: #2c2c2a !important;
}
section[data-testid="stSidebar"] .stMarkdown p {
    font-size: 12px;
    color: #5f5e5a !important;
}

/* ── signal card ── */
.signal-card {
    background: #ffffff;
    border: 0.5px solid #ddd8ce;
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 12px;
}
.signal-card-strong {
    border-left: 3px solid #3b6d11;
}
.signal-card-warn {
    border-left: 3px solid #ba7517;
}

/* ── price boxes inside card ── */
.metric-box {
    background: #faf8f4;
    border: 0.5px solid #e8e4db;
    border-radius: 7px;
    padding: 10px 12px;
    text-align: left;
}

/* ── condition tags ── */
.tag-green {
    background: #eaf3de;
    border: 0.5px solid #c0dd97;
    color: #3b6d11;
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 11px;
    margin-right: 4px;
}
.tag-yellow {
    background: #faeeda;
    border: 0.5px solid #fac775;
    color: #633806;
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 11px;
    margin-right: 4px;
}
.tag-red {
    background: #fcebeb;
    border: 0.5px solid #f7c1c1;
    color: #a32d2d;
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 11px;
    margin-right: 4px;
}
.tag-blue {
    background: #e6f1fb;
    border: 0.5px solid #b5d4f4;
    color: #0c447c;
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 11px;
    margin-right: 4px;
}

/* ── st.metric cards ── */
div[data-testid="stMetric"] {
    background: #ffffff;
    border: 0.5px solid #ddd8ce;
    border-radius: 10px;
    padding: 14px 16px;
}
div[data-testid="stMetric"] label {
    color: #888780 !important;
    font-size: 11px !important;
    font-weight: 400 !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #2c2c2a !important;
    font-size: 22px !important;
    font-weight: 600 !important;
}

/* ── buttons ── */
.stButton>button {
    background: #faf8f4;
    border: 0.5px solid #ddd8ce;
    color: #5f5e5a;
    border-radius: 6px;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 500;
}
.stButton>button:hover {
    background: #eaf3de;
    border-color: #c0dd97;
    color: #3b6d11;
}

/* ── text inputs ── */
.stTextInput>div>div>input {
    background: #faf8f4 !important;
    border: 0.5px solid #ddd8ce !important;
    color: #2c2c2a !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
}

/* ── checkbox accent ── */
.stCheckbox span { color: #5f5e5a !important; font-size: 13px !important; }
input[type=checkbox] { accent-color: #639922 !important; }

/* ── slider accent ── */
.stSlider div[data-baseweb="slider"] div { background: #639922 !important; }

/* ── progress bar ── */
.stProgress > div > div { background: #639922 !important; }

/* ── success / info banners ── */
.stSuccess { background: #eaf3de !important; color: #3b6d11 !important; border-radius: 7px !important; }

/* ── divider ── */
hr { border-color: #e8e4db !important; }

/* ── captions ── */
.stCaption, small { color: #b4b2a9 !important; font-size: 11px !important; }

/* ── headings in main area ── */
h1, h2, h3 { color: #2c2c2a !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "signal_log": [],
        "notified": {},       # key -> timestamp, for dedup
        "last_refresh": None,
        "signals": [],
        "running": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def get_telegram_creds(manual_token, manual_chat):
    """Prefer st.secrets, fallback to manual input."""
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
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        r = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
        return r.ok
    except Exception:
        return False


def send_telegram_photo(token, chat_id, img_bytes, caption=""):
    if not token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        r = requests.post(url,
            data={"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"},
            files={"photo": ("chart.png", img_bytes, "image/png")},
            timeout=15)
        return r.ok
    except Exception:
        return False


def build_telegram_message(sig):
    cond_names = [
        "EMA完美多頭排列",
        "無連續兩根K跌穿EMA15",
        "K線主體在EMA10之上",
        "MACD雙線零軸之上",
        "量能配合上漲",
    ]
    cond_lines = "\n".join(
        f"{'✅' if v else '❌'} {cond_names[i]}"
        for i, v in enumerate(sig["conditions"])
    )
    score_bar = "🟢" * sig["score"] + "⚫" * (5 - sig["score"])

    msg = f"""🚨 <b>最穩上升趨勢訊號</b> — {sig['ticker']} {sig['timeframe']}

{cond_lines}

{score_bar}  強度 {sig['score']}/5
📊 趨勢持續 {sig['duration']} 根K線

🟢 <b>入場價：</b>${sig['entry']:.2f}
🎯 <b>目標一：</b>${sig['t1']:.2f}（+{sig['up1']:.1f}%）
🎯 <b>目標二：</b>${sig['t2']:.2f}（+{sig['up2']:.1f}%）
🔴 <b>止損價：</b>${sig['stop']:.2f}（-{sig['risk_pct']:.1f}%）
📐 <b>風險回報：</b>{sig['rrr']}

🕐 {sig['time']}"""
    return msg


# ─────────────────────────────────────────────
# INDICATORS  (pure pandas/numpy, no TA-Lib)
# ─────────────────────────────────────────────
def calc_ema(series, n):
    return series.ewm(span=n, adjust=False).mean()

def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast = calc_ema(close, fast)
    ema_slow = calc_ema(close, slow)
    dif = ema_fast - ema_slow
    dea = calc_ema(dif, signal)
    hist = (dif - dea) * 2
    return dif, dea, hist

def calc_indicators(df):
    c = df["Close"]
    v = df["Volume"]
    df["ema5"]   = calc_ema(c, 5)
    df["ema10"]  = calc_ema(c, 10)
    df["ema15"]  = calc_ema(c, 15)
    df["ema20"]  = calc_ema(c, 20)
    df["ema50"]  = calc_ema(c, 50)
    df["ema120"] = calc_ema(c, 120)
    df["ema200"] = calc_ema(c, 200)
    df["dif"], df["dea"], df["macd_hist"] = calc_macd(c)
    df["vol_ma5"] = v.rolling(5).mean()
    return df


# ─────────────────────────────────────────────
# DATA FETCH
# ─────────────────────────────────────────────
TF_MAP = {
    "1m":  ("7d",  "1m"),
    "5m":  ("60d", "5m"),
    "15m": ("60d", "15m"),
    "1h":  ("730d","1h"),
    "1d":  ("5y",  "1d"),
}

@st.cache_data(ttl=25, show_spinner=False)
def fetch_data(ticker, timeframe):
    period, interval = TF_MAP[timeframe]
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False)
        if df.empty:
            return None
        # flatten MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[["Open","High","Low","Close","Volume"]].dropna()
        df = calc_indicators(df)
        return df
    except Exception:
        return None


# ─────────────────────────────────────────────
# SIGNAL EVALUATION
# ─────────────────────────────────────────────
def check_signals(df, enabled_conditions, dynamic_stop, market_filter_ok):
    if df is None or len(df) < 210:
        return None

    last   = df.iloc[-1]
    prev   = df.iloc[-2]
    c      = last["Close"]

    # ── 5 core conditions ──
    c1 = (last["ema5"] > last["ema10"] > last["ema15"] > last["ema20"]
          > last["ema50"] > last["ema120"] > last["ema200"])

    c2 = (last["Close"] >= last["ema15"] and prev["Close"] >= prev["ema15"])

    c3 = last["Close"] > last["ema10"]

    c4 = (last["dif"] > 0 and last["dea"] > 0)

    c5 = (pd.notna(last["vol_ma5"]) and last["Volume"] > last["vol_ma5"])

    raw_results = [c1, c2, c3, c4, c5]

    # only evaluate enabled conditions
    active_results = [
        raw_results[i] if enabled_conditions[i] else True   # disabled = skip (pass)
        for i in range(5)
    ]

    # score = how many ENABLED conditions pass
    enabled_indices = [i for i in range(5) if enabled_conditions[i]]
    score = sum(raw_results[i] for i in enabled_indices)
    max_score = len(enabled_indices) if enabled_indices else 1

    all_pass = all(active_results)

    if not all_pass:
        return None
    if not market_filter_ok:
        return None

    # ── trend duration: how many bars EMA aligned ──
    duration = 0
    for i in range(len(df) - 1, -1, -1):
        row = df.iloc[i]
        if (row["ema5"] > row["ema10"] > row["ema15"] > row["ema20"]
                > row["ema50"] > row["ema120"] > row["ema200"]):
            duration += 1
        else:
            break

    # ── entry / targets / stop ──
    entry = c
    if dynamic_stop:
        stop = last["ema20"]
    else:
        stop = entry * 0.995   # 0.5% fixed

    risk_per_share = entry - stop
    if risk_per_share <= 0:
        risk_per_share = entry * 0.005

    t1 = entry + risk_per_share * 2.5
    t2 = entry + risk_per_share * 4.0

    up1 = (t1 - entry) / entry * 100
    up2 = (t2 - entry) / entry * 100
    risk_pct = (entry - stop) / entry * 100
    rrr = f"1 : {risk_per_share and (t1-entry)/risk_per_share:.1f}"

    london_now = datetime.now(ZoneInfo("Europe/London")).strftime("%H:%M:%S")

    return {
        "conditions": raw_results,
        "enabled":    enabled_conditions,
        "score":      score,
        "max_score":  max_score,
        "duration":   duration,
        "entry":      entry,
        "t1":         t1,
        "t2":         t2,
        "stop":       stop,
        "up1":        up1,
        "up2":        up2,
        "risk_pct":   risk_pct,
        "rrr":        rrr,
        "time":       london_now,
        "df":         df,
    }


# ─────────────────────────────────────────────
# CHART GENERATION (for Telegram)
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
        for i, (idx, row) in enumerate(plot_df.iterrows()):
            color = "#3b6d11" if row["Close"] >= row["Open"] else "#a32d2d"
            ax1.plot([i, i], [row["Low"], row["High"]], color=color, linewidth=0.8)
            ax1.bar(i, abs(row["Close"] - row["Open"]),
                    bottom=min(row["Open"], row["Close"]),
                    color=color, width=0.6, alpha=0.9)

        for ema, col, lw in [("ema5","#00ff88",1.2),("ema10","#ffff00",1.2),
                              ("ema15","#ff8800",1.0),("ema20","#ff4444",1.0),
                              ("ema50","#cc44ff",0.8),("ema200","#44ccff",0.8)]:
            ax1.plot(x, plot_df[ema].values, color=col, linewidth=lw, alpha=0.85)

        # entry / target / stop lines
        ax1.axhline(sig["entry"], color="#185fa5", linewidth=1.2, linestyle="--", alpha=0.8)
        ax1.axhline(sig["t1"],    color="#3b6d11", linewidth=1.2, linestyle="--", alpha=0.8)
        ax1.axhline(sig["stop"],  color="#a32d2d", linewidth=1.2, linestyle="--", alpha=0.8)

        ax1.set_title(f"{ticker} {timeframe}  —  最穩上升趨勢訊號",
                      color="#2c2c2a", fontsize=13, pad=10)
        ax1.tick_params(colors="#888780"); ax1.spines[:].set_color("#e8e4db")

        # volume
        colors_v = ["#3b6d11" if r["Close"] >= r["Open"] else "#a32d2d"
                    for _, r in plot_df.iterrows()]
        ax2.bar(x, plot_df["Volume"].values, color=colors_v, alpha=0.7, width=0.6)
        ax2.tick_params(colors="#888780"); ax2.spines[:].set_color("#e8e4db")

        plt.tight_layout(pad=1.5)
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=120, facecolor="#f5f2eb")
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    except Exception:
        return None


# ─────────────────────────────────────────────
# DEDUP KEY
# ─────────────────────────────────────────────
def dedup_key(ticker, timeframe):
    return hashlib.md5(f"{ticker}-{timeframe}".encode()).hexdigest()


# ─────────────────────────────────────────────
# MARKET FILTER  (SPY / VIX)
# ─────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def get_market_ok(vix_threshold, spy_drop_threshold):
    try:
        vix = yf.download("^VIX", period="2d", interval="1d", progress=False)
        spy = yf.download("SPY",  period="2d", interval="1d", progress=False)
        if isinstance(vix.columns, pd.MultiIndex):
            vix.columns = vix.columns.get_level_values(0)
        if isinstance(spy.columns, pd.MultiIndex):
            spy.columns = spy.columns.get_level_values(0)
        vix_val  = float(vix["Close"].iloc[-1])
        spy_chg  = float((spy["Close"].iloc[-1] - spy["Close"].iloc[-2]) / spy["Close"].iloc[-2] * 100)
        ok = (vix_val <= vix_threshold) and (spy_chg >= -spy_drop_threshold)
        return ok, vix_val, spy_chg
    except Exception:
        return True, None, None   # fail open


# ─────────────────────────────────────────────
# RENDER SIGNAL CARD
# ─────────────────────────────────────────────
COND_NAMES = [
    "EMA多頭排列",
    "不跌穿EMA15",
    "主體EMA10上",
    "MACD零軸上",
    "量能配合",
]

def render_signal_card(ticker, timeframe, sig):
    score    = sig["score"]
    max_s    = sig["max_score"]
    border   = "signal-card-strong" if score == max_s else "signal-card-warn"
    score_dots = "🟢" * score + "⚫" * (max_s - score)

    cond_html = " ".join(
        f'<span class="{"tag-green" if sig["conditions"][i] else "tag-red"}">'
        f'{"✓" if sig["conditions"][i] else "✗"} {COND_NAMES[i]}</span>'
        for i in range(5) if sig["enabled"][i]
    )

    st.markdown(f"""
    <div class="signal-card {border}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
        <div>
          <span style="font-size:20px;font-weight:600;color:#2c2c2a;font-family:'JetBrains Mono',monospace">{ticker}</span>
          <span class="tag-green" style="margin-left:8px;font-family:'JetBrains Mono',monospace">{timeframe}</span>
          <span style="font-size:10px;color:#639922;margin-left:6px">● LIVE</span>
          <div style="font-size:11px;color:#b4b2a9;margin-top:4px">
            訊號時間 {sig['time']}
            {'&nbsp;&nbsp;·&nbsp;&nbsp;趨勢持續 <b style="color:#854f0b">' + str(sig['duration']) + '</b> 根K線' if True else ''}
          </div>
        </div>
        <div style="text-align:right">
          <div style="font-size:15px">{score_dots}</div>
          <div style="font-size:10px;color:#b4b2a9;margin-top:3px">強度 {score}/{max_s}</div>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;margin-bottom:12px">
        <div class="metric-box">
          <div style="font-size:9px;color:#b4b2a9;margin-bottom:3px">入場價</div>
          <div style="font-size:14px;font-weight:500;color:#185fa5;font-family:'JetBrains Mono',monospace">${sig['entry']:.2f}</div>
        </div>
        <div class="metric-box">
          <div style="font-size:9px;color:#b4b2a9;margin-bottom:3px">目標一</div>
          <div style="font-size:14px;font-weight:500;color:#3b6d11;font-family:'JetBrains Mono',monospace">${sig['t1']:.2f}</div>
          <div style="font-size:10px;color:#639922">+{sig['up1']:.1f}%</div>
        </div>
        <div class="metric-box">
          <div style="font-size:9px;color:#b4b2a9;margin-bottom:3px">目標二</div>
          <div style="font-size:14px;font-weight:500;color:#639922;font-family:'JetBrains Mono',monospace">${sig['t2']:.2f}</div>
          <div style="font-size:10px;color:#97c459">+{sig['up2']:.1f}%</div>
        </div>
        <div class="metric-box">
          <div style="font-size:9px;color:#b4b2a9;margin-bottom:3px">止損</div>
          <div style="font-size:14px;font-weight:500;color:#a32d2d;font-family:'JetBrains Mono',monospace">${sig['stop']:.2f}</div>
          <div style="font-size:10px;color:#d85a30">-{sig['risk_pct']:.1f}%</div>
        </div>
      </div>

      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>{cond_html}</div>
        <div style="font-size:11px;font-weight:500;color:#633806;background:#faeeda;
                    border:0.5px solid #fac775;border-radius:5px;padding:4px 10px;
                    font-family:'JetBrains Mono',monospace;white-space:nowrap">
          RRR {sig['rrr']}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ════════════════  SIDEBAR  ═════════════════
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-size:18px;font-weight:600;color:#2c2c2a;letter-spacing:-0.5px">最穩訊號</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:9px;color:#b4b2a9;letter-spacing:3px;margin-bottom:12px">SIGNAL MONITOR</div>', unsafe_allow_html=True)
    st.divider()

    # ── stocks ──
    st.markdown("**📊 監控股票**")
    stocks_raw = st.text_input(
        "輸入股票代碼（逗號分隔）",
        value="TSLA,NVDA,AAPL",
        placeholder="TSLA,AMZN,AAPL,MSFT,…",
        label_visibility="collapsed",
    )
    stocks = [s.strip().upper() for s in stocks_raw.split(",") if s.strip()]
    st.caption(f"共 {len(stocks)} 隻：{', '.join(stocks)}")

    st.divider()

    # ── timeframes ──
    st.markdown("**⏱ 週期選擇**")
    tf_options = ["1m", "5m", "15m", "1h", "1d"]
    selected_tfs = []
    cols_tf = st.columns(5)
    tf_defaults = {"1m": False, "5m": True, "15m": True, "1h": False, "1d": False}
    for i, tf in enumerate(tf_options):
        if cols_tf[i].checkbox(tf, value=tf_defaults[tf], key=f"tf_{tf}"):
            selected_tfs.append(tf)
    if not selected_tfs:
        selected_tfs = ["5m"]
        st.caption("⚠️ 最少選一個週期，預設5m")

    st.divider()

    # ── refresh ──
    st.markdown("**🔄 刷新間隔**")
    refresh_sec = st.slider("秒", min_value=10, max_value=300, value=30, step=10, label_visibility="collapsed")
    st.caption(f"每 {refresh_sec} 秒自動刷新")

    st.divider()

    # ── core conditions ──
    st.markdown("**🎯 核心條件（個別開關）**")
    core_labels_full = [
        "C1：EMA完美多頭排列",
        "C2：無連續兩根K跌穿EMA15",
        "C3：K線主體在EMA10之上",
        "C4：MACD雙線零軸之上",
        "C5：量能配合上漲",
    ]
    core_defaults = [True, True, True, True, True]
    enabled_conditions = []
    for i, label in enumerate(core_labels_full):
        enabled_conditions.append(
            st.checkbox(label, value=core_defaults[i], key=f"cc_{i}")
        )
    active_count = sum(enabled_conditions)
    st.caption(f"✅ 已啟用 {active_count}/5 個條件")

    st.divider()

    # ── enhancements ──
    st.markdown("**⚙️ 增強功能**")

    use_score_filter = st.checkbox("訊號強度過濾", value=True)
    if use_score_filter:
        min_score_pct = st.slider("最低通過比例（啟用條件中）",
                                   min_value=50, max_value=100, value=80, step=10,
                                   format="%d%%")
    else:
        min_score_pct = 0

    show_duration = st.checkbox("顯示趨勢持續K線數", value=True)

    dynamic_stop = st.checkbox("止損用 EMA20（動態）", value=True)
    if not dynamic_stop:
        st.caption("止損改用固定 0.5%")

    use_market_filter = st.checkbox("VIX / SPY 大市過濾", value=False)
    if use_market_filter:
        vix_threshold    = st.slider("VIX 上限", 15, 40, 25)
        spy_drop_thresh  = st.slider("SPY 單日跌幅上限 (%)", 0.5, 3.0, 1.5, step=0.5)
    else:
        vix_threshold, spy_drop_thresh = 999, 999

    send_chart = st.checkbox("Telegram 附帶K線截圖", value=False)

    st.divider()

    # ── telegram ──
    st.markdown("**📡 Telegram 通知**")

    tg_enabled = st.checkbox("啟用 Telegram 通知", value=True)

    # Detect if secrets exist
    try:
        secret_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
        secret_chat  = st.secrets.get("TELEGRAM_CHAT_ID",   "")
        has_secrets  = bool(secret_token and secret_chat)
    except Exception:
        secret_token, secret_chat, has_secrets = "", "", False

    if has_secrets:
        st.success("✅ 已從 Streamlit Secrets 讀取 Token", icon="🔐")
        manual_token, manual_chat = "", ""
    else:
        st.caption("未偵測到 Secrets，請手動輸入：")
        manual_token = st.text_input("Bot Token", type="password", placeholder="110201543:AAHdq...")
        manual_chat  = st.text_input("Chat ID",  placeholder="-1001234567890")

    tg_token, tg_chat = get_telegram_creds(manual_token, manual_chat)

    if tg_enabled:
        cooldown_min = st.slider("通知冷卻（分鐘）", 1, 60, 15)
    else:
        cooldown_min = 15

    if st.button("📤 測試 Telegram"):
        ok = send_telegram_text(tg_token, tg_chat,
                                "✅ 最穩訊號系統 — Telegram 連線測試成功！")
        st.success("發送成功 ✓") if ok else st.error("發送失敗，請檢查 Token / Chat ID")

    st.divider()
    if st.button("🗑 清除今日訊號記錄"):
        st.session_state.signal_log = []
        st.session_state.notified   = {}
        st.rerun()


# ─────────────────────────────────────────────
# ════════════════  MAIN  ════════════════════
# ─────────────────────────────────────────────

# ── header ──
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown('<h2 style="color:#2c2c2a;font-weight:600;margin:0">最穩上升趨勢 入場訊號系統</h2>', unsafe_allow_html=True)
    st.caption(f"監控中：{', '.join(stocks)}　週期：{', '.join(selected_tfs)}　刷新：{refresh_sec}s")
with col_h2:
    london_time = datetime.now(ZoneInfo("Europe/London")).strftime("%H:%M:%S")
    st.markdown(f'<div style="text-align:right;font-size:20px;color:#2c2c2a;font-weight:600;font-family:\'JetBrains Mono\',monospace">{london_time}<br><span style="font-size:10px;color:#b4b2a9;font-family:\'Inter\',sans-serif">LONDON TIME</span></div>', unsafe_allow_html=True)

st.divider()

# ── market filter status ──
if use_market_filter:
    mkt_ok, vix_val, spy_chg = get_market_ok(vix_threshold, spy_drop_thresh)
    cols_mkt = st.columns(3)
    cols_mkt[0].metric("大市狀態", "✅ 允許入場" if mkt_ok else "🚫 過濾中")
    if vix_val:
        cols_mkt[1].metric("VIX", f"{vix_val:.1f}", delta=f"上限 {vix_threshold}")
    if spy_chg is not None:
        cols_mkt[2].metric("SPY 今日", f"{spy_chg:+.2f}%", delta=f"下限 -{spy_drop_thresh}%")
    st.divider()
else:
    mkt_ok = True

# ── scan ──
scan_pairs = [(t, tf) for t in stocks for tf in selected_tfs]
total_pairs = len(scan_pairs)

live_signals = []
progress_bar = st.progress(0, text="🔍 掃描中...")

for idx, (ticker, tf) in enumerate(scan_pairs):
    progress_bar.progress((idx + 1) / total_pairs,
                          text=f"🔍 掃描 {ticker} {tf}…")
    df = fetch_data(ticker, tf)
    sig = check_signals(df, enabled_conditions, dynamic_stop, mkt_ok)

    if sig is None:
        continue

    # score filter
    if use_score_filter and sig["max_score"] > 0:
        pct = sig["score"] / sig["max_score"] * 100
        if pct < min_score_pct:
            continue

    sig["ticker"]    = ticker
    sig["timeframe"] = tf

    # ── Telegram notify (dedup) ──
    if tg_enabled:
        key = dedup_key(ticker, tf)
        last_sent = st.session_state.notified.get(key, 0)
        now_ts    = time.time()
        if now_ts - last_sent > cooldown_min * 60:
            msg = build_telegram_message(sig)
            if send_chart:
                chart_bytes = make_chart_bytes(df, ticker, tf, sig)
                if chart_bytes:
                    send_telegram_photo(tg_token, tg_chat, chart_bytes, caption=msg[:1000])
                else:
                    send_telegram_text(tg_token, tg_chat, msg)
            else:
                send_telegram_text(tg_token, tg_chat, msg)
            st.session_state.notified[key] = now_ts
            # add to log
            st.session_state.signal_log.insert(0, {
                "time": sig["time"], "ticker": ticker, "tf": tf,
                "score": sig["score"], "entry": sig["entry"],
            })

    live_signals.append(sig)

progress_bar.empty()

# ── stats row ──
today_count = len(st.session_state.signal_log)
col1, col2, col3, col4 = st.columns(4)
col1.metric("🔴 即時訊號", len(live_signals))
col2.metric("📋 今日累計", today_count)
col3.metric("📡 監控組合", total_pairs)
col4.metric("✅ 啟用條件", f"{active_count}/5")

st.divider()

# ── signal cards ──
if live_signals:
    st.markdown(f'<div style="font-size:10px;color:#b4b2a9;letter-spacing:2px;margin-bottom:14px">LIVE SIGNALS — {len(live_signals)} 個訊號</div>', unsafe_allow_html=True)
    for sig in live_signals:
        render_signal_card(sig["ticker"], sig["timeframe"], sig)
else:
    st.markdown("""
    <div style="border:0.5px dashed #d3d1c7;border-radius:10px;padding:40px;text-align:center;color:#b4b2a9;margin-top:20px;background:#ffffff">
      <div style="font-size:32px;margin-bottom:12px">◎</div>
      <div style="font-size:13px;letter-spacing:1px">暫無訊號 — 系統持續監控中</div>
      <div style="font-size:11px;margin-top:8px;color:#d3d1c7">條件未全數成立，等待最佳入場時機</div>
    </div>
    """, unsafe_allow_html=True)

# ── activity log ──
if st.session_state.signal_log:
    st.divider()
    st.markdown('<div style="font-size:9px;color:#b4b2a9;letter-spacing:2px;margin-bottom:6px">SIGNAL LOG</div>', unsafe_allow_html=True)
    for entry in st.session_state.signal_log[:10]:
        col_l1, col_l2, col_l3, col_l4 = st.columns([1, 1, 1, 2])
        col_l1.markdown(f'<span style="color:#b4b2a9;font-size:11px;font-family:\'JetBrains Mono\',monospace">{entry["time"]}</span>', unsafe_allow_html=True)
        col_l2.markdown(f'<span style="color:#3b6d11;font-size:12px;font-weight:500;font-family:\'JetBrains Mono\',monospace">{entry["ticker"]}</span>', unsafe_allow_html=True)
        col_l3.markdown(f'<span style="color:#854f0b;font-size:11px;font-family:\'JetBrains Mono\',monospace">{entry["tf"]}</span>', unsafe_allow_html=True)
        col_l4.markdown(f'<span style="color:#5f5e5a;font-size:11px;font-family:\'JetBrains Mono\',monospace">入場 ${entry["entry"]:.2f}　強度 {"🟢"*entry["score"]}</span>', unsafe_allow_html=True)

# ── last refresh + auto-refresh ──
st.divider()
st.markdown(f'<div style="font-size:10px;color:#b4b2a9">最後掃描：{datetime.now(ZoneInfo("Europe/London")).strftime("%Y-%m-%d %H:%M:%S")} London　·　下次刷新 {refresh_sec}s 後</div>', unsafe_allow_html=True)

time.sleep(refresh_sec)
st.rerun()
