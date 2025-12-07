import time
import requests
import pandas as pd
import altair as alt
import streamlit as st
from datetime import datetime
import pytz

# =========================================
# CONFIG
# =========================================
BACKEND_URL = "https://n8n-pop-3yxb.onrender.com/api/workflows/"
STATUS_URL = "https://n8n-pop-3yxb.onrender.com/api/status/"
TRIGGER_URL = "https://n8n-pop-3yxb.onrender.com/trigger"
TRIGGER_SECRET = "f91b2d88219a83f0aaecc3fa4423c8d4"

IST = pytz.timezone("Asia/Kolkata")

st.set_page_config(
    page_title="n8n Popularity Intelligence Dashboard",
    layout="wide",
    page_icon="🔗",
)

# =========================================
# STYLES
# =========================================
st.markdown(
    """
<style>
.metric-card {
    padding: 18px;
    border-radius: 14px;
    background: #f7f9fc;
    border: 1px solid #e2e6f0;
    margin-bottom: 12px;
    text-align: center;
}
.metric-label {
    font-size: 13px;
    font-weight: 600;
    color: #555;
}
.metric-value {
    font-size: 24px;
    font-weight: 700;
    color: #1f4fe0;
}
.pill-green {
    background: #e6f7ec; padding:6px 12px; border-radius:6px; color:#137333; font-weight:600;
}
.pill-red {
    background: #fde8e8; padding:6px 12px; border-radius:6px; color:#b91c1c; font-weight:600;
}
.hr-soft {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 1rem 0;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================
# HELPERS
# =========================================
def utc_to_ist(ts):
    if not ts:
        return "Unknown"
    try:
        utc_dt = pd.to_datetime(ts).tz_localize("UTC")
        ist_dt = utc_dt.tz_convert(IST)
        return ist_dt.strftime("%Y-%m-%d %H:%M IST")
    except:
        return ts


def safe_get(url, params=None, timeout=20, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
        except:
            time.sleep(1)
    return None


@st.cache_data(ttl=300, show_spinner=False)
def fetch_workflows(params):
    return safe_get(BACKEND_URL, params=params)


@st.cache_data(ttl=60, show_spinner=False)
def fetch_status():
    return safe_get(STATUS_URL)


# =========================================
# HEADER
# =========================================
st.title("🔗 n8n Workflow Popularity Intelligence Dashboard")

header_left, header_right = st.columns([0.75, 0.25])

with header_left:
    st.markdown("""
Tracks **real-time popularity** of n8n workflows across:
- 🎥 YouTube  
- 💬 Forum  
- 📈 Google Trends  
""")

with header_right:
    health = safe_get(STATUS_URL, timeout=5, retries=1)
    if health:
        st.markdown('<div class="pill-green">● Backend: Healthy</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="pill-red">● Backend: Offline</div>', unsafe_allow_html=True)

st.markdown('<hr class="hr-soft" />', unsafe_allow_html=True)

# =========================================
# SIDEBAR FILTERS
# =========================================
st.sidebar.header("🔍 Filters")

platform = st.sidebar.selectbox("Platform", ["All", "YouTube", "Forum", "GoogleTrends"])
country = st.sidebar.selectbox("Country", ["All", "US", "IN"])
sort_by = st.sidebar.selectbox("Sort By", ["popularity_score", "workflow"])
order = st.sidebar.radio("Order", ["Descending", "Ascending"], index=0)
limit = st.sidebar.slider("Max results", 10, 500, 50)
search_keyword = st.sidebar.text_input("Search workflow")

st.sidebar.markdown("---")
st.sidebar.subheader("⚙ Backend Actions")

if st.sidebar.button("🔄 Trigger Backend Fetch"):
    try:
        for src in ["youtube", "forum", "trends"]:
            for c in ["US", "IN"]:
                requests.post(
                    f"{TRIGGER_URL}/{src}/{c}/",
                    headers={"X-Trigger-Secret": TRIGGER_SECRET},
                )
        st.sidebar.success("Fetch triggered successfully ✔")
    except Exception as e:
        st.sidebar.error(f"Trigger failed: {e}")

if st.sidebar.button("🧹 Clear Cache"):
    fetch_workflows.clear()
    fetch_status.clear()
    st.sidebar.success("Cache cleared.")
    st.rerun()

# =========================================
# CRON STATUS
# =========================================
st.subheader("⏱ Cron / Auto-Refresh Status")

status = fetch_status()

col1, col2, col3 = st.columns(3)

if status:
    last_run = utc_to_ist(status.get("last_run"))
    next_run = utc_to_ist(status.get("next_run"))
    interval = status.get("interval_hours", 6)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Last Update</div>
            <div class="metric-value">{last_run}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Next Update</div>
            <div class="metric-value">{next_run}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Interval</div>
            <div class="metric-value">{interval} hrs</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.error("Failed to load cron data.")

st.markdown('<hr class="hr-soft" />', unsafe_allow_html=True)

# =========================================
# LOAD WORKFLOW DATA
# =========================================
with st.spinner("📥 Loading workflow database..."):
    params = {"limit": limit}
    if platform != "All":
        params["platform"] = platform
    if country != "All":
        params["country"] = country

    data = fetch_workflows(params)

if not data:
    st.error("Backend unavailable — try clearing cache or retry later.")
    st.stop()

df = pd.DataFrame(data)

if search_keyword:
    df = df[df["workflow"].str.contains(search_keyword, case=False, na=False)]

df = df.sort_values(by=sort_by, ascending=(order == "Ascending"))

# =========================================
# METRICS SUMMARY
# =========================================
st.subheader("📊 High-Level Insights")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Workflows</div>
        <div class="metric-value">{len(df)}</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    avg_score = round(df["popularity_score"].mean(), 2)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Avg Score</div>
        <div class="metric-value">{avg_score}</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    top_platform = df["platform"].value_counts().idxmax()
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Top Platform</div>
        <div class="metric-value">{top_platform}</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    top_country = df["country"].value_counts().idxmax()
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Top Country</div>
        <div class="metric-value">{top_country}</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================
# TABS
# =========================================
tab1, tab2, tab3 = st.tabs(["📋 Overview", "🧩 Platform Breakdown", "🔎 Evidence Explorer"])

# --- TAB 1 ---
with tab1:
    st.dataframe(df, use_container_width=True)

    st.markdown("### 📊 Popularity Score Chart")
    chart = (
        alt.Chart(df.head(30))
        .mark_bar()
        .encode(
            x=alt.X("workflow:N", sort="-y"),
            y="popularity_score:Q",
            color="platform:N",
            tooltip=["workflow", "platform", "popularity_score"],
        )
        .properties(height=400)
    )
    st.altair_chart(chart, use_container_width=True)

# --- TAB 2 ---
with tab2:
    st.bar_chart(df["platform"].value_counts())

    st.markdown("### Avg Score by Platform")
    st.dataframe(df.groupby("platform")["popularity_score"].mean().round(2))

# --- TAB 3 ---
with tab3:
    title = st.selectbox("Choose workflow", df["workflow"].unique())
    selected = df[df["workflow"] == title]

    st.markdown(f"### 📌 {title}")
    for _, row in selected.iterrows():
        st.write(f"**Platform:** {row['platform']}")
        st.write(f"**Country:** {row['country']}")
        st.write(f"**Source:** {row['source_url']}")
        st.write(f"**Score:** {row['popularity_score']}")
        st.json(row["popularity_metrics"])

# =========================================
# FOOTER
# =========================================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("Built by **Bandapu Vivekananda** · SpeakGenie Internship Assignment")

