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
        [data-testid="collapsedControl"] {
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
@st.cache_resource
def get_engine():
    """Create SQLite connection from /data/serie_a.db relative to app.py."""
    app_dir = Path(__file__).parent
    db_path = app_dir / "data" / "serie_a.db"

    if not db_path.exists():
        st.error(f"❌ Database not found at: {db_path}")
        st.stop()

    return create_engine(f"sqlite:///{db_path}")

# ===============================================================
# DATA LOADING (CACHED FOR PERFORMANCE)
# ===============================================================
@st.cache_data(ttl=3600)
def load_standings():
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM standings", engine)
    return df


@st.cache_data(ttl=3600)
def load_matches():
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM matches", engine)
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(ttl=3600)
def load_player_data(player_file_base: str):
    """
    Load player goal data (e.g., Lautaro Martinez) from /data/ relative to app.py.
    Expected filename format: 'lautaro_martinez_goals.csv'
    """
    app_dir = Path(__file__).parent
    data_dir = app_dir / "data"
    player_path = data_dir / f"{player_file_base}_goals.csv"

    if not player_path.exists():
        st.error(f"❌ Player data file not found at: {player_path}")
        return None

    try:
        df = pd.read_csv(player_path)
    except Exception as e:
        st.error(f"⚠️ Could not read file: {player_path}\n\n{e}")
        return None

    st.success(f"Loaded {len(df)} goal records from {player_path.name}")
    return df

# ===============================================================
# LANDING PAGE
# ===============================================================
def show_landing_page():
    st.markdown("<br>", unsafe_allow_html=True)

    # Title
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <h1 style='text-align: center; color: #1f77b4;'>
            ⚽ Serie A Analytics Hub
        </h1>
        <p style='text-align: center; font-size: 1.2em; color: #555;'>
            Explore Italy’s top flight through interactive data on team and player performance.<br>
            Compare seasons, analyze trends, and dive into Inter Milan’s star players.
        </p>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # App selection cards
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Historical Standings App
        with st.container():
            st.markdown("""
            <div style='padding: 2rem; border-radius: 10px; background-color: #f0f7ff; border: 2px solid #1f77b4;'>
                <h2 style='color: #1f77b4; margin-top: 0;'>📊 Historical Standings</h2>
                <p style='font-size: 1.1em; color: #333;'>
                    Compare Serie A standings across multiple seasons (2009–2025).<br>
                    Track team trajectories, analyze points distributions, and follow title races.
                </p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🚀 Launch Historical Standings", use_container_width=True, type="primary"):
                st.session_state.app_selection = "standings"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Inter Stats App
        with st.container():
            st.markdown("""
            <div style='padding: 2rem; border-radius: 10px; background-color: #f0f7ff; border: 2px solid #0066cc;'>
                <h2 style='color: #0066cc; margin-top: 0;'>⚫🔵 Inter Stats</h2>
                <p style='font-size: 1.1em; color: #333;'>
                    Explore Inter Milan’s player performances across seasons — goals, assists, and match data.<br>
                    Currently featuring Lautaro Martínez, with more players coming soon.
                </p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🚀 Launch Inter Stats", use_container_width=True, type="primary"):
                st.session_state.app_selection = "inter_stats"
                st.rerun()

    # Footer
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; color: #999; font-size: 0.9em;'>
        Data Sources: <a href='https://football-data.co.uk' target='_blank'>football-data.co.uk</a> and public archives | 
        Made with ❤️ using Streamlit + Plotly
    </div>
    """, unsafe_allow_html=True)

# ===============================================================
# HISTORICAL STANDINGS APP
# ===============================================================
def show_standings_app():
    if st.button("← Back to Home"):
        st.session_state.app_selection = None
        st.rerun()

    standings = load_standings()
    matches = load_matches()
    available_seasons = sorted(standings["season"].unique())
    max_matchday = int(standings["matchday"].max())

    st.title("📊 Serie A Historical Standings")
    st.caption(f"Seasons: {available_seasons[0]} → {available_seasons[-1]}  |  Matchdays: {max_matchday}")
    st.markdown("Analyze team performance and league dynamics across Serie A seasons.")
    st.markdown("---")

    st.subheader("🎯 Comparison Settings")

    col1, col2 = st.columns([1, 2])
    with col1:
        matchday = st.slider("Select Matchday", 1, max_matchday, 11)
    with col2:
        default_seasons = available_seasons[-5:] if len(available_seasons) >= 5 else available_seasons
        selected_seasons = st.multiselect(
            "Select Seasons to Compare", options=available_seasons, default=default_seasons
        )

    st.markdown("---")

    if not selected_seasons:
        st.warning("⚠️ Please select at least one season to compare.")
        return

    filtered_standings = standings[
        (standings["matchday"] == matchday)
        & (standings["season"].isin(selected_seasons))
    ]

    # --- Table comparison section ---
    st.header(f"📋 Standings at Matchday {matchday}")
    st.subheader("Top 10 Teams per Season")

    cols = st.columns(len(selected_seasons))
    for idx, season in enumerate(sorted(selected_seasons)):
        with cols[idx]:
            st.markdown(f"**{season}**")
            season_data = (
                filtered_standings[filtered_standings["season"] == season]
                .sort_values("position")
                .head(10)
            )
            display_df = season_data[["position", "team", "points", "goal_diff"]].copy()
            display_df.columns = ["Pos", "Team", "Pts", "GD"]
            st.dataframe(display_df, hide_index=True, height=400)

    # --- Visualizations ---
    st.markdown("---")
    st.header("📈 Visual Analysis")

    tab1, tab2, tab3 = st.tabs(["Points Distribution", "Team Tracker", "Top Teams Evolution"])

    # Tab 1: Points Distribution
    with tab1:
        fig = px.box(
            filtered_standings,
            x="season",
            y="points",
            title=f"Points Distribution at Matchday {matchday}",
            labels={"points": "Points", "season": "Season"},
        )
        fig.update_layout(xaxis=dict(tickangle=45), template="plotly_white", height=500)
        st.plotly_chart(fig, use_container_width=True)

    # Tab 2: Team Tracker
    with tab2:
        st.subheader("Track a Specific Team")
        available_teams = sorted(filtered_standings["team"].unique())
        selected_team = st.selectbox("Select Team", available_teams)

        if selected_team:
            team_trajectory = standings[
                (standings["team"] == selected_team)
                & (standings["season"].isin(selected_seasons))
            ]

            fig = go.Figure()
            for season in sorted(selected_seasons):
                season_data = team_trajectory[team_trajectory["season"] == season]
                fig.add_trace(
                    go.Scatter(
                        x=season_data["matchday"],
                        y=season_data["position"],
                        mode="lines+markers",
                        name=season,
                        line=dict(width=2),
                    )
                )

            fig.update_layout(
                title=f"{selected_team} – League Position Over Seasons",
                xaxis_title="Matchday",
                yaxis_title="Position (1 = Top)",
                yaxis=dict(autorange="reversed"),
                hovermode="x unified",
                height=500,
            )
            fig.add_vline(x=matchday, line_dash="dash", line_color="red", annotation_text=f"MD {matchday}")
            st.plotly_chart(fig, use_container_width=True)

    # Tab 3: Top Teams Evolution
    with tab3:
        st.subheader("Championship Race Evolution")
        top_n = st.slider("Track top N teams", 1, 10, 4)
        top_teams_at_md = filtered_standings[filtered_standings["position"] <= top_n]["team"].unique()
        selected_race_season = st.selectbox("Select Season", sorted(selected_seasons, reverse=True))

        race_data = standings[
            (standings["season"] == selected_race_season)
            & (standings["team"].isin(top_teams_at_md))
        ]

        fig = go.Figure()
        for team in sorted(race_data["team"].unique()):
            team_data = race_data[race_data["team"] == team].sort_values("matchday")
            fig.add_trace(
                go.Scatter(
                    x=team_data["matchday"],
                    y=team_data["points"],
                    mode="lines+markers",
                    name=team,
                    line=dict(width=2),
                )
            )

        fig.update_layout(
            title=f"Points Accumulation – {selected_race_season} (Top {top_n})",
            xaxis_title="Matchday",
            yaxis_title="Total Points",
            hovermode="x unified",
            height=500,
        )
        fig.add_vline(x=matchday, line_dash="dash", line_color="red", annotation_text=f"MD {matchday}")
        st.plotly_chart(fig, use_container_width=True)

# ===============================================================
# INTER STATS APP
# ===============================================================
def show_inter_stats_app():
    if st.button("← Back to Home"):
        st.session_state.app_selection = None
        st.rerun()

    st.title("⚫🔵 Inter Milan Player Statistics")
    st.caption("Goal analysis and performance metrics for Inter players")
    st.markdown("---")

    # Available players
    available_players = {
        "Lautaro Martínez": "lautaro_martinez",
    }

    st.subheader("Select Player")
    selected_player = st.selectbox(
        "Choose a player to analyze", options=list(available_players.keys()), index=0
    )

    player_data = load_player_data(available_players[selected_player])
    if player_data is None:
        st.info("💡 Run `scripts/Inter/scrape_lautaro.py` to fetch player data and store it in /data.")
        return

    player_data = player_data[player_data["Season"].notna()]
    st.header(f"📊 {selected_player} – Career Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Goals", len(player_data))
    with col2:
        st.metric("Seasons", player_data["Season"].nunique())
    with col3:
        st.metric("Competitions", player_data["Competition"].nunique())
    with col4:
        st.metric("Assisted Goals", player_data["Goal_assist"].notna().sum())

    # Simple bar chart by season
    st.markdown("---")
    st.subheader("Goals per Season")
    season_goals = player_data.groupby("Season").size().reset_index(name="Goals")
    fig = px.bar(season_goals, x="Season", y="Goals", text="Goals", title=f"{selected_player} – Goals per Season")
    fig.update_traces(marker_color="#0066cc", textposition="outside")
    fig.update_layout(template="plotly_white", height=500, xaxis=dict(tickangle=45))
    st.plotly_chart(fig, use_container_width=True)

# ===============================================================
# MAIN APP ROUTER
# ===============================================================
if st.session_state.app_selection is None:
    show_landing_page()
elif st.session_state.app_selection == "standings":
    show_standings_app()
elif st.session_state.app_selection == "inter_stats":
    show_inter_stats_app()
