#!/usr/bin/env python3
"""
Error Flow Demonstration for Inframate

This script demonstrates how the error handling secondary flow works in Inframate
by deliberately triggering errors and showing how they are handled by the system.

Usage:
  python examples/error_flow_demo.py --error-type ERROR_TYPE [--repo-path REPO_PATH]

Error Types:
  terraform - Terraform syntax/resource errors
  api - API rate limit errors
  network - Network connectivity errors
  permission - Permission/access denied errors
  validation - Input validation errors
  unrecoverable - Unrecoverable system errors
"""

import os
import sys
import json
import time
import argparse
import random
from pathlib import Path

# Add parent directory to path to import Inframate modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity
    from scripts.agentic_error_workflow import AgenticWorkflow, ErrorType
except ImportError:
    print("Error: Inframate modules not found. Make sure you're running from the project root.")
    sys.exit(1)

def simulate_terraform_error(repo_path):
    """Simulate a Terraform error flow"""
    print("🧪 Simulating Terraform error with secondary flow...")
    
    # Create a workflow that will trigger a deliberate error
    workflow = AgenticWorkflow(
        repo_path=repo_path,
        action="analyze",
        autonomous=True
    )
    
    # Patch the _analyze_infrastructure_impl method to raise a Terraform error
    def patched_analyze(*args, **kwargs):
        error_message = """
        Error: Error applying plan:

        1 error occurred:
            * aws_instance.example: 1 error occurred:
            * aws_instance.example: Error launching source instance: 
              InvalidParameterValue: Value (ami-12345) for parameter imageId is invalid.
        """
        raise Exception(f"Terraform error: {error_message}")
    
    # Save original method and patch
    original_method = workflow._analyze_repo
    workflow._analyze_repo = patched_analyze
    
    try:
        # Run the workflow which will trigger our simulated error
        print("\n📋 Running workflow with deliberate Terraform error...")
        start_time = time.time()
        results = workflow.execute()
        elapsed_time = time.time() - start_time
        
        # Display results
        print(f"\n⏱️ Total execution time: {elapsed_time:.2f} seconds")
        print("\n📊 Results:")
        print(f"✅ Success: {results['success']}")
        
        if not results['success']:
            print(f"❌ Error Type: {results.get('error', {}).get('type', 'Unknown')}")
            print(f"❌ Error Message: {results.get('error', {}).get('message', 'Unknown')}")
            
            # Show recovery attempts
            recovery_attempts = results.get('error', {}).get('recovery_attempts', [])
            if recovery_attempts:
                print(f"\n🔄 Recovery Attempts: {len(recovery_attempts)}")
                for i, attempt in enumerate(recovery_attempts):
                    print(f"  Attempt #{i+1}:")
                    print(f"  - Success: {attempt.get('success', False)}")
                    print(f"  - Duration: {attempt.get('duration', 0):.2f} seconds")
            
            # Show AI solution
            ai_solution = results.get('error', {}).get('ai_solution', {})
            if ai_solution:
                print("\n🤖 AI-Generated Solution:")
                print(f"  Root Cause: {ai_solution.get('root_cause', 'Unknown')}")
                
                solution_text = ai_solution.get('solution', 'No solution provided')
                print(f"  Solution: {solution_text[:100]}..." if len(solution_text) > 100 else f"  Solution: {solution_text}")
                
                prevention = ai_solution.get('prevention', 'No prevention tips provided')
                print(f"  Prevention: {prevention[:100]}..." if len(prevention) > 100 else f"  Prevention: {prevention}")
        
        # Save results to file
        output_file = "error_flow_terraform_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
        
    finally:
        # Restore original method
        workflow._analyze_repo = original_method

def simulate_api_error(repo_path):
    """Simulate an API rate limit error flow"""
    print("🧪 Simulating API rate limit error with secondary flow...")
    
    # Create a workflow
    workflow = AgenticWorkflow(
        repo_path=repo_path,
        action="optimize",
        autonomous=True
    )
    
    # Patch the method to raise an API rate limit error
    def patched_optimize(*args, **kwargs):
        error_message = "Rate limit exceeded: API calls quota exceeded for Gemini API, retry after 60 seconds"
        raise Exception(f"API error: {error_message}")
    
    # Save original method and patch
    original_method = workflow._optimize_infra
    workflow._optimize_infra = patched_optimize
    
    try:
        # Run the workflow which will trigger our simulated error
        print("\n📋 Running workflow with deliberate API rate limit error...")
        start_time = time.time()
        results = workflow.execute()
        elapsed_time = time.time() - start_time
        
        # Display results
        print(f"\n⏱️ Total execution time: {elapsed_time:.2f} seconds")
        print("\n📊 Results:")
        print(f"✅ Success: {results['success']}")
        
        if not results['success']:
            print(f"❌ Error Type: {results.get('error', {}).get('type', 'Unknown')}")
            print(f"❌ Error Message: {results.get('error', {}).get('message', 'Unknown')}")
            
            # Show recovery attempts
            recovery_attempts = results.get('error', {}).get('recovery_attempts', [])
            if recovery_attempts:
                print(f"\n🔄 Recovery Attempts: {len(recovery_attempts)}")
                for i, attempt in enumerate(recovery_attempts):
                    print(f"  Attempt #{i+1}:")
                    print(f"  - Success: {attempt.get('success', False)}")
                    print(f"  - Duration: {attempt.get('duration', 0):.2f} seconds")
            
        # Save results to file
        output_file = "error_flow_api_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
        
    finally:
        # Restore original method
        workflow._optimize_infra = original_method

def simulate_permission_error(repo_path):
    """Simulate a permission denied error flow"""
    print("🧪 Simulating permission denied error with secondary flow...")
    
    # Create a workflow
    workflow = AgenticWorkflow(
        repo_path=repo_path,
        action="secure",
        autonomous=True
    )
    
    # Patch the method to raise a permission error
    def patched_secure(*args, **kwargs):
        error_message = """
        Error: AccessDeniedException: User: arn:aws:iam::123456789012:user/terraform is not authorized to 
        perform: sts:AssumeRole on resource: arn:aws:iam::987654321098:role/OrganizationAccountAccessRole
        """
        raise PermissionError(error_message)
    
    # Save original method and patch
    original_method = workflow._secure_infra
    workflow._secure_infra = patched_secure
    
    try:
        # Run the workflow which will trigger our simulated error
        print("\n📋 Running workflow with deliberate permission error...")
        start_time = time.time()
        results = workflow.execute()
        elapsed_time = time.time() - start_time
        
        # Display results
        print(f"\n⏱️ Total execution time: {elapsed_time:.2f} seconds")
        print("\n📊 Results:")
        print(f"✅ Success: {results['success']}")
        
        if not results['success']:
            print(f"❌ Error Type: {results.get('error', {}).get('type', 'Unknown')}")
            print(f"❌ Error Message: {results.get('error', {}).get('message', 'Unknown')}")
            
            # Show recovery attempts
            recovery_attempts = results.get('error', {}).get('recovery_attempts', [])
            if recovery_attempts:
                print(f"\n🔄 Recovery Attempts: {len(recovery_attempts)}")
                for i, attempt in enumerate(recovery_attempts):
                    print(f"  Attempt #{i+1}:")
                    print(f"  - Success: {attempt.get('success', False)}")
                    print(f"  - Duration: {attempt.get('duration', 0):.2f} seconds")
            
            # Show AI solution
            ai_solution = results.get('error', {}).get('ai_solution', {})
            if ai_solution:
                print("\n🤖 AI-Generated Solution:")
                print(f"  Root Cause: {ai_solution.get('root_cause', 'Unknown')}")
                
                solution_text = ai_solution.get('solution', 'No solution provided')
                print(f"  Solution: {solution_text[:100]}..." if len(solution_text) > 100 else f"  Solution: {solution_text}")
        
        # Save results to file
        output_file = "error_flow_permission_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
        
    finally:
        # Restore original method
        workflow._secure_infra = original_method

def simulate_multi_error_auto(repo_path):
    """Simulate the auto flow with multiple errors"""
    print("🧪 Simulating auto flow with multiple errors and secondary flow...")
    
    # Create a workflow
    workflow = AgenticWorkflow(
        repo_path=repo_path,
        action="auto",
        autonomous=True
    )
    
    # Create a list of errors to simulate
    errors = [
        ("API rate limit exceeded", ErrorType.API.value, ErrorSeverity.MEDIUM),
        ("Permission denied to access resource", ErrorType.PERMISSION.value, ErrorSeverity.HIGH),
        ("Terraform state lock could not be acquired", ErrorType.TERRAFORM.value, ErrorSeverity.HIGH)
    ]
    
    # Override the handle_error method to simulate random recovery success
    original_handle_error = workflow.error_handler.handle_error
    
    def patched_handle_error(error_type, message, severity, context_data=None):
        print(f"  Handling error: {error_type}")
        
        # Wait a random time to simulate processing
        time.sleep(random.uniform(0.5, 2.0))
        
        # Random recovery success
        success = random.choice([True, True, False])
        
        # Create a simulated AI solution
        ai_solution = {
            "root_cause": f"Simulated root cause for {error_type}",
            "solution": f"Steps to resolve {error_type}:\n1. Step one\n2. Step two\n3. Step three",
            "prevention": f"To prevent {error_type} in the future, implement these best practices..."
        }
        
        print(f"  Recovery success: {success}")
        return success, ai_solution
    
    # Patch the _auto_manage method to simulate multiple errors
    original_auto_manage = workflow._auto_manage
    
    def patched_auto_manage(*args, **kwargs):
        print("\n📋 Running auto workflow with multiple simulated errors...")
        
        # Simulate running multiple actions with errors
        for i, (error_msg, error_type, severity) in enumerate(errors):
            print(f"\n➡️ Step {i+1}: Simulating {error_type} error")
            
            # Simulate start of action
            time.sleep(1)
            
            # Simulate error detection and entry into secondary flow
            workflow.error_state = workflow.error_state.DETECTED
            
            # Execute error flow
            context_data = {
                "stack_trace": f"Simulated stack trace for {error_type}",
                "action": f"action_{i}",
                "repo_path": repo_path
            }
            
            # Run error flow
            workflow._execute_error_flow(error_type, error_msg, severity, context_data)
            
            # Record in results
            workflow.results["errors"].append({
                "type": error_type,
                "message": error_msg,
                "recovery_success": workflow.recovery_history[-1]["success"] if workflow.recovery_history else False
            })
        
        # Simulate completion
        workflow.results["autonomous_actions"] = {
            "applied_changes": [
                "Simulated change 1",
                "Simulated change 2",
                "Simulated change 3"
            ],
            "failures": [
                {
                    "action": "action_1",
                    "error_type": errors[0][1],
                    "message": errors[0][0],
                    "recovery_success": workflow.recovery_history[0]["success"] if workflow.recovery_history else False
                } if not workflow.recovery_history[0]["success"] else None,
                {
                    "action": "action_2",
                    "error_type": errors[1][1],
                    "message": errors[1][0],
                    "recovery_success": workflow.recovery_history[1]["success"] if len(workflow.recovery_history) > 1 else False
                } if len(workflow.recovery_history) > 1 and not workflow.recovery_history[1]["success"] else None,
                {
                    "action": "action_3",
                    "error_type": errors[2][1],
                    "message": errors[2][0],
                    "recovery_success": workflow.recovery_history[2]["success"] if len(workflow.recovery_history) > 2 else False
                } if len(workflow.recovery_history) > 2 and not workflow.recovery_history[2]["success"] else None
            ]
        }
        
        # Remove None values from failures
        workflow.results["autonomous_actions"]["failures"] = [
            f for f in workflow.results["autonomous_actions"]["failures"] if f is not None
        ]
        
        # Set overall success based on recovery successes
        workflow.results["success"] = all(
            attempt.get("success", False) for attempt in workflow.recovery_history
        )
        
        return workflow.results
    
    try:
        # Apply patches
        workflow.error_handler.handle_error = patched_handle_error
        workflow._auto_manage = patched_auto_manage
        
        # Run the workflow which will simulate multiple errors
        start_time = time.time()
        results = workflow.execute()
        elapsed_time = time.time() - start_time
        
        # Display results
        print(f"\n⏱️ Total execution time: {elapsed_time:.2f} seconds")
        print("\n📊 Results Summary:")
        print(f"✅ Overall Success: {results['success']}")
        print(f"🔄 Total Error Count: {len(results.get('errors', []))}")
        print(f"🔄 Recovery Attempts: {len(workflow.recovery_history)}")
        
        # Calculate recovery rate
        successful_recoveries = sum(1 for attempt in workflow.recovery_history if attempt.get("success", False))
        recovery_rate = successful_recoveries / len(workflow.recovery_history) if workflow.recovery_history else 0
        print(f"✅ Recovery Success Rate: {recovery_rate:.0%}")
        
        # Save results to file
        output_file = "error_flow_multi_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
        
    finally:
        # Restore original methods
        workflow.error_handler.handle_error = original_handle_error
        workflow._auto_manage = original_auto_manage

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Inframate Error Flow Demonstration')
    parser.add_argument('--error-type', choices=['terraform', 'api', 'permission', 'multi'], 
                       default='terraform', help='Type of error to simulate')
    parser.add_argument('--repo-path', default='.', help='Path to repository (can be any directory)')
    return parser.parse_args()

def main():
    """Main entry point"""
    print("=" * 80)
    print("🤖 Inframate Error Handling Secondary Flow Demonstration")
    print("=" * 80)
    
    args = parse_args()
    
    # Check for Gemini API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠️ GEMINI_API_KEY not set in environment. AI-powered solutions will be limited.")
        print("Set the environment variable with: export GEMINI_API_KEY=your_key_here")
    
    # Run the appropriate simulation
    if args.error_type == 'terraform':
        simulate_terraform_error(args.repo_path)
    elif args.error_type == 'api':
        simulate_api_error(args.repo_path)
    elif args.error_type == 'permission':
        simulate_permission_error(args.repo_path)
    elif args.error_type == 'multi':
        simulate_multi_error_auto(args.repo_path)
    
    print("\n" + "=" * 80)
    print("✨ Error flow demonstration completed")
    print("=" * 80)

if __name__ == "__main__":
    main() 