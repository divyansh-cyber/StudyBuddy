from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime

from .planner import PlannerAgent
from .researcher import ResearcherAgent
from .executor import ExecutorAgent
from .db import Database

app = FastAPI(title="StudyBuddy API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents and database
planner = PlannerAgent()
researcher = ResearcherAgent()
executor = ExecutorAgent()
db = Database()

# Pydantic models
class PlanRequest(BaseModel):
    goal: str

class StepExecutionRequest(BaseModel):
    step_id: str

class PlanEditRequest(BaseModel):
    plan_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None

@app.get("/")
async def root():
    return {"message": "StudyBuddy API is running!"}

@app.post("/api/plan")
async def create_plan(request: PlanRequest):
    """Create a new study plan"""
    try:
        # Generate plan using planner agent
        plan_data = planner.create_study_plan(request.goal)
        
        # Save to database
        plan_id = db.create_plan(request.goal, json.dumps(plan_data))
        
        return {
            "plan_id": plan_id,
            "goal": request.goal,
            "plan": plan_data,
            "status": "created"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute_step")
async def execute_step(request: StepExecutionRequest):
    """Execute a single study step"""
    try:
        # Get step from database
        step_data = db.get_step(request.step_id)
        if not step_data:
            raise HTTPException(status_code=404, detail="Step not found")
        
        # Get plan to find step details
        plan_data = db.get_plan(step_data["plan_id"])
        if not plan_data:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Find step in plan
        step_info = None
        for step in plan_data["plan_json"]["steps"]:
            if step["id"] == request.step_id:
                step_info = step
                break
        
        if not step_info:
            raise HTTPException(status_code=404, detail="Step not found in plan")
        
        # Update step status to running
        db.update_step_status(request.step_id, "running")
        
        try:
            # Research step if needed
            context = None
            if step_info.get("tool") in ["RAG", "FLASHCARDS", "QUIZ"]:
                context = researcher.research_step(step_info["description"], step_info["tool"])
            
            # Execute step
            result = executor.execute_step(step_info, context)
            
            # Update step status to completed
            db.update_step_status(request.step_id, "completed", json.dumps(result))
            
            return {
                "step_id": request.step_id,
                "status": "completed",
                "result": result,
                "context": context
            }
            
        except Exception as e:
            # Update step status to failed
            db.update_step_status(request.step_id, "failed", json.dumps({"error": str(e)}))
            raise HTTPException(status_code=500, detail=f"Step execution failed: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/edit_plan")
async def edit_plan(request: PlanEditRequest):
    """Edit an existing plan"""
    try:
        # Get current plan
        plan_data = db.get_plan(request.plan_id)
        if not plan_data:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Update plan data
        updated_plan = plan_data["plan_json"]
        
        if request.title:
            updated_plan["title"] = request.title
        
        if request.description:
            updated_plan["description"] = request.description
        
        if request.steps:
            updated_plan["steps"] = request.steps
        
        # Save updated plan
        # Note: In a real implementation, you'd want to update the database
        # For now, we'll just return the updated plan
        
        return {
            "plan_id": request.plan_id,
            "plan": updated_plan,
            "status": "updated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/plan/{plan_id}")
async def get_plan(plan_id: int):
    """Get a specific plan"""
    try:
        plan_data = db.get_plan(plan_id)
        if not plan_data:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Get step statuses
        steps_with_status = []
        for step in plan_data["plan_json"]["steps"]:
            step_data = db.get_step(step["id"])
            step["status"] = step_data["status"] if step_data else "pending"
            step["result"] = step_data["result_json"] if step_data else None
            steps_with_status.append(step)
        
        plan_data["plan_json"]["steps"] = steps_with_status
        
        return plan_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
async def get_logs(agent: Optional[str] = None):
    """Get interaction logs"""
    try:
        logs = db.get_logs(agent)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
