#!/usr/bin/env python3
"""
Inframate CLI - Command line interface for Inframate
"""
import os
import sys
import json
import yaml
import shutil
import requests
from pathlib import Path

from inframate.analyzers.repository import analyze_repository
from inframate.agents.ai_analyzer import analyze_with_ai, fallback_analyze, generate_terraform_template

def main():
    """Main CLI entry point"""
    if len(sys.argv) != 2:
        print("Usage: inframate <repository_path>")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    try:
        # Analyze repository
        analysis = analyze_repository(repo_path)
        
        # Generate Terraform files
        generate_terraform_files(repo_path, analysis)
        
        print("Inframate analysis completed successfully")
        print("Terraform files generated in terraform/ directory")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 