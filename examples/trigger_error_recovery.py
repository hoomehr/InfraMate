#!/usr/bin/env python3
"""
Trigger Error Recovery Example

This script demonstrates how to programmatically trigger the error recovery workflow
for Inframate. This can be used in scripts, CI/CD pipelines, or automated monitoring
systems to handle errors in infrastructure management.

Usage:
  python trigger_error_recovery.py --error-type terraform_error --message "Failed to apply Terraform"
"""

import os
import sys
import json
import argparse
import requests
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def trigger_github_workflow(repo_owner, repo_name, workflow_id, ref, inputs, token):
    """Trigger a GitHub workflow using the GitHub API"""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/{workflow_id}/dispatches"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }
    data = {
        "ref": ref,
        "inputs": inputs
    }
    
    logger.info(f"Triggering workflow '{workflow_id}' with inputs: {inputs}")
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 204:
        logger.info("Workflow triggered successfully")
        return True
    else:
        logger.error(f"Failed to trigger workflow: {response.status_code} - {response.text}")
        return False

def trigger_local_error_recovery(error_type, error_message, repo_path="."):
    """Trigger error recovery locally using the debug_error_flow.py script"""
    # Add parent directory to path to import scripts
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from scripts.debug_error_flow import ErrorDebugger, ErrorType
        
        logger.info(f"Triggering local error recovery for {error_type}")
        debugger = ErrorDebugger(repo_path)
        
        # Convert string error type to enum if needed
        if isinstance(error_type, str):
            try:
                error_type = ErrorType(error_type)
            except ValueError:
                logger.warning(f"Unknown error type: {error_type}, defaulting to validation_error")
                error_type = ErrorType.VALIDATION
        
        # Inject error and attempt recovery
        success, solution = debugger.inject_error(error_type, error_message)
        
        if success:
            logger.info("Error recovery was successful")
            if solution:
                logger.info(f"Solution: {json.dumps(solution, indent=2)}")
        else:
            logger.warning("Error recovery was not successful")
            
        return success, solution
        
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Make sure you're running this script from the Inframate project directory")
        return False, None

def main():
    parser = argparse.ArgumentParser(description='Trigger Inframate error recovery')
    parser.add_argument('--mode', choices=['github', 'local'], default='local',
                      help='Mode to trigger recovery (github or local)')
    parser.add_argument('--repo-owner', help='GitHub repository owner (for github mode)')
    parser.add_argument('--repo-name', help='GitHub repository name (for github mode)')
    parser.add_argument('--token', help='GitHub API token (for github mode)')
    parser.add_argument('--ref', default='main', help='Git reference (for github mode)')
    parser.add_argument('--error-type', required=True, 
                      help='Type of error (api_error, terraform_error, etc.)')
    parser.add_argument('--message', required=True,
                      help='Error message')
    parser.add_argument('--repo-path', default='.',
                      help='Repository path (for local mode)')
    parser.add_argument('--autonomous', action='store_true',
                      help='Apply fixes automatically')
    
    args = parser.parse_args()
    
    if args.mode == 'github':
        # Validate required arguments for GitHub mode
        if not all([args.repo_owner, args.repo_name, args.token]):
            logger.error("For GitHub mode, you must provide --repo-owner, --repo-name, and --token")
            sys.exit(1)
            
        # Prepare inputs for the workflow
        inputs = {
            "error_type": args.error_type,
            "error_message": args.message,
            "repo_path": ".",  # GitHub Actions works in the repo root
            "autonomous_mode": str(args.autonomous).lower()
        }
        
        # Trigger the workflow
        success = trigger_github_workflow(
            args.repo_owner,
            args.repo_name,
            "error_recovery.yml",
            args.ref,
            inputs,
            args.token
        )
        
        sys.exit(0 if success else 1)
    else:
        # Local mode
        success, _ = trigger_local_error_recovery(
            args.error_type,
            args.message,
            args.repo_path
        )
        
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 