#!/usr/bin/env python3
"""
Error Injection Utility for Inframate

This script demonstrates the error handling capabilities of Inframate
by simulating different types of errors and showing how they are handled.

Usage:
  python examples/inject_error.py [error_type]

Error Types:
  terraform - Terraform syntax/resource errors
  api - API rate limit errors
  resource - Resource conflict errors
  unrecoverable - Unrecoverable system errors
"""

import sys
import os
import json
import time
import asyncio
from pathlib import Path

# Add parent directory to path to import Inframate modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity
except ImportError:
    print("Error: Inframate modules not found. Make sure you're running from the project root.")
    sys.exit(1)

def inject_terraform_error():
    """Simulate Terraform syntax and resource errors"""
    handler = ErrorLoopHandler()
    
    print("🧪 Simulating Terraform syntax error...")
    
    # Simulate a Terraform syntax error
    error_message = """
    Error: Error parsing /path/to/main.tf: Invalid block definition
    
    on main.tf line 15:
      15: resource aws_instance "example" {
    
    A block definition must have block content delimited by "{" and "}", starting on the same line as the block header.
    """
    
    context_data = {
        "file": "main.tf",
        "line": 15,
        "terraform_version": "1.5.0",
        "action": "terraform plan",
        "repository": "example-repo"
    }
    
    print(f"Error Message: {error_message.strip()}")
    print(f"Context Data: {json.dumps(context_data, indent=2)}")
    print("\nProcessing error with AI-powered handler...\n")
    
    # Handle the error and get results
    start_time = time.time()
    success, solution = handler.handle_error(
        error_type="terraform_error",
        message=error_message,
        severity=ErrorSeverity.HIGH,
        context_data=context_data
    )
    elapsed_time = time.time() - start_time
    
    # Display results
    print(f"⏱️ Processing time: {elapsed_time:.2f} seconds")
    print(f"✅ Recovery successful: {success}")
    
    if solution:
        print("\n🤖 AI Solution:")
        print(f"🔍 Root cause: {solution.get('root_cause', 'Unknown')}")
        print(f"🛠️ Solution: {solution.get('solution', 'Not provided')}")
        print(f"🛡️ Prevention: {solution.get('prevention', 'Not provided')}")
    else:
        print("\n❌ No AI solution was generated")
    
    # Return for additional testing
    return success, solution

def inject_api_error():
    """Simulate API rate limit errors"""
    handler = ErrorLoopHandler()
    
    print("🧪 Simulating API rate limit error...")
    
    # Simulate a rate limit error
    error_message = "Rate limit exceeded: API calls quota exceeded for Gemini API, retry after 60 seconds"
    
    context_data = {
        "api": "Gemini",
        "endpoint": "/v1beta/models/gemini-2.0-flash:generateContent",
        "status_code": 429,
        "headers": {
            "Retry-After": "60"
        }
    }
    
    print(f"Error Message: {error_message}")
    print(f"Context Data: {json.dumps(context_data, indent=2)}")
    print("\nProcessing error with automatic retry logic...\n")
    
    # Handle the error
    start_time = time.time()
    success, solution = handler.handle_error(
        error_type="api_error",
        message=error_message,
        severity=ErrorSeverity.MEDIUM,
        context_data=context_data
    )
    elapsed_time = time.time() - start_time
    
    # Display results
    print(f"⏱️ Processing time: {elapsed_time:.2f} seconds")
    print(f"✅ Recovery successful: {success}")
    
    if solution:
        print("\n🤖 AI Solution:")
        print(f"🔍 Root cause: {solution.get('root_cause', 'Unknown')}")
        print(f"🛠️ Solution: {solution.get('solution', 'Not provided')}")
        print(f"🛡️ Prevention: {solution.get('prevention', 'Not provided')}")
    
    # Show how many retries were performed
    print(f"\n🔄 Retries performed: {len(handler.supervisor.error_history)}")
    
    return success, solution

def inject_resource_conflict():
    """Simulate resource conflict errors"""
    handler = ErrorLoopHandler()
    
    print("🧪 Simulating resource conflict error...")
    
    # Simulate a resource conflict
    error_message = """
    Error: Error creating DB Instance: DBInstanceAlreadyExists: DB instance already exists
    Status code: 400, request id: 5da782a5-c397-45a3-9b6d-1234567890ab
    
    on main.tf line 25, in resource "aws_db_instance" "database":
      25: resource "aws_db_instance" "database" {
    """
    
    context_data = {
        "resource_type": "aws_db_instance",
        "resource_name": "database",
        "aws_region": "us-west-2",
        "error_code": "DBInstanceAlreadyExists"
    }
    
    print(f"Error Message: {error_message.strip()}")
    print(f"Context Data: {json.dumps(context_data, indent=2)}")
    print("\nProcessing resource conflict with AI-powered handler...\n")
    
    # Handle the error
    start_time = time.time()
    success, solution = handler.handle_error(
        error_type="resource_conflict",
        message=error_message,
        severity=ErrorSeverity.HIGH,
        context_data=context_data
    )
    elapsed_time = time.time() - start_time
    
    # Display results
    print(f"⏱️ Processing time: {elapsed_time:.2f} seconds")
    print(f"✅ Recovery successful: {success}")
    
    if solution:
        print("\n🤖 AI Solution:")
        print(f"🔍 Root cause: {solution.get('root_cause', 'Unknown')}")
        print(f"🛠️ Solution: {solution.get('solution', 'Not provided')}")
        print(f"🛡️ Prevention: {solution.get('prevention', 'Not provided')}")
    
    return success, solution

def inject_unrecoverable_error():
    """Simulate unrecoverable system errors"""
    handler = ErrorLoopHandler()
    
    print("🧪 Simulating unrecoverable system error...")
    
    # Simulate a critical system error
    error_message = """
    Fatal error: Could not access the AWS credentials. 
    AccessDenied: User: arn:aws:iam::123456789012:user/terraform is not authorized to perform: sts:AssumeRole on resource: arn:aws:iam::987654321098:role/OrganizationAccountAccessRole
    """
    
    context_data = {
        "aws_credentials_file": "~/.aws/credentials",
        "aws_config_file": "~/.aws/config",
        "environment": "production",
        "role": "arn:aws:iam::987654321098:role/OrganizationAccountAccessRole",
        "user": "arn:aws:iam::123456789012:user/terraform"
    }
    
    print(f"Error Message: {error_message.strip()}")
    print(f"Context Data: {json.dumps(context_data, indent=2)}")
    print("\nProcessing unrecoverable error with AI-powered analysis...\n")
    
    # Handle the error
    start_time = time.time()
    success, solution = handler.handle_error(
        error_type="unrecoverable_error",
        message=error_message,
        severity=ErrorSeverity.CRITICAL,
        context_data=context_data
    )
    elapsed_time = time.time() - start_time
    
    # Display results
    print(f"⏱️ Processing time: {elapsed_time:.2f} seconds")
    print(f"✅ Recovery successful: {success}")
    
    if solution:
        print("\n🤖 AI Solution:")
        print(f"🔍 Root cause: {solution.get('root_cause', 'Unknown')}")
        print(f"🛠️ Solution: {solution.get('solution', 'Not provided')}")
        print(f"🛡️ Prevention: {solution.get('prevention', 'Not provided')}")
    
    # Generate error report
    error_report = handler.get_error_report()
    report_path = Path("error_report.json")
    
    with open(report_path, "w") as f:
        json.dump(error_report, f, indent=2)
    
    print(f"\n📊 Full error report saved to: {report_path.absolute()}")
    
    return success, solution

def main():
    """Main entry point"""
    print("=" * 80)
    print("🤖 Inframate Error Injection Utility")
    print("=" * 80)
    
    # Check for Gemini API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠️ GEMINI_API_KEY not set in environment. AI-powered solutions will be limited.")
        print("Set the environment variable with: export GEMINI_API_KEY=your_key_here")
    
    # Get error type from command line argument or use default
    error_type = sys.argv[1] if len(sys.argv) > 1 else "terraform"
    
    # Check API key
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # Dispatch to appropriate error injection function
    dispatch = {
        "terraform": inject_terraform_error,
        "api": inject_api_error,
        "resource": inject_resource_conflict,
        "unrecoverable": inject_unrecoverable_error
    }
    
    if error_type not in dispatch:
        print(f"Error: Unknown error type '{error_type}'")
        print("Available error types: terraform, api, resource, unrecoverable")
        sys.exit(1)
    
    # Run the error injection function
    dispatch[error_type]()
    
    print("\n" + "=" * 80)
    print("✨ Error injection completed")
    print("=" * 80)

if __name__ == "__main__":
    main() 