import json
import uuid
from typing import Dict, Any, List
from .llm import LLMClient
from .db import Database

class ExecutorAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.db = Database()
    
    def execute_step(self, step: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a study step and generate artifacts"""
        
        step_tool = step.get("tool", "LLM")
        
        if step_tool == "RAG":
            return self._execute_rag_step(step, context)
        elif step_tool == "FLASHCARDS":
            return self._execute_flashcards_step(step, context)
        elif step_tool == "QUIZ":
            return self._execute_quiz_step(step, context)
        else:
            return self._execute_llm_step(step, context)
    
    def _execute_rag_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute RAG-based step"""
        
        system_prompt = """You are a study assistant. Create a comprehensive summary and study guide 
        based on the research context provided. Make it actionable and well-structured."""
        
        context_text = context.get("context", "") if context else ""
        summary = context.get("summary", "") if context else ""
        
        prompt = f"""Create a study guide for this step: "{step['title']}"
        
        Step description: {step['description']}
        
        Research context:
        {context_text}
        
        Research summary:
        {summary}
        
        Create:
        1. A comprehensive summary
        2. Key takeaways
        3. Action items
        4. Additional resources
        
        Format as structured content."""
        
        study_guide = self.llm.generate_response(prompt, system_prompt)
        
        result = {
            "type": "study_guide",
            "content": study_guide,
            "key_takeaways": self._extract_takeaways(study_guide),
            "action_items": self._extract_action_items(study_guide)
        }
        
        # Log interaction
        self.db.log_interaction("executor", json.dumps(step), json.dumps(result))
        
        return result
    
    def _execute_flashcards_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute flashcards creation step"""
        
        system_prompt = """You are a flashcard creation expert. Create educational flashcards 
        in JSON format with question-answer pairs."""
        
        context_text = context.get("context", "") if context else ""
        
        prompt = f"""Create flashcards for this study step: "{step['title']}"
        
        Step description: {step['description']}
        
        Context: {context_text}
        
        Create 5-8 flashcards in this JSON format:
        {{
            "flashcards": [
                {{
                    "id": "card_1",
                    "question": "Question text",
                    "answer": "Answer text",
                    "category": "Category name"
                }}
            ]
        }}"""
        
        flashcards_data = self.llm.generate_json_response(prompt, system_prompt)
        
        if "error" in flashcards_data:
            # Fallback flashcards
            flashcards_data = {
                "flashcards": [
                    {
                        "id": "card_1",
                        "question": f"What is the main concept in {step['title']}?",
                        "answer": "Main concept explanation",
                        "category": "General"
                    }
                ]
            }
        
        result = {
            "type": "flashcards",
            "flashcards": flashcards_data.get("flashcards", []),
            "total_cards": len(flashcards_data.get("flashcards", []))
        }
        
        # Log interaction
        self.db.log_interaction("executor", json.dumps(step), json.dumps(result))
        
        return result
    
    def _execute_quiz_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute quiz creation step"""
        
        system_prompt = """You are a quiz creation expert. Create educational quiz questions 
        in JSON format with multiple choice options."""
        
        context_text = context.get("context", "") if context else ""
        
        prompt = f"""Create a quiz for this study step: "{step['title']}"
        
        Step description: {step['description']}
        
        Context: {context_text}
        
        Create 5-7 quiz questions in this JSON format:
        {{
            "quiz": [
                {{
                    "id": "q1",
                    "question": "Question text",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "explanation": "Why this answer is correct"
                }}
            ]
        }}"""
        
        quiz_data = self.llm.generate_json_response(prompt, system_prompt)
        
        if "error" in quiz_data:
            # Fallback quiz
            quiz_data = {
                "quiz": [
                    {
                        "id": "q1",
                        "question": f"Which of the following is most important for {step['title']}?",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": "Option A",
                        "explanation": "Explanation for the correct answer"
                    }
                ]
            }
        
        result = {
            "type": "quiz",
            "quiz": quiz_data.get("quiz", []),
            "total_questions": len(quiz_data.get("quiz", []))
        }
        
        # Log interaction
        self.db.log_interaction("executor", json.dumps(step), json.dumps(result))
        
        return result
    
    def _execute_llm_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general LLM-based step"""
        
        system_prompt = """You are a study assistant. Help the student complete their study step 
        by providing guidance, examples, and actionable content."""
        
        context_text = context.get("guidance", "") if context else ""
        
        prompt = f"""Help complete this study step: "{step['title']}"
        
        Step description: {step['description']}
        
        Expected output: {step.get('expected_output', '')}
        
        Context: {context_text}
        
        Provide:
        1. Step-by-step guidance
        2. Examples or templates
        3. Tips for success
        4. How to verify completion"""
        
        guidance = self.llm.generate_response(prompt, system_prompt)
        
        result = {
            "type": "guidance",
            "content": guidance,
            "completion_checklist": self._extract_checklist(guidance)
        }
        
        # Log interaction
        self.db.log_interaction("executor", json.dumps(step), json.dumps(result))
        
        return result
    
    def _extract_takeaways(self, text: str) -> List[str]:
        """Extract key takeaways from text"""
        takeaways = []
        lines = text.split('\n')
        for line in lines:
            if 'takeaway' in line.lower() or 'key point' in line.lower():
                takeaways.append(line.strip())
        return takeaways[:5]
    
    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items from text"""
        actions = []
        lines = text.split('\n')
        for line in lines:
            if line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                actions.append(line.strip())
        return actions[:5]
    
    def _extract_checklist(self, text: str) -> List[str]:
        """Extract checklist items from text"""
        checklist = []
        lines = text.split('\n')
        for line in lines:
            if 'checklist' in line.lower() or 'verify' in line.lower():
                checklist.append(line.strip())
        return checklist[:5]
