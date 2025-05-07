#!/usr/bin/env python
"""
Verify that all dependencies can be imported correctly.
This script helps identify import issues before running the full application.
"""
import sys
import importlib

# List of all required modules
REQUIRED_MODULES = [
    "requests",
    "pathlib",
    "boto3",
    "yaml",
    "dotenv",
    "google.generativeai",
    "git",
    "click",
    "colorama",
    "numpy",
]

# List of RAG-related modules
RAG_MODULES = [
    "tiktoken",
    "langchain",
    "langchain.text_splitter",
    "langchain.vectorstores",
    "langchain.embeddings",
    "sentence_transformers",
    "faiss",
]

def check_imports(modules, category):
    """Check that each module can be imported."""
    print(f"\nChecking {category} modules...")
    success = True
    
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {str(e)}")
            success = False
    
    return success

def main():
    """Main function."""
    print("Verifying Inframate dependencies...")
    
    core_success = check_imports(REQUIRED_MODULES, "core")
    rag_success = check_imports(RAG_MODULES, "RAG")
    
    if core_success and rag_success:
        print("\n✅ All dependencies verified successfully!")
        return 0
    else:
        print("\n❌ Some dependencies are missing or incompatible.")
        print("Please fix the issues before running Inframate.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 