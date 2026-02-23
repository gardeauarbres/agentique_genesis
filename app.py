import sys
import os

import streamlit as st
from langchain_core.messages import HumanMessage

# ====== PAGE CONFIG ======
st.set_page_config(
    page_title="Agent Local V5",
    page_icon="🤖",
    layout="wide",
)

# CSS Custom
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
    background-color: #0d0f14;
    color: #e2e8f0;
}

.stTextArea > div > div > textarea {
    background-color: #1a1d27 !important;
    color: #e2e8f0 !important;
    border: 1px solid #2d3748 !important;
    border-radius: 8px !important;
}

.step-box {
    background: #1a1d27;
    border-left: 3px solid #6c63ff;
    padding: 8px 14px;
    border-radius: 6px;
    margin: 4px 0;
    font-size: 0.85rem;
    color: #a0aec0;
}
.step-done  { border-left-color: #48bb78; color: #9ae6b4; }
.step-warn  { border-left-color: #f6ad55; color: #fbd38d; }

.header-block {
    background: linear-gradient(135deg, #1a1d27, #252836);
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 20px;
    border: 1px solid #2d3748;
}

.badge-pass  { display:inline-block; padding:3px 10px; border-radius:99px; background:#276749; color:#9ae6b4; font-size:.75rem; font-weight:600; }
.badge-stop  { display:inline-block; padding:3px 10px; border-radius:99px; background:#742a2a; color:#fc8181; font-size:.75rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ====== HEADER ======
st.markdown("""
<div class='header-block'>
    <h1 style='margin:0; font-size:1.8rem;'>🤖 Agent Local V5</h1>
    <p style='color:#718096; margin:6px 0 0;'>Ollama · LangGraph · DuckDuckGo · Web Fetch · Streaming · Async</p>
</div>
""", unsafe_allow_html=True)

# ====== LAYOUT ======
col_left, col_right = st.columns([1, 2], gap="large")

NODE_LABELS = {
    "planner":   "🧠 Planner — Analyse et planification",
    "tools":     "🔧 Researcher — Recherche & Outils",
    "writer":    "✍️ Writer — Rédaction du rapport",
    "verifier":  "🔍 Verifier — Validation",
    "finalizer": "💾 Finalizer — Sauvegarde",
}

with col_left:
    st.markdown("### 🎯 Objectif")
    user_goal = st.text_area(
        label="Décrivez votre objectif ici :",
        placeholder="Ex : Résume la page https://example.com\nOu : Qui a fondé Anthropic ?",
        height=130,
        key="user_goal",
    )
    run_btn = st.button("🚀 Lancer la mission", use_container_width=True, type="primary")

    st.markdown("---")
    st.markdown("### 🔄 Étapes")
    steps_ph = st.empty()

with col_right:
    st.markdown("### 📄 Rapport")
    report_ph = st.empty()
    stats_ph  = st.empty()

# ====== RUN ======
if run_btn and user_goal.strip():

    # Import ici pour éviter le blocage au démarrage de Streamlit
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from agent_local_v5 import build_v5

    steps_log  = []
    report_txt = ""
    tool_count = search_count = 0
    final_verdict = "?"

    def render_steps(steps):
        html = ""
        for s in steps:
            css = "step-done" if "✅" in s else "step-warn" if "⚠️" in s else ""
            html += f"<div class='step-box {css}'>{s}</div>"
        steps_ph.markdown(html, unsafe_allow_html=True)

    steps_ph.info("🟡 Initialisation de l'agent…")

    agent  = build_v5()
    inputs = {
        "goal": user_goal,
        "messages": [HumanMessage(content=user_goal)],
        "facts": [],
        "tool_count": 0, "read_bytes": 0, "search_count": 0,
        "fetch_count": 0, "web_bytes": 0,
        "iteration": 0, "tool_events": [],
        "verdict": "RETRY", "last_critique": "", "critique_history": [],
    }

    for output in agent.stream(inputs):
        for node_name, val in output.items():
            label = NODE_LABELS.get(node_name, node_name)
            steps_log.append(f"✅ {label}")
            render_steps(steps_log)

            if isinstance(val, dict):
                tool_count    = val.get("tool_count",    tool_count)
                search_count  = val.get("search_count",  search_count)
                v = val.get("verdict", "")
                if v: final_verdict = v
                if val.get("verdict") == "RETRY":
                    steps_log.append(f"⚠️ Critique : {val.get('last_critique','')}")

            if node_name == "writer":
                msgs = val.get("messages", [])
                if msgs:
                    report_txt = msgs[-1].content
                    report_ph.markdown(report_txt)

    badge = "badge-pass" if final_verdict == "PASS" else "badge-stop"
    stats_ph.markdown(f"""
<div style='margin-top:10px; color:#718096; font-size:.85rem;'>
  <span class='{badge}'>{final_verdict}</span>&nbsp;
  Outils : <b>{tool_count}</b>&nbsp;|&nbsp;Recherches web : <b>{search_count}</b>
</div>
""", unsafe_allow_html=True)

elif run_btn:
    st.warning("⚠️ Veuillez saisir un objectif avant de lancer l'agent.")
