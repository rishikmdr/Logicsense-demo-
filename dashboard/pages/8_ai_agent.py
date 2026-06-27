import streamlit as st
from utils.auth import has_permission
from utils.api import api_get, api_post
from utils import ui

st.set_page_config(page_title="AI Agent · LogiSense 360", page_icon="✨", layout="wide")

# Determine provider badge before header
status = None

token = ui.boot("pages/8_ai_agent.py", "AI Agent",
                "Ask anything — the agent queries your live fleet data to answer")

if not has_permission("ai:read"):
    st.error("Access denied. Admin or Manager role required.")
    st.stop()

status = api_get("/ai/agent/status", token=token) or {}
provider = status.get("provider", "offline")
live = status.get("live", False)

# Provider status line
if live:
    label = {"anthropic": "Claude (Anthropic)", "openai": "GPT (OpenAI)"}.get(provider, provider)
    st.markdown(
        f"<span class='ls-badge live'>● LIVE · {label}</span>  "
        f"<span style='color:#9AA4B2;font-size:.85rem'>"
        f"{len(status.get('tools', []))} data tools available</span>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        "<span class='ls-badge offline'>○ OFFLINE DEMO</span>  "
        "<span style='color:#9AA4B2;font-size:.85rem'>"
        "Add ANTHROPIC_API_KEY or OPENAI_API_KEY to .env to go live</span>",
        unsafe_allow_html=True,
    )

st.write("")

# ── Conversation state ────────────────────────────────────────────────────────
if "agent_msgs" not in st.session_state:
    st.session_state.agent_msgs = []  # [{role, content, steps?}]

# Suggested prompts (only on empty conversation)
if not st.session_state.agent_msgs:
    st.caption("Try asking:")
    suggestions = [
        "Summarize today's fleet health and the top 3 risks I should act on.",
        "Which routes have the worst cost per km, and how do they compare on revenue?",
        "How many vehicles are idle vs active, and what's our utilization?",
        "Who are my best-performing drivers right now?",
    ]
    cols = st.columns(2)
    for i, s in enumerate(suggestions):
        if cols[i % 2].button(s, key=f"sugg_{i}", use_container_width=True):
            st.session_state["_pending"] = s
            st.rerun()

# Render history
for m in st.session_state.agent_msgs:
    with st.chat_message(m["role"], avatar="✨" if m["role"] == "assistant" else None):
        st.markdown(m["content"])
        if m.get("steps"):
            with st.expander(f"🔧 Agent used {len(m['steps'])} data tool(s)"):
                for s in m["steps"]:
                    st.markdown(f"**`{s['tool']}`**")
                    if s.get("input"):
                        st.caption(f"input: {s['input']}")
                    st.json(s.get("output", {}), expanded=False)


def run_agent(question: str):
    st.session_state.agent_msgs.append({"role": "user", "content": question})
    # Build history (text-only) for context — exclude the message we just added
    history = [
        {"role": x["role"], "content": x["content"]}
        for x in st.session_state.agent_msgs[:-1]
    ][-8:]
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("Thinking and querying fleet data..."):
            result = api_post("/ai/agent", {"message": question, "history": history}, token=token)
        if result:
            answer = result.get("response", "No response.")
            steps = result.get("steps", [])
            st.markdown(answer)
            if steps:
                with st.expander(f"🔧 Agent used {len(steps)} data tool(s)"):
                    for s in steps:
                        st.markdown(f"**`{s['tool']}`**")
                        if s.get("input"):
                            st.caption(f"input: {s['input']}")
                        st.json(s.get("output", {}), expanded=False)
            st.session_state.agent_msgs.append(
                {"role": "assistant", "content": answer, "steps": steps}
            )
        else:
            st.error("Agent request failed. Is the backend running?")


# Handle a clicked suggestion
pending = st.session_state.pop("_pending", None)
if pending:
    run_agent(pending)

# Chat input
prompt = st.chat_input("Ask the LogiSense agent…")
if prompt:
    run_agent(prompt)

if st.session_state.agent_msgs:
    if st.button("Clear conversation"):
        st.session_state.agent_msgs = []
        st.rerun()
