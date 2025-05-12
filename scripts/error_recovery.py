#!/usr/bin/env python3
"""
Error Recovery Script for Inframate CI/CD Workflows

This script analyzes workflow execution errors and attempts automated recovery.
It serves as an entrypoint for the error recovery process in GitHub Actions.

Usage:
  python scripts/error_recovery.py --error-type TYPE [--workflow-id ID] [--workflow-name NAME] [--failed-job JOB] [--error-logs LOGS] [--output FILE] [--autonomous]
"""

import os
import sys
import json
import argparse
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Any, List
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("error_recovery.log")
    ]
)
logger = logging.getLogger(__name__)

# Try to import Gemini API if available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("Google Generative AI module not available. Using basic recovery only.")
    GEMINI_AVAILABLE = False

def setup_gemini_api():
    """Setup Gemini API with proper error handling"""
    if not GEMINI_AVAILABLE:
        return None
        
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not found in environment variables")
        return None
    
    try:
        genai.configure(api_key=api_key)
        # Use an appropriate model version
        return genai.GenerativeModel('gemini-1.5-pro')
    except Exception as e:
        logger.error(f"Failed to initialize Gemini API: {e}")
        return None

def analyze_error(error_type: str, workflow_name: str, failed_job: str, error_logs: str, model) -> Dict[str, Any]:
    """
    Analyze an error with Gemini AI and generate recovery steps
    
    Args:
        error_type: Type of error (terraform_error, visualization_error, etc.)
        workflow_name: Name of the failed workflow
        failed_job: Name of the failed job
        error_logs: Error logs from the failed job
        model: Initialized Gemini model
    
    Returns:
        Dictionary with analysis results
    """
    if not model:
        logger.warning(f"Gemini model not available, using basic analysis for {error_type}")
        return _basic_analysis(error_type, error_logs, workflow_name, failed_job)
    
    # Limit log size for prompt
    error_logs_excerpt = error_logs[-4000:] if len(error_logs) > 4000 else error_logs
    
    prompt = f"""
    As an infrastructure deployment expert, analyze this error from the Inframate system and provide recovery steps:
    
    ERROR TYPE: {error_type}
    WORKFLOW: {workflow_name}
    FAILED JOB: {failed_job}
    ERROR LOGS (excerpt):
    {error_logs_excerpt}
    
    Please provide:
    1. Root cause analysis
    2. Step-by-step recovery instructions
    3. Preventive measures
    
    Format your response as JSON with these keys:
    - "error_type": The specific error type identified
    - "root_cause": Brief explanation of what caused the error
    - "solution": Array of specific commands or actions to fix the issue
    - "prevention": How to prevent this error in the future
    """
    
    try:
        response = model.generate_content(prompt)
        
        # Parse the response to extract the JSON
        try:
            solution = response.text
            # Extract just the JSON part if there's additional text
            if "{" in solution and "}" in solution:
                start_idx = solution.find("{")
                end_idx = solution.rfind("}") + 1
                solution_json = json.loads(solution[start_idx:end_idx])
                return solution_json
            return json.loads(solution)
        except json.JSONDecodeError:
            # If not valid JSON, structure the raw text
            return {
                "error_type": error_type,
                "root_cause": "Analysis failed to return structured data",
                "solution": f"Manual analysis required. Response was: {solution[:200]}...",
                "prevention": "Improve error handling"
            }
    
    except Exception as e:
        logger.error(f"Error analyzing with Gemini: {e}")
        return _basic_analysis(error_type, error_logs, workflow_name, failed_job)

def _basic_analysis(error_type: str, error_logs: str, workflow_name: str, failed_job: str) -> Dict[str, Any]:
    """Provide basic error analysis when AI is not available"""
    solution = []
    
    if "terraform" in error_type.lower() or "infrastructure" in error_type.lower():
        if "state_lock" in error_logs.lower():
            solution = [
                "Wait for any running Terraform operations to complete",
                "Run: terraform force-unlock [LOCK_ID]",
                "Retry the failed operation"
            ]
        elif "no such file" in error_logs.lower():
            solution = [
                "Run: terraform init",
                "Retry the failed operation"
            ]
        else:
            solution = [
                "Check Terraform configuration files for syntax errors",
                "Verify AWS credentials are properly configured",
                "Run: terraform validate"
            ]
    
    elif "visualization" in error_type.lower() or "infra visualization" in workflow_name.lower():
        if "token" in error_logs.lower() or "authentication" in error_logs.lower():
            solution = [
                "Check that REPO_PAT has correct permissions",
                "Ensure GitHub token is properly configured",
                "Fix token permissions and retry visualization"
            ]
        elif "file size" in error_logs.lower() or "large" in error_logs.lower():
            solution = [
                "Add large provider files to .gitignore",
                "Remove large terraform provider files before commit",
                "Use terraform-local to manage provider files"
            ]
        else:
            solution = [
                "Check for syntax errors in Terraform files",
                "Verify GraphViz is properly installed",
                "Make visualization optional to prevent workflow failure"
            ]
    
    elif "permission" in error_type.lower():
        solution = [
            "Check IAM permissions",
            "Verify GitHub action permissions",
            "Ensure necessary environment variables are set"
        ]
    
    else:
        solution = [
            "Check logs for detailed error information",
            "Verify all dependencies are installed",
            "Check environment configuration"
        ]
    
    return {
        "error_type": error_type,
        "root_cause": f"Basic analysis for {error_type} in {workflow_name} (job: {failed_job})",
        "solution": "\n".join(solution),
        "prevention": "Implement more comprehensive error handling and improved workflow steps"
    }

def save_recovery_plan(analysis: Dict[str, Any], output_path: str = "recovery_plan.json"):
    """Save the recovery analysis to a file"""
    
    # Ensure analysis has the required fields
    if "error_type" not in analysis:
        analysis["error_type"] = "unknown"
    if "root_cause" not in analysis:
        analysis["root_cause"] = "Unknown root cause"
    if "solution" not in analysis:
        analysis["solution"] = "No solution provided"
    if "prevention" not in analysis:
        analysis["prevention"] = "Implement more comprehensive error handling"
    
    try:
        with open(output_path, "w") as f:
            json.dump(analysis, f, indent=2)
        logger.info(f"Recovery plan saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save recovery plan: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Inframate Error Recovery Tool")
    parser.add_argument("--error-type", type=str, default="auto_detect", help="Type of error to handle")
    parser.add_argument("--workflow-id", type=str, help="ID of the failed workflow")
    parser.add_argument("--workflow-name", type=str, default="Unknown", help="Name of the failed workflow")
    parser.add_argument("--failed-job", type=str, default="Unknown", help="Name of the failed job")
    parser.add_argument("--error-logs", type=str, help="Error logs from the failed job")
    parser.add_argument("--error-file", type=str, help="Path to the error file (deprecated)")
    parser.add_argument("--repo-path", type=str, default=".", help="Path to the repository")
    parser.add_argument("--autonomous", action="store_true", help="Run in autonomous mode")
    parser.add_argument("--output", type=str, default="recovery_plan.json", help="Output file path")
    
    args = parser.parse_args()
    
    logger.info(f"Starting error recovery process...")
    logger.info(f"Error type: {args.error_type}")
    logger.info(f"Workflow name: {args.workflow_name}")
    logger.info(f"Failed job: {args.failed_job}")
    
    # Initialize the Gemini model if available
    model = setup_gemini_api()
    
    # Get error logs from argument or file
    error_logs = args.error_logs or "No error logs provided"
    
    # Analyze the error
    analysis = analyze_error(
        args.error_type,
        args.workflow_name,
        args.failed_job,
        error_logs,
        model
    )
    
    # Save recovery plan
    success = save_recovery_plan(analysis, args.output)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 