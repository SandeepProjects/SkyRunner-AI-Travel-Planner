import streamlit as st
import os
import psycopg
import json
import streamlit.components.v1 as components
from dotenv import load_dotenv
from main import run_travel_agent

load_dotenv()

st.set_page_config(page_title="SkyRunner Command Center", page_icon="✈️", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@400;500;600&display=swap');

    /* Global Variables */
    :root {
        --bg-color: #0B0E14;
        --card-bg: rgba(22, 27, 34, 0.6);
        --accent-glow: rgba(78, 205, 196, 0.15);
        --accent-color: #4ECDC4;
        --text-primary: #F8FAFC;
        --text-secondary: #94A3B8;
        --border-color: rgba(255, 255, 255, 0.08);
    }

    /* Base Styling */
    .stApp {
        background-color: var(--bg-color);
        background-image: 
            radial-gradient(circle at 15% 50%, rgba(78, 205, 196, 0.05), transparent 25%),
            radial-gradient(circle at 85% 30%, rgba(255, 107, 107, 0.05), transparent 25%);
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }

    /* Radar Background Grid Pattern */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background-image: 
            linear-gradient(var(--border-color) 1px, transparent 1px),
            linear-gradient(90deg, var(--border-color) 1px, transparent 1px);
        background-size: 40px 40px;
        opacity: 0.3;
        z-index: -1;
        pointer-events: none;
    }

    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .hero-title {
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        background: -webkit-linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        letter-spacing: -1px;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        color: var(--text-secondary);
        font-weight: 300;
        margin-bottom: 2rem;
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: var(--card-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px 0 var(--accent-glow);
    }

    /* Flight & Hotel Sub-cards */
    .data-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 4px solid var(--accent-color);
    }
    .data-card-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 1.1rem;
        color: #fff;
        margin-bottom: 4px;
    }
    .data-card-text {
        font-size: 0.9rem;
        color: var(--text-secondary);
        margin: 2px 0;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .badge-success { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-error { background: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-info { background: rgba(56, 189, 248, 0.15); color: #7DD3FC; border: 1px solid rgba(56, 189, 248, 0.3); }

    /* Sidebar Restyling */
    [data-testid="stSidebar"] {
        background-color: #0F1219 !important;
        border-right: 1px solid var(--border-color);
    }
    .sidebar-block {
        background: rgba(255,255,255,0.02);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 16px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Custom Streamlit component overrides */
    div[data-baseweb="input"] > div {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #fff !important;
    }
    .stTextArea textarea {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #fff !important;
        font-family: 'Inter', sans-serif !important;
        border-radius: 12px !important;
    }
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #4ECDC4 0%, #2E9D95 100%) !important;
        color: #000 !important;
        border: none !important;
    }
    .stButton>button[kind="primary"]:hover {
        box-shadow: 0 4px 15px rgba(78, 205, 196, 0.4) !important;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER PARSERS ---

def parse_flight_results(text):
    if not text or "No flight results found" in text or "error" in text.lower():
        return None
    flights = []
    blocks = text.split("\n---\n")
    for block in blocks:
        if not block.strip(): continue
        lines = block.strip().split('\n')
        flight_dict = {}
        for line in lines:
            if ':' in line:
                key, val = line.split(':', 1)
                flight_dict[key.strip()] = val.strip()
        if flight_dict:
            flights.append(flight_dict)
    return flights

def parse_hotel_results(text):
    if not text or "No Tavily search results" in text or "error" in text.lower():
        return None
    hotels = []
    blocks = text.split("\n---\n")
    for block in blocks:
        if not block.strip(): continue
        lines = block.strip().split('\n')
        hotel_dict = {}
        for line in lines:
            if ':' in line:
                key, val = line.split(':', 1)
                hotel_dict[key.strip()] = val.strip()
        if hotel_dict:
            hotels.append(hotel_dict)
    return hotels

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='font-weight:800; text-align:center;'>✈️ SkyRunner</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94A3B8; font-size:0.9rem; margin-top:-10px;'>Command Center</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:rgba(255,255,255,0.05); margin:10px 0;'>", unsafe_allow_html=True)

    # Database Status
    db_url = os.getenv("DATABASE_URL")
    db_status = "Disconnected"
    try:
        with psycopg.connect(db_url) as conn:
            db_status = "Connected"
    except Exception:
        db_status = "Error"
        
    badge_cls = "badge-success" if db_status == "Connected" else "badge-error"
    
    st.markdown(f"""
    <div class='sidebar-block'>
        <div style='font-size:0.8rem; color:#94A3B8; margin-bottom:5px;'>SYSTEM STATUS</div>
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
            <span style='font-size:0.9rem;'>PostgreSQL</span>
            <span class='badge {badge_cls}'>{db_status}</span>
        </div>
        <div style='font-size:0.8rem; color:#64748B;'>DB: multi_agent_flight</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Memory Status
    st.markdown("<div style='font-size:0.8rem; color:#94A3B8; margin-bottom:5px;'>MEMORY THREAD ID</div>", unsafe_allow_html=True)
    thread_id = st.text_input("", value="skyrunner_cmd_1", label_visibility="collapsed")
    
    # API Variables
    st.markdown("""<div class='sidebar-block'>
        <div style='font-size:0.8rem; color:#94A3B8; margin-bottom:10px;'>API CONNECTIVITY</div>""", unsafe_allow_html=True)
        
    for key in ["GROQ_API_KEY", "TAVILY_API_KEY", "AVIATIONSTACK_API_KEY"]:
        val = os.getenv(key)
        status_html = "<span class='badge badge-success' style='float:right;'>OK</span>" if val and val.strip(" ;\"'") else "<span class='badge badge-error' style='float:right;'>ERR</span>"
        label = key.replace('_API_KEY', '')
        st.markdown(f"<div style='margin-bottom:8px; font-size:0.85rem;'>{label} {status_html}</div>", unsafe_allow_html=True)
        
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("Reset Session / Clear Memory", use_container_width=True):
        if 'agent_result' in st.session_state:
            del st.session_state['agent_result']
        st.rerun()

# --- MAIN AREA ---
st.markdown("<div class='hero-title'>SkyRunner</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-subtitle'>Search flights, discover hotels, and generate smart itineraries in one workflow.</div>", unsafe_allow_html=True)

# Query Input
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
col_input, col_chips = st.columns([2, 1])

with col_input:
    # Initialize query state
    if "current_query" not in st.session_state:
        st.session_state.current_query = "Find flights from LCA to ATH and suggest hotels for 2 nights."
        
    user_query = st.text_area("What is your mission?", value=st.session_state.current_query, height=120, placeholder="E.g., Find flights from JFK to LHR this weekend...")
    
    if st.button("🚀 Execute Mission", type="primary", use_container_width=True):
        st.session_state.run_query = user_query

with col_chips:
    st.markdown("<div style='font-size:0.85rem; color:#94A3B8; margin-bottom:8px;'>Suggested Prompts:</div>", unsafe_allow_html=True)
    if st.button("🛫 LCA to ATH, 2 nights", use_container_width=True):
        st.session_state.current_query = "Find flights from LCA to ATH and suggest hotels for 2 nights."
        st.rerun()
    if st.button("🏙️ LCA to LHR, weekend trip", use_container_width=True):
        st.session_state.current_query = "Find flights from LCA to LHR for a weekend trip."
        st.rerun()
    if st.button("🏨 ATH to Paris, center hotels", use_container_width=True):
        st.session_state.current_query = "Find flights from ATH to CDG and suggest hotels near the Eiffel Tower."
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# Process execution
if getattr(st.session_state, 'run_query', None):
    query_to_run = st.session_state.run_query
    st.session_state.run_query = None  # reset
    
    if not query_to_run.strip():
        st.warning("Please enter a travel query.")
    else:
        status_box = st.empty()
        with status_box.container():
            st.markdown("<div class='glass-card' style='text-align:center;'>", unsafe_allow_html=True)
            with st.spinner("Initiating Multi-Agent Workflow..."):
                result = run_travel_agent(query_to_run, thread_id)
                st.session_state['agent_result'] = result
            st.markdown("</div>", unsafe_allow_html=True)
        status_box.empty()

# Results Render
if 'agent_result' in st.session_state:
    res = st.session_state['agent_result']
    
    if res["success"]:
        # --- TOP HEADER: Agent Progress & Copy Button ---
        col_prog, col_copy = st.columns([3, 1])
        with col_prog:
            st.markdown("<h3 style='margin:0;'>📡 Execution Log</h3>", unsafe_allow_html=True)
            steps_html = " ".join([f"<span class='badge badge-info' style='margin-right:8px;'>✓ {s}</span>" for s in res["agent_steps"]])
            st.markdown(f"<div style='margin-top:10px;'>{steps_html}</div>", unsafe_allow_html=True)
            
        with col_copy:
            copy_text = f"SkyRunner Travel Plan\\n\\nUser Query:\\n{res.get('user_query', '')}\\n\\nFlight Results:\\n{res.get('flight_results', '')}\\n\\nHotel Research:\\n{res.get('hotel_results', '')}\\n\\nFinal Itinerary:\\n{res.get('itinerary', '')}\\n\\nTotal LLM Calls: {res.get('llm_calls', 0)}\\nThread ID: {res.get('thread_id', '')}"
            safe_text = json.dumps(copy_text.replace('\\n', '\n'))
            copy_html = f"""
            <button id="copyBtn" style="
                background-color: #4ECDC4; color: #1A1C23; border: none; border-radius: 8px;
                padding: 12px 16px; font-weight: 600; font-family: 'Inter', sans-serif; cursor: pointer;
                width: 100%; transition: all 0.2s ease; box-shadow: 0 4px 15px rgba(78, 205, 196, 0.2);
                margin-top:5px;
            ">📋 Copy Full Plan</button>
            <script>
            const btn = document.getElementById("copyBtn");
            btn.addEventListener("click", () => {{
                const copyStr = {safe_text};
                const fallback = () => {{
                    const ta = document.createElement("textarea"); ta.value = copyStr;
                    ta.style.position = "fixed"; ta.style.left = "-9999px"; document.body.appendChild(ta);
                    ta.select(); document.execCommand("copy"); ta.remove(); success();
                }};
                const success = () => {{
                    btn.innerText = "✅ Plan Copied!"; btn.style.background = "#10B981"; btn.style.color = "white";
                    setTimeout(() => {{ btn.innerText = "📋 Copy Full Plan"; btn.style.background = "#4ECDC4"; btn.style.color = "#1A1C23"; }}, 2500);
                }};
                if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(copyStr).then(success).catch(fallback);
                else fallback();
            }});
            </script>
            """
            components.html(copy_html, height=60)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- CARDS ---
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3>📝 AI Generated Itinerary</h3>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:1.05rem; line-height:1.6; color:#E2E8F0;'>{res['itinerary']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        col_f, col_h = st.columns(2)
        
        with col_f:
            st.markdown("<div class='glass-card' style='height:100%;'>", unsafe_allow_html=True)
            st.markdown("<h4>🛫 Flight Intelligence</h4>", unsafe_allow_html=True)
            flight_data = parse_flight_results(res["flight_results"])
            if flight_data:
                for f in flight_data:
                    st.markdown(f"""
                    <div class='data-card'>
                        <div class='data-card-title'>{f.get('Airline', 'Unknown')} - {f.get('Flight', '')}</div>
                        <div class='data-card-text'><b>Route:</b> {f.get('From', '')} → {f.get('To', '')}</div>
                        <div class='data-card-text'><b>Status:</b> <span style='color:#4ECDC4;'>{f.get('Status', 'Unknown').upper()}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<div class='data-card' style='border-left-color:#F59E0B;'>No structured flight data available.</div>", unsafe_allow_html=True)
                with st.expander("Raw Flight Output"):
                    st.text(res["flight_results"])
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_h:
            st.markdown("<div class='glass-card' style='height:100%;'>", unsafe_allow_html=True)
            st.markdown("<h4>🏨 Hotel Intelligence</h4>", unsafe_allow_html=True)
            hotel_data = parse_hotel_results(res["hotel_results"])
            if hotel_data:
                for h in hotel_data:
                    st.markdown(f"""
                    <div class='data-card'>
                        <div class='data-card-title'>{h.get('Title', 'Unknown Property')}</div>
                        <div class='data-card-text'><a href="{h.get('URL', '#')}" target="_blank" style="color:#4ECDC4;">View Source ↗</a></div>
                        <div class='data-card-text' style='margin-top:8px; font-size:0.85rem; opacity:0.8;'>{h.get('Content', '')[:150]}...</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<div class='data-card' style='border-left-color:#F59E0B;'>No structured hotel data available.</div>", unsafe_allow_html=True)
                with st.expander("Raw Hotel Output"):
                    st.text(res["hotel_results"])
            st.markdown("</div>", unsafe_allow_html=True)
            
    else:
        st.markdown(f"""
        <div class='glass-card' style='border-color:#EF4444;'>
            <h3 style='color:#F87171;'>❌ Mission Failed</h3>
            <p>{res.get('final_answer')}</p>
        </div>
        """, unsafe_allow_html=True)
