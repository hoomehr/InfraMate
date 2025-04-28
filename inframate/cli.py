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
import click
from inframate.flow import main as inframate_flow_main

from inframate.analyzers.repository import analyze_repository
from inframate.agents.ai_analyzer import analyze_with_ai, fallback_analyze, generate_terraform_template

@click.command()
@click.argument('repo_path', type=click.Path(exists=True))
def main(repo_path):
    """Inframate CLI - Generate infrastructure recommendations and Terraform files"""
    # Convert the repo path to an absolute path
    abs_repo_path = str(Path(repo_path).resolve())
    
    # Execute the main flow with the repo path as an argument
    try:
        # Pass as a list with the first element as the script name
        # and the second element as the repo path
        inframate_flow_main(["inframate", abs_repo_path])
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 