# Debug Script for StudyBuddy Step Execution Issues
# Run this to test the components individually

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

def test_environment():
    """Test environment variables"""
    print("🔍 Testing Environment Variables...")
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"✅ GOOGLE_API_KEY found: {api_key[:20]}...")
    else:
        print("❌ GOOGLE_API_KEY not found!")
        return False
    
    db_url = os.getenv("DATABASE_URL")
    print(f"✅ DATABASE_URL: {db_url}")
    
    return True

def test_llm_client():
    """Test LLM client directly"""
    print("\n🤖 Testing LLM Client...")
    try:
        from llm import LLMClient
        
        llm = LLMClient()
        response = llm.generate_response("Say 'Hello from StudyBuddy!'")
        print(f"✅ LLM Response: {response[:100]}...")
        return True
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return False

def test_database():
    """Test database connection"""
    print("\n🗄️ Testing Database...")
    try:
        from db import Database
        
        db = Database()
        # Try to create a test plan
        test_plan = {"title": "Test Plan", "steps": [{"id": "test_1", "title": "Test Step"}]}
        plan_id = db.create_plan("Test goal", json.dumps(test_plan))
        print(f"✅ Database working, created test plan ID: {plan_id}")
        
        # Clean up
        conn = db.init_db()
        return True
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return False

def test_agents():
    """Test individual agents"""
    print("\n🤝 Testing Agents...")
    
    # Test Planner
    try:
        from planner import PlannerAgent
        planner = PlannerAgent()
        plan = planner.create_study_plan("Learn basic math")
        print(f"✅ Planner working: {plan.get('title', 'No title')}")
    except Exception as e:
        print(f"❌ Planner Error: {e}")
        return False
    
    # Test Researcher
    try:
        from researcher import ResearcherAgent
        researcher = ResearcherAgent()
        context = researcher.research_step("Learn algebra", "LLM")
        print(f"✅ Researcher working: {len(str(context))} chars of context")
    except Exception as e:
        print(f"❌ Researcher Error: {e}")
        return False
    
    # Test Executor
    try:
        from executor import ExecutorAgent
        executor = ExecutorAgent()
        test_step = {"id": "test", "title": "Test", "description": "Test step", "tool": "LLM"}
        result = executor.execute_step(test_step)
        print(f"✅ Executor working: {result.get('type', 'No type')}")
    except Exception as e:
        print(f"❌ Executor Error: {e}")
        return False
    
    return True

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API Endpoints...")
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("Make sure backend is running with: python backend/app.py")
        return False
    
    # Test plan creation
    try:
        response = requests.post(
            f"{base_url}/api/plan",
            json={"goal": "Test goal from debug script"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            plan_id = data.get("plan_id")
            print(f"✅ Plan creation working, ID: {plan_id}")
            
            # Test step execution
            plan_steps = data.get("plan", {}).get("steps", [])
            if plan_steps:
                step_id = plan_steps[0]["id"]
                exec_response = requests.post(
                    f"{base_url}/api/execute_step",
                    json={"step_id": step_id},
                    timeout=60
                )
                if exec_response.status_code == 200:
                    result = exec_response.json()
                    print(f"✅ Step execution working: {result.get('status')}")
                    print(f"   Result type: {result.get('result', {}).get('type', 'No type')}")
                    if result.get('result'):
                        print(f"   Result content length: {len(str(result['result']))}")
                else:
                    print(f"❌ Step execution failed: {exec_response.status_code}")
                    print(f"   Response: {exec_response.text}")
                    return False
        else:
            print(f"❌ Plan creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 StudyBuddy Debug Script\n")
    
    tests = [
        ("Environment", test_environment),
        ("LLM Client", test_llm_client),
        ("Database", test_database),
        ("Agents", test_agents),
        ("API Endpoints", test_api_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n📊 Test Summary:")
    print("=" * 40)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests passed! Your StudyBuddy should be working correctly.")
        print("If you're still seeing issues, try:")
        print("1. Restart both backend and frontend")
        print("2. Clear browser cache")
        print("3. Check the browser console for errors")
    else:
        print("\n⚠️ Some tests failed. Check the errors above and fix them.")

if __name__ == "__main__":
    main()