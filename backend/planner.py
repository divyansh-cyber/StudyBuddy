import json
import uuid
from typing import Dict, Any, List
from .llm import LLMClient
from .db import Database

class PlannerAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.db = Database()
    
    def create_study_plan(self, goal: str) -> Dict[str, Any]:
        """Create a comprehensive study plan"""
        
        # Generate a unique plan identifier
        plan_uuid = str(uuid.uuid4())[:8]  # Use first 8 characters of UUID
        
        system_prompt = f"""You are an expert study planner. Create a detailed study plan with 4-6 steps.
        Each step should have:
        - id: unique identifier (use format: {plan_uuid}_step_1, {plan_uuid}_step_2, etc.)
        - title: clear, actionable title
        - description: detailed description of what to do
        - tool: one of [RAG, LLM, FLASHCARDS, QUIZ]
        - expected_output: what the student should produce
        
        Return valid JSON with this structure:
        {{
            "title": "Study Plan Title",
            "description": "Overall plan description",
            "steps": [
                {{
                    "id": "{plan_uuid}_step_1",
                    "title": "Step Title",
                    "description": "Detailed step description",
                    "tool": "RAG",
                    "expected_output": "What to produce"
                }}
            ]
        }}"""
        
        prompt = f"""Create a comprehensive study plan for this goal: "{goal}"
        
        The plan should be practical, achievable, and include a mix of research, practice, and assessment.
        Make sure each step builds upon the previous one."""
        
        # Generate plan with retry logic
        plan_data = self.llm.generate_json_response(prompt, system_prompt)
        
        # Validate and fix plan structure
        if "error" in plan_data:
            # Fallback plan
            plan_data = self._create_fallback_plan(goal, plan_uuid)
        
        # Ensure all steps have required fields and unique IDs
        if "steps" in plan_data:
            for i, step in enumerate(plan_data["steps"]):
                if "id" not in step or not step["id"].startswith(plan_uuid):
                    step["id"] = f"{plan_uuid}_step_{i+1}"
                if "tool" not in step:
                    step["tool"] = "LLM"
        
        # Log interaction
        self.db.log_interaction("planner", prompt, json.dumps(plan_data))
        
        return plan_data
    
    def _create_fallback_plan(self, goal: str, plan_uuid: str) -> Dict[str, Any]:
        """Create a fallback plan if LLM fails"""
        return {
            "title": f"Study Plan: {goal}",
            "description": f"A comprehensive study plan to achieve: {goal}",
            "steps": [
                {
                    "id": f"{plan_uuid}_step_1",
                    "title": "Research and Gather Information",
                    "description": f"Research key concepts and gather relevant information about {goal}",
                    "tool": "RAG",
                    "expected_output": "Summary of key concepts and resources"
                },
                {
                    "id": f"{plan_uuid}_step_2",
                    "title": "Create Study Materials",
                    "description": "Create flashcards and study notes based on research",
                    "tool": "FLASHCARDS",
                    "expected_output": "Set of flashcards and study notes"
                },
                {
                    "id": f"{plan_uuid}_step_3",
                    "title": "Practice and Apply",
                    "description": "Practice applying the concepts through exercises",
                    "tool": "LLM",
                    "expected_output": "Completed practice exercises"
                },
                {
                    "id": f"{plan_uuid}_step_4",
                    "title": "Self-Assessment",
                    "description": "Take a quiz to test understanding",
                    "tool": "QUIZ",
                    "expected_output": "Quiz results and areas for improvement"
                }
            ]
        }
