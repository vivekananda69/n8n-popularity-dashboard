import time
import requests
import pandas as pd
import altair as alt
import streamlit as st

# =========================================
# CONFIG
# =========================================
BACKEND_URL = "https://n8n-pop-3yxb.onrender.com/api/workflows/"
STATUS_URL = "https://n8n-pop-3yxb.onrender.com/api/status/"
TRIGGER_URL = "https://n8n-pop-3yxb.onrender.com/trigger"
TRIGGER_SECRET = "f91b2d88219a83f0aaecc3fa4423c8d4"  # NOTE: in real prod, use env var

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
/* Global */
body {
    font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* KPI cards */
.metric-card {
    padding: 18px;
    border-radius: 14px;
    background: #f7f9fc;
    border: 1px solid #e2e6f0;
    margin-bottom: 10px;
}
.metric-label {
    font-size: 13px;
    font-weight: 600;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.metric-value {
    font-size: 26px;
    font-weight: 700;
    color: #1f4fe0;
}

/* Pills */
.pill {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    margin-right: 6px;
}
.pill-green { background: #e6f7ec; color: #137333; }
.pill-red { background: #fde8e8; color: #b91c1c; }
.pill-blue { background: #e0ebff; color: #1d4ed8; }

/* Section headings */
h2, h3 {
    margin-top: 0.2rem;
}

/* Thin divider */
.hr-soft {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 0.5rem 0 1rem;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================
# SMALL HELPERS
# =========================================
def fmt_ts(ts: str | None) -> str:
    """Format ISO timestamp to a short readable UTC string."""
    if not ts:
        return "Unknown"
    try:
        return pd.to_datetime(ts).strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return str(ts)


def safe_get(url, params=None, timeout=25, retries=2, sleep_sec=2):
    """GET with small retry logic, safe for Render cold starts."""
    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            last_err = f"HTTP {resp.status_code}"
        except Exception as e:
            last_err = str(e)
        if attempt < retries - 1:
            time.sleep(sleep_sec)
    return None


@st.cache_data(ttl=300, show_spinner=False)
def fetch_workflows_cached(params: dict):
    return safe_get(BACKEND_URL, params=params)


@st.cache_data(ttl=60, show_spinner=False)
def fetch_status_cached():
    return safe_get(STATUS_URL)


def backend_health() -> bool:
    """Quick boolean health, using status endpoint."""
    try:
        data = safe_get(STATUS_URL, timeout=5, retries=1)
        return data is not None
    except Exception:
        return False


# =========================================
# HEADER
# =========================================
st.title("🔗 n8n Workflow Popularity Intelligence Dashboard")

sub_left, sub_right = st.columns([0.7, 0.3])

with sub_left:
    st.markdown(
        """
Tracks **real-world popularity** of n8n workflows across:

- 🎥 **YouTube**
- 💬 **n8n Community Forum**
- 📈 **Google Trends**

Use the filters on the left to slice by platform, country, and score.
        """
    )

with sub_right:
    healthy = backend_health()
    if healthy:
        st.markdown(
            '<div class="pill pill-green">● Backend: Healthy</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="pill pill-red">● Backend: Unreachable</div>',
            unsafe_allow_html=True,
        )

st.markdown('<hr class="hr-soft" />', unsafe_allow_html=True)

# =========================================
# SIDEBAR – FILTERS & ACTIONS
# =========================================
st.sidebar.header("🔍 Filters")

platform = st.sidebar.selectbox(
    "Platform",
    ["All", "YouTube", "Forum", "GoogleTrends"],
)

country = st.sidebar.selectbox(
    "Country",
    ["All", "US", "IN"],
)

sort_by = st.sidebar.selectbox("Sort By", ["popularity_score", "workflow"])
order = st.sidebar.radio("Order", ["Descending", "Ascending"], index=0, horizontal=True)
limit = st.sidebar.slider("Max results", 10, 500, 50, step=10)
search_keyword = st.sidebar.text_input("Search in workflow title")

st.sidebar.markdown("---")

# Manual backend refresh
st.sidebar.subheader("⚙ Backend Refresh")

if st.sidebar.button("🔄 Trigger Fetch on Backend"):
    try:
        for src in ["youtube", "forum", "trends"]:
            for c in ["US", "IN"]:
                requests.post(
                    f"{TRIGGER_URL}/{src}/{c}/",
                    headers={"X-Trigger-Secret": TRIGGER_SECRET},
                    timeout=40,
                )
        st.sidebar.success("✔ Fetch started on backend (check Cron Status).")
    except Exception as e:
        st.sidebar.error(f"Trigger error: {e}")

# Clear cache button
if st.sidebar.button("🧹 Clear Cached Data"):
    fetch_workflows_cached.clear()
    fetch_status_cached.clear()
    st.sidebar.success("Cache cleared. Data will be re-fetched on next load.")
    st.experimental_rerun()

# =========================================
# CRON STATUS
# =========================================
st.subheader("⏱ Cron / Data Refresh Status")

status = fetch_status_cached()
colA, colB, colC = st.columns(3)

if status:
    last_run = fmt_ts(status.get("last_run"))
    next_run = fmt_ts(status.get("next_run"))
    interval = status.get("interval_hours", 6)

    with colA:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Last DB Update</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{last_run}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Next Scheduled Update</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{next_run}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with colC:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Interval (hours)</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{interval}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("Could not load `/api/status/`. Check backend logs or endpoint.")

st.markdown('<hr class="hr-soft" />', unsafe_allow_html=True)

# =========================================
# LOAD WORKFLOW DATA
# =========================================
with st.spinner("📥 Fetching workflow data from backend..."):
    params = {"limit": limit}
    if platform != "All":
        params["platform"] = platform
    if country != "All":
        params["country"] = country

    df_data = fetch_workflows_cached(params)

if not df_data:
    st.error(
        "❌ Could not load data from backend. "
        "If this is after a cold start, wait a bit and click 'Clear Cached Data' in sidebar."
    )
    st.stop()

df = pd.DataFrame(df_data)

if df.empty:
    st.warning("No workflows match your current filters.")
    st.stop()

# Text search
if search_keyword:
    df = df[df["workflow"].str.contains(search_keyword, case=False, na=False)]

if df.empty:
    st.warning("No workflows after applying text search filter.")
    st.stop()

# Sorting
df = df.sort_values(by=sort_by, ascending=(order == "Ascending"))

# =========================================
# GLOBAL METRICS
# =========================================
st.subheader("📊 High-level Insights")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Total Workflows</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{len(df)}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with m2:
    avg_score = round(df["popularity_score"].mean(), 2)
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Average Popularity Score</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{avg_score}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with m3:
    platform_counts = df["platform"].value_counts()
    top_platform = platform_counts.idxmax()
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Most Active Platform</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{top_platform}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with m4:
    country_counts = df["country"].value_counts()
    top_country = country_counts.idxmax()
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Top Country (by #Workflows)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{top_country}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================
# TABS: Overview | Platforms | Details
# =========================================
tab_overview, tab_platforms, tab_details = st.tabs(
    ["📋 Overview", "🧩 Platforms Breakdown", "🔎 Workflow Evidence"]
)

# ------------------ OVERVIEW TAB ------------------
with tab_overview:
    st.markdown("### 📄 Workflow List (filtered)")
    st.dataframe(
        df[["workflow", "platform", "country", "popularity_score"]],
        use_container_width=True,
    )

    st.markdown("### 📊 Popularity Score Comparison")
    top_n = min(len(df), 40)  # avoid overcrowded chart
    df_chart = df.head(top_n)

    chart = (
        alt.Chart(df_chart)
        .mark_bar()
        .encode(
            x=alt.X("workflow:N", sort="-y", title="Workflow"),
            y=alt.Y("popularity_score:Q", title="Popularity Score"),
            color=alt.Color("platform:N", title="Platform"),
            tooltip=["workflow", "platform", "country", "popularity_score"],
        )
        .properties(height=420)
    )

    st.altair_chart(chart, use_container_width=True)

# ------------------ PLATFORMS TAB ------------------
with tab_platforms:
    st.markdown("### 🧩 Platform-wise Breakdown")

    colp1, colp2 = st.columns(2)

    with colp1:
        st.markdown("**Workflows by Platform**")
        st.bar_chart(df["platform"].value_counts())

    with colp2:
        st.markdown("**Average Score per Platform**")
        avg_by_plat = df.groupby("platform")["popularity_score"].mean().sort_values(ascending=False)
        st.dataframe(avg_by_plat.rename("avg_score").round(2))

    st.markdown("---")

    plat_choice = st.selectbox(
        "Focus on a specific platform for Top Workflows",
        ["YouTube", "Forum", "GoogleTrends"],
    )

    df_plat = df[df["platform"] == plat_choice]

    if df_plat.empty:
        st.info(f"No workflows for platform **{plat_choice}** with current filters.")
    else:
        st.markdown(f"#### ⭐ Top 10 {plat_choice} Workflows (by score)")
        st.dataframe(
            df_plat.sort_values("popularity_score", ascending=False).head(10)[
                ["workflow", "country", "popularity_score", "source_url"]
            ],
            use_container_width=True,
        )

# ------------------ DETAILS TAB ------------------
with tab_details:
    st.markdown("### 🔎 Evidence per Workflow")

    # small selectbox to jump to a single workflow
    titles = df["workflow"].unique().tolist()
    selected_title = st.selectbox("Select workflow to inspect", titles)

    df_selected = df[df["workflow"] == selected_title]

    for _, row in df_selected.iterrows():
        st.markdown("---")
        st.markdown(f"#### 📌 {row['workflow']}")
        st.markdown(
            f"""
- Platform: **{row['platform']}**
- Country: **{row['country']}**
- Source: [{row['source_url']}]({row['source_url']})
- Popularity Score: **{round(row['popularity_score'], 2)}**
            """
        )
        st.json(row["popularity_metrics"], expanded=False)

# =========================================
# FOOTER
# =========================================
st.markdown("---")
st.markdown(
    """
Built by **Bandapu Vivekananda**  
for the **SpeakGenie AI/Data Internship Technical Assignment**.  
Backend: Django + DRF on Render · Data from YouTube, n8n Forum, and Google Trends.
"""
)
