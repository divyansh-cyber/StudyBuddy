from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
from fastapi.responses import StreamingResponse

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

class BulkExecutionRequest(BaseModel):
    step_ids: List[str]

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

@app.post("/api/execute_steps_bulk")
async def execute_steps_bulk(request: BulkExecutionRequest):
    """Execute multiple study steps in sequence"""
    try:
        results = []
        failed_steps = []
        
        for step_id in request.step_ids:
            try:
                # Get step from database
                step_data = db.get_step(step_id)
                if not step_data:
                    failed_steps.append({"step_id": step_id, "error": "Step not found"})
                    continue
                
                # Get plan to find step details
                plan_data = db.get_plan(step_data["plan_id"])
                if not plan_data:
                    failed_steps.append({"step_id": step_id, "error": "Plan not found"})
                    continue
                
                # Find step in plan
                step_info = None
                for step in plan_data["plan_json"]["steps"]:
                    if step["id"] == step_id:
                        step_info = step
                        break
                
                if not step_info:
                    failed_steps.append({"step_id": step_id, "error": "Step not found in plan"})
                    continue
                
                # Update step status to running
                db.update_step_status(step_id, "running")
                
                try:
                    # Research step if needed
                    context = None
                    if step_info.get("tool") in ["RAG", "FLASHCARDS", "QUIZ"]:
                        context = researcher.research_step(step_info["description"], step_info["tool"])
                    
                    # Execute step
                    result = executor.execute_step(step_info, context)
                    
                    # Update step status to completed
                    db.update_step_status(step_id, "completed", json.dumps(result))
                    
                    results.append({
                        "step_id": step_id,
                        "status": "completed",
                        "result": result,
                        "context": context
                    })
                    
                except Exception as e:
                    # Update step status to failed
                    db.update_step_status(step_id, "failed", json.dumps({"error": str(e)}))
                    failed_steps.append({"step_id": step_id, "error": str(e)})
                    
            except Exception as e:
                failed_steps.append({"step_id": step_id, "error": str(e)})
        
        return {
            "executed_steps": len(results),
            "failed_steps": len(failed_steps),
            "results": results,
            "failures": failed_steps,
            "status": "completed"
        }
            
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

@app.get("/api/plans")
async def get_all_plans():
    """Get all study plans with their status"""
    try:
        all_plans = db.get_all_plans()
        
        # Add step statuses for each plan
        for plan_data in all_plans:
            steps_with_status = []
            for step in plan_data["plan_json"]["steps"]:
                step_data = db.get_step(step["id"])
                step["status"] = step_data["status"] if step_data else "pending"
                step["result"] = step_data["result_json"] if step_data else None
                steps_with_status.append(step)
            
            plan_data["plan_json"]["steps"] = steps_with_status
        
        return {"plans": all_plans}
        
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

@app.post("/api/clear_database")
async def clear_database():
    """Clear all data from the database (useful for testing)"""
    try:
        db.clear_all_data()
        return {"message": "Database cleared successfully", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/database_stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        stats = db.get_database_stats()
        return {"stats": stats, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download_plan_pdf/{plan_id}")
async def download_plan_pdf(plan_id: int):
    """Generate and download plan as PDF"""
    try:
        # Get plan data
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
        
        # Generate PDF
        pdf_buffer = generate_pdf_report(plan_data)
        
        # Return as streaming response
        def generate():
            pdf_buffer.seek(0)
            yield from pdf_buffer
        
        filename = f"study_plan_{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        
        return StreamingResponse(
            generate(),
            media_type='application/pdf',
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_pdf_report(plan_data: Dict[str, Any]) -> io.BytesIO:
    """Generate PDF report for a study plan"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.darkblue,
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.darkgreen
    )
    
    content = []
    plan = plan_data["plan_json"]
    
    # Title
    content.append(Paragraph(plan.get("title", "Study Plan"), title_style))
    content.append(Spacer(1, 0.3*inch))
    
    # Overview
    if plan.get("overview"):
        content.append(Paragraph("Overview", heading_style))
        content.append(Paragraph(plan["overview"], styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
    
    # Description
    if plan.get("description"):
        content.append(Paragraph("Description", heading_style))
        content.append(Paragraph(plan["description"], styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
    
    # Steps
    content.append(Paragraph("Study Steps", heading_style))
    content.append(Spacer(1, 0.1*inch))
    
    for i, step in enumerate(plan.get("steps", []), 1):
        # Step header
        step_title = f"Step {i}: {step.get('title', 'Untitled Step')}"
        content.append(Paragraph(step_title, styles['Heading3']))
        
        # Step details
        content.append(Paragraph(f"<b>Description:</b> {step.get('description', '')}", styles['Normal']))
        content.append(Paragraph(f"<b>Tool:</b> {step.get('tool', 'LLM')}", styles['Normal']))
        content.append(Paragraph(f"<b>Status:</b> {step.get('status', 'pending').title()}", styles['Normal']))
        
        # Step result if available
        if step.get("result") and step.get("status") == "completed":
            try:
                result = step["result"] if isinstance(step["result"], dict) else json.loads(step["result"])
                if result.get("content"):
                    content.append(Paragraph("<b>Result:</b>", styles['Normal']))
                    content.append(Paragraph(str(result["content"])[:500] + "...", styles['Normal']))
            except:
                pass
        
        content.append(Spacer(1, 0.15*inch))
    
    # Generated info
    content.append(Spacer(1, 0.3*inch))
    content.append(Paragraph("---", styles['Normal']))
    content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    content.append(Paragraph("Powered by StudyBuddy AI", styles['Normal']))
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
