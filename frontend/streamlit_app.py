import streamlit as st
import requests
import json
import pandas as pd
import zipfile
import os
from datetime import datetime
from typing import Dict, Any, List

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="StudyBuddy AI Agent",
    page_icon="📘",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    /* Import beautiful fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Global font styling */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 400;
        line-height: 1.6;
        letter-spacing: -0.01em;
    }
    
    /* Headers with better typography */
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        letter-spacing: -0.025em;
        line-height: 1.2;
    }
    
    /* Code elements */
    code, pre, .stCode {
        font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
        font-weight: 400;
    }
    
    /* Soft pastel page background */
    .stApp { 
        background-color: #f3fbf5; 
        font-family: 'Inter', sans-serif;
    }
    .agent-tag {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        font-weight: bold;
        margin: 0.125rem;
    }
    .planner-tag { background-color: #e3f2fd; color: #1976d2; }
    .researcher-tag { background-color: #f3e5f5; color: #7b1fa2; }
    .executor-tag { background-color: #e8f5e8; color: #388e3c; }
    
    /* Enhanced step cards with better hover effects and typography */
    .step-card {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        background-color: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        font-family: 'Inter', sans-serif;
    }
    .step-card:hover {
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        transform: translateY(-2px);
        border-color: #22c55e;
    }
    .step-card:hover::before {
        opacity: 1;
    }
    .step-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.02) 0%, rgba(34, 197, 94, 0.08) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
        pointer-events: none;
    }
    
    /* Step card content wrapper */
    .step-content {
        position: relative;
        z-index: 1;
    }
    
    /* Step title styling */
    .step-title {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.1rem;
        color: #1f2937;
        line-height: 1.3;
        letter-spacing: -0.02em;
    }
    
    /* Step description styling */
    .step-description {
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        color: #4b5563;
        font-style: italic;
        line-height: 1.5;
        margin: 0.5rem 0 1rem 0;
    }
    
    /* Step badges */
    .step-badge {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 500;
        color: #6b7280;
        background: #f3f4f6;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        letter-spacing: 0.01em;
    }
    
    /* Status-based border styling with enhanced hover effects */
    .completed-step { 
        border-left: 5px solid #22c55e; 
        background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
    }
    .completed-step:hover {
        border-left-width: 8px;
        box-shadow: 0 8px 25px rgba(34, 197, 94, 0.2);
    }
    .running-step { 
        border-left: 5px solid #f59e0b; 
        background: linear-gradient(135deg, #fffbeb 0%, #ffffff 100%);
    }
    .running-step:hover {
        border-left-width: 8px;
        box-shadow: 0 8px 25px rgba(245, 158, 11, 0.2);
    }
    .failed-step { 
        border-left: 5px solid #ef4444; 
        background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
    }
    .failed-step:hover {
        border-left-width: 8px;
        box-shadow: 0 8px 25px rgba(239, 68, 68, 0.2);
    }
    .pending-step { 
        border-left: 5px solid #6b7280; 
        background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
    }
    .pending-step:hover {
        border-left-width: 8px;
        box-shadow: 0 8px 25px rgba(107, 114, 128, 0.2);
    }
    
    /* Enhanced button styling with better hover effects */
    .stButton>button { 
        border-radius: 8px; 
        padding: 0.5rem 1rem; 
        border: 1px solid #e5e7eb; 
        background: #f8fafc; 
        color: #111827;
        font-weight: 500;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stButton>button:hover { 
        border-color: #22c55e; 
        background: #f0fdf4; 
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.15);
    }
    .stButton>button:active {
        transform: translateY(0);
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Enhanced primary button styling */
    .stButton>button[kind="primary"] {
        background: #22c55e;
        color: white;
        border-color: #22c55e;
        box-shadow: 0 2px 8px rgba(34, 197, 94, 0.2);
    }
    .stButton>button[kind="primary"]:hover {
        background: #16a34a;
        border-color: #16a34a;
        box-shadow: 0 6px 20px rgba(34, 197, 94, 0.3);
        transform: translateY(-2px);
    }
    .stButton>button[kind="primary"]:active {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.25);
    }
    
    /* Compact result card with just heading */
    .result-card { 
        border: 1px solid #e5e7eb; 
        border-radius: 12px; 
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); 
        padding: 1rem 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin: 0.75rem 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        font-family: 'Inter', sans-serif;
        min-height: auto;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .result-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        border-color: #22c55e;
    }
    .result-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.02) 0%, rgba(34, 197, 94, 0.05) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
        pointer-events: none;
        z-index: 0;
    }
    .result-card:hover::before {
        opacity: 1;
    }
    
    /* Compact result card header - now just text inside */
    .result-card-header {
        position: relative;
        z-index: 2;
        text-align: center;
        width: 100%;
    }
    
    /* Remove the separate content section for compactness */
    .result-card-title {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.1rem;
        color: #1f2937;
        margin: 0;
        letter-spacing: -0.02em;
        line-height: 1.3;
    }
    
    /* Ensure content is above the overlay */
    .result-card > * {
        position: relative;
        z-index: 1;
    }
    
    /* Soft cards */
    .soft-card { 
        background: #ffffff; 
        border: 1px solid #e5e7eb; 
        border-radius: 12px; 
        padding: 1rem; 
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }
    .soft-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transform: translateY(-1px);
    }
    
    /* Enhanced checkbox styling */
    .stCheckbox > label {
        transition: all 0.2s ease;
    }
    .stCheckbox > label:hover {
        transform: scale(1.05);
    }
    
    /* Enhanced selectbox and other inputs */
    .stSelectbox > div > div {
        transition: all 0.2s ease;
    }
    .stSelectbox > div > div:hover {
        border-color: #22c55e;
        box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.1);
    }
    
    /* Progress and status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* Execution controls styling */
    .execution-controls {
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Step title styling */
    .step-title {
        color: #1f2937;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .step-description {
        color: #6b7280;
        font-style: italic;
        margin-bottom: 0.5rem;
    }
    
    .step-meta {
        color: #374151;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

def make_api_request(endpoint: str, method: str = "GET", data: Dict = None, timeout_seconds: int = 30) -> Dict:
    """Make API request with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        # Add timeout to prevent hanging
        timeout = timeout_seconds
        
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=timeout)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as e:
        st.error(f"❌ Connection Error: Cannot connect to backend at {API_BASE_URL}")
        st.info("💡 Make sure the backend server is running on http://localhost:8000")
        return {}
    except requests.exceptions.Timeout as e:
        st.error(f"⏰ Timeout Error: Request took too long to complete")
        return {}
    except requests.exceptions.HTTPError as e:
        st.error(f"🚫 HTTP Error {response.status_code}: {str(e)}")
        try:
            error_detail = response.json()
            st.error(f"Details: {error_detail}")
        except:
            st.error(f"Response: {response.text}")
        return {}
    except requests.exceptions.RequestException as e:
        st.error(f"🔧 API Error: {str(e)}")
        return {}
    except Exception as e:
        st.error(f"💥 Unexpected Error: {str(e)}")
        return {}

def display_agent_tag(agent_name: str):
    """Display agent tag with appropriate styling"""
    if agent_name.lower() == "planner":
        st.markdown(f'<span class="agent-tag planner-tag">🧠 {agent_name}</span>', unsafe_allow_html=True)
    elif agent_name.lower() == "researcher":
        st.markdown(f'<span class="agent-tag researcher-tag">🔎 {agent_name}</span>', unsafe_allow_html=True)
    elif agent_name.lower() == "executor":
        st.markdown(f'<span class="agent-tag executor-tag">⚡ {agent_name}</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="agent-tag">{agent_name}</span>', unsafe_allow_html=True)

def display_step_result(result: Dict[str, Any]):
    """Display step execution result"""
    if not result:
        return
    
    result_type = result.get("type", "unknown")
    
    if result_type == "flashcards":
        st.subheader("📚 Flashcards Created")
        flashcards = result.get("flashcards", [])
        for i, card in enumerate(flashcards, 1):
            with st.expander(f"Card {i}: {card.get('question', 'No question')[:50]}..."):
                st.write(f"**Question:** {card.get('question', '')}")
                st.write(f"**Answer:** {card.get('answer', '')}")
                if card.get('category'):
                    st.write(f"**Category:** {card['category']}")
    
    elif result_type == "quiz":
        st.subheader("📝 Quiz Created")
        quiz = result.get("quiz", [])
        for i, question in enumerate(quiz, 1):
            with st.expander(f"Question {i}"):
                st.write(f"**Question:** {question.get('question', '')}")
                options = question.get('options', [])
                for j, option in enumerate(options):
                    st.write(f"{chr(65+j)}. {option}")
                st.write(f"**Correct Answer:** {question.get('correct_answer', '')}")
                if question.get('explanation'):
                    st.write(f"**Explanation:** {question['explanation']}")
    
    elif result_type == "study_guide":
        st.subheader("📖 Study Guide")
        st.write(result.get("content", ""))

        # Consistent headings and bullets for lists
        if result.get("key_takeaways"):
            st.subheader("✅ Key Takeaways")
            st.markdown("\n".join([f"- {t}" for t in result["key_takeaways"]]))

        if result.get("action_items"):
            st.subheader("✅ Action Items")
            st.markdown("\n".join([f"- {a}" for a in result["action_items"]]))
    
    else:
        st.subheader("📝 Result")
        st.write(result.get("content", str(result)))

def try_build_plan_pdf_bytes(plan: Dict[str, Any]) -> bytes:
    """Build a simple PDF from plan data. Uses FPDF if available, else returns empty bytes."""
    try:
        from fpdf import FPDF  # type: ignore
    except Exception:
        return b""

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    title = plan.get("title", "Study Plan")
    pdf.cell(0, 10, txt=title, ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", size=12)
    desc = plan.get("description", "")
    if desc:
        for line in desc.split("\n"):
            pdf.multi_cell(0, 7, txt=line)
        pdf.ln(3)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, txt="Steps", ln=True)
    pdf.set_font("Arial", size=12)
    for idx, step in enumerate(plan.get("steps", []), 1):
        pdf.ln(2)
        pdf.set_font("Arial", "B", 12)
        pdf.multi_cell(0, 7, txt=f"Step {idx}: {step.get('title', 'Untitled Step')}")
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 6, txt=f"Description: {step.get('description', '')}")
        pdf.multi_cell(0, 6, txt=f"Tool: {step.get('tool', 'LLM')} | Expected: {step.get('expected_output', '')}")
        pdf.multi_cell(0, 6, txt=f"ID: {step.get('id', '')}")

    return pdf.output(dest='S').encode('latin1')

def main():
    st.title("📚 StudyBuddy AI Agent System")
    st.markdown("Multi-Agent Study Planning and Execution Platform")
    
    # Connection status in sidebar
    st.sidebar.title("🔗 System Status")
    if test_connection():
        st.sidebar.success("✅ Backend Connected")
    else:
        st.sidebar.error("❌ Backend Disconnected")
        st.sidebar.info("Please start the backend server")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Create Plan", "View Plans", "Execute Steps", "Study History", "View Logs", "Database Management"])
    
    # Add current plan info in sidebar
    if hasattr(st.session_state, 'current_plan_id'):
        st.sidebar.title("📋 Current Plan")
        st.sidebar.info(f"Plan ID: {st.session_state.current_plan_id}")
        if st.sidebar.button("Clear Current Plan"):
            del st.session_state.current_plan_id
            st.rerun()
    
    if page == "Create Plan":
        create_plan_page()
    elif page == "View Plans":
        view_plans_page()
    elif page == "Execute Steps":
        execute_steps_page()
    elif page == "Study History":
        study_history_page()
    elif page == "View Logs":
        view_logs_page()
    elif page == "Database Management":
        database_management_page()

def create_plan_page():
    st.header("🎯 Create New Study Plan")
    
    with st.form("create_plan_form"):
        goal = st.text_area(
            "What do you want to study?",
            placeholder="e.g., Learn Python programming fundamentals, Prepare for calculus exam, Master machine learning concepts...",
            height=100
        )
        
        submitted = st.form_submit_button("Generate Study Plan", type="primary")
        
        if submitted and goal:
            st.session_state.form_submitted = True
            st.session_state.user_goal = goal
    
    if hasattr(st.session_state, 'form_submitted') and st.session_state.form_submitted and hasattr(st.session_state, 'user_goal'):
        # Reset the form submission flag
        st.session_state.form_submitted = False
        goal = st.session_state.user_goal
        with st.spinner("🤖 Planner Agent is creating your study plan..."):
            response = make_api_request("/api/plan", "POST", {"goal": goal})
            
            if response:
                st.success("✅ Study plan created successfully!")
                
                # Store plan_id in session state
                st.session_state.current_plan_id = response["plan_id"]
                
                # Display the plan
                st.subheader("📄 Generated Study Plan")
                plan = response["plan"]
                
                st.write(f"**Title:** {plan.get('title', 'Untitled Plan')}")
                st.subheader("🧭 Overall Summary")
                
                if plan.get("overview"):
                    st.info(plan["overview"])
                
                if plan.get("description"):
                    st.write(plan["description"])
                
                # Display step options for user selection
                st.subheader("📋 Generated Study Steps")
                st.write("Select which steps you want to include in your study plan:")
                
                # Initialize step selection state
                if 'plan_step_selection' not in st.session_state:
                    st.session_state.plan_step_selection = {}
                
                plan_id = response["plan_id"]
                
                for i, step in enumerate(plan.get("steps", []), 1):
                    col1, col2 = st.columns([1, 10])
                    
                    with col1:
                        selected = st.checkbox(
                            "",
                            value=True,  # Default all selected
                            key=f"plan_step_{plan_id}_{step.get('id', i)}"
                        )
                        st.session_state.plan_step_selection[step.get('id', str(i))] = selected
                    
                    with col2:
                        st.write(f"**Step {i}: {step.get('title', 'Untitled Step')}**")
                        st.write(f"*{step.get('description', '')}*")
                        st.write(f"**Tool:** {step.get('tool', 'LLM')}")
                    
                    st.markdown("---")
                
                # Description
                st.write(plan.get('description', ''))
                
                # Display steps
                st.subheader("📝 Study Steps")
                tool_to_icon = {"RAG": "📚", "LLM": "🧠", "FLASHCARDS": "🗂️", "QUIZ": "🎤"}
                for i, step in enumerate(plan.get("steps", []), 1):
                    icon = tool_to_icon.get(step.get("tool", "LLM"), "🧠")
                    with st.expander(f"{icon} Step {i}: {step.get('title', 'Untitled Step')}"):
                        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
                        st.write(f"**Description:** {step.get('description', '')}")
                        st.write(f"**Tool:** {step.get('tool', 'LLM')}")
                        st.write(f"**Expected Output:** {step.get('expected_output', '')}")
                        st.write(f"**Step ID:** `{step.get('id', '')}`")
                        st.markdown('</div>', unsafe_allow_html=True)
                
                # Download plan buttons
                pdf_bytes = try_build_plan_pdf_bytes(plan)
                dcol1, dcol2 = st.columns(2)
                with dcol1:
                    st.download_button(
                        label="⬇️ Download Plan (JSON)",
                        file_name=f"study_plan_{plan_id}.json",
                        mime="application/json",
                        data=json.dumps(plan, indent=2)
                    )
                with dcol2:
                    if pdf_bytes:
                        st.download_button(
                            label="⬇️ Download Plan (PDF)",
                            file_name=f"study_plan_{plan_id}.pdf",
                            mime="application/pdf",
                            data=pdf_bytes
                        )
                    else:
                        st.info("Install 'fpdf' to enable PDF download: pip install fpdf")

                # Navigation to execute steps
                st.info("💡 Go to 'Execute Steps' page to run individual steps or execute the entire plan.")

def view_plans_page():
    st.header("📋 View Study Plans")
    
    # For demo purposes, we'll show a placeholder
    # In a real implementation, you'd fetch all plans from the API
    st.info("📝 This page would show all your study plans. For now, use the 'Create Plan' page to generate a new plan.")
    
    if hasattr(st.session_state, 'current_plan_id'):
        st.subheader("Current Plan")
        plan_id = st.session_state.current_plan_id
        
        with st.spinner("Loading plan..."):
            response = make_api_request(f"/api/plan/{plan_id}")
            
            if response:
                plan = response["plan_json"]
                
                st.write(f"**Goal:** {response['goal']}")
                st.write(f"**Title:** {plan.get('title', 'Untitled Plan')}")
                st.write(f"**Description:** {plan.get('description', '')}")

                # Download plan buttons
                pdf_bytes = try_build_plan_pdf_bytes(plan)
                d1, d2 = st.columns(2)
                with d1:
                    st.download_button(
                        label="⬇️ Download Plan (JSON)",
                        file_name=f"study_plan_{plan_id}.json",
                        mime="application/json",
                        data=json.dumps(plan, indent=2)
                    )
                with d2:
                    if pdf_bytes:
                        st.download_button(
                            label="⬇️ Download Plan (PDF)",
                            file_name=f"study_plan_{plan_id}.pdf",
                            mime="application/pdf",
                            data=pdf_bytes
                        )
                    else:
                        st.info("Install 'fpdf' to enable PDF download: pip install fpdf")
                
                # Display steps with status
                st.subheader("📝 Study Steps")
                for i, step in enumerate(plan.get("steps", []), 1):
                    status = step.get("status", "pending")
                    
                    # Determine CSS class based on status
                    css_class = f"{status}-step"
                    
                    with st.expander(f"Step {i}: {step.get('title', 'Untitled Step')} - {status.title()}"):
                        st.markdown(f'<div class="step-card {css_class}">', unsafe_allow_html=True)
                        st.write(f"**Description:** {step.get('description', '')}")
                        st.write(f"**Tool:** {step.get('tool', 'LLM')}")
                        st.write(f"**Status:** {status.title()}")
                        st.write(f"**Step ID:** `{step.get('id', '')}`")
                        
                        if step.get("result"):
                            st.write("**Result:**")
                            display_step_result(step["result"])
                        
                        st.markdown('</div>', unsafe_allow_html=True)

def execute_steps_page():
    st.header("⚡ Execute Study Steps")
    
    if not hasattr(st.session_state, 'current_plan_id'):
        st.warning("⚠️ No plan selected. Please create a plan first.")
        return
    
    plan_id = st.session_state.current_plan_id
    
    with st.spinner("Loading plan..."):
        response = make_api_request(f"/api/plan/{plan_id}")
        
        if not response:
            st.error("❌ Failed to load plan. Please try again.")
            return
        
        plan = response["plan_json"]
        
        # Display plan header with overall summary
        st.subheader(f"📋 Plan: {plan.get('title', 'Untitled Plan')}")
        
        # Show overview/description if available
        if plan.get("overview"):
            st.info(f"**Overview:** {plan['overview']}")
        
        if plan.get("description"):
            st.write(f"**Description:** {plan['description']}")
        
        st.markdown("---")

        # Initialize session state for results and step selection
        if 'selected_results' not in st.session_state:
            st.session_state.selected_results = []  # Changed to list for multiple results
        
        if 'selected_steps' not in st.session_state:
            st.session_state.selected_steps = {}

        # Enhanced batch controls
        st.subheader("🔧 Execution Controls")
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            select_all = st.button("☑️ Select All")
        with col2:
            deselect_all = st.button("☐ Deselect All")
        with col3:
            run_selected_clicked = st.button("▶️ Run Selected", type="primary")
        with col4:
            run_all_clicked = st.button("⏭️ Run All Pending")

        # Handle select/deselect all
        if select_all:
            for step in plan.get("steps", []):
                st.session_state.selected_steps[step["id"]] = True
            st.rerun()
        
        if deselect_all:
            for step in plan.get("steps", []):
                st.session_state.selected_steps[step["id"]] = False
            st.rerun()

        st.markdown("---")
        st.subheader("📝 Study Steps")

        # Display steps with improved UI
        for i, step in enumerate(plan.get("steps", []), 1):
            status = step.get("status", "pending")
            step_id = step["id"]
            
            # Status-based styling
            if status == "completed":
                card_class = "completed-step"
                status_emoji = "✅"
            elif status == "running":
                card_class = "running-step"
                status_emoji = "🔄"
            elif status == "failed":
                card_class = "failed-step"
                status_emoji = "❌"
            else:
                card_class = "pending-step"
                status_emoji = "⏳"

            # Step card container with proper content structure
            with st.container():
                st.markdown(f'''
                <div class="step-card {card_class}">
                    <div class="step-content">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
                            <h4 style="margin: 0; color: #1f2937; font-size: 1.1rem;">
                                {status_emoji} Step {i}: {step.get('title', 'Untitled Step')}
                            </h4>
                            <div style="display: flex; gap: 0.5rem; align-items: center;">
                                <span style="font-size: 0.85rem; color: #6b7280; background: #f3f4f6; padding: 0.25rem 0.5rem; border-radius: 4px;">
                                    {step.get('tool', 'LLM')}
                                </span>
                                <span style="font-size: 0.85rem; color: #6b7280; background: #f3f4f6; padding: 0.25rem 0.5rem; border-radius: 4px;">
                                    {status.title()}
                                </span>
                            </div>
                        </div>
                        <p style="margin: 0 0 1rem 0; color: #4b5563; font-style: italic; line-height: 1.5;">
                            {step.get('description', '')}
                        </p>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                # Action buttons row (outside the card for proper Streamlit interaction)
                col1, col2, col3, col4 = st.columns([6, 1, 1, 1])

                with col2:
                    # Selection checkbox
                    checked = st.checkbox(
                        "Select", 
                        key=f"sel_{step_id}", 
                        value=st.session_state.selected_steps.get(step_id, False)
                    )
                    st.session_state.selected_steps[step_id] = checked

                with col3:
                    # Execute button with auto-display
                    if status == "pending":
                        if st.button(f"Execute", key=f"exec_{step_id}", type="primary"):
                            with st.spinner(f"Executing step {i}..."):
                                exec_response = make_api_request(
                                    "/api/execute_step",
                                    "POST",
                                    {"step_id": step_id},
                                    timeout_seconds=120,
                                )
                                if exec_response:
                                    # Add result to the list for display
                                    result_data = {
                                        'result': exec_response.get("result"),
                                        'title': f"Executed Step {i}",
                                        'step_id': step_id
                                    }
                                    st.session_state.selected_results.append(result_data)
                                    st.success(f"✅ Step {i} executed successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to execute step {i}")
                    elif status == "running":
                        st.info("🔄 Running...")
                    elif status == "completed":
                        st.success("✅ Done")
                    elif status == "failed":
                        st.error("❌ Failed")

                with col4:
                    # View result button
                    if status in ["completed", "failed"] and step.get("result"):
                        if st.button(f"View", key=f"view_{step_id}"):
                            result_data = {
                                'result': step["result"],
                                'title': f"Step {i}",
                                'step_id': step_id
                            }
                            # Clear previous results and add this one
                            st.session_state.selected_results = [result_data]
                            st.rerun()

        # Enhanced batch execution with progress tracking
        if run_selected_clicked or run_all_clicked:
            steps_to_run = []
            
            # Determine which steps to run
            for step in plan.get("steps", []):
                if run_all_clicked and step.get("status", "pending") == "pending":
                    steps_to_run.append(step["id"])
                elif run_selected_clicked and st.session_state.selected_steps.get(step["id"], False):
                    if step.get("status", "pending") == "pending":  # Only run pending steps
                        steps_to_run.append(step["id"])

            total = len(steps_to_run)
            if total == 0:
                st.info("ℹ️ No pending steps selected to run.")
            else:
                # Progress tracking
                progress_bar = st.progress(0)
                status_container = st.empty()
                results_container = st.empty()
                
                with st.spinner("Executing steps..."):
                    # Use bulk execution API
                    # Increase timeout for bulk execution as it can be long-running
                    bulk_response = make_api_request(
                        "/api/execute_steps_bulk",
                        "POST",
                        {"step_ids": steps_to_run},
                        timeout_seconds=300,
                    )
                    
                    if bulk_response:
                        executed = bulk_response.get("executed_steps", 0)
                        failed = bulk_response.get("failed_steps", 0)
                        
                        progress_bar.progress(100)
                        status_container.success(f"✅ Batch execution completed! {executed} successful, {failed} failed")
                        
                        # Store all results for display
                        results = bulk_response.get("results", [])
                        if results:
                            # Clear previous results and add all new ones
                            st.session_state.selected_results = []
                            for idx, result_item in enumerate(results):
                                if result_item.get("result"):
                                    result_data = {
                                        'result': result_item.get("result"),
                                        'title': f"Executed Step {idx + 1}",
                                        'step_id': result_item.get('step_id', f'bulk_{idx}')
                                    }
                                    st.session_state.selected_results.append(result_data)
                        
                        # Auto-refresh to show updated statuses
                        st.rerun()
                    else:
                        status_container.error("❌ Batch execution failed")

        # Download PDF button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📄 Download Plan as PDF", type="secondary"):
                try:
                    pdf_url = f"{API_BASE_URL}/api/download_plan_pdf/{plan_id}"
                    response = requests.get(pdf_url)
                    if response.status_code == 200:
                        st.download_button(
                            label="⬇️ Download PDF",
                            data=response.content,
                            file_name=f"study_plan_{plan_id}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error("Failed to generate PDF")
                except Exception as e:
                    st.error(f"Error downloading PDF: {str(e)}")

        # Enhanced result display section - showing all results
        if st.session_state.selected_results:
            st.markdown("---")
            st.markdown("### 📋 Step Results")
            
            # Header with clear all button
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(f"Showing {len(st.session_state.selected_results)} Result(s)")
            with col2:
                if st.button("✕ Clear All", key="clear_all_results"):
                    st.session_state.selected_results = []
                    st.rerun()
            
            # Display each result - compact cards with just headings
            for idx, result_data in enumerate(st.session_state.selected_results):
                # Create compact result card with heading and close button
                col1, col2 = st.columns([10, 1])
                
                with col1:
                    st.markdown(f'''
                    <div class="result-card">
                        <div class="result-card-header">
                            <h3 class="result-card-title">
                                {result_data.get('title', f"Result {idx + 1}")}
                            </h3>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with col2:
                    if st.button("✕", key=f"close_result_{idx}", help="Close this result"):
                        st.session_state.selected_results.pop(idx)
                        st.rerun()
                
                # Add separator between results (except for the last one)
                if idx < len(st.session_state.selected_results) - 1:
                    st.markdown("---")

def study_history_page():
    st.header("📖 Study History")
    st.markdown("Access your previous study plans, results, and progress")
    
    # Initialize history storage in session state
    if 'study_history' not in st.session_state:
        st.session_state.study_history = []
    
    # Add filter and search options
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search study topics", placeholder="e.g., Python, Machine Learning")
    
    with col2:
        date_filter = st.selectbox("📅 Filter by Date", ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days"])
    
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Get all plans from the database
    with st.spinner("Loading study history..."):
        response = make_api_request("/api/plans")
        
        if response and response.get("plans"):
            plans = response["plans"]
            
            # Filter plans based on search and date
            filtered_plans = []
            for plan in plans:
                # Search filter
                if search_term:
                    goal = plan.get("goal", "").lower()
                    title = plan.get("plan_json", {}).get("title", "").lower()
                    if search_term.lower() not in goal and search_term.lower() not in title:
                        continue
                
                # Date filter (this would need actual dates from the database)
                # For now, we'll show all plans
                filtered_plans.append(plan)
            
            if filtered_plans:
                st.subheader(f"📚 Found {len(filtered_plans)} Study Plan(s)")
                
                # Display plans in a nice grid
                for idx, plan in enumerate(filtered_plans):
                    plan_data = plan.get("plan_json", {})
                    goal = plan.get("goal", "No goal specified")
                    title = plan_data.get("title", "Untitled Plan")
                    description = plan_data.get("description", "No description")
                    steps = plan_data.get("steps", [])
                    plan_id = plan.get("id")
                    
                    # Calculate completion statistics
                    completed_steps = len([s for s in steps if s.get("status") == "completed"])
                    total_steps = len(steps)
                    completion_rate = (completed_steps / total_steps * 100) if total_steps > 0 else 0
                    
                    # Create expandable card for each plan
                    with st.expander(f"📋 {title} - {completion_rate:.0f}% Complete", expanded=False):
                        # Plan overview
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**🎯 Goal:** {goal}")
                            st.markdown(f"**📝 Description:** {description}")
                            st.markdown(f"**📊 Progress:** {completed_steps}/{total_steps} steps completed")
                            
                            # Progress bar
                            if total_steps > 0:
                                st.progress(completion_rate / 100)
                        
                        with col2:
                            st.markdown(f"**Plan ID:** `{plan_id}`")
                            
                            # Action buttons
                            if st.button(f"🔄 Resume Plan", key=f"resume_{plan_id}"):
                                st.session_state.current_plan_id = plan_id
                                st.success(f"✅ Resumed plan: {title}")
                                st.info("💡 Go to 'Execute Steps' page to continue working on this plan")
                        
                        # Show step results if any are completed
                        completed_step_results = [s for s in steps if s.get("status") == "completed" and s.get("result")]
                        
                        if completed_step_results:
                            st.markdown("---")
                            st.markdown("**📋 Previous Results:**")
                            
                            # Show results in a compact view
                            for step_idx, step in enumerate(completed_step_results[:3]):  # Show max 3 results
                                step_title = step.get("title", f"Step {step_idx + 1}")
                                step_result = step.get("result", {})
                                
                                with st.container():
                                    st.markdown(f"**{step_title}**")
                                    
                                    # Show a preview of the result
                                    if step_result.get("type") == "text":
                                        content = step_result.get("content", "")
                                        preview = content[:200] + "..." if len(content) > 200 else content
                                        st.markdown(f"*{preview}*")
                                    elif step_result.get("type") == "flashcards":
                                        flashcards = step_result.get("flashcards", [])
                                        st.markdown(f"*📚 {len(flashcards)} flashcard(s) created*")
                                    elif step_result.get("type") == "quiz":
                                        questions = step_result.get("questions", [])
                                        st.markdown(f"*❓ {len(questions)} quiz question(s) created*")
                                    else:
                                        st.markdown(f"*Result type: {step_result.get('type', 'unknown')}*")
                                    
                                    # Button to view full result
                                    if st.button(f"👁️ View Full Result", key=f"view_history_{plan_id}_{step_idx}"):
                                        result_data = {
                                            'result': step_result,
                                            'title': f"{title} - {step_title}",
                                            'step_id': step.get('id', f'history_{step_idx}')
                                        }
                                        
                                        # Add to current results for viewing
                                        if 'selected_results' not in st.session_state:
                                            st.session_state.selected_results = []
                                        st.session_state.selected_results.append(result_data)
                                        st.success(f"✅ Added {step_title} result to current view!")
                            
                            if len(completed_step_results) > 3:
                                st.info(f"📋 {len(completed_step_results) - 3} more completed results available")
                        
                        # Download options
                        st.markdown("---")
                        dcol1, dcol2 = st.columns(2)
                        
                        with dcol1:
                            st.download_button(
                                label="⬇️ Download Plan (JSON)",
                                file_name=f"study_plan_{plan_id}_history.json",
                                mime="application/json",
                                data=json.dumps(plan_data, indent=2),
                                key=f"download_json_{plan_id}"
                            )
                        
                        with dcol2:
                            # Generate PDF download (if available)
                            try:
                                from fpdf import FPDF
                                pdf_bytes = try_build_plan_pdf_bytes(plan_data)
                                if pdf_bytes:
                                    st.download_button(
                                        label="⬇️ Download Plan (PDF)",
                                        file_name=f"study_plan_{plan_id}_history.pdf",
                                        mime="application/pdf",
                                        data=pdf_bytes,
                                        key=f"download_pdf_{plan_id}"
                                    )
                                else:
                                    st.info("Install 'fpdf' for PDF download")
                            except ImportError:
                                st.info("Install 'fpdf' for PDF download")
            else:
                if search_term:
                    st.info(f"🔍 No study plans found matching '{search_term}'")
                else:
                    st.info("📝 No study plans found. Create your first plan!")
        else:
            st.error("❌ Failed to load study history")
    
    # Show current results if any
    if hasattr(st.session_state, 'selected_results') and st.session_state.selected_results:
        st.markdown("---")
        st.markdown("### 📋 Viewing Results")
        
        # Header with clear all button
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader(f"Showing {len(st.session_state.selected_results)} Result(s)")
        with col2:
            if st.button("✕ Clear All", key="clear_all_history_results"):
                st.session_state.selected_results = []
                st.rerun()
        
        # Display each result - compact cards with just headings
        for idx, result_data in enumerate(st.session_state.selected_results):
            # Create compact result card with heading and close button
            col1, col2 = st.columns([10, 1])
            
            with col1:
                st.markdown(f'''
                <div class="result-card">
                    <div class="result-card-header">
                        <h3 class="result-card-title">
                            {result_data.get('title', f"Result {idx + 1}")}
                        </h3>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                if st.button("✕", key=f"close_history_result_{idx}", help="Close this result"):
                    st.session_state.selected_results.pop(idx)
                    st.rerun()
            
            # Add separator between results (except for the last one)
            if idx < len(st.session_state.selected_results) - 1:
                st.markdown("---")

def view_logs_page():
    st.header("📊 System Logs")
    
    # Add filter options
    col1, col2 = st.columns(2)
    
    with col1:
        agent_filter = st.selectbox("Filter by Agent", ["All", "planner", "researcher", "executor"])
    
    with col2:
        if st.button("🔄 Refresh Logs"):
            st.rerun()
    
    # Fetch logs
    agent_param = None if agent_filter == "All" else agent_filter
    
    with st.spinner("Loading logs..."):
        response = make_api_request(f"/api/logs?agent={agent_param}" if agent_param else "/api/logs")
        
        if response and response.get("logs"):
            logs = response["logs"]
            
            if logs:
                st.subheader(f"📋 Logs ({len(logs)} entries)")
                
                for log in logs:
                    with st.expander(f"{log.get('timestamp', 'Unknown time')} - {log.get('agent', 'Unknown agent')}"):
                        st.write(f"**Agent:** {log.get('agent', 'Unknown')}")
                        st.write(f"**Action:** {log.get('action', 'Unknown')}")
                        st.write(f"**Timestamp:** {log.get('timestamp', 'Unknown')}")
                        
                        if log.get('details'):
                            st.write("**Details:**")
                            st.json(log['details'])
            else:
                st.info("📝 No logs found.")
        else:
            st.error("❌ Failed to load logs.")

def database_management_page():
    st.header("🗄️ Database Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Database Statistics")
        if st.button("🔄 Refresh Stats"):
            st.rerun()
        
        with st.spinner("Loading database statistics..."):
            response = make_api_request("/api/database_stats")
            
            if response and response.get("stats"):
                stats = response["stats"]
                st.metric("Plans", stats.get("plans", 0))
                st.metric("Steps", stats.get("steps", 0))
                st.metric("Logs", stats.get("logs", 0))
            else:
                st.error("❌ Failed to load database statistics")
    
    with col2:
        st.subheader("🧹 Database Actions")
        st.warning("⚠️ These actions will permanently delete data!")
        
        if st.button("🗑️ Clear All Data", type="secondary"):
            if st.session_state.get("confirm_clear", False):
                with st.spinner("Clearing database..."):
                    response = make_api_request("/api/clear_database", "POST")
                    
                    if response and response.get("status") == "success":
                        st.success("✅ Database cleared successfully!")
                        st.session_state.confirm_clear = False
                        st.rerun()
                    else:
                        st.error("❌ Failed to clear database")
            else:
                st.session_state.confirm_clear = True
                st.warning("⚠️ Click again to confirm clearing all data")
        
        if st.session_state.get("confirm_clear", False):
            if st.button("❌ Cancel"):
                st.session_state.confirm_clear = False
                st.rerun()

def test_connection():
    """Test connection to backend API"""
    st.subheader("🔗 Connection Test")
    
    with st.spinner("Testing connection to backend..."):
        try:
            response = make_api_request("/")
            if response and response.get("message"):
                st.success(f"✅ Backend connected successfully!")
                st.write(f"**Response:** {response['message']}")
                return True
            else:
                st.error("❌ Backend responded but with unexpected format")
                return False
        except Exception as e:
            st.error(f"❌ Failed to connect to backend: {str(e)}")
            st.info("💡 Make sure the backend server is running on http://localhost:8000")
            return False

if __name__ == "__main__":
    main()