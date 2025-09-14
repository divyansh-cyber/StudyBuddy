import json
from typing import Dict, Any, List
from .llm import LLMClient
from .tools.rag import RAGTool
from .db import Database

class ResearcherAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.rag = RAGTool()
        self.db = Database()
    
    def research_step(self, step_description: str, step_tool: str) -> Dict[str, Any]:
        """Research context for a study step"""
        
        if step_tool == "RAG":
            return self._research_with_rag(step_description)
        else:
            return self._research_with_llm(step_description)
    
    def _research_with_rag(self, step_description: str) -> Dict[str, Any]:
        """Research using RAG tool"""
        
        # Generate search queries
        system_prompt = """You are a research assistant. Generate 2-3 specific search queries 
        to find relevant information for the given study step. Return as JSON array of strings."""
        
        prompt = f"""Generate search queries for this study step: "{step_description}"
        
        Return as JSON array: ["query1", "query2", "query3"]"""
        
        queries_response = self.llm.generate_json_response(prompt, system_prompt)
        
        # Extract queries
        if isinstance(queries_response, list):
            queries = queries_response
        elif isinstance(queries_response, dict) and "queries" in queries_response:
            queries = queries_response["queries"]
        else:
            queries = [step_description]  # Fallback
        
        # Search using RAG
        search_results = []
        for query in queries[:3]:  # Limit to 3 queries
            results = self.rag.tool_rag(query)
            search_results.extend(results)
        
        # Summarize findings
        context_text = "\n\n".join([result["content"] for result in search_results[:5]])
        
        summary_prompt = f"""Summarize the following research findings for this study step: "{step_description}"
        
        Research findings:
        {context_text}
        
        Provide a concise summary focusing on key concepts and actionable insights."""
        
        summary = self.llm.generate_response(summary_prompt)
        
        result = {
            "search_queries": queries,
            "search_results": search_results[:5],
            "summary": summary,
            "context": context_text
        }
        
        # Log interaction
        self.db.log_interaction("researcher", step_description, json.dumps(result))
        
        return result
    
    def _research_with_llm(self, step_description: str) -> Dict[str, Any]:
        """Research using LLM for non-RAG steps"""
        
        system_prompt = """You are a study research assistant. Provide helpful context and guidance 
        for the given study step. Include key concepts, tips, and resources."""
        
        prompt = f"""Provide research context and guidance for this study step: "{step_description}"
        
        Include:
        - Key concepts to focus on
        - Study tips and strategies
        - Recommended resources
        - Common pitfalls to avoid"""
        
        research_guidance = self.llm.generate_response(prompt, system_prompt)
        
        result = {
            "research_type": "llm_guidance",
            "guidance": research_guidance,
            "key_concepts": self._extract_key_concepts(research_guidance)
        }
        
        # Log interaction
        self.db.log_interaction("researcher", step_description, json.dumps(result))
        
        return result
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from research text"""
        # Simple extraction - in production, use more sophisticated NLP
        concepts = []
        lines = text.split('\n')
        for line in lines:
            if line.strip().startswith('-') or line.strip().startswith('•'):
                concepts.append(line.strip()[1:].strip())
        return concepts[:5]  # Limit to 5 concepts
