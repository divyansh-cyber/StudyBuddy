import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import os

class Database:
    def __init__(self, db_path: str = "studybuddy.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Steps table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS steps (
                step_id TEXT PRIMARY KEY,
                plan_id INTEGER,
                status TEXT DEFAULT 'pending',
                result_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES plans (id)
            )
        ''')
        
        # Logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_plan(self, goal: str, plan_json: str) -> int:
        """Create a new plan and return plan_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO plans (goal, plan_json) VALUES (?, ?)",
            (goal, plan_json)
        )
        plan_id = cursor.lastrowid
        
        # Create step records
        plan_data = json.loads(plan_json)
        for step in plan_data.get('steps', []):
            cursor.execute(
                "INSERT INTO steps (step_id, plan_id, status) VALUES (?, ?, ?)",
                (step['id'], plan_id, 'pending')
            )
        
        conn.commit()
        conn.close()
        return plan_id
    
    def get_plan(self, plan_id: int) -> Optional[Dict[str, Any]]:
        """Get plan by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT goal, plan_json, created_at FROM plans WHERE id = ?",
            (plan_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': plan_id,
                'goal': result[0],
                'plan_json': json.loads(result[1]),
                'created_at': result[2]
            }
        return None
    
    def update_step_status(self, step_id: str, status: str, result_json: str = None):
        """Update step status and result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE steps SET status = ?, result_json = ?, updated_at = CURRENT_TIMESTAMP WHERE step_id = ?",
            (status, result_json, step_id)
        )
        
        conn.commit()
        conn.close()
    
    def get_step(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Get step by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT step_id, plan_id, status, result_json, created_at, updated_at FROM steps WHERE step_id = ?",
            (step_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'step_id': result[0],
                'plan_id': result[1],
                'status': result[2],
                'result_json': json.loads(result[3]) if result[3] else None,
                'created_at': result[4],
                'updated_at': result[5]
            }
        return None
    
    def log_interaction(self, agent: str, prompt: str, response: str):
        """Log agent interaction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO logs (agent, prompt, response) VALUES (?, ?, ?)",
            (agent, prompt, response)
        )
        
        conn.commit()
        conn.close()
    
    def get_logs(self, agent: str = None) -> List[Dict[str, Any]]:
        """Get logs, optionally filtered by agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if agent:
            cursor.execute(
                "SELECT agent, timestamp, prompt, response FROM logs WHERE agent = ? ORDER BY timestamp DESC",
                (agent,)
            )
        else:
            cursor.execute(
                "SELECT agent, timestamp, prompt, response FROM logs ORDER BY timestamp DESC"
            )
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'agent': row[0],
                'timestamp': row[1],
                'prompt': row[2],
                'response': row[3]
            }
            for row in results
        ]
