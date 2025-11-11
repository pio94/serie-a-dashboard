"""
Main Streamlit app for Serie A Dashboard.

The Lautaro Martínez player statistics page is currently
marked as "Work in progress" while goal data and context
variables are being revalidated.
"""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path


# ===============================================================
# Database connection helper
# ===============================================================
def get_engine():
    """Return SQLAlchemy engine for the Serie A database."""
    project_root = Path(__file__).resolve().parents[1]
    db_path = project_root / "data" / "serie_a.db"
    if not db_path.exists():
        st.error(f"❌ Database not found at {db_path}")
        st.stop()
    return create_engine(f"sqlite:///{db_path}")


# ===============================================================
# Home Page
# ===============================================================
def show_home():
    st.title("⚽ Serie A Analytics Dashboard")
    st.markdown("Explore Inter Milan player performance, match data, and more.")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏟️ Serie A Standings")
        st.markdown("Check the latest table and points by team.")
        if st.button("View Standings"):
            st.session_state.app_selection = "standings"
            st.rerun()

    with col2:
        st.subheader("⚫🔵 Inter Player Stats")
        st.caption("🚧 Work in progress — data validation ongoing.")
        st.markdown("Compare Lautaro Martínez's goals, minutes, and match context.")
        if st.button("View Lautaro Stats"):
            st.session_state.app_selection = "inter_stats"
            st.rerun()


# ===============================================================
# Standings Page
# ===============================================================
def show_standings():
    if st.button("← Back to Home"):
        st.session_state.app_selection = None
        st.rerun()

    st.title("🏆 Serie A Standings")

    try:
        engine = get_engine()
        df = pd.read_sql("SELECT * FROM league_standings", engine)
        if not df.empty:
            st.dataframe(df)
        else:
            st.warning("No standings data found in the database.")
    except Exception as e:
        st.error(f"Error loading standings: {e}")


# ===============================================================
# Lautaro Martínez Page (Work in Progress)
# ===============================================================
def show_inter_stats_app():
    """Temporarily disable player stats while validating numbers."""
    if st.button("← Back to Home"):
        st.session_state.app_selection = None
        st.rerun()

    st.title("⚫🔵 Inter Milan Player Statistics")
    st.caption("🚧 Work in progress — data validation ongoing.")
    st.markdown("---")

    st.info("""
    We're currently improving:
    - Goal event parsing and match context classification  
    - Season alignment and pre-/post-Inter filtering  
    - Aggregated stats across Serie A, Coppa Italia, and Europe  

    Please check back soon for the updated version.
    """)

    # Optional: show recent data sample
    try:
        engine = get_engine()
        df = pd.read_sql(
            "SELECT * FROM player_goals WHERE player_name = 'Lautaro Martinez' ORDER BY date DESC",
            engine
        )
        if not df.empty:
            st.write("### Latest goal entries")
            st.dataframe(df.head(10))
        else:
            st.warning("No goal data found for Lautaro Martínez in the database.")
    except Exception as e:
        st.error(f"Database error: {e}")


# ===============================================================
# Main Navigation
# ===============================================================
def main():
    if "app_selection" not in st.session_state:
        st.session_state.app_selection = None

    st.sidebar.title("⚽ Navigation")
    choice = st.sidebar.radio(
        "Go to:",
        ("Home", "Standings", "Inter Player Stats"),
        index=0 if st.session_state.app_selection is None else
        ["Home", "Standings", "Inter Player Stats"].index(
            "Inter Player Stats" if st.session_state.app_selection == "inter_stats"
            else st.session_state.app_selection
        )
    )

    if choice == "Home":
        show_home()
    elif choice == "Standings":
        show_standings()
    elif choice == "Inter Player Stats":
        show_inter_stats_app()


if __name__ == "__main__":
    main()
