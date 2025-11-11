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
# DATABASE CONNECTION
# ===============================================================
def get_data_dir():
    app_dir = Path(__file__).parent
    data_dir = app_dir / "data"
    return data_dir

@st.cache_resource
def get_engine():
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
def load_standings():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM standings", engine)

@st.cache_data(ttl=3600)
def load_matches():
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM matches", engine)
    df["date"] = pd.to_datetime(df["date"])
    return df

@st.cache_data(ttl=3600)
def load_player_goals():
    engine = get_engine()
    try:
        df = pd.read_sql("SELECT * FROM player_goals", engine)
        return df
    except Exception:
        return None

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
        with st.container():
            st.markdown("""
            <div style='padding: 2rem; border-radius: 10px; background-color: #f0f7ff; border: 2px solid #1f77b4;'>
                <h2 style='color: #1f77b4;'>📊 Historical Standings</h2>
                <p>Compare Serie A standings across multiple seasons.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 Launch Historical Standings", use_container_width=True):
                st.session_state.app_selection = "standings"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        with st.container():
            st.markdown("""
            <div style='padding: 2rem; border-radius: 10px; background-color: #f0f7ff; border: 2px solid #0066cc;'>
                <h2 style='color: #0066cc;'>⚫🔵 Inter Stats</h2>
                <p>Deep dive into Inter player goal data.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 Launch Inter Stats", use_container_width=True):
                st.session_state.app_selection = "inter_stats"
                st.rerun()

# ===============================================================
# INTER STATS APP
# ===============================================================
def show_inter_stats_app():
    if st.button("← Back to Home"):
        st.session_state.app_selection = None
        st.rerun()

    st.title("⚫🔵 Inter Player Statistics")
    st.caption("Goal analysis and performance metrics for Inter players")
    st.markdown("---")

    available_players = ["Lautaro Martinez"]
    selected_player = st.selectbox("Choose Player", available_players, index=0)

    all_player_data = load_player_goals()
    if all_player_data is None:
        st.error("❌ No player data found in database")
        return

    player_data = all_player_data[all_player_data["player_name"] == selected_player]
    if len(player_data) == 0:
        st.warning(f"No data found for {selected_player}")
        return

    # --- Only keep Inter-period goals ---
    if "inter_period" in player_data.columns:
        player_data = player_data[player_data["inter_period"] == 1]

    player_data = player_data[player_data["season"].notna()]

    st.markdown("---")
    st.header(f"📊 {selected_player} – Career Overview (Inter Only)")

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

    # ===============================================================
    # GOAL CONTEXT CLASSIFICATION
    # ===============================================================
    def classify_goal(row):
        """Infer match situation (Opening, Equalizer, Lead, etc.)"""
        at_score = row.get("at_score")
        result = row.get("result")
        if pd.isna(at_score) or ":" not in str(at_score):
            return "Unknown"
        try:
            team_goals, opp_goals = map(int, at_score.split(":"))
        except Exception:
            return "Unknown"

        if team_goals == 0 and opp_goals == 0:
            return "Opening Goal"
        elif team_goals < opp_goals:
            return "Equalizer"
        elif team_goals == opp_goals:
            return "In vantaggio dopo un pareggio"
        elif team_goals > opp_goals:
            if isinstance(result, str) and ":" in result:
                try:
                    final_team, final_opp = map(int, result.split(":"))
                    if final_team < final_opp:
                        return "Consolation Goal"
                except Exception:
                    pass
            return "Goal While Leading"
        else:
            return "Unknown"

    player_data["goal_context"] = player_data.apply(classify_goal, axis=1)

    # ===============================================================
    # VISUAL TABS
    # ===============================================================
    tab1, tab2, tab3 = st.tabs(["Goals by Season", "Assist Providers", "Goal Distribution"])

    # --- Tab 1: Goals per season ---
    with tab1:
        season_goals = player_data.groupby("season").size().reset_index(name="Goals")
        fig = px.bar(
            season_goals, x="season", y="Goals",
            title=f"{selected_player}'s Goals per Season (Inter)",
            text="Goals", color_discrete_sequence=["#0066cc"]
        )
        fig.update_layout(template="plotly_white", height=450)
        st.plotly_chart(fig, use_container_width=True)

    # --- Tab 2: Top assists ---
    with tab2:
        df_assists = player_data[
            player_data["goal_assist"].notna() & (player_data["goal_assist"] != "")
        ]
        if len(df_assists) > 0:
            assists = df_assists.groupby("goal_assist").size().reset_index(name="Count")
            top15 = assists.sort_values("Count", ascending=False).head(15)
            fig = px.bar(top15, x="goal_assist", y="Count", title="Top Assist Providers",
                         text="Count", color_discrete_sequence=["#0066cc"])
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No assist data available")

    # --- Tab 3: Goal distribution and context ---
    with tab3:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🏠 Venue Distribution")
            venue = player_data["venue"].map({"H": "Home", "A": "Away"}).value_counts().reset_index()
            venue.columns = ["Venue", "Goals"]
            fig = px.pie(venue, names="Venue", values="Goals",
                         color_discrete_sequence=["#0066cc", "#87CEEB"])
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("🎯 Goal Context (Match Situation)")
            ctx = player_data["goal_context"].value_counts().reset_index()
            ctx.columns = ["Context", "Goals"]
            fig = px.pie(ctx, names="Context", values="Goals",
                         color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🕒 Goals by Match Minute")
        player_data["minute_clean"] = player_data["minute"].str.replace("'", "").str.replace("+", "")
        player_data["minute_clean"] = pd.to_numeric(player_data["minute_clean"], errors="coerce")

        minute_data = player_data[player_data["minute_clean"].notna()]
        bins = [0, 15, 30, 45, 60, 75, 90, 120]
        labels = ["0-15", "16-30", "31-45", "46-60", "61-75", "76-90", "90+"]
        minute_data["minute_range"] = pd.cut(minute_data["minute_clean"], bins=bins, labels=labels)
        minute_dist = minute_data["minute_range"].value_counts().sort_index().reset_index()
        minute_dist.columns = ["Minute Range", "Goals"]
        fig = px.bar(minute_dist, x="Minute Range", y="Goals",
                     title="Goals by Match Period", text="Goals",
                     color_discrete_sequence=["#0066cc"])
        fig.update_layout(template="plotly_white", height=400)
        st.plotly_chart(fig, use_container_width=True)

# ===============================================================
# MAIN ROUTER
# ===============================================================
if "app_selection" not in st.session_state:
    st.session_state.app_selection = None

if st.session_state.app_selection is None:
    show_landing_page()
elif st.session_state.app_selection == "standings":
    st.write("📊 Standings app (unchanged).")
elif st.session_state.app_selection == "inter_stats":
    show_inter_stats_app()
