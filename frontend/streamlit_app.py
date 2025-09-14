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
    page_icon="��",
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
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {}

def display_agent_tag(agent_name: str):
    """Display agent tag with appropriate styling"""
    if agent_name.lower() == "planner":
        st.markdown(f'<span class="agent-tag planner-tag">�� {agent_name}</span>', unsafe_allow_html=True)
    elif agent_name.lower() == "researcher":
        st.markdown(f'<span class="agent-tag researcher-tag">�� {agent_name}</span>', unsafe_allow_html=True)
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
        st.subheader("�� Quiz Created")
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
        
        if result.get("key_takeaways"):
            st.subheader("�� Key Takeaways")
            for takeaway in result["key_takeaways"]:
                st.write(f"• {takeaway}")
        
        if result.get("action_items"):
            st.subheader("✅ Action Items")
            for item in result["action_items"]:
                st.write(f"• {item}")
    
    else:
        st.subheader("📝 Result")
        st.write(result.get("content", str(result)))

def main():
    st.title("📚 StudyBuddy AI Agent System")
    st.markdown("Multi-Agent Study Planning and Execution Platform")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Create Plan", "View Plans", "Execute Steps", "View Logs"])
    
    if page == "Create Plan":
        create_plan_page()
    elif page == "View Plans":
        view_plans_page()
    elif page == "Execute Steps":
        execute_steps_page()
    elif page == "View Logs":
        view_logs_page()

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
                    st.subheader("�� Generated Study Plan")
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
