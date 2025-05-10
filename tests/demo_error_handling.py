#!/usr/bin/env python3
"""
Demonstration of AI-powered error handling with Gemini
Run this script with:
    GEMINI_API_KEY=your_api_key python tests/demo_error_handling.py
"""

import os
import sys
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity

def simulate_terraform_error():
    """Simulate a Terraform execution error"""
    
    # Initialize error handler
    handler = ErrorLoopHandler()
    
    # Prepare error details
    error_type = "terraform_error"
    error_message = """
    Error: Error creating DB Instance: DBInstanceAlreadyExists: DB instance already exists
    Status code: 400, request id: 5da782a5-c397-45a3-9b6d-1234567890abc
    
    on main.tf line 25, in resource "aws_db_instance" "database":
      25: resource "aws_db_instance" "database" {
    """
    
    context_data = {
        "terraform_version": "1.5.0",
        "aws_resource": "aws_db_instance",
        "resource_name": "database",
        "file": "main.tf",
        "line": 25
    }
    
    # Handle the error with AI assistance
    print(f"Handling error: {error_type}")
    print(f"Error message: {error_message}")
    print("Context data:", json.dumps(context_data, indent=2))
    print("\nSending to Gemini for analysis...")
    
    recovery_success, ai_solution = handler.handle_error(
        error_type=error_type,
        message=error_message,
        severity=ErrorSeverity.HIGH,
        context_data=context_data
    )
    
    # Display results
    print("\n" + "="*50)
    print("RECOVERY ATTEMPT RESULT")
    print("="*50)
    print(f"Recovery successful: {recovery_success}")
    print("\n" + "="*50)
    print("AI SOLUTION")
    print("="*50)
    if ai_solution:
        print(json.dumps(ai_solution, indent=2))
    else:
        print("No AI solution available. Make sure GEMINI_API_KEY is set.")
    
    # Display error report
    print("\n" + "="*50)
    print("ERROR REPORT")
    print("="*50)
    error_report = handler.get_error_report()
    print(json.dumps(error_report, indent=2))

def simulate_api_error():
    """Simulate an API rate limit error"""
    
    # Initialize error handler
    handler = ErrorLoopHandler()
    
    # Prepare error details
    error_type = "api_error"
    error_message = "Rate limit exceeded: API calls quota exceeded, retry after 60 seconds"
    
    context_data = {
        "api_name": "aws_s3_api",
        "endpoint": "/buckets",
        "rate_limit": "100 requests per minute",
        "current_rate": "120 requests per minute"
    }
    
    # Handle the error with AI assistance
    print(f"Handling error: {error_type}")
    print(f"Error message: {error_message}")
    print("Context data:", json.dumps(context_data, indent=2))
    print("\nSending to Gemini for analysis...")
    
    recovery_success, ai_solution = handler.handle_error(
        error_type=error_type,
        message=error_message,
        severity=ErrorSeverity.MEDIUM,
        context_data=context_data
    )
    
    # Display results
    print("\n" + "="*50)
    print("RECOVERY ATTEMPT RESULT")
    print("="*50)
    print(f"Recovery successful: {recovery_success}")
    print("\n" + "="*50)
    print("AI SOLUTION")
    print("="*50)
    if ai_solution:
        print(json.dumps(ai_solution, indent=2))
    else:
        print("No AI solution available. Make sure GEMINI_API_KEY is set.")
    
    # Display error report
    print("\n" + "="*50)
    print("ERROR REPORT")
    print("="*50)
    error_report = handler.get_error_report()
    print(json.dumps(error_report, indent=2))

if __name__ == "__main__":
    # Check if Gemini API key is set
    if not os.environ.get("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY environment variable not set.")
        print("AI-powered solutions will not be available.")
    
    # Simulate errors
    simulate_terraform_error()
    print("\n\n" + "="*70)
    print("SIMULATING ANOTHER ERROR TYPE")
    print("="*70 + "\n")
    simulate_api_error() 