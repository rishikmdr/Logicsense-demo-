import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.auth import require_login, current_user, get_token, has_permission, do_logout
from utils.api import api_get

st.set_page_config(page_title="Cost Analysis · LogiSense 360", page_icon="💰", layout="wide")
require_login()

with st.sidebar:
    u = current_user()
    st.markdown(f"**{u.get('full_name', 'User')}**")
    st.caption(u.get("role", "").replace("_", " ").title())
    if st.button("Logout"):
        do_logout()
        st.switch_page("app.py")

st.title("💰 Cost Analysis")

if not has_permission("finance:read"):
    st.error("Access denied. Finance Manager or Admin role required.")
    st.stop()

token = get_token()
trends = api_get("/analytics/kpis/trends", token=token) or []
cost_breakdown = api_get("/analytics/cost/breakdown", token=token) or {}
trips = api_get("/trips", params={"limit": 300}, token=token) or []

if trends:
    df = pd.DataFrame(trends)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["week"], y=df["revenue_inr"], name="Revenue ₹", marker_color="#22c55e"))
    fig.update_layout(title="Weekly Revenue Trend", template="plotly_dark", height=350)
    st.plotly_chart(fig, use_container_width=True)

if cost_breakdown:
    labels = ["Fuel", "Driver", "Toll", "Maintenance"]
    values = [
        cost_breakdown.get("fuel_inr", 0),
        cost_breakdown.get("driver_inr", 0),
        cost_breakdown.get("toll_inr", 0),
        cost_breakdown.get("maintenance_inr", 0),
    ]
    fig2 = px.pie(
        values=values, names=labels,
        title="Cost Breakdown (All Time)",
        template="plotly_dark",
        color_discrete_sequence=["#FF6B35", "#3b82f6", "#f59e0b", "#22c55e"],
        hole=0.4,
    )
    st.plotly_chart(fig2, use_container_width=True)

if trips:
    df_t = pd.DataFrame(trips)
    df_t = df_t[df_t["status"] == "delivered"][["trip_number", "origin_city", "destination_city", "revenue_inr", "total_cost_inr", "profit_inr", "cost_per_km"]].head(50)
    df_t.columns = ["Trip #", "Origin", "Destination", "Revenue ₹", "Cost ₹", "Profit ₹", "₹/km"]
    st.markdown("**Recent Trip Profitability**")
    st.dataframe(df_t, use_container_width=True)
