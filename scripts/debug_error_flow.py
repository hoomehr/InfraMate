#!/usr/bin/env python3
"""
Debug Error Flow Utility for Inframate

This script helps debug the error handling flow in Inframate by:
1. Tracing error handling calls and flows
2. Verifying connections between workflow and error handling
3. Testing error recovery mechanisms
"""

import os
import sys
import json
import logging
import argparse
import traceback
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.agentic_workflow import InfraAgent, WorkflowState
    from scripts.agentic_error_workflow import AgenticWorkflow, ErrorState
    from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity
except ImportError:
    print("Error: Required modules not found. Please check your installation.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("error_debug.log")
    ]
)
logger = logging.getLogger("error_debug")

class ErrorType(Enum):
    """Test error types"""
    API = "api_error"
    TERRAFORM = "terraform_error"
    PERMISSION = "permission_error"
    VALIDATION = "validation_error"
    RESOURCE = "resource_error"
    GEMINI = "gemini_error"
    NETWORK = "network_error"
    SYSTEM = "system_error"

class ErrorDebugger:
    """Error flow debugger and tester"""
    
    def __init__(self, repo_path="."):
        self.repo_path = repo_path
        self.error_handler = ErrorLoopHandler()
        
    def inject_error(self, error_type: ErrorType, error_message: str = None):
        """Inject a specific error type to test error handling"""
        logger.info(f"Injecting error of type {error_type.value}")
        
        if error_message is None:
            error_message = f"TEST ERROR: Injected {error_type.value} for testing"
            
        # Create error context
        error_context = {
            "function": "debug_injection",
            "error_type": error_type.value,
            "error_message": error_message,
            "stack_trace": "Injected error - no stack trace",
            "timestamp": 0,
            "recovery_attempt": 0
        }
        
        # Test error handler directly
        try:
            # Determine severity based on error type
            severity = ErrorSeverity.MEDIUM
            if error_type in [ErrorType.PERMISSION, ErrorType.SYSTEM]:
                severity = ErrorSeverity.HIGH
            elif error_type == ErrorType.RESOURCE:
                severity = ErrorSeverity.CRITICAL
                
            # Call error handler
            logger.info(f"Calling error_handler.handle_error with {error_type.value}")
            success, solution = self.error_handler.handle_error(
                error_type=error_type.value,
                message=error_message,
                severity=severity,
                context_data=error_context
            )
            
            # Log results
            logger.info(f"Error handler result: success={success}")
            if solution:
                logger.info(f"Solution provided: {json.dumps(solution, indent=2)}")
            else:
                logger.info("No solution provided")
                
            return success, solution
        except Exception as e:
            logger.error(f"Error calling error handler: {type(e).__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            return False, None
    
    def test_error_integration(self):
        """Test integration between agentic workflow and error handler"""
        logger.info("Testing error handling integration...")
        
        # Create agent
        agent = InfraAgent(self.repo_path)
        
        # Verify error handler initialization
        if not hasattr(agent, 'error_handler'):
            logger.critical("❌ Agent does not have error_handler attribute")
            return False
            
        if agent.error_handler is None:
            logger.critical("❌ Agent has error_handler attribute but it's None")
            return False
            
        logger.info("✅ Agent has error_handler initialized")
        
        # Test handle_error_flow method
        try:
            error_context = {
                "function": "test_function",
                "error_type": "test_error",
                "error_message": "Test error message",
                "stack_trace": "Test stack trace",
                "timestamp": 0
            }
            
            logger.info("Testing handle_error_flow method...")
            recovery_success, solution = agent.handle_error_flow(error_context)
            
            logger.info(f"handle_error_flow returned: success={recovery_success}")
            if solution:
                logger.info(f"Solution: {json.dumps(solution, indent=2)}")
            
            logger.info("✅ handle_error_flow method called successfully")
            return True
        except Exception as e:
            logger.critical(f"❌ handle_error_flow method failed: {type(e).__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
    
    def trace_error_flow(self, error_type: ErrorType):
        """Trace the complete error flow from agentic workflow to error handler"""
        logger.info(f"Tracing complete error flow for {error_type.value}...")
        
        # Create agent
        agent = InfraAgent(self.repo_path)
        
        # Inject method to raise error
        def _analyze_infrastructure_impl_error(*args, **kwargs):
            logger.info(f"Raising injected {error_type.value}")
            
            if error_type == ErrorType.API:
                raise ConnectionError(f"TEST ERROR: API connection failed")
            elif error_type == ErrorType.TERRAFORM:
                raise RuntimeError(f"TEST ERROR: Terraform execution failed")
            elif error_type == ErrorType.PERMISSION:
                raise PermissionError(f"TEST ERROR: Permission denied")
            else:
                raise ValueError(f"TEST ERROR: {error_type.value} injection")
        
        # Save original and replace
        original_method = agent._analyze_infrastructure_impl
        agent._analyze_infrastructure_impl = _analyze_infrastructure_impl_error
        
        try:
            # Enable debug logging for all modules
            logging.getLogger().setLevel(logging.DEBUG)
            
            # Run action that will trigger error
            logger.info("Running analyze action (will trigger error)...")
            result = agent.run_action("analyze")
            
            # Check result
            if result.get("status") == "error":
                logger.info("✅ Error was detected and reported")
                
                # Check error details
                error_context = result.get("error", {})
                logger.info(f"Error type: {error_context.get('error_type')}")
                logger.info(f"Error message: {error_context.get('error_message')}")
                
                # Check AI solution
                ai_solution = result.get("ai_solution")
                if ai_solution:
                    logger.info("✅ AI solution was generated")
                    logger.info(f"Solution: {json.dumps(ai_solution, indent=2)}")
                else:
                    logger.warning("⚠️ No AI solution was generated")
                
                # Check error report
                error_report = result.get("error_report", {})
                if error_report:
                    logger.info("✅ Error report was generated")
                    logger.info(f"Error report: {json.dumps(error_report, indent=2)}")
                else:
                    logger.warning("⚠️ No error report was generated")
                    
                return True
            else:
                logger.error("❌ Error was not detected")
                logger.error(f"Result: {json.dumps(result, indent=2)}")
                return False
        except Exception as e:
            logger.error(f"Exception during trace: {type(e).__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
        finally:
            # Restore original method
            agent._analyze_infrastructure_impl = original_method
            
            # Reset logging level
            logging.getLogger().setLevel(logging.INFO)
    
def main():
    parser = argparse.ArgumentParser(description="Debug Inframate error handling flow")
    parser.add_argument("--repo-path", default=".", help="Path to repository")
    parser.add_argument("--action", choices=["inject", "test", "trace"], default="test", 
                        help="Action to perform")
    parser.add_argument("--error-type", choices=[e.value for e in ErrorType], default="validation_error",
                        help="Type of error to inject/trace")
    
    args = parser.parse_args()
    
    debugger = ErrorDebugger(args.repo_path)
    
    if args.action == "inject":
        error_type = ErrorType(args.error_type)
        debugger.inject_error(error_type)
    elif args.action == "test":
        debugger.test_error_integration()
    elif args.action == "trace":
        error_type = ErrorType(args.error_type)
        debugger.trace_error_flow(error_type)
        
if __name__ == "__main__":
    main() 