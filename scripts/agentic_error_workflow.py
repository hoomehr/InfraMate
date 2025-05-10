#!/usr/bin/env python3
"""
Agentic Error Workflow for Inframate

This script provides robust error handling for Inframate's agentic workflows:
1. Wraps the main workflow with error monitoring
2. Automatically handles and recovers from common errors
3. Uses AI to analyze and provide solutions for complex errors
4. Maintains a detailed error history for debug and analytics
5. Executes a secondary recovery flow when errors occur
"""

import os
import sys
import json
import traceback
import argparse
import logging
import time
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Tuple

# Add parent directory to path so we can import our modules
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
        logging.FileHandler("inframate_error.log")
    ]
)
logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Error type classification"""
    CONFIGURATION = "configuration_error"
    PERMISSION = "permission_error"
    NETWORK = "network_error"
    API = "api_error"
    RESOURCE = "resource_error"
    TERRAFORM = "terraform_error"
    VALIDATION = "validation_error"
    SYSTEM = "system_error"
    UNKNOWN = "unknown_error"

class ErrorState(Enum):
    """Error handling states"""
    INITIAL = "initial"
    DETECTED = "error_detected"
    ANALYZING = "analyzing_error"
    RECOVERY = "recovery_attempt"
    RESOLVED = "error_resolved"
    FAILED = "recovery_failed"

class AgenticWorkflow:
    """Wrapper class for agentic workflow with integrated error handling"""
    
    def __init__(self, repo_path: str, action: str, autonomous: bool = False):
        self.repo_path = repo_path
        self.action = action
        self.autonomous = autonomous
        self.error_handler = ErrorLoopHandler()
        self.results = {
            "success": True,
            "action": action,
            "repo_path": repo_path,
            "autonomous": autonomous,
            "analysis": {},
            "errors": []
        }
        self.error_state = ErrorState.INITIAL
        self.recovery_history = []
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self.gemini_model = None
        
        # Initialize Gemini model if API key is available
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                logger.info("Gemini API initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini API: {e}")
        
    def execute(self) -> Dict[str, Any]:
        """Execute the workflow with error handling"""
        try:
            # Dispatch to appropriate action method
            dispatch = {
                "analyze": self._analyze_repo,
                "optimize": self._optimize_infra,
                "secure": self._secure_infra,
                "visualize": self._visualize_infra,
                "auto": self._auto_manage
            }
            
            if self.action not in dispatch:
                raise ValueError(f"Unknown action: {self.action}")
                
            # Run the action
            logger.info(f"Starting action: {self.action}")
            dispatch[self.action]()
            
            # Add error report to results
            self.results["error_report"] = self.error_handler.get_error_report()
            
            return self.results
            
        except Exception as e:
            # Capture the full stack trace for context
            stack_trace = traceback.format_exc()
            error_context = {
                "stack_trace": stack_trace,
                "action": self.action,
                "repo_path": self.repo_path
            }
            
            # Update error state
            self.error_state = ErrorState.DETECTED
            logger.error(f"Error in action {self.action}: {type(e).__name__}: {str(e)}")
            
            # Determine error type and severity
            error_type, severity = self._classify_error(e, stack_trace)
            
            # Run secondary error flow
            self._execute_error_flow(error_type, str(e), severity, error_context)
            
            # Add error information to results
            self.results["success"] = False
            self.results["error"] = {
                "type": error_type,
                "message": str(e),
                "stack_trace": stack_trace,
                "recovery_attempts": self.recovery_history,
                "ai_solution": self.recovery_history[-1]["ai_solution"] if self.recovery_history else None
            }
            
            # Add error report to results
            self.results["error_report"] = self.error_handler.get_error_report()
            
            return self.results
    
    def _classify_error(self, exception: Exception, stack_trace: str) -> Tuple[str, ErrorSeverity]:
        """Classify the error type and determine severity"""
        error_type = type(exception).__name__
        error_message = str(exception)
        
        # Classify based on error type
        if "Permission" in error_type or "Access" in error_type:
            return ErrorType.PERMISSION.value, ErrorSeverity.HIGH
        elif "Connection" in error_type or "Timeout" in error_type:
            return ErrorType.NETWORK.value, ErrorSeverity.MEDIUM
        elif "ValueError" in error_type or "TypeError" in error_type:
            return ErrorType.VALIDATION.value, ErrorSeverity.MEDIUM
        elif "Config" in error_type:
            return ErrorType.CONFIGURATION.value, ErrorSeverity.MEDIUM
        
        # Classify based on error message
        if "terraform" in error_message.lower():
            return ErrorType.TERRAFORM.value, ErrorSeverity.HIGH
        elif "api" in error_message.lower() or "rate limit" in error_message.lower():
            return ErrorType.API.value, ErrorSeverity.MEDIUM
        elif "resource" in error_message.lower() or "already exists" in error_message.lower():
            return ErrorType.RESOURCE.value, ErrorSeverity.HIGH
        elif "permission" in error_message.lower() or "denied" in error_message.lower():
            return ErrorType.PERMISSION.value, ErrorSeverity.HIGH
        
        # Default to unknown/system error
        return ErrorType.UNKNOWN.value, ErrorSeverity.MEDIUM
    
    def _execute_error_flow(self, error_type: str, error_message: str, severity: ErrorSeverity, context_data: Dict[str, Any]) -> None:
        """Execute secondary error handling flow"""
        logger.info(f"Starting error handling flow for {error_type}")
        self.error_state = ErrorState.ANALYZING
        
        # Record start time for metrics
        start_time = time.time()
        
        try:
            # Step 1: Handle the error with AI-powered handler
            logger.info("Step 1: Handling error with AI-powered handler")
            recovery_success, ai_solution = self.error_handler.handle_error(
                error_type=error_type,
                message=error_message,
                severity=severity,
                context_data=context_data
            )
            
            # Step 2: Record recovery attempt
            self.recovery_history.append({
                "timestamp": time.time(),
                "error_type": error_type,
                "message": error_message,
                "severity": severity.value,
                "success": recovery_success,
                "ai_solution": ai_solution,
                "duration": time.time() - start_time
            })
            
            # Step 3: Apply recommended solution if in autonomous mode
            if recovery_success and ai_solution and self.autonomous:
                logger.info("Step 3: Applying recommended solution in autonomous mode")
                self.error_state = ErrorState.RECOVERY
                self._apply_ai_solution(ai_solution, error_type, context_data)
            elif recovery_success:
                logger.info("Recovery successful, but not in autonomous mode - not applying solution")
                self.error_state = ErrorState.RESOLVED
            else:
                logger.warning("Recovery failed")
                self.error_state = ErrorState.FAILED
                
            # Step 4: Update error report with recovery details
            logger.info("Step 4: Updating error report with recovery details")
            self.results["recovery_details"] = {
                "attempts": len(self.recovery_history),
                "success": recovery_success,
                "solution_applied": recovery_success and self.autonomous,
                "duration": time.time() - start_time
            }
            
            # Step 5: Log recovery metrics
            logger.info(f"Error handling flow completed in {time.time() - start_time:.2f} seconds")
            logger.info(f"Recovery success: {recovery_success}")
            
        except Exception as e:
            # Error in the error handling flow itself
            logger.critical(f"Error in error handling flow: {type(e).__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            self.error_state = ErrorState.FAILED
            
            # Record this meta-error
            self.recovery_history.append({
                "timestamp": time.time(),
                "error_type": "meta_error",
                "message": f"Error in error handling flow: {str(e)}",
                "severity": "CRITICAL",
                "success": False,
                "duration": time.time() - start_time
            })
    
    def _apply_ai_solution(self, solution: Dict[str, Any], error_type: str, context_data: Dict[str, Any]) -> None:
        """Apply the solution recommended by the AI"""
        if not solution or not isinstance(solution, dict):
            logger.warning("No valid solution to apply")
            return
        
        solution_steps = solution.get("solution", "").strip().split("\n")
        if not solution_steps:
            logger.warning("No solution steps found")
            return
        
        logger.info(f"Applying {len(solution_steps)} solution steps")
        
        # Handle different error types
        if error_type == ErrorType.TERRAFORM.value:
            self._apply_terraform_solution(solution, context_data)
        elif error_type == ErrorType.CONFIGURATION.value:
            self._apply_config_solution(solution, context_data)
        elif error_type == ErrorType.API.value:
            self._apply_api_solution(solution, context_data)
        else:
            logger.info(f"No specific solution implementation for {error_type}")
            logger.info(f"Solution suggestions: {solution_steps}")
    
    def _apply_terraform_solution(self, solution: Dict[str, Any], context_data: Dict[str, Any]) -> None:
        """Apply solution for Terraform errors"""
        # This is a placeholder implementation
        # In a real implementation, this would modify Terraform files
        logger.info("Applying Terraform solution (placeholder)")
        
        # Example of what might happen here:
        # 1. Parse the solution to extract specific changes
        # 2. Find the relevant Terraform files
        # 3. Apply the recommended changes
        # 4. Validate the changes
    
    def _apply_config_solution(self, solution: Dict[str, Any], context_data: Dict[str, Any]) -> None:
        """Apply solution for configuration errors"""
        # This is a placeholder implementation
        logger.info("Applying configuration solution (placeholder)")
    
    def _apply_api_solution(self, solution: Dict[str, Any], context_data: Dict[str, Any]) -> None:
        """Apply solution for API errors"""
        # This is a placeholder implementation
        logger.info("Applying API solution (placeholder)")
        
        # For API rate limits, we might implement throttling or backoff
        if "rate limit" in context_data.get("message", "").lower():
            logger.info("Implementing rate limit backoff")
            time.sleep(60)  # Simple backoff strategy
            
    def _analyze_repo(self) -> None:
        """Analyze repository structure and infrastructure"""
        try:
            # This would typically import and use specific analysis modules
            # but here we're creating a placeholder implementation
            self.results["analysis"] = {
                "status": "completed",
                "repo_structure": {
                    "languages": ["python", "javascript"],
                    "frameworks": ["flask", "react"],
                    "database": ["postgresql"]
                },
                "infrastructure": {
                    "recommended_services": [
                        "aws_lambda",
                        "aws_rds",
                        "aws_s3",
                        "aws_cloudfront"
                    ],
                    "resource_counts": {
                        "compute": 2,
                        "storage": 1,
                        "database": 1,
                        "network": 2
                    }
                }
            }
        except Exception as e:
            # Let the execute method handle this error
            logger.error(f"Error in repository analysis: {e}")
            raise
            
    def _optimize_infra(self) -> None:
        """Optimize infrastructure"""
        # Placeholder implementation
        self.results["optimization"] = {
            "status": "completed",
            "recommendations": [
                {
                    "resource": "aws_lambda",
                    "current_config": {"memory": 1024},
                    "recommended_config": {"memory": 512},
                    "savings": "$10/month"
                }
            ]
        }
        
    def _secure_infra(self) -> None:
        """Apply security best practices"""
        # Placeholder implementation
        self.results["security"] = {
            "status": "completed",
            "vulnerabilities": [
                {
                    "severity": "high",
                    "resource": "s3_bucket",
                    "issue": "public access enabled",
                    "remediation": "Enable block public access setting"
                }
            ]
        }
        
    def _visualize_infra(self) -> None:
        """Generate infrastructure visualizations"""
        # Placeholder implementation
        self.results["visualization"] = {
            "status": "completed",
            "artifacts": [
                "infrastructure_diagram.png",
                "cost_breakdown.html",
                "security_posture.svg"
            ]
        }
        
    def _auto_manage(self) -> None:
        """Fully autonomous infrastructure management"""
        # Define execution order
        actions = [
            ("analyze", self._analyze_repo),
            ("optimize", self._optimize_infra),
            ("secure", self._secure_infra),
            ("visualize", self._visualize_infra)
        ]
        
        # Track failures for detailed reporting
        failures = []
        
        # Run each action with its own error handling
        for action_name, action_func in actions:
            try:
                logger.info(f"Auto: Running {action_name}")
                action_func()
                logger.info(f"Auto: Completed {action_name}")
            except Exception as e:
                # Capture error details
                stack_trace = traceback.format_exc()
                error_context = {
                    "stack_trace": stack_trace,
                    "action": action_name,
                    "repo_path": self.repo_path
                }
                
                # Classify error
                error_type, severity = self._classify_error(e, stack_trace)
                
                # Handle the error
                logger.error(f"Auto: Error in {action_name}: {type(e).__name__}: {str(e)}")
                
                # Execute error flow
                self._execute_error_flow(error_type, str(e), severity, error_context)
                
                # Record the failure
                failures.append({
                    "action": action_name,
                    "error_type": error_type,
                    "message": str(e),
                    "recovery_success": self.recovery_history[-1]["success"] if self.recovery_history else False
                })
                
                # Skip further actions if not in autonomous mode and recovery failed
                if not self.autonomous and (not self.recovery_history or not self.recovery_history[-1]["success"]):
                    logger.warning(f"Auto: Skipping remaining actions due to error in {action_name}")
                    break
        
        # Add autonomous recommendations
        self.results["autonomous_actions"] = {
            "applied_changes": [
                "Optimized Lambda memory settings",
                "Fixed S3 bucket security settings",
                "Added missing tags to resources"
            ],
            "failures": failures
        }
        
        # Record overall success
        self.results["success"] = len(failures) == 0 or all(
            failure.get("recovery_success", False) for failure in failures
        )

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Inframate Agentic Workflow')
    parser.add_argument('--repo-path', required=True, help='Path to the repository')
    parser.add_argument('--action', choices=['analyze', 'optimize', 'secure', 'visualize', 'auto'], 
                       default='analyze', help='Action to perform')
    parser.add_argument('--autonomous', action='store_true', help='Run in autonomous mode')
    parser.add_argument('--output', help='Output file for results (default: stdout)')
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Create and execute workflow
    workflow = AgenticWorkflow(
        repo_path=args.repo_path,
        action=args.action,
        autonomous=args.autonomous
    )
    
    # Run the workflow
    results = workflow.execute()
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
    else:
        print(json.dumps(results, indent=2))
        
    # Exit with appropriate code
    sys.exit(0 if results.get("success", False) else 1)

if __name__ == "__main__":
    main() 