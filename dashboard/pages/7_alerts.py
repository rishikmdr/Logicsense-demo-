import streamlit as st
import pandas as pd
from utils.auth import require_login, current_user, get_token, has_permission, do_logout
from utils.api import api_get, api_patch

st.set_page_config(page_title="Alerts · LogiSense 360", page_icon="🚨", layout="wide")
require_login()

with st.sidebar:
    u = current_user()
    st.markdown(f"**{u.get('full_name', 'User')}**")
    st.caption(u.get("role", "").replace("_", " ").title())
    if st.button("Logout"):
        do_logout()
        st.switch_page("app.py")

st.title("🚨 Alerts")
token = get_token()

summary = api_get("/alerts/summary", token=token) or {}
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Active", summary.get("total_active", 0))
c2.metric("Critical", summary.get("critical", 0))
c3.metric("High", summary.get("high", 0))
c4.metric("Medium", summary.get("medium", 0))

col_l, col_r = st.columns([1, 2])
with col_l:
    show_resolved = st.checkbox("Show resolved alerts", value=False)
    severity_filter = st.selectbox("Severity", ["All", "critical", "high", "medium", "low"])

params = {"resolved": show_resolved}
if severity_filter != "All":
    params["severity"] = severity_filter

alerts = api_get("/alerts", params=params, token=token) or []

if not alerts:
    st.info("No alerts found.")
else:
    SEVERITY_ICONS = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
    for a in alerts:
        icon = SEVERITY_ICONS.get(a.get("severity", "medium"), "⚪")
        with st.expander(f"{icon} [{a['severity'].upper()}] {a['title']} — {a['created_at'][:16]}"):
            st.markdown(a.get("description", ""))
            if a.get("ai_analysis"):
                st.info(f"**AI Analysis:** {a['ai_analysis']}")
            if not a.get("is_resolved") and has_permission("alerts:write"):
                if st.button(f"Mark Resolved", key=f"resolve_{a['id']}"):
                    result = api_patch(f"/alerts/{a['id']}/resolve", token=token)
                    if result:
                        st.success("Alert resolved.")
                        st.rerun()
                    else:
                        st.error("Failed to resolve alert.")
            elif a.get("is_resolved"):
                st.caption(f"✅ Resolved at {a.get('resolved_at', '')[:16]}")
