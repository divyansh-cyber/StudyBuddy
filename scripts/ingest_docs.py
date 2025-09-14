import os
import PyPDF2
from typing import List
from backend.tools.rag import RAGTool

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end - overlap
    
    return chunks

def ingest_documents(documents_path: str = "./documents"):
    """Ingest documents and create index"""
    
    # Create documents directory if it doesn't exist
    os.makedirs(documents_path, exist_ok=True)
    
    # Initialize RAG tool
    rag = RAGTool()
    
    # Sample documents for demo
    sample_docs = [
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
    
    # Process PDF files if they exist
    pdf_files = [f for f in os.listdir(documents_path) if f.endswith('.pdf')]
    
    all_chunks = []
    
    # Add sample documents
    all_chunks.extend(sample_docs)
    
    # Process PDF files
    for pdf_file in pdf_files:
        pdf_path = os.path.join(documents_path, pdf_file)
        print(f"Processing {pdf_file}...")
        
        text = extract_text_from_pdf(pdf_path)
        if text:
            chunks = chunk_text(text)
            all_chunks.extend(chunks)
            print(f"Extracted {len(chunks)} chunks from {pdf_file}")
    
    # Create index
    if all_chunks:
        print(f"Creating index with {len(all_chunks)} chunks...")
        rag.create_index(all_chunks)
        print("Index created successfully!")
    else:
        print("No documents found to process.")

if __name__ == "__main__":
    ingest_documents()
