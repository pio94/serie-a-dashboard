import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ===============================================================
# PAGE CONFIG
# ===============================================================
st.set_page_config(
    page_title="Serie A Analytics",
    page_icon="⚽",
    layout="wide"
)

# Hide sidebar completely
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

# ===============================================================
# SESSION STATE INITIALIZATION
# ===============================================================
if "app_selection" not in st.session_state:
    st.session_state.app_selection = None

# ===============================================================
# DATABASE CONNECTION
# ===============================================================
def get_data_dir():
    """Locate the data folder (shared by database and CSVs)."""
    return Path(__file__).parent / "data"

@st.cache_resource
def get_engine():
    """Connect to the SQLite database in /data/serie_a.db."""
    data_dir = get_data_dir()
    db_path = data_dir / "serie_a.db"

    if not db_path.exists():
        st.error(f"❌ Database not found at: {db_path}")
        st.stop()

    return create_engine(f"sqlite:///{db_path}")

# ===============================================================
# DATA LOADERS
# ===============================================================
@st.cache_data(ttl=3600)
def load_table(name: str):
    """Generic cached loader for any DB table."""
    engine = get_engine()
    try:
        return pd.read_sql(f"SELECT * FROM {name}", engine)
    except Exception as e:
        st.warning(f"⚠️ Could not load table '{name}': {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_standings():
    df = load_table("standings")
    if not df.empty and "matchday" in df.columns:
        df["matchday"] = pd.to_numeric(df["matchday"], errors="coerce")
    return df

@st.cache_data(ttl=3600)
def load_matches():
    df = load_table("matches")
    if not df.empty and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

@st.cache_data(ttl=3600)
def load_player_goals():
    """Load player goal data (used in Inter Stats)."""
    return load_table("player_goals")

# ===============================================================
# LANDING PAGE
# ===============================================================
def show_landing_page():
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <h1 style='text-align: center; color: #1f77b4;'>⚽ Serie A Analytics Hub</h1>
        <p style='text-align: center; font-size: 1.2em; color: #666;'>
            Explore historical data and team statistics
        </p>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Historical Standings
        with st.container():
            st.markdown("""
            <div style='padding: 2rem; border-radius: 10px; background-color: #f0f7ff; border: 2px solid #1f77b4;'>
                <h2 style='color: #1f77b4;'>📊 Historical Standings</h2>
                <p>Compare Serie A standings across multiple seasons (2009–2025).
                Track team performance, analyze points distribution, and visualize championship races.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 Launch Historical Standings", use_container_width=True):
                st.session_state.app_selection = "standings"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Inter Stats
        with st.container():
            st.markdown("""
            <div style='padding: 2rem; border-radius: 10px; background-color: #f0f7ff; border: 2px solid #0066cc;'>
                <h2 style='color: #0066cc;'>⚫🔵 Inter Stats</h2>
                <p>Deep dive into Inter Milan player statistics and goal analysis.
                Explore goal distributions, assist providers, and performance trends.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 Launch Inter Stats", use_container_width=True):
                st.session_state.app_selection = "inter_stats"
                st.rerun()

# ===============================================================
# HISTORICAL STANDINGS APP
# ===============================================================
def show_standings_app():
    if st.button("← Back to Home"):
        st.session_state.app_selection = None
        st.rerun()

    standings = load_standings()
    matches = load_matches()

    if standings.empty:
        st.error("❌ No standings data found.")
        return

    available_seasons = sorted(standings["season"].dropna().unique())
    max_matchday = int(standings["matchday"].max())

    st.title("⚽ Serie A Historical Standings")
    st.caption(f"Seasons: {available_seasons[0]} → {available_seasons[-1]} | Matchdays: {max_matchday}")
    st.markdown("Compare standings, points, and team trajectories across Serie A seasons.")
    st.markdown("---")

    st.subheader("🎯 Comparison Settings")
    col1, col2 = st.columns([1, 2])

    with col1:
        matchday = st.slider("Select Matchday", 1, max_matchday, 11)

    with col2:
        default_seasons = available_seasons[-5:] if len(available_seasons) >= 5 else available_seasons
        selected_seasons = st.multiselect("Select Seasons to Compare", options=available_seasons, default=default_seasons)

    st.markdown("---")

    if selected_seasons:
        filtered = standings[
            (standings["matchday"] == matchday) &
            (standings["season"].isin(selected_seasons))
        ]

        st.header(f"📊 Standings at Matchday {matchday}")
        cols = st.columns(len(selected_seasons))
        for i, season in enumerate(sorted(selected_seasons)):
            with cols[i]:
                season_data = (
                    filtered[filtered["season"] == season]
                    .sort_values("position")
                    .head(10)
                )
                display_df = season_data[["position", "team", "points", "goal_diff"]].rename(
                    columns={"position": "Pos", "team": "Team", "points": "Pts", "goal_diff": "GD"}
                )
                st.markdown(f"**{season}**")
                st.dataframe(display_df, hide_index=True, height=400)

        st.markdown("---")
        st.header("📈 Points Distribution")
        fig = px.box(filtered, x="season", y="points", template="plotly_white", height=500)
        fig.update_layout(xaxis=dict(tickangle=45))
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("⚠️ Please select at least one season to compare")

# ===============================================================
# INTER STATS APP (FILTERED TO INTER ERA)
# ===============================================================
def show_inter_stats_app():
    if st.button("← Back to Home"):
        st.session_state.app_selection = None
        st.rerun()

    st.title("⚫🔵 Inter Milan Player Statistics")
    st.caption("Goal analysis and performance metrics for Inter players")
    st.markdown("---")

    all_player_data = load_player_goals()
    if all_player_data.empty:
        st.error("❌ No player data found in database.")
        return

    selected_player = st.selectbox("Select Player", ["Lautaro Martinez"], index=0)

    player_data = all_player_data[all_player_data["player_name"] == selected_player].copy()

    # --- Keep only Inter competitions (since July 2018) ---
    inter_competitions = [
        "Serie A", "Coppa Italia", "UEFA Champions League",
        "UEFA Europa League", "Supercoppa Italiana", "UEFA Super Cup"
    ]
    player_data = player_data[
        player_data["competition"].str.contains("|".join(inter_competitions), case=False, na=False)
    ]

    # --- Optional date filter (joined 4 July 2018) ---
    if "date" in player_data.columns:
        player_data["date"] = pd.to_datetime(player_data["date"], errors="coerce", format="%d/%m/%y")
        player_data = player_data[player_data["date"] >= "2018-07-04"]

    if player_data.empty:
        st.warning("⚠️ No Inter Milan data found for this player.")
        return

    st.caption(f"Filtered to Inter Milan period – {len(player_data)} goals since 4 July 2018")
    st.markdown("---")

    # === Overview metrics ===
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Goals", len(player_data))
    with col2:
        st.metric("Seasons", player_data["season"].nunique())
    with col3:
        st.metric("Competitions", player_data["competition"].nunique())
    with col4:
        st.metric("Assisted Goals", player_data["goal_assist"].notna().sum())

    st.markdown("---")

    # === Goals by Season ===
    tab1, tab2, tab3 = st.tabs(["Goals by Season", "Assist Providers", "Goal Distribution"])

    with tab1:
        season_goals = player_data.groupby("season").size().reset_index(name="Goals")
        fig = px.bar(season_goals, x="season", y="Goals", text="Goals", template="plotly_white")
        fig.update_traces(marker_color="#0066cc", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        df_filtered = player_data[player_data["goal_assist"].notna() & (player_data["goal_assist"] != "")]
        if not df_filtered.empty:
            top_assists = (
                df_filtered.groupby("goal_assist")
                .size().reset_index(name="Assists")
                .sort_values("Assists", ascending=False).head(10)
            )
            fig = px.bar(top_assists, x="goal_assist", y="Assists", text="Assists", template="plotly_white")
            fig.update_traces(marker_color="#0066cc", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No assist data available")

    with tab3:
        player_data["minute_clean"] = (
            player_data["minute"].str.replace("'", "").str.replace("+", "")
        )
        player_data["minute_clean"] = pd.to_numeric(player_data["minute_clean"], errors="coerce")
        minute_data = player_data[player_data["minute_clean"].notna()]
        if not minute_data.empty:
            bins = [0, 15, 30, 45, 60, 75, 90, 120]
            labels = ["0–15", "16–30", "31–45", "46–60", "61–75", "76–90", "90+"]
            minute_data["minute_range"] = pd.cut(minute_data["minute_clean"], bins=bins, labels=labels)
            minute_dist = minute_data["minute_range"].value_counts().sort_index().reset_index()
            minute_dist.columns = ["Minute Range", "Goals"]
            fig = px.bar(minute_dist, x="Minute Range", y="Goals", text="Goals", template="plotly_white")
            fig.update_traces(marker_color="#0066cc", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

# ===============================================================
# MAIN ROUTER
# ===============================================================
if st.session_state.app_selection is None:
    show_landing_page()
elif st.session_state.app_selection == "standings":
    show_standings_app()
elif st.session_state.app_selection == "inter_stats":
    show_inter_stats_app()
