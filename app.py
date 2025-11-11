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
def get_data_dir():
    """Get the data directory path - shared by database and player data loading."""
    app_dir = Path(__file__).parent
    data_dir = app_dir / "data"
    return data_dir

@st.cache_resource
def get_engine():
    """Create SQLite connection from /data/serie_a.db relative to app.py."""
    data_dir = get_data_dir()  # Use shared path function
    db_path = data_dir / "serie_a.db"

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

@st.cache_data(ttl=3600)
def load_player_data(player_name):
    """Load player goal data from CSV in the data/ folder (same as serie_a.db)."""
    data_dir = get_data_dir()  # Use EXACT same path function as database
    
    # Convert player name to filename format: "Lautaro Martinez" -> "lautaro_martinez_goals.csv"
    player_file = data_dir / f"{player_name.lower().replace(' ', '_')}_goals.csv"
    
    if player_file.exists():
        df = pd.read_csv(player_file)
        return df
    else:
        return None

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
        
        # Inter Stats App
        with st.container():
            st.markdown("""
            <div style='padding: 2rem; border-radius: 10px; background-color: #f0f7ff; border: 2px solid #0066cc;'>
                <h2 style='color: #0066cc; margin-top: 0;'>⚫🔵 Inter Stats</h2>
                <p style='font-size: 1.1em; color: #333;'>
                    Deep dive into Inter Milan player statistics and goal analysis.<br>
                    Explore goal distributions, assist providers, and performance trends.
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
# INTER STATS APP
# ===============================================================
def show_inter_stats_app():
    # Back button
    if st.button("← Back to Home"):
        st.session_state.app_selection = None
        st.rerun()
    
    st.title("⚫🔵 Inter Milan Player Statistics")
    st.caption("Goal analysis and performance metrics for Inter players")
    st.markdown("---")
    
    # Available players - just list the names, no need to pre-convert
    available_players = [
        "Lautaro Martinez"
    ]
    
    # Player selector
    st.subheader("Select Player")
    selected_player = st.selectbox(
        "Choose a player to analyze",
        options=available_players,
        index=0
    )
    
    # Load player data - pass the actual player name, function will handle conversion
    player_data = load_player_data(selected_player)
    
    if player_data is None:
        # Show exactly where we're looking
        data_dir = get_data_dir()
        expected_file = data_dir / f"{selected_player.lower().replace(' ', '_')}_goals.csv"
        
        st.error(f"❌ No data found for {selected_player}")
        st.info(f"📁 Looking for: `{expected_file}`")
        st.info(f"📁 Data directory: `{data_dir}`")
        
        # Check if data directory exists
        if not data_dir.exists():
            st.warning(f"⚠️ Data directory does not exist: `{data_dir}`")
        else:
            st.success(f"✅ Data directory exists: `{data_dir}`")
            # List what's in the data directory
            files = list(data_dir.glob("*"))
            st.write("Files in data directory:", [f.name for f in files])
        
        st.markdown("### To fetch player data:")
        st.code("""
# Option 1: Run from scripts/Inter folder
cd scripts/Inter
python scrape_lautaro.py

# Option 2: Run from project root
python scripts/Inter/scrape_lautaro.py
        """, language="bash")
        st.info("💡 The script will automatically save data to the data/ folder (same location as serie_a.db)")
        return
    
    # Clean the data
    player_data = player_data[player_data['Season'].notna()]
    
    st.markdown("---")
    
    # ===============================================================
    # OVERVIEW METRICS
    # ===============================================================
    st.header(f"📊 {selected_player} - Career Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_goals = len(player_data)
        st.metric("Total Goals", total_goals)
    
    with col2:
        seasons = player_data['Season'].nunique()
        st.metric("Seasons", seasons)
    
    with col3:
        competitions = player_data['Competition'].nunique()
        st.metric("Competitions", competitions)
    
    with col4:
        assisted_goals = player_data['Goal_assist'].notna().sum()
        st.metric("Assisted Goals", assisted_goals)
    
    st.markdown("---")
    
    # ===============================================================
    # VISUALIZATIONS
    # ===============================================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "Goals by Season",
        "Top Assist Providers", 
        "Goal Distribution",
        "Detailed Stats"
    ])
    
    # --- Tab 1: Goals by Season ---
    with tab1:
        st.subheader("Goals per Season")
        
        season_goals = player_data.groupby('Season').size().reset_index(name='Goals')
        season_goals = season_goals.sort_values('Season')
        
        fig = px.bar(
            season_goals,
            x='Season',
            y='Goals',
            title=f"{selected_player}'s Goals per Season",
            labels={'Goals': 'Number of Goals', 'Season': 'Season'},
            text='Goals'
        )
        fig.update_traces(
            marker_color='#0066cc',
            textposition='outside'
        )
        fig.update_layout(
            template="plotly_white",
            height=500,
            xaxis=dict(tickangle=45)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Show breakdown by competition
        st.subheader("Goals by Competition")
        comp_season = player_data.groupby(['Season', 'Competition']).size().reset_index(name='Goals')
        
        fig2 = px.bar(
            comp_season,
            x='Season',
            y='Goals',
            color='Competition',
            title=f"{selected_player}'s Goals by Competition and Season",
            labels={'Goals': 'Number of Goals'},
            barmode='stack'
        )
        fig2.update_layout(
            template="plotly_white",
            height=500,
            xaxis=dict(tickangle=45)
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # --- Tab 2: Top Assist Providers ---
    with tab2:
        st.subheader("Top 15 Assist Providers")
        
        # Filter out blank/NA assists
        df_filtered = player_data[
            player_data['Goal_assist'].notna() & 
            (player_data['Goal_assist'] != "")
        ]
        
        if len(df_filtered) > 0:
            assist_counts = df_filtered.groupby('Goal_assist').size().reset_index(name='Assists')
            top_15_assists = assist_counts.sort_values(by='Assists', ascending=False).head(15)
            
            fig = px.bar(
                top_15_assists,
                x='Goal_assist',
                y='Assists',
                title=f"Top 15 Players Who Assisted {selected_player}",
                labels={'Goal_assist': 'Player', 'Assists': 'Number of Assists'},
                text='Assists'
            )
            fig.update_traces(
                marker_color='#0066cc',
                textposition='outside'
            )
            fig.update_layout(
                template="plotly_white",
                height=500,
                xaxis=dict(tickangle=45)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Show assist network
            st.markdown("**Assist Partnerships**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(
                    top_15_assists.head(10),
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Goal_assist": "Player",
                        "Assists": st.column_config.NumberColumn("Assists", format="%d")
                    }
                )
        else:
            st.info("No assist data available")
    
    # --- Tab 3: Goal Distribution ---
    with tab3:
        st.subheader("Goal Distribution Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Home vs Away
            venue_goals = player_data['Venue'].value_counts().reset_index()
            venue_goals.columns = ['Venue', 'Goals']
            venue_goals['Venue'] = venue_goals['Venue'].map({'H': 'Home', 'A': 'Away'})
            
            fig = px.pie(
                venue_goals,
                values='Goals',
                names='Venue',
                title='Goals: Home vs Away',
                color_discrete_sequence=['#0066cc', '#87CEEB']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Goals by competition type
            comp_goals = player_data['Competition'].value_counts().head(10).reset_index()
            comp_goals.columns = ['Competition', 'Goals']
            
            fig = px.pie(
                comp_goals,
                values='Goals',
                names='Competition',
                title='Goals by Competition (Top 10)'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Goals by minute range
        st.subheader("Goals by Match Minute")
        
        # Clean minute data
        player_data['Minute_clean'] = player_data['Minute'].str.replace("'", "").str.replace("+", "")
        player_data['Minute_clean'] = pd.to_numeric(player_data['Minute_clean'], errors='coerce')
        
        minute_data = player_data[player_data['Minute_clean'].notna()].copy()
        
        if len(minute_data) > 0:
            # Create bins
            bins = [0, 15, 30, 45, 60, 75, 90, 120]
            labels = ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90', '90+']
            minute_data['Minute_range'] = pd.cut(
                minute_data['Minute_clean'], 
                bins=bins, 
                labels=labels,
                include_lowest=True
            )
            
            minute_dist = minute_data['Minute_range'].value_counts().sort_index().reset_index()
            minute_dist.columns = ['Minute Range', 'Goals']
            
            fig = px.bar(
                minute_dist,
                x='Minute Range',
                y='Goals',
                title='Goals Distribution by Match Period',
                labels={'Goals': 'Number of Goals'},
                text='Goals'
            )
            fig.update_traces(marker_color='#0066cc', textposition='outside')
            fig.update_layout(template="plotly_white", height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # --- Tab 4: Detailed Stats ---
    with tab4:
        st.subheader("Recent Goals")
        
        # Show last 20 goals
        recent_goals = player_data.head(20).copy()
        
        display_cols = ['Season', 'Competition', 'Date', 'Opponent', 'Venue', 'Minute', 'Goal_assist']
        display_df = recent_goals[display_cols].copy()
        display_df['Venue'] = display_df['Venue'].map({'H': 'Home', 'A': 'Away'})
        display_df.columns = ['Season', 'Competition', 'Date', 'Opponent', 'Venue', 'Minute', 'Assist By']
        
        st.dataframe(display_df, hide_index=True, use_container_width=True)
        
        # Season breakdown
        st.subheader("Season-by-Season Breakdown")
        season_stats = player_data.groupby('Season').agg({
            'Competition': 'count',
            'Goal_assist': lambda x: x.notna().sum(),
            'Venue': lambda x: (x == 'H').sum()
        }).reset_index()
        season_stats.columns = ['Season', 'Total Goals', 'Assisted Goals', 'Home Goals']
        season_stats['Away Goals'] = season_stats['Total Goals'] - season_stats['Home Goals']
        season_stats = season_stats.sort_values('Season', ascending=False)
        
        st.dataframe(
            season_stats,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Season": "Season",
                "Total Goals": st.column_config.NumberColumn("Total Goals", format="%d"),
                "Assisted Goals": st.column_config.NumberColumn("Assisted Goals", format="%d"),
                "Home Goals": st.column_config.NumberColumn("Home Goals", format="%d"),
                "Away Goals": st.column_config.NumberColumn("Away Goals", format="%d")
            }
        )

# ===============================================================
# MAIN APP ROUTER
# ===============================================================
if st.session_state.app_selection is None:
    show_landing_page()
elif st.session_state.app_selection == "standings":
    show_standings_app()
elif st.session_state.app_selection == "inter_stats":
    show_inter_stats_app()