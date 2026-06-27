import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from utils.api import api_get
from utils import ui

st.set_page_config(page_title="Fleet Map · LogiSense 360", page_icon="🗺️", layout="wide")
token = ui.boot("pages/1_fleet_map.py", "Live Fleet Map",
                "Real-time vehicle positions and fleet status")
vehicles = api_get("/fleet/vehicles", token=token) or []
summary = api_get("/fleet/summary", token=token) or {}
active_trips = api_get("/trips/active", token=token) or []

# KPI row
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Vehicles", summary.get("total", len(vehicles)))
c2.metric("Active", summary.get("active", 0), delta=f"{summary.get('utilization_pct', 0):.1f}% utilization")
c3.metric("Idle", summary.get("idle", 0))
c4.metric("Maintenance", summary.get("maintenance", 0))

STATUS_COLORS = {"active": "#22c55e", "idle": "#f59e0b", "maintenance": "#3b82f6", "breakdown": "#ef4444"}

# Map
m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="CartoDB dark_matter")

for v in vehicles:
    lat, lng = v.get("current_lat"), v.get("current_lng")
    if lat is None or lng is None:
        continue
    color = STATUS_COLORS.get(v.get("status", "idle"), "#aaa")
    folium.CircleMarker(
        location=[lat, lng],
        radius=6,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.9,
        popup=folium.Popup(
            f"<b>{v['registration_number']}</b><br>"
            f"Status: {v['status']}<br>"
            f"Speed: {v.get('current_speed_kmh', 0):.0f} km/h<br>"
            f"Fuel: {v.get('fuel_level_pct', 0):.0f}%",
            max_width=200,
        ),
        tooltip=v["registration_number"],
    ).add_to(m)

for trip in active_trips:
    if trip.get("origin_lat") and trip.get("destination_lat"):
        folium.PolyLine(
            locations=[
                [trip["origin_lat"], trip["origin_lng"]],
                [trip["destination_lat"], trip["destination_lng"]],
            ],
            color="#FF6B35",
            weight=1.5,
            opacity=0.5,
        ).add_to(m)

col_map, col_table = st.columns([2, 1])
with col_map:
    st_folium(m, height=500, returned_objects=[])

with col_table:
    st.markdown("**Vehicle List**")
    if vehicles:
        df = pd.DataFrame(vehicles)[["registration_number", "vehicle_type", "status", "fuel_level_pct", "current_speed_kmh"]]
        df.columns = ["Reg No", "Type", "Status", "Fuel %", "Speed"]
        df["Fuel %"] = df["Fuel %"].map(lambda x: f"{x:.0f}%")
        df["Speed"] = df["Speed"].map(lambda x: f"{x:.0f}")
        st.dataframe(df, height=480, use_container_width=True)
    else:
        st.info("No vehicle data available.")
