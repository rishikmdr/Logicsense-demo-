import streamlit as st
from utils.auth import do_login, is_logged_in, do_logout
from utils.api import backend_is_healthy

st.set_page_config(
    page_title="LogiSense 360",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Redirect logged-in users
if is_logged_in():
    st.switch_page("pages/1_fleet_map.py")

# ── Header ──────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding: 2rem 0 1rem'>
    <h1 style='color:#FF6B35; font-size:2.5rem; margin:0'>🚚 LogiSense 360</h1>
    <p style='color:#aaa; font-size:1.1rem'>Logistics Intelligence Platform · Powered by Quatex Consulting</p>
</div>
""", unsafe_allow_html=True)

# ── Backend health check ─────────────────────────────────────────────────
healthy = backend_is_healthy()
if not healthy:
    st.error(
        "**Backend not reachable.**\n\n"
        "The API server is not running or still starting up.\n\n"
        "**Steps to fix:**\n"
        "1. Run `make start` in the project directory\n"
        "2. Wait ~60 seconds for services to initialize\n"
        "3. Refresh this page\n\n"
        "If already running: `make logs-backend` to check for errors.",
        icon="🔴",
    )
    st.stop()

st.success("Backend connected", icon="🟢")

# ── Login form ───────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 1.2, 1])
with col2:
    st.markdown("### Sign In")
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="admin@fasttrack.in")
        password = st.text_input("Password", type="password", placeholder="Admin@123")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

    if submitted:
        if not email or not password:
            st.error("Please enter email and password.")
        else:
            with st.spinner("Signing in..."):
                result = do_login(email.strip(), password)

            if result["success"]:
                st.success(f"Welcome, {result['user']['full_name']}!")
                st.rerun()
            else:
                err = result.get("error", "unknown")
                if err == "backend_down":
                    st.error("Cannot connect to backend. Run `make start` and wait ~60s.")
                elif err == "invalid_credentials":
                    st.error("Invalid email or password. Check the credentials below.")
                else:
                    detail = result.get("detail", "")
                    st.error(f"Login failed ({detail or err}). Try again or check `make logs-backend`.")

# ── Demo credentials ─────────────────────────────────────────────────────
st.divider()
st.markdown("#### Demo Credentials")
creds = [
    ("admin@fasttrack.in", "Admin@123", "Admin", "Full access to all features"),
    ("ops@fasttrack.in", "Ops@123", "Operations Manager", "Fleet, trips, alerts"),
    ("finance@fasttrack.in", "Finance@123", "Finance Manager", "Cost & revenue analytics"),
    ("branch@fasttrack.in", "Branch@123", "Branch Manager", "Branch-level view"),
    ("driver1@fasttrack.in", "Driver@123", "Driver", "Own trips only"),
    ("customer@acme.in", "Customer@123", "Customer", "Shipment tracking"),
]

cols = st.columns(3)
for i, (email_d, pwd, role, desc) in enumerate(creds):
    with cols[i % 3]:
        st.markdown(f"""
<div style='background:#1E2130; border-radius:8px; padding:12px; margin-bottom:8px; border-left:3px solid #FF6B35'>
    <b style='color:#FF6B35'>{role}</b><br>
    <code style='font-size:0.8rem'>{email_d}</code><br>
    <code style='font-size:0.8rem'>{pwd}</code><br>
    <small style='color:#aaa'>{desc}</small>
</div>
""", unsafe_allow_html=True)

st.markdown(
    "<p style='text-align:center; color:#555; font-size:0.85rem; margin-top:2rem'>"
    "LogiSense 360 Demo · Quatex Consulting · For evaluation purposes only</p>",
    unsafe_allow_html=True,
)
