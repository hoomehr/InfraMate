"""
RAG (Retrieval Augmented Generation) utilities
"""
import os
import glob
import numpy as np
import tiktoken
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
try:
    from langchain_huggingface import HuggingFaceEmbeddings as NewHuggingFaceEmbeddings
except ImportError:
    # For older versions of langchain
    from langchain.embeddings import HuggingFaceEmbeddings as NewHuggingFaceEmbeddings
from typing import List, Dict, Any

class RAGManager:
    """
    Manages the RAG (Retrieval Augmented Generation) process
    for Terraform infrastructure templates
    """
    
    def __init__(self):
        """
        Initialize the RAG manager
        """
        self.templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "terraform")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize embeddings
        self.embeddings = self._initialize_local_embeddings()
        self.vector_store = None
        self.templates = {}
    
    def _initialize_local_embeddings(self):
        """
        Initialize local embeddings using HuggingFace
        
        Returns:
            HuggingFaceEmbeddings: Initialized embeddings
        """
        try:
            # Try the new HuggingFace embeddings first
            return NewHuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
        except ImportError:
            # Fallback to the community version
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
    
    def _load_terraform_templates(self):
        """
        Load Terraform templates from the templates directory
        
        Returns:
            list: List of template documents with metadata
        """
        templates = []
        for tf_file in glob.glob(os.path.join(self.templates_dir, "*.tf")):
            filename = os.path.basename(tf_file)
            template_type = os.path.splitext(filename)[0]
            
            with open(tf_file, 'r') as file:
                content = file.read()
                templates.append({
                    'content': content,
                    'metadata': {
                        'filename': filename,
                        'type': template_type
                    }
                })
        
        return templates
    
    def _load_or_create_vectordb(self):
        """
        Load the vector database if it exists, otherwise create it
        
        Returns:
            FAISS: Vector database
        """
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vectordb")
        
        # Create the vectordb directory if it doesn't exist
        os.makedirs(db_path, exist_ok=True)
        
        # Check if the vector database exists
        if os.path.exists(os.path.join(db_path, "index.faiss")):
            try:
                vector_db = FAISS.load_local(db_path, self.embeddings)
                return vector_db
            except Exception as e:
                print(f"Error loading vector database: {str(e)}")
                print("Creating a new vector database...")
        
        # Create a new vector database
        templates = self._load_terraform_templates()
        documents = []
        
        for template in templates:
            chunks = self.text_splitter.split_text(template['content'])
            for chunk in chunks:
                documents.append({
                    'content': chunk,
                    'metadata': template['metadata']
                })
        
        texts = [doc['content'] for doc in documents]
        metadatas = [doc['metadata'] for doc in documents]
        
        vector_db = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
        
        # Save the vector database
        vector_db.save_local(db_path)
        
        return vector_db
    
    def retrieve_similar_templates(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve similar templates based on the query
        
        Args:
            query (str): Query to search for
            k (int): Number of results to return
            
        Returns:
            list: List of similar templates with metadata and score
        """
        if not self.vector_store:
            # Create vector store from templates
            texts = list(self.templates.values())
            metadatas = [{"name": name} for name in self.templates.keys()]
            self.vector_store = FAISS.from_texts(
                texts=texts,
                embedding=self.embeddings,
                metadatas=metadatas
            )
        
        # Search for similar templates
        docs = self.vector_store.similarity_search_with_score(query, k=k)
        return [
            {
                "content": doc[0].page_content,
                "metadata": doc[0].metadata,
                "score": doc[1]
            }
            for doc in docs
        ]
    
    def get_template_by_name(self, name: str) -> str:
        """
        Get a template by name
        
        Args:
            name (str): Name of the template (without .tf extension)
            
        Returns:
            str: Template content or None if not found
        """
        return self.templates.get(name, "")
    
    def load_templates(self, template_dir: str):
        """
        Load Terraform templates from directory
        
        Args:
            template_dir (str): Directory containing Terraform templates
        """
        template_path = Path(template_dir)
        if not template_path.exists():
            return
        
        for template_file in template_path.glob("*.tf"):
            with open(template_file, "r") as f:
                self.templates[template_file.stem] = f.read() 