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
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.embeddings import HuggingFaceEmbeddings

class RAGManager:
    """
    Manages the RAG (Retrieval Augmented Generation) process
    for Terraform infrastructure templates
    """
    
    def __init__(self, embeddings_type="local"):
        """
        Initialize the RAG manager
        
        Args:
            embeddings_type (str): Type of embeddings to use ("local" or "openai")
        """
        self.templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "terraform")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize embeddings
        if embeddings_type == "openai":
            # Check if OPENAI_API_KEY is set
            if os.getenv("OPENAI_API_KEY"):
                self.embeddings = OpenAIEmbeddings()
            else:
                print("OPENAI_API_KEY not found, falling back to local embeddings")
                self.embeddings = self._initialize_local_embeddings()
        else:
            self.embeddings = self._initialize_local_embeddings()
        
        # Load the vector database if it exists, otherwise create it
        self.vector_db = self._load_or_create_vectordb()
    
    def _initialize_local_embeddings(self):
        """
        Initialize local embeddings using HuggingFace
        
        Returns:
            HuggingFaceEmbeddings: Initialized embeddings
        """
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
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
    
    def retrieve_similar_templates(self, query, n_results=3):
        """
        Retrieve similar templates based on the query
        
        Args:
            query (str): Query to search for
            n_results (int): Number of results to return
            
        Returns:
            list: List of similar templates with metadata
        """
        results = self.vector_db.similarity_search(query, k=n_results)
        return [
            {
                'content': doc.page_content,
                'metadata': doc.metadata
            }
            for doc in results
        ]
    
    def get_template_by_name(self, name):
        """
        Get a template by name
        
        Args:
            name (str): Name of the template (without .tf extension)
            
        Returns:
            str: Template content or None if not found
        """
        template_path = os.path.join(self.templates_dir, f"{name}.tf")
        if os.path.exists(template_path):
            with open(template_path, 'r') as file:
                return file.read()
        return None 