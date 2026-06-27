import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.auth import require_login, current_user, get_token, do_logout
from utils.api import api_get

st.set_page_config(page_title="Operations · LogiSense 360", page_icon="⚙️", layout="wide")
require_login()

with st.sidebar:
    u = current_user()
    st.markdown(f"**{u.get('full_name', 'User')}**")
    st.caption(u.get("role", "").replace("_", " ").title())
    if st.button("Logout"):
        do_logout()
        st.switch_page("app.py")

st.title("⚙️ Operations Dashboard")
token = get_token()

kpis = api_get("/analytics/kpis/summary", token=token) or {}
trends = api_get("/analytics/kpis/trends", token=token) or []
alert_summary = api_get("/alerts/summary", token=token) or {}

c1, c2, c3, c4 = st.columns(4)
c1.metric("OTIF %", f"{kpis.get('otif_pct', 0):.1f}%")
c2.metric("Total Trips", kpis.get("total_trips", 0))
c3.metric("Revenue", f"₹{kpis.get('total_revenue_inr', 0)/100000:.1f}L")
c4.metric("Active Alerts", alert_summary.get("total_active", 0))

if trends:
    df = pd.DataFrame(trends)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["week"], y=df["trips"], name="Trips", yaxis="y"))
    fig.add_trace(go.Scatter(x=df["week"], y=df["cost_per_km"], name="Cost/km (₹)", yaxis="y2", line=dict(color="#FF6B35")))
    fig.update_layout(
        title="Weekly Trips & Cost/km",
        yaxis=dict(title="Trips"),
        yaxis2=dict(title="₹/km", overlaying="y", side="right"),
        template="plotly_dark",
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    if alert_summary:
        labels = ["Critical", "High", "Medium", "Low"]
        vals = [
            alert_summary.get("critical", 0),
            alert_summary.get("high", 0),
            alert_summary.get("medium", 0),
            alert_summary.get("low", 0),
        ]
        fig2 = px.bar(
            x=labels, y=vals,
            color=labels,
            color_discrete_map={"Critical": "#ef4444", "High": "#f97316", "Medium": "#f59e0b", "Low": "#22c55e"},
            title="Active Alerts by Severity",
            template="plotly_dark",
        )
        st.plotly_chart(fig2, use_container_width=True)

with col2:
    trips = api_get("/trips", params={"limit": 200}, token=token) or []
    if trips:
        df_t = pd.DataFrame(trips)
        status_counts = df_t["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig3 = px.pie(status_counts, names="Status", values="Count", title="Trip Status Distribution", template="plotly_dark", hole=0.4)
        st.plotly_chart(fig3, use_container_width=True)
