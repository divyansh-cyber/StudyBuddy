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
        """Extract key takeaways by scanning for a 'Key Takeaways' section and collecting bullets."""
        collected: List[str] = []
        lines = [l.rstrip() for l in text.split('\n')]
        in_section = False

        for raw_line in lines:
            line = raw_line.strip()

            # Detect start of section
            if not in_section and ('key takeaways' in line.lower() or 'key takeaway' in line.lower() or 'key points' in line.lower()):
                in_section = True
                continue

            if in_section:
                # End section on blank line or next heading-like line
                if line == "" or any(h in line.lower() for h in ["action items", "additional resources", "summary", "resources"]):
                    if collected:
                        break
                # Collect bullet/numbered items
                if line.startswith(('- ', '• ', '* ', '– ')) or any(line.startswith(f"{n}. ") for n in range(1, 21)):
                    item = line[2:] if line[:2] in ['- ', '• ', '* ', '– '] else line.split(' ', 1)[1] if ' ' in line else line
                    collected.append(item.strip())

        # Fallback: collect any generic bullet lines if section not detected
        if not collected:
            for raw_line in lines:
                s = raw_line.strip()
                if s.startswith(('- ', '• ', '* ')):
                    collected.append(s[2:].strip())
                if len(collected) >= 5:
                    break

        return collected[:10]
    
    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items by scanning for an 'Action Items' section and collecting bullets."""
        actions: List[str] = []
        lines = [l.rstrip() for l in text.split('\n')]
        in_section = False

        for raw_line in lines:
            line = raw_line.strip()

            if not in_section and ('action items' in line.lower() or 'actions' in line.lower() or 'next steps' in line.lower()):
                in_section = True
                continue

            if in_section:
                if line == "" or any(h in line.lower() for h in ["key takeaways", "additional resources", "summary"]):
                    if actions:
                        break
                if line.startswith(('- ', '• ', '* ', '– ')) or any(line.startswith(f"{n}. ") for n in range(1, 21)):
                    item = line[2:] if line[:2] in ['- ', '• ', '* ', '– '] else line.split(' ', 1)[1] if ' ' in line else line
                    actions.append(item.strip())

        # Fallback: pick numbered lines anywhere
        if not actions:
            for raw_line in lines:
                s = raw_line.strip()
                if any(s.startswith(f"{n}. ") for n in range(1, 21)):
                    actions.append(s.split(' ', 1)[1].strip() if ' ' in s else s)
                if len(actions) >= 5:
                    break

        return actions[:10]
    
    def _extract_checklist(self, text: str) -> List[str]:
        """Extract checklist items from text"""
        checklist = []
        lines = text.split('\n')
        for line in lines:
            if 'checklist' in line.lower() or 'verify' in line.lower():
                checklist.append(line.strip())
        return checklist[:5]
