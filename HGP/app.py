import streamlit as st
from src.ui import (
    apply_css,
    initialize_session_state,
    render_law_settings,
    render_save_load_settings,
    render_state_loader,
    render_state_settings,
    render_tech_settings,
    render_construction_projects,
    render_simulation_controls,
    render_simulation_output
)

st.set_page_config(page_title="HOI4 Planner", layout="wide")
apply_css()
st.title("Hearts of Iron IV Planner")
initialize_session_state()

tab1, tab2, tab3, tab4 = st.tabs(["State Management", "Law & Tech Settings", "Construction", "Simulation"])

with tab1:
    render_state_loader()
    render_state_settings()
    render_save_load_settings()

with tab2:
    render_law_settings()
    render_tech_settings()

with tab3:
    render_construction_projects()

with tab4:
    render_simulation_controls()
    render_simulation_output()