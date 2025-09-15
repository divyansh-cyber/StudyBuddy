#!/usr/bin/env python3
"""
Test script for the new StudyBuddy features:
1. Auto-display results on execute
2. Bulk execution with progress tracking  
3. Step selection interface
4. PDF download functionality
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_api_connection():
    """Test if the API server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health")
        if response.status_code == 200:
            print("✅ API server is running")
            return True
        else:
            print(f"❌ API server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure backend is running on http://localhost:8000")
        return False

def test_plan_creation():
    """Test creating a study plan"""
    print("\n📝 Testing plan creation...")
    
    plan_request = {
        "goal": "Learn Python programming fundamentals with focus on data structures and algorithms"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/plan", json=plan_request, timeout=30)
        if response.status_code == 200:
            data = response.json()
            plan_id = data.get("plan_id")
            print(f"✅ Plan created successfully with ID: {plan_id}")
            
            # Display plan overview
            plan = data.get("plan", {})
            print(f"📋 Title: {plan.get('title', 'No title')}")
            print(f"📄 Overview: {plan.get('overview', 'No overview')}")
            print(f"📝 Steps: {len(plan.get('steps', []))}")
            
            return plan_id
        else:
            print(f"❌ Plan creation failed: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error creating plan: {e}")
        return None

def test_bulk_execution(plan_id):
    """Test bulk execution of steps"""
    if not plan_id:
        print("⚠️ No plan ID provided, skipping bulk execution test")
        return
    
    print(f"\n⚡ Testing bulk execution for plan {plan_id}...")
    
    # First get the plan to see available steps
    try:
        response = requests.get(f"{API_BASE_URL}/api/plan/{plan_id}")
        if response.status_code != 200:
            print(f"❌ Failed to get plan: {response.status_code}")
            return
        
        plan_data = response.json()
        steps = plan_data["plan_json"]["steps"]
        
        # Get step IDs for pending steps
        pending_steps = [step["id"] for step in steps if step.get("status", "pending") == "pending"]
        
        if not pending_steps:
            print("ℹ️ No pending steps to execute")
            return
        
        print(f"🔄 Found {len(pending_steps)} pending steps")
        
        # Test bulk execution with first 2 steps
        test_steps = pending_steps[:2] if len(pending_steps) >= 2 else pending_steps
        
        bulk_request = {"step_ids": test_steps}
        
        print(f"🚀 Executing {len(test_steps)} steps in bulk...")
        response = requests.post(f"{API_BASE_URL}/api/execute_steps_bulk", json=bulk_request, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Bulk execution completed:")
            print(f"   - Executed: {result.get('executed_steps', 0)}")
            print(f"   - Failed: {result.get('failed_steps', 0)}")
            
            # Show results summary
            for i, res in enumerate(result.get('results', [])[:2], 1):
                print(f"   Step {i}: {res.get('status', 'unknown')}")
        else:
            print(f"❌ Bulk execution failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error in bulk execution: {e}")

def test_pdf_generation(plan_id):
    """Test PDF generation"""
    if not plan_id:
        print("⚠️ No plan ID provided, skipping PDF test")
        return
    
    print(f"\n📄 Testing PDF generation for plan {plan_id}...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/download_plan_pdf/{plan_id}", timeout=30)
        
        if response.status_code == 200:
            # Save PDF to test file
            with open(f"test_plan_{plan_id}.pdf", "wb") as f:
                f.write(response.content)
            print(f"✅ PDF generated successfully and saved as test_plan_{plan_id}.pdf")
            print(f"📏 PDF size: {len(response.content)} bytes")
        else:
            print(f"❌ PDF generation failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")

def test_single_step_execution(plan_id):
    """Test single step execution with auto-display"""
    if not plan_id:
        print("⚠️ No plan ID provided, skipping single step test")
        return
    
    print(f"\n🎯 Testing single step execution for plan {plan_id}...")
    
    try:
        # Get plan steps
        response = requests.get(f"{API_BASE_URL}/api/plan/{plan_id}")
        if response.status_code != 200:
            print(f"❌ Failed to get plan: {response.status_code}")
            return
        
        plan_data = response.json()
        steps = plan_data["plan_json"]["steps"]
        
        # Find first pending step
        pending_step = None
        for step in steps:
            if step.get("status", "pending") == "pending":
                pending_step = step
                break
        
        if not pending_step:
            print("ℹ️ No pending steps to execute")
            return
        
        print(f"🔄 Executing step: {pending_step.get('title', 'Untitled')}")
        
        # Execute the step
        exec_request = {"step_id": pending_step["id"]}
        response = requests.post(f"{API_BASE_URL}/api/execute_step", json=exec_request, timeout=45)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Step executed successfully!")
            print(f"   Status: {result.get('status', 'unknown')}")
            
            # Show result preview
            step_result = result.get('result', {})
            if isinstance(step_result, dict) and step_result.get('content'):
                content_preview = str(step_result['content'])[:200] + "..." if len(str(step_result['content'])) > 200 else str(step_result['content'])
                print(f"   Result preview: {content_preview}")
            
        else:
            print(f"❌ Step execution failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error in step execution: {e}")

def main():
    """Main test function"""
    print("🧪 Testing StudyBuddy Enhanced Features")
    print("=" * 50)
    
    # Test API connection
    if not test_api_connection():
        print("\n❌ Cannot proceed without API connection")
        return
    
    # Test plan creation
    plan_id = test_plan_creation()
    
    if plan_id:
        # Test single step execution
        test_single_step_execution(plan_id)
        
        # Wait a bit before bulk test
        time.sleep(2)
        
        # Test bulk execution
        test_bulk_execution(plan_id)
        
        # Test PDF generation
        test_pdf_generation(plan_id)
    
    print("\n🏁 Testing completed!")
    print("\nTo test the frontend features:")
    print("1. Run: streamlit run frontend/streamlit_app.py")
    print("2. Navigate to 'Create Plan' and create a new study plan")
    print("3. Check the overview summary and step selection checkboxes")
    print("4. Go to 'Execute Steps' to test the enhanced execution interface")
    print("5. Try the 'Run Selected' and 'Download PDF' features")

if __name__ == "__main__":
    main()