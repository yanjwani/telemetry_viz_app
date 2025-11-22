import streamlit as st
import pandas as pd
import fastf1 as f1
import fastf1.plotting
import plotly.graph_objects as go

# ---------------------------------------------------------
# Page setup
# ---------------------------------------------------------
st.set_page_config(page_title="F1 Telemetry App", layout="wide")
st.title("🏎️ Lap Telemetry")

# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------
@st.cache_data(show_spinner=True)
def get_race_schedule(year):
    # Fetch race schedule for a given year.
    return f1.get_event_schedule(year)

@st.cache_data(show_spinner=True)
def load_session(year, race_name, session_type):
    # Load a FastF1 session (cached).
    session = f1.get_session(year, race_name, session_type)
    session.load()
    return session

def get_driver_color(driver_code, session):
    # Return the official team color for a driver.
    return fastf1.plotting.get_driver_color(driver_code, session)

def format_laptime(td):
    if pd.isnull(td):
        return "N/A"
    total_seconds = td.total_seconds()
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:06.3f}"

# ---------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------
with st.sidebar:
    st.header("Session Selection")
    year = st.number_input("Year", min_value=2015, max_value=2025, value=2025)
    schedule = get_race_schedule(year)
    race_name = st.selectbox("Race", schedule["EventName"].tolist())
    session_type = st.selectbox("Session", ["R", "Q", "FP1", "FP2", "FP3"])


session = load_session(year, race_name, session_type)
session_drivers = session.results["Abbreviation"].tolist()

col1, col2 = st.columns(2)
with col1:
    driver1 = st.selectbox("Driver 1", session_drivers, key="d1")
with col2:
    driver2 = st.selectbox("Driver 2", session_drivers, key="d2")

if driver1 and driver2:
    # Get driver laps
    laps_d1 = session.laps.pick_drivers(driver1)
    laps_d2 = session.laps.pick_drivers(driver2)

    compare_fastest_lap =st.toggle("Compare Fastest Lap", value=True)

    if compare_fastest_lap:
        lap_d1 = laps_d1.pick_fastest()
        lap_d2 = laps_d2.pick_fastest()
    else:
        # Allow user to select lap
        col3, col4 = st.columns(2)
        with col3:
            lap_d1_num = st.selectbox(f"{driver1} Lap", laps_d1["LapNumber"], key="lap_d1")
        with col4:
            lap_d2_num = st.selectbox(f"{driver2} Lap", laps_d2["LapNumber"], key="lap_d2")

        # Get telemetry
        lap_d1 = laps_d1.pick_laps(lap_d1_num).iloc[0]
        lap_d2 = laps_d2.pick_laps(lap_d2_num).iloc[0]
    
    lap_telemetry_d1 = lap_d1.telemetry
    lap_telemetry_d2 = lap_d2.telemetry

    # Colors
    color_d1 = get_driver_color(driver1, session)
    color_d2 = get_driver_color(driver2, session)

    # ---------------------------------------------------------
    # Plotly figure
    # ---------------------------------------------------------
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=lap_telemetry_d1["Distance"], y=lap_telemetry_d1["Speed"],
        mode="lines", name=driver1, line=dict(color=color_d1, width=3)
    ))
    fig.add_trace(go.Scatter(
        x=lap_telemetry_d2["Distance"], y=lap_telemetry_d2["Speed"],
        mode="lines", name=driver2, line=dict(color=color_d2, width=3)
    ))

    fig.update_layout(
        title=f"{driver1} vs {driver2} — {race_name} {year} ({session_type})",
        xaxis_title="Distance (m)",
        yaxis_title="Speed (km/h)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(x=0, y=1, bgcolor="rgba(0,0,0,0)")
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------
    # Session summary
    # ---------------------------------------------------------

    lap_time_d1 = lap_d1['LapTime']
    lap_time_d2 = lap_d2['LapTime']
    
    if pd.notnull(lap_time_d1) and pd.notnull(lap_time_d2):
        delta = lap_time_d1 - lap_time_d2
        if delta.total_seconds() < 0:
            faster_driver = driver1
        else:
            faster_driver = driver2
        time_diff = abs(delta.total_seconds())

        st.markdown("### Lap Time Summary")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric(driver1, format_laptime(lap_time_d1))
        col_b.metric(driver2, format_laptime(lap_time_d2))
        col_c.metric("Faster Driver", faster_driver, f"{time_diff:.3f} s faster")

        st.success(f"**{faster_driver}** was quicker by **{time_diff:.3f} seconds** in this lap.")

else:
    st.warning("Please select both drivers to compare their laps.")