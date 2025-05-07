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
    "sentence_transformers",
    "faiss",
]

# List of import alternatives - we only need one from each list to work
ALTERNATIVE_IMPORTS = [
    # Text splitters
    ["langchain.text_splitter", "langchain_text_splitters"],
    # Vector stores
    ["langchain.vectorstores", "langchain_community.vectorstores"],
    # Embeddings
    ["langchain.embeddings", "langchain_community.embeddings"],
    # Huggingface
    ["langchain_huggingface"],
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

def check_alternative_imports(alternative_groups):
    """Check that at least one module from each alternative group can be imported."""
    print("\nChecking alternative imports (need at least one from each group)...")
    success = True
    
    for group in alternative_groups:
        group_success = False
        for module in group:
            try:
                importlib.import_module(module)
                print(f"✅ {module}")
                group_success = True
                break
            except ImportError:
                pass
        
        if not group_success:
            print(f"❌ None of these alternatives could be imported: {', '.join(group)}")
            success = False
    
    return success

def main():
    """Main function."""
    print("Verifying Inframate dependencies...")
    
    core_success = check_imports(REQUIRED_MODULES, "core")
    rag_success = check_imports(RAG_MODULES, "RAG")
    alt_success = check_alternative_imports(ALTERNATIVE_IMPORTS)
    
    if core_success and rag_success and alt_success:
        print("\n✅ All dependencies verified successfully!")
        return 0
    else:
        print("\n❌ Some dependencies are missing or incompatible.")
        print("Please fix the issues before running Inframate.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 