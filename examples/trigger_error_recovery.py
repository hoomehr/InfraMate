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

def get_latest_failed_workflow(repo_owner, repo_name, token):
    """Get the latest failed workflow from GitHub Actions"""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs?status=failure&per_page=5"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }
    
    logger.info("Fetching latest failed workflows...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch workflow runs: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    workflow_runs = data.get("workflow_runs", [])
    
    if not workflow_runs:
        logger.info("No failed workflow runs found")
        return None
    
    # Filter out error recovery workflows to avoid circular processing
    relevant_runs = [run for run in workflow_runs if "error recovery" not in run.get("name", "").lower()]
    
    if not relevant_runs:
        logger.info("No relevant failed workflow runs found")
        return None
    
    # Get the latest failed run
    latest_run = relevant_runs[0]
    logger.info(f"Found latest failed workflow: {latest_run['name']} (ID: {latest_run['id']})")
    
    return {
        "id": latest_run["id"],
        "name": latest_run["name"],
        "workflow_id": latest_run["workflow_id"]
    }

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
    parser.add_argument('--mode', choices=['github', 'local', 'latest'], default='local',
                      help='Mode to trigger recovery (github, local, or latest)')
    parser.add_argument('--repo-owner', help='GitHub repository owner (for github/latest mode)')
    parser.add_argument('--repo-name', help='GitHub repository name (for github/latest mode)')
    parser.add_argument('--token', help='GitHub API token (for github/latest mode)')
    parser.add_argument('--ref', default='main', help='Git reference (for github mode)')
    parser.add_argument('--error-type', 
                      help='Type of error (api_error, terraform_error, etc.)')
    parser.add_argument('--message',
                      help='Error message')
    parser.add_argument('--repo-path', default='.',
                      help='Repository path (for local mode)')
    parser.add_argument('--autonomous', action='store_true',
                      help='Apply fixes automatically')
    parser.add_argument('--workflow-id', help='Specific workflow ID to recover (for github mode)')
    
    args = parser.parse_args()
    
    if args.mode == 'github':
        # Validate required arguments for GitHub mode
        if not all([args.repo_owner, args.repo_name, args.token]):
            logger.error("For GitHub mode, you must provide --repo-owner, --repo-name, and --token")
            sys.exit(1)
            
        # Error type and message are required for direct GitHub mode
        if not all([args.error_type, args.message]):
            logger.error("For GitHub mode, you must provide --error-type and --message")
            sys.exit(1)
            
        # Prepare inputs for the workflow
        inputs = {
            "error_type": args.error_type,
            "error_message": args.message,
            "repo_path": ".",  # GitHub Actions works in the repo root
            "autonomous_mode": str(args.autonomous).lower()
        }
        
        # Add workflow ID if specified
        if args.workflow_id:
            inputs["workflow_id"] = args.workflow_id
        
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
    elif args.mode == 'latest':
        # Validate required arguments for latest mode
        if not all([args.repo_owner, args.repo_name, args.token]):
            logger.error("For latest mode, you must provide --repo-owner, --repo-name, and --token")
            sys.exit(1)
            
        # Get the latest failed workflow
        latest_workflow = get_latest_failed_workflow(args.repo_owner, args.repo_name, args.token)
        
        if not latest_workflow:
            logger.error("No failed workflows found to recover")
            sys.exit(1)
            
        # Prepare inputs for the workflow - use workflow ID directly
        inputs = {
            "workflow_id": str(latest_workflow["id"]),
            "autonomous_mode": str(args.autonomous).lower()
        }
        
        # Add error type and message if provided (otherwise will be extracted from artifacts)
        if args.error_type:
            inputs["error_type"] = args.error_type
        if args.message:
            inputs["error_message"] = args.message
        
        logger.info(f"Triggering error recovery for latest failed workflow: {latest_workflow['name']}")
        
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
        # Local mode - error type and message are required
        if not all([args.error_type, args.message]):
            logger.error("For local mode, you must provide --error-type and --message")
            sys.exit(1)
            
        # Local mode
        success, _ = trigger_local_error_recovery(
            args.error_type,
            args.message,
            args.repo_path
        )
        
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 