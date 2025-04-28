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
from inframate.flow import main as inframate_main

from inframate.analyzers.repository import analyze_repository
from inframate.agents.ai_analyzer import analyze_with_ai, fallback_analyze, generate_terraform_template

@click.command()
@click.argument('repo_path', type=click.Path(exists=True))
def main(repo_path):
    """Inframate CLI - Generate infrastructure recommendations and Terraform files"""
    try:
        inframate_main([str(Path(repo_path).resolve())])
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

if __name__ == "__main__":
    main() 