#!/usr/bin/env python3
"""
Error Recovery Script for CI/CD Environments

This script analyzes workflow execution errors and attempts automated recovery.
It integrates with GitHub Actions and can be run both automatically and manually.

Usage:
  python scripts/error_recovery_script.py --error-type TYPE --error-message MSG [--repo-path PATH] [--autonomous]
"""

import os
import sys
import json
import argparse
import logging
import time
import subprocess
from pathlib import Path
from typing import Dict, Optional, Any, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity
    import google.generativeai as genai
except ImportError:
    print("Error: Required modules not found. Please install missing dependencies.")
    sys.exit(1)

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

def setup_gemini_api():
    """Setup Gemini API with proper error handling"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not found in environment variables")
        return None
    
    try:
        genai.configure(api_key=api_key)
        # Use the updated model version
        return genai.GenerativeModel('gemini-2.5-pro-exp-03-25')
    except Exception as e:
        logger.error(f"Failed to initialize Gemini API: {e}")
        return None

def analyze_error(error_type: str, error_message: str, model) -> Dict[str, Any]:
    """
    Analyze an error with Gemini AI and generate recovery steps
    
    Args:
        error_type: Type of error (terraform_error, api_error, etc.)
        error_message: Detailed error message
        model: Initialized Gemini model
    
    Returns:
        Dictionary with analysis results
    """
    if not model:
        logger.warning("Gemini model not available, using basic analysis")
        return _basic_analysis(error_type, error_message)
    
    prompt = f"""
    As an infrastructure deployment expert, analyze this error and provide recovery steps:
    
    ERROR TYPE: {error_type}
    ERROR MESSAGE: {error_message}
    
    Please provide:
    1. Root cause analysis
    2. Step-by-step recovery instructions
    3. Preventive measures
    
    Format your response as JSON with these keys:
    - root_cause: Brief explanation of what caused the error
    - recovery_steps: Array of specific commands or actions to fix the issue
    - prevention: How to prevent this error in the future
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
                "root_cause": "Analysis failed to return structured data",
                "recovery_steps": [f"Manual analysis required: {solution[:200]}..."],
                "prevention": "Improve error handling"
            }
    
    except Exception as e:
        logger.error(f"Error analyzing with Gemini: {e}")
        return _basic_analysis(error_type, error_message)

def _basic_analysis(error_type: str, error_message: str) -> Dict[str, Any]:
    """Provide basic error analysis when AI is not available"""
    recovery_steps = []
    
    if error_type == "terraform_error":
        if "state_lock" in error_message.lower():
            recovery_steps = [
                "Wait for any running Terraform operations to complete",
                "Run: terraform force-unlock [LOCK_ID]",
                "Retry the failed operation"
            ]
        elif "no such file" in error_message.lower():
            recovery_steps = [
                "Run: terraform init",
                "Retry the failed operation"
            ]
        else:
            recovery_steps = [
                "Check Terraform configuration files for syntax errors",
                "Verify AWS credentials are properly configured",
                "Run: terraform validate"
            ]
    
    elif error_type == "api_error":
        if "rate limit" in error_message.lower():
            recovery_steps = [
                "Wait for rate limit to reset (usually 1 hour)",
                "Retry the operation with exponential backoff"
            ]
        else:
            recovery_steps = [
                "Check API credentials",
                "Verify network connectivity",
                "Retry with exponential backoff"
            ]
    
    elif error_type == "permission_error":
        recovery_steps = [
            "Check IAM permissions",
            "Verify GitHub action permissions",
            "Ensure necessary environment variables are set"
        ]
    
    elif error_type == "network_error":
        recovery_steps = [
            "Check network connectivity",
            "Verify firewall settings",
            "Retry the operation with exponential backoff"
        ]
    
    else:
        recovery_steps = [
            "Check logs for detailed error information",
            "Verify all dependencies are installed",
            "Check environment configuration"
        ]
    
    return {
        "root_cause": f"Basic analysis for {error_type}: {error_message[:100]}...",
        "recovery_steps": recovery_steps,
        "prevention": "Implement more comprehensive error handling"
    }

def apply_recovery_steps(steps: List[str], repo_path: str, autonomous: bool) -> bool:
    """
    Apply recovery steps based on the error analysis
    
    Args:
        steps: List of recovery steps to apply
        repo_path: Path to the repository
        autonomous: Whether to apply steps automatically
    
    Returns:
        Success status (True/False)
    """
    if not steps:
        logger.error("No recovery steps provided")
        return False
    
    logger.info(f"Applying {len(steps)} recovery steps")
    
    for i, step in enumerate(steps):
        logger.info(f"Step {i+1}: {step}")
        
        # Extract command if present in the step
        command = None
        if "Run:" in step:
            command = step.split("Run:")[1].strip()
        elif "Execute:" in step:
            command = step.split("Execute:")[1].strip()
        elif ":" in step and any(cmd in step.lower() for cmd in ["terraform", "aws ", "git ", "python", "npm", "mkdir"]):
            command = step.split(":", 1)[1].strip()
        
        if command and autonomous:
            try:
                logger.info(f"Executing: {command}")
                result = subprocess.run(
                    command, 
                    shell=True, 
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info(f"Command succeeded: {result.stdout[:100]}")
                else:
                    logger.error(f"Command failed: {result.stderr[:100]}")
                    return False
            except Exception as e:
                logger.error(f"Failed to execute command: {e}")
                return False
        elif command:
            logger.info(f"Suggested command (not executed in non-autonomous mode): {command}")
        
        time.sleep(1)  # Small delay between steps
    
    return True

def save_recovery_report(analysis: Dict[str, Any], success: bool, output_path: str = "recovery_report.json"):
    """Save the recovery analysis and results to a file"""
    report = {
        "timestamp": time.time(),
        "analysis": analysis,
        "recovery_success": success,
        "actions_taken": []
    }
    
    try:
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Recovery report saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save recovery report: {e}")

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description="Error recovery script for CI/CD environments")
    parser.add_argument("--error-type", required=True, help="Type of error to recover from")
    parser.add_argument("--error-message", required=True, help="Error message")
    parser.add_argument("--repo-path", default=".", help="Path to repository")
    parser.add_argument("--autonomous", action="store_true", help="Apply recovery steps automatically")
    parser.add_argument("--workflow-name", help="Name of the workflow that failed")
    parser.add_argument("--run-id", help="ID of the workflow run")
    parser.add_argument("--output-file", default="recovery_report.json", help="Output file path")
    
    args = parser.parse_args()
    
    logger.info(f"Starting error recovery for {args.error_type}")
    logger.info(f"Error message: {args.error_message[:100]}...")
    
    # Initialize Gemini API
    model = setup_gemini_api()
    
    # Analyze the error
    analysis = analyze_error(args.error_type, args.error_message, model)
    logger.info(f"Error analysis complete: {len(analysis.get('recovery_steps', [])) if analysis else 0} recovery steps found")
    
    # Apply recovery steps if available
    success = False
    if analysis and "recovery_steps" in analysis:
        success = apply_recovery_steps(analysis["recovery_steps"], args.repo_path, args.autonomous)
    
    # Save the report
    save_recovery_report(analysis, success, args.output_file)
    
    if success:
        logger.info("✅ Recovery completed successfully")
        print("::set-output name=recovery_status::success")
    else:
        logger.warning("❌ Recovery failed or partial")
        print("::set-output name=recovery_status::failure")
    
    # Exit with appropriate status
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 