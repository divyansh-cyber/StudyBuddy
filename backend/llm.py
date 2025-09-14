import os
import json
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self):
        # Configure Gemini Pro
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Generate response using Gemini Pro"""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"Error: {str(e)}"
    
    def generate_json_response(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """Generate JSON response with retry logic"""
        system_prompt = system_prompt or "You are a helpful AI assistant. Always respond with valid JSON format."
        
        for attempt in range(3):
            try:
                response = self.generate_response(prompt, system_prompt)
                
                # Try to extract JSON from response
                if response.startswith('```json'):
                    response = response.replace('```json', '').replace('```', '').strip()
                elif response.startswith('```'):
                    response = response.replace('```', '').strip()
                
                return json.loads(response)
            except json.JSONDecodeError:
                if attempt == 2:
                    # Last attempt, try to fix common JSON issues
                    response = response.strip()
                    if not response.startswith('{'):
                        response = '{' + response
                    if not response.endswith('}'):
                        response = response + '}'
                    try:
                        return json.loads(response)
                    except:
                        return {"error": "Failed to generate valid JSON"}
                continue
        
        return {"error": "Failed to generate valid JSON after 3 attempts"}
