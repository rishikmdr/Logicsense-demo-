import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.api import api_get
from utils import ui

st.set_page_config(page_title="Analytics · LogiSense 360", page_icon="📊", layout="wide")
token = ui.boot("pages/3_analytics.py", "Analytics",
                "Performance trends, route economics and utilization")

kpis = api_get("/analytics/kpis/summary", token=token) or {}
trends = api_get("/analytics/kpis/trends", token=token) or []
routes = api_get("/analytics/routes/performance", token=token) or []

c1, c2, c3, c4 = st.columns(4)
c1.metric("OTIF %", f"{kpis.get('otif_pct', 0):.1f}%")
c2.metric("Avg Cost/km", f"₹{kpis.get('avg_cost_per_km', 0):.2f}")
c3.metric("Fleet Utilization", f"{kpis.get('fleet_utilization_pct', 0):.1f}%")
c4.metric("Total Revenue", f"₹{kpis.get('total_revenue_inr', 0)/100000:.1f}L")

if trends:
    df = pd.DataFrame(trends)
    fig = px.bar(df, x="week", y="trips", title="Weekly Trip Volume", template=ui.plotly_template(), color_discrete_sequence=["#FF6B35"])
    ui.show_chart(fig)

if routes:
    df_r = pd.DataFrame(routes)
    fig2 = px.bar(
        df_r, x="route", y="avg_cost_per_km",
        title="Avg Cost/km by Route", template=ui.plotly_template(),
        color="avg_cost_per_km", color_continuous_scale="Oranges",
        labels={"avg_cost_per_km": "₹/km", "route": "Route"},
    )
    fig2.update_xaxes(tickangle=45)
    ui.show_chart(fig2)

    st.markdown("**Route Performance Table**")
    st.dataframe(pd.DataFrame(routes), use_container_width=True)
