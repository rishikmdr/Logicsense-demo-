import streamlit as st
from utils.auth import has_permission
from utils.api import api_get, api_post
from utils import ui

st.set_page_config(page_title="AI Insights · LogiSense 360", page_icon="🧠", layout="wide")
token = ui.boot("pages/6_ai_insights.py", "AI Insights",
                "Daily briefs, anomaly detection and shift handovers")

if not has_permission("ai:read"):
    st.error("Access denied. Admin or Manager role required.")
    st.stop()
tab1, tab2, tab3, tab4 = st.tabs(["Daily Brief", "Ask AI", "Anomaly Detection", "Handover Report"])

with tab1:
    st.markdown("### Daily Operations Brief")
    if st.button("Generate Brief", key="brief_btn"):
        with st.spinner("Generating..."):
            data = api_get("/ai/brief", token=token)
        if data:
            st.markdown(data.get("brief", "No brief available."))
        else:
            st.error("Could not fetch brief.")

with tab2:
    st.markdown("### Ask Your Fleet AI")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("Ask anything about your fleet...")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                data = api_post("/ai/query", {"question": question}, token=token)
            answer = data.get("answer", "Unable to answer.") if data else "Backend error."
            st.markdown(answer)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

with tab3:
    st.markdown("### Anomaly Detection")
    if st.button("Scan for Anomalies", key="anomaly_btn"):
        with st.spinner("Scanning fleet data..."):
            data = api_get("/ai/anomalies", token=token)
        if data:
            anomalies = data.get("anomalies", [])
            if not anomalies:
                st.success("No anomalies detected.")
            for a in anomalies:
                severity = a.get("severity", "medium")
                icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
                with st.expander(f"{icon} {a.get('type', 'Unknown').replace('_', ' ').title()} — {severity.upper()}"):
                    st.markdown(a.get("description", ""))
                    if a.get("recommendation"):
                        st.info(f"**Recommendation:** {a['recommendation']}")
        else:
            st.error("Could not fetch anomalies.")

with tab4:
    st.markdown("### Shift Handover Report")
    if st.button("Generate Report", key="handover_btn"):
        with st.spinner("Compiling shift data..."):
            data = api_post("/ai/handover-report", token=token)
        if data:
            st.markdown(data.get("report", "No report available."))
        else:
            st.error("Could not generate report.")
