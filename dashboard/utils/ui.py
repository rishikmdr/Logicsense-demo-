"""Shared UI: enterprise theming (dark/light), Title Case navigation, layout helpers."""
import streamlit as st
from utils.auth import is_logged_in, current_user, do_logout, has_permission

# ── Navigation (Title Case labels + icons + required permission) ───────────────
NAV = [
    ("pages/1_fleet_map.py",    "Fleet Map",     "🗺️", "fleet:read"),
    ("pages/2_operations.py",   "Operations",    "📡", "analytics:read"),
    ("pages/3_analytics.py",    "Analytics",     "📊", "analytics:read"),
    ("pages/4_cost_analysis.py","Cost Analysis", "💰", "finance:read"),
    ("pages/5_compliance.py",   "Compliance",    "🛡️", "compliance:read"),
    ("pages/6_ai_insights.py",  "AI Insights",   "🧠", "ai:read"),
    ("pages/7_alerts.py",       "Alerts",        "🔔", "alerts:read"),
    ("pages/8_ai_agent.py",     "AI Agent",      "✨", "ai:read"),
]

THEMES = {
    "dark": {
        "bg": "#0E1117", "panel": "#161B26", "panel2": "#1C2230",
        "text": "#E6EAF1", "muted": "#9AA4B2", "border": "#262C3A",
        "sidebar": "#0B0E15", "accent": "#FF6B35", "accent2": "#3B82F6",
        "plotly": "plotly_dark",
    },
    "light": {
        "bg": "#F4F6FB", "panel": "#FFFFFF", "panel2": "#FFFFFF",
        "text": "#0F172A", "muted": "#64748B", "border": "#E2E8F0",
        "sidebar": "#FFFFFF", "accent": "#FF6B35", "accent2": "#2563EB",
        "plotly": "plotly_white",
    },
}


def init_state():
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"


def theme() -> dict:
    init_state()
    return THEMES[st.session_state["theme"]]


def plotly_template() -> str:
    return theme()["plotly"]


def accent() -> str:
    return theme()["accent"]


def show_chart(fig, height: int | None = None):
    """Render a Plotly figure with a transparent background so it matches the
    active theme (light or dark) regardless of the figure's template."""
    t = theme()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=t["text"],
        title_font_color=t["text"],
        legend=dict(font=dict(color=t["text"])),
        margin=dict(t=46, l=10, r=10, b=10),
    )
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, use_container_width=True)


