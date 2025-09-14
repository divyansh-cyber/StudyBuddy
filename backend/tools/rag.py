import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class RAGTool:
    def __init__(self):
        self.documents = []
        self.index_path = os.getenv("FAISS_INDEX_PATH", "./faiss_index")
        self.load_index()
    
    def load_index(self):
        """Load documents if they exist"""
        try:
            if os.path.exists(f"{self.index_path}.json"):
                with open(f"{self.index_path}.json", 'r') as f:
                    self.documents = json.load(f)
                print(f"Loaded {len(self.documents)} documents")
            else:
                # Initialize with sample documents
                self.documents = [
                    "Python is a high-level programming language known for its simplicity and readability. It's widely used in web development, data science, artificial intelligence, and automation.",
                    "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed for every task.",
                    "Data structures are ways of organizing and storing data in a computer so that it can be accessed and modified efficiently. Common examples include arrays, linked lists, stacks, and queues.",
                    "Algorithms are step-by-step procedures for solving problems or performing tasks. They are fundamental to computer science and programming.",
                    "Web development involves creating websites and web applications using technologies like HTML, CSS, JavaScript, and various frameworks and libraries.",
                    "Database management systems (DBMS) are software systems that manage databases. They provide an interface for users to interact with data stored in databases.",
                    "Software engineering is the systematic approach to designing, developing, and maintaining software systems. It involves various methodologies and best practices.",
                    "Computer networks enable communication between devices. They can be local area networks (LAN), wide area networks (WAN), or the internet.",
                    "Operating systems manage computer hardware and software resources. They provide services for computer programs and users.",
                    "Cybersecurity involves protecting computer systems, networks, and data from digital attacks, damage, or unauthorized access."
                ]
                self.save_documents()
                print(f"Initialized with {len(self.documents)} sample documents")
        except Exception as e:
            print(f"Error loading documents: {e}")
    
    def save_documents(self):
        """Save documents to file"""
        try:
            with open(f"{self.index_path}.json", 'w') as f:
                json.dump(self.documents, f)
        except Exception as e:
            print(f"Error saving documents: {e}")
    
    def create_index(self, documents: List[str]):
        """Create document index"""
        if not documents:
            return
        
        self.documents = documents
        self.save_documents()
        print(f"Created index with {len(documents)} documents")
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant documents using simple text matching"""
        if not self.documents:
            return [{"content": "No documents available for search.", "score": 0.0}]
        
        query_lower = query.lower()
        results = []
        
        for doc in self.documents:
            doc_lower = doc.lower()
            # Simple scoring based on word overlap
            query_words = set(query_lower.split())
            doc_words = set(doc_lower.split())
            
            # Calculate similarity score
            common_words = query_words.intersection(doc_words)
            score = len(common_words) / len(query_words) if query_words else 0
            
            # Boost score if query appears as substring
            if query_lower in doc_lower:
                score += 0.5
            
            if score > 0:
                results.append({
                    "content": doc,
                    "score": score
                })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def tool_rag(self, query: str) -> List[Dict[str, Any]]:
        """Main RAG tool function"""
        return self.search(query, top_k=3)
