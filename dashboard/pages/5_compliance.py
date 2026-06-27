import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from utils.auth import require_login, current_user, get_token, do_logout
from utils.api import api_get

st.set_page_config(page_title="Compliance · LogiSense 360", page_icon="📋", layout="wide")
require_login()

with st.sidebar:
    u = current_user()
    st.markdown(f"**{u.get('full_name', 'User')}**")
    st.caption(u.get("role", "").replace("_", " ").title())
    if st.button("Logout"):
        do_logout()
        st.switch_page("app.py")

st.title("📋 Compliance & Documents")
token = get_token()
vehicles = api_get("/fleet/vehicles", token=token) or []

if not vehicles:
    st.info("No vehicle data.")
    st.stop()

today = date.today()

rows = []
for v in vehicles:
    for doc, field in [("Insurance", "insurance_expiry"), ("Fitness", "fitness_expiry"), ("Road Tax", "road_tax_expiry"), ("PUC", "puc_expiry")]:
        expiry_str = v.get(field)
        if not expiry_str:
            continue
        expiry = date.fromisoformat(expiry_str)
        days_left = (expiry - today).days
        if days_left < 0:
            status = "EXPIRED"
        elif days_left <= 7:
            status = "CRITICAL"
        elif days_left <= 30:
            status = "WARNING"
        else:
            status = "OK"
        rows.append({
            "Registration": v["registration_number"],
            "Document": doc,
            "Expiry": expiry_str,
            "Days Left": days_left,
            "Status": status,
        })

df = pd.DataFrame(rows)

status_counts = df["Status"].value_counts()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Expired", status_counts.get("EXPIRED", 0), delta_color="inverse")
c2.metric("Critical (≤7d)", status_counts.get("CRITICAL", 0), delta_color="inverse")
c3.metric("Warning (≤30d)", status_counts.get("WARNING", 0), delta_color="inverse")
c4.metric("OK", status_counts.get("OK", 0))

status_filter = st.selectbox("Filter by status", ["All", "EXPIRED", "CRITICAL", "WARNING", "OK"])
if status_filter != "All":
    df = df[df["Status"] == status_filter]

def color_status(val):
    colors = {"EXPIRED": "background-color:#ef4444", "CRITICAL": "background-color:#f97316",
              "WARNING": "background-color:#f59e0b; color:#000", "OK": "background-color:#22c55e; color:#000"}
    return colors.get(val, "")

st.dataframe(
    df.style.applymap(color_status, subset=["Status"]),
    use_container_width=True,
    height=400,
)

fig = px.bar(
    df.groupby(["Document", "Status"]).size().reset_index(name="Count"),
    x="Document", y="Count", color="Status",
    color_discrete_map={"EXPIRED": "#ef4444", "CRITICAL": "#f97316", "WARNING": "#f59e0b", "OK": "#22c55e"},
    title="Document Status by Type",
    template="plotly_dark",
)
st.plotly_chart(fig, use_container_width=True)