def _css() -> str:
    t = theme()
    return f"""
    <style>
    /* App surfaces */
    .stApp {{ background: {t['bg']}; color: {t['text']}; }}
    [data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stAppViewContainer"] .main .block-container {{ padding-top: 2.2rem; max-width: 1400px; }}
    h1, h2, h3, h4, h5, h6, p, span, label, li {{ color: {t['text']}; }}

    /* Sidebar */
    [data-testid="stSidebar"] {{ background: {t['sidebar']}; border-right: 1px solid {t['border']}; }}
    [data-testid="stSidebar"] * {{ color: {t['text']}; }}
    [data-testid="stSidebarNav"] {{ display: none; }}  /* hide default lowercase file nav */

    /* Custom nav links (st.page_link) */
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {{
        border-radius: 10px; padding: 8px 12px; margin: 2px 0;
        font-weight: 500; transition: background .15s ease, color .15s ease;
    }}
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {{
        background: {t['panel2']};
    }}

    /* Metric cards -> enterprise tiles */
    [data-testid="stMetric"] {{
        background: {t['panel']}; border: 1px solid {t['border']};
        border-radius: 14px; padding: 16px 18px;
        box-shadow: 0 1px 2px rgba(0,0,0,.05);
    }}
    [data-testid="stMetricLabel"] p {{ color: {t['muted']}; font-size: .82rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: .04em; }}
    [data-testid="stMetricValue"] {{ color: {t['text']}; font-weight: 700; }}

    /* Buttons */
    .stButton > button, .stFormSubmitButton > button {{
        border-radius: 10px; border: 1px solid {t['border']};
        background: {t['panel']}; color: {t['text']}; font-weight: 600;
    }}
    .stButton > button[kind="primary"], .stFormSubmitButton > button {{
        background: {t['accent']}; border-color: {t['accent']}; color: #fff;
    }}
    .stButton > button:hover {{ border-color: {t['accent']}; color: {t['accent']}; }}

    /* Inputs */
    [data-testid="stTextInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    [data-testid="stTextArea"] textarea {{
        background: {t['panel']}; color: {t['text']}; border-radius: 10px;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
    .stTabs [data-baseweb="tab"] {{ border-radius: 8px 8px 0 0; }}
    .stTabs [aria-selected="true"] {{ color: {t['accent']}; }}

    /* Dataframe container */
    [data-testid="stDataFrame"] {{ border: 1px solid {t['border']}; border-radius: 12px; }}

    /* Brand + section helpers */
    .ls-brand {{ display:flex; align-items:center; gap:10px; padding: 4px 6px 14px; }}
    .ls-brand .logo {{ font-size: 1.6rem; }}
    .ls-brand .name {{ font-size: 1.25rem; font-weight: 800; color: {t['accent']}; line-height:1; }}
    .ls-brand .tag {{ font-size: .68rem; color: {t['muted']}; letter-spacing:.05em; }}
    .ls-usercard {{
        background: {t['panel']}; border: 1px solid {t['border']}; border-radius: 12px;
        padding: 12px 14px; margin: 8px 0 12px;
    }}
    .ls-usercard .nm {{ font-weight: 700; }}
    .ls-usercard .rl {{ font-size: .78rem; color: {t['muted']}; }}
    .ls-pageheader {{ margin-bottom: .4rem; }}
    .ls-pageheader .h {{ font-size: 1.9rem; font-weight: 800; margin:0; }}
    .ls-pageheader .s {{ color: {t['muted']}; margin: 2px 0 0; }}
    .ls-divider {{ border:none; border-top:1px solid {t['border']}; margin: 10px 0 14px; }}
    .ls-badge {{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:.72rem;
        font-weight:700; }}
    .ls-badge.live {{ background: rgba(34,197,94,.15); color:#22c55e; }}
    .ls-badge.offline {{ background: rgba(148,163,184,.18); color:{t['muted']}; }}
    </style>
    """


def inject_css():
    st.markdown(_css(), unsafe_allow_html=True)


def render_sidebar(active: str):
    role = (current_user().get("role") or "").replace("_", " ").title()
    name = current_user().get("full_name", "User")
    with st.sidebar:
        st.markdown(
            "<div class='ls-brand'><span class='logo'>🚚</span>"
            "<div><div class='name'>LogiSense 360</div>"
            "<div class='tag'>QUATEX CONSULTING</div></div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='ls-usercard'><div class='nm'>{name}</div>"
            f"<div class='rl'>{role}</div></div>",
            unsafe_allow_html=True,
        )

        for path, label, icon, perm in NAV:
            if perm and not has_permission(perm):
                continue
            st.page_link(path, label=label, icon=icon)

        st.markdown("<hr class='ls-divider'>", unsafe_allow_html=True)

        # Theme toggle
        cur = st.session_state.get("theme", "dark")
        choice = st.radio(
            "Appearance",
            ["🌙 Dark", "☀️ Light"],
            index=0 if cur == "dark" else 1,
            horizontal=True,
            label_visibility="collapsed",
        )
        new = "dark" if "Dark" in choice else "light"
        if new != cur:
            st.session_state["theme"] = new
            st.rerun()

        if st.button("Sign Out", use_container_width=True):
            do_logout()
            st.switch_page("app.py")


def page_header(title: str, subtitle: str = "", badge_html: str = ""):
    st.markdown(
        f"<div class='ls-pageheader'><div class='h'>{title} {badge_html}</div>"
        f"<div class='s'>{subtitle}</div></div><hr class='ls-divider'>",
        unsafe_allow_html=True,
    )


def boot(active: str, title: str, subtitle: str = "", badge_html: str = ""):
    """Standard page boot: require login, theme, sidebar, header. Returns auth token."""
    from utils.auth import require_login, get_token
    require_login()
    init_state()
    inject_css()
    render_sidebar(active)
    page_header(title, subtitle, badge_html)
    return get_token()
