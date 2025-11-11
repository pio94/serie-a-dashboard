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
if 'app_selection' not in st.session_state:
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
    df['date'] = pd.to_datetime(df['date'])
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
        <p style='text-align: center; font-size: 1.2em; color: #666;'>
            Explore historical data and team statistics
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
                    Compare Serie A standings across multiple seasons (2009-2025).<br>
                    Track team performance, analyze points distribution, and visualize championship races.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 Launch Historical Standings", use_container_width=True, type="primary"):
                st.session_state.app_selection = "standings"
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Inter Stats App (Coming Soon)
        with st.container():
            st.markdown("""
            <div style='padding: 2rem; border-radius: 10px; background-color: #f5f5f5; border: 2px solid #999;'>
                <h2 style='color: #666; margin-top: 0;'>⚫🔵 Inter Stats</h2>
                <p style='font-size: 1.1em; color: #666;'>
                    Deep dive into Inter Milan's performance metrics, player statistics, and historical achievements.
                </p>
                <p style='font-style: italic; color: #999;'>🚧 Work in Progress</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.button("🔒 Coming Soon", use_container_width=True, disabled=True)
    
    # Footer
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; color: #999; font-size: 0.9em;'>
        Data Source: <a href='https://football-data.co.uk' target='_blank'>football-data.co.uk</a> | 
        Made with ❤️ using Streamlit and Plotly
    </div>
    """, unsafe_allow_html=True)

# ===============================================================
# HISTORICAL STANDINGS APP
# ===============================================================
def show_standings_app():
    # Back button
    if st.button("← Back to Home"):
        st.session_state.app_selection = None
        st.rerun()
    
    # Load data
    standings = load_standings()
    matches = load_matches()
    
    # Basic info
    available_seasons = sorted(standings['season'].unique())
    max_matchday = int(standings['matchday'].max())
    
    # ===============================================================
    # TITLE & INTRO
    # ===============================================================
    st.title("⚽ Serie A Historical Standings")
    st.caption(f"Seasons: {available_seasons[0]} → {available_seasons[-1]} | "
               f"Total matchdays: {max_matchday}")
    
    st.markdown("Compare standings, points, and team trajectories across Serie A seasons.")
    st.markdown("---")
    
    # ===============================================================
    # FILTERS (ON MAIN PAGE)
    # ===============================================================
    st.subheader("🎯 Comparison Settings")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        matchday = st.slider(
            "Select Matchday",
            min_value=1,
            max_value=max_matchday,
            value=11,
            help="Choose which matchday to compare across seasons"
        )
    
    with col2:
        default_seasons = available_seasons[-5:] if len(available_seasons) >= 5 else available_seasons
        selected_seasons = st.multiselect(
            "Select Seasons to Compare",
            options=available_seasons,
            default=default_seasons,
            help="Select multiple seasons to compare"
        )
    
    st.markdown("---")
    
    # ===============================================================
    # MAIN CONTENT
    # ===============================================================
    if selected_seasons:
        filtered_standings = standings[
            (standings['matchday'] == matchday) &
            (standings['season'].isin(selected_seasons))
        ]
        
        # --- TABLE COMPARISON SECTION ---
        st.header(f"📊 Standings at Matchday {matchday}")
        st.subheader("Top 10 Teams per Season")
        
        cols = st.columns(len(selected_seasons))
        for idx, season in enumerate(sorted(selected_seasons)):
            with cols[idx]:
                st.markdown(f"**{season}**")
                season_data = (
                    filtered_standings[filtered_standings['season'] == season]
                    .sort_values('position')
                    .head(10)
                )
                
                display_df = season_data[['position', 'team', 'points', 'goal_diff']].copy()
                display_df.columns = ['Pos', 'Team', 'Pts', 'GD']
                
                st.dataframe(display_df, hide_index=True, height=400)
        
        # ===============================================================
        # VISUALIZATIONS
        # ===============================================================
        st.markdown("---")
        st.header("📈 Visual Analysis")
        
        tab1, tab2, tab3 = st.tabs(["Points Distribution", "Team Tracker", "Top Teams Evolution"])
        
        # --- Tab 1: Points Distribution ---
        with tab1:
            st.subheader(f"Points Distribution at Matchday {matchday}")
            fig = px.box(
                filtered_standings,
                x='season',
                y='points',
                title=f'Points Distribution at Matchday {matchday}',
                labels={'points': 'Points', 'season': 'Season'}
            )
            fig.update_layout(
                xaxis=dict(tickangle=45),
                template="plotly_white",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # --- Tab 2: Team Tracker ---
        with tab2:
            st.subheader("Track a Specific Team")
            
            available_teams = sorted(filtered_standings['team'].unique())
            selected_team = st.selectbox("Select Team", available_teams)
            
            if selected_team:
                team_trajectory = standings[
                    (standings['team'] == selected_team) &
                    (standings['season'].isin(selected_seasons))
                ]
                
                fig = go.Figure()
                for season in sorted(selected_seasons):
                    season_data = team_trajectory[team_trajectory['season'] == season]
                    fig.add_trace(go.Scatter(
                        x=season_data['matchday'],
                        y=season_data['position'],
                        mode='lines+markers',
                        name=season,
                        line=dict(width=2)
                    ))
                
                fig.update_layout(
                    title=f"{selected_team}'s League Position Throughout Selected Seasons",
                    xaxis_title="Matchday",
                    yaxis_title="Position (1 = Top)",
                    yaxis=dict(autorange="reversed"),
                    hovermode='x unified',
                    height=500
                )
                
                fig.add_vline(
                    x=matchday, line_dash="dash", line_color="red",
                    annotation_text=f"MD {matchday}"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Stats overview
                st.markdown(f"**{selected_team} at Matchday {matchday}:**")
                team_md_stats = filtered_standings[filtered_standings['team'] == selected_team]
                
                if not team_md_stats.empty:
                    cols = st.columns(len(selected_seasons))
                    for idx, season in enumerate(sorted(selected_seasons)):
                        season_stats = team_md_stats[team_md_stats['season'] == season]
                        if not season_stats.empty:
                            with cols[idx]:
                                stats = season_stats.iloc[0]
                                st.metric(f"{season}",
                                          f"Position: {int(stats['position'])}",
                                          f"{int(stats['points'])} pts")
                                st.caption(
                                    f"W:{int(stats['won'])} D:{int(stats['drawn'])} "
                                    f"L:{int(stats['lost'])} | GD:{int(stats['goal_diff'])}"
                                )
        
        # --- Tab 3: Top Teams Evolution ---
        with tab3:
            st.subheader("Championship Race Evolution")
            
            top_n = st.slider("Track top N teams", 1, 10, 4)
            
            top_teams_at_md = filtered_standings[filtered_standings['position'] <= top_n]['team'].unique()
            
            selected_race_season = st.selectbox(
                "Select Season for Race Visualization",
                sorted(selected_seasons, reverse=True)
            )
            
            race_data = standings[
                (standings['season'] == selected_race_season) &
                (standings['team'].isin(top_teams_at_md))
            ]
            
            fig = go.Figure()
            for team in sorted(race_data['team'].unique()):
                team_data = race_data[race_data['team'] == team].sort_values('matchday')
                fig.add_trace(go.Scatter(
                    x=team_data['matchday'],
                    y=team_data['points'],
                    mode='lines+markers',
                    name=team,
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                title=f"Points Accumulation – {selected_race_season} (Top {top_n} teams at MD {matchday})",
                xaxis_title="Matchday",
                yaxis_title="Total Points",
                hovermode='x unified',
                height=500
            )
            
            fig.add_vline(
                x=matchday, line_dash="dash", line_color="red",
                annotation_text=f"MD {matchday}"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # ===============================================================
        # SUMMARY STATS
        # ===============================================================
        st.markdown("---")
        st.header("📉 Summary Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_leader_pts = filtered_standings[filtered_standings['position'] == 1]['points'].mean()
            st.metric("Avg Leader Points", f"{avg_leader_pts:.1f}")
        
        with col2:
            avg_top4_pts = filtered_standings[filtered_standings['position'] <= 4]['points'].mean()
            st.metric("Avg Top 4 Points", f"{avg_top4_pts:.1f}")
        
        with col3:
            max_pts = filtered_standings['points'].max()
            st.metric("Highest Points", int(max_pts))
        
        with col4:
            total_teams = filtered_standings['team'].nunique()
            st.metric("Unique Teams", total_teams)
    
    else:
        st.warning("⚠️ Please select at least one season to compare")

# ===============================================================
# MAIN APP ROUTER
# ===============================================================
if st.session_state.app_selection is None:
    show_landing_page()
elif st.session_state.app_selection == "standings":
    show_standings_app()