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
    .step-card {
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f9f9f9;
    }
    .completed-step { border-left: 4px solid #4caf50; }
    .running-step { border-left: 4px solid #ff9800; }
    .failed-step { border-left: 4px solid #f44336; }
    .pending-step { border-left: 4px solid #9e9e9e; }
</style>
""", unsafe_allow_html=True)

def make_api_request(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Make API request with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        # Add timeout to prevent hanging
        timeout = 30
        
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
    page = st.sidebar.selectbox("Choose a page", ["Create Plan", "View Plans", "Execute Steps", "View Logs", "Database Management"])
    
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
                    st.write(f"**Description:** {plan.get('description', '')}")
                    
                    # Display steps
                    st.subheader("📝 Study Steps")
                    for i, step in enumerate(plan.get("steps", []), 1):
                        with st.expander(f"Step {i}: {step.get('title', 'Untitled Step')}"):
                            st.write(f"**Description:** {step.get('description', '')}")
                            st.write(f"**Tool:** {step.get('tool', 'LLM')}")
                            st.write(f"**Expected Output:** {step.get('expected_output', '')}")
                            st.write(f"**Step ID:** `{step.get('id', '')}`")
                    
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
        st.subheader(f"📋 Plan: {plan.get('title', 'Untitled Plan')}")

        # Prepare a place to render a focused result section below the table
        if 'selected_result' not in st.session_state:
            st.session_state.selected_result = None
            st.session_state.selected_result_title = None
        
        # Display steps with execution buttons
        for i, step in enumerate(plan.get("steps", []), 1):
            status = step.get("status", "pending")
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**Step {i}:** {step.get('title', 'Untitled Step')}")
                st.write(f"*{step.get('description', '')}*")
                st.write(f"**Tool:** {step.get('tool', 'LLM')} | **Status:** {status.title()}")
            
            with col2:
                if status == "pending":
                    if st.button(f"Execute", key=f"exec_{step['id']}"):
                        with st.spinner(f"Executing step {i}..."):
                            exec_response = make_api_request("/api/execute_step", "POST", {"step_id": step["id"]})
                            
                            if exec_response:
                                st.success(f"✅ Step {i} executed successfully!")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to execute step {i}")
                elif status == "running":
                    st.info("🔄 Running...")
                elif status == "completed":
                    st.success("✅ Completed")
                elif status == "failed":
                    st.error("❌ Failed")
            
            with col3:
                if status in ["completed", "failed"] and step.get("result"):
                    if st.button(f"View Result", key=f"view_{step['id']}"):
                        # Store selection to show centered below the plan table
                        st.session_state.selected_result = step["result"]
                        st.session_state.selected_result_title = f"Step {i} Result"
                        st.rerun()
            
            st.divider()

        # Centered result panel below the plan table
        if st.session_state.selected_result:
            st.markdown("---")
            _, center_col, _ = st.columns([1, 2, 1])
            with center_col:
                st.subheader(st.session_state.selected_result_title or "Step Result")
                display_step_result(st.session_state.selected_result)
                if st.button("Close Result"):
                    st.session_state.selected_result = None
                    st.session_state.selected_result_title = None
                    st.rerun()

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