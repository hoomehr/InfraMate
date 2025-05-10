#!/usr/bin/env python3
"""
Test script to demonstrate and fix the error recovery flow issue in Inframate.
This script will:
1. Intentionally trigger an error in the agentic workflow
2. Verify error detection and recovery flow is triggered
3. Demonstrate the fix needed
"""

import os
import sys
import logging
import traceback
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.agentic_workflow import InfraAgent, WorkflowState
    from scripts.agentic_error_workflow import AgenticWorkflow
    from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity
except ImportError:
    print("Error: Required modules not found. Please check your installation.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ErrorRecoveryTester:
    """Test harness for error recovery flow"""
    
    def __init__(self, repo_path="."):
        self.repo_path = repo_path
        self.error_handler = ErrorLoopHandler()
        
    def test_agentic_workflow_error_recovery(self):
        """Test that errors in agentic workflow trigger the recovery flow"""
        logger.info("=== Testing error recovery in agentic workflow ===")
        
        # Create agent with intentional error trigger
        agent = InfraAgent(self.repo_path)
        
        # Patch the analyze method to intentionally raise an error
        def _analyze_infrastructure_impl_error(*args, **kwargs):
            logger.info("Intentionally raising an error to test recovery flow")
            raise ValueError("TEST ERROR: This is an intentional error to test recovery")
        
        # Save original method and replace with error-raising version
        original_method = agent._analyze_infrastructure_impl
        agent._analyze_infrastructure_impl = _analyze_infrastructure_impl_error
        
        try:
            # Run the action that should now fail
            logger.info("Running analyze action (should fail)...")
            result = agent.run_action("analyze")
            
            # Check if error was detected
            if result.get("status") == "error":
                logger.info("✅ Error detected correctly")
                logger.info(f"Error type: {result.get('error', {}).get('error_type')}")
                logger.info(f"Error message: {result.get('error', {}).get('error_message')}")
                
                # Check if recovery was attempted
                if "ai_solution" in result.get("error", {}):
                    logger.info("✅ Recovery flow was triggered")
                    logger.info(f"AI solution: {result.get('error', {}).get('ai_solution')}")
                else:
                    logger.error("❌ Recovery flow was NOT triggered")
                    logger.error("This indicates a disconnection in the error handling system")
                    self._suggest_fix_for_missing_recovery()
            else:
                logger.error("❌ Error was not detected")
                logger.error("Expected status 'error' but got: " + result.get("status", "unknown"))
                
        except Exception as e:
            logger.error(f"Unexpected error during test: {type(e).__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
        finally:
            # Restore original method
            agent._analyze_infrastructure_impl = original_method

    def test_direct_error_flow(self):
        """Test the error flow directly using the AgenticWorkflow class"""
        logger.info("=== Testing direct error flow ===")
        
        # Create agentic error workflow
        workflow = AgenticWorkflow(
            repo_path=self.repo_path,
            action="analyze",
            autonomous=False
        )
        
        try:
            # Patch execution method to trigger error
            def _analyze_repo_error(*args, **kwargs):
                logger.info("Intentionally raising an error in direct error flow")
                raise ValueError("TEST ERROR: Intentional error in direct error flow")
                
            # Save original and replace
            original_method = workflow._analyze_repo
            workflow._analyze_repo = _analyze_repo_error
            
            # Execute workflow (should fail)
            logger.info("Running error workflow...")
            result = workflow.execute()
            
            # Check results
            if not result.get("success", True):
                logger.info("✅ Error detected in direct error flow")
                
                # Check recovery history
                recovery_attempts = result.get("error", {}).get("recovery_attempts", [])
                if recovery_attempts:
                    logger.info(f"✅ Recovery was attempted {len(recovery_attempts)} times")
                    
                    for i, attempt in enumerate(recovery_attempts):
                        logger.info(f"  Attempt {i+1}:")
                        logger.info(f"    Error type: {attempt.get('error_type')}")
                        logger.info(f"    Success: {attempt.get('success')}")
                        
                    # Check AI solution
                    ai_solution = result.get("error", {}).get("ai_solution")
                    if ai_solution:
                        logger.info("✅ AI solution was generated")
                    else:
                        logger.warning("⚠️ No AI solution was generated")
                else:
                    logger.error("❌ No recovery attempts were made")
            else:
                logger.error("❌ Error was not detected in direct error flow")
                
        except Exception as e:
            logger.error(f"Unexpected error during direct flow test: {type(e).__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
        finally:
            # Restore original method
            workflow._analyze_repo = original_method
            
    def _suggest_fix_for_missing_recovery(self):
        """Provide suggestions to fix the disconnection between error detection and recovery"""
        logger.info("\n=== SUGGESTED FIX ===")
        logger.info("The issue is likely in how errors are being passed to the recovery system.")
        logger.info("Here's what to check:")
        
        logger.info("\n1. Verify the error handler initialization in agentic_workflow.py:")
        logger.info("   Make sure self.error_handler = ErrorLoopHandler() is properly initialized")
        
        logger.info("\n2. Check execute_with_error_handling method in InfraAgent class:")
        logger.info("   Ensure it properly captures and passes errors to handle_error_flow")
        
        logger.info("\n3. Fix connection between agentic_workflow.py and error_handler.py:")
        logger.info("   Add this patch to scripts/agentic_workflow.py:")
        
        patch = """
def handle_error_flow(self, error_info: Dict) -> Tuple[bool, Optional[Dict]]:
    # Update workflow state
    previous_state = self.current_state
    self.current_state = WorkflowState.ERROR_HANDLING
    
    # Log error handling start
    logger.info(f"Starting error handling flow for error in {error_info.get('function')}")
    logger.info(f"Error type: {error_info.get('error_type')}")
    logger.info(f"Error message: {error_info.get('error_message')}")
    
    # Determine error severity based on type and context
    severity = self._determine_error_severity(error_info)
    
    # Use the error handler to handle the error
    try:
        # Call error handler with appropriate context and trace for troubleshooting
        logger.debug(f"Calling error_handler.handle_error with type: {error_info.get('error_type')}")
        recovery_success, ai_solution = self.error_handler.handle_error(
            error_type=error_info.get('error_type', 'unknown_error'),
            message=error_info.get('error_message', 'Unknown error'),
            severity=severity,
            context_data=error_info
        )
        
        # Log result from error handler
        logger.info(f"Error handler returned: success={recovery_success}, solution={'provided' if ai_solution else 'none'}")
        
        # Rest of method remains the same...
        """
        
        logger.info(patch)
        
        logger.info("\n4. Verify error handler is correctly processing errors:")
        logger.info("   Check handle_error method in ErrorLoopHandler class")
        
        logger.info("\n5. Add direct connection in run_action to ensure errors always trigger recovery:")
        
        action_patch = """
def run_action(self, action: str) -> Dict[str, Any]:
    try:
        # Existing code...
    except Exception as e:
        # Handle any unhandled exceptions
        error_type = type(e).__name__
        error_message = str(e)
        stack_trace = traceback.format_exc()
        
        logger.error(f"Unhandled error in run_action: {error_type}: {error_message}")
        
        # Ensure error handler exists
        if not hasattr(self, 'error_handler') or self.error_handler is None:
            logger.critical("Error handler not initialized! Creating one now.")
            self.error_handler = ErrorLoopHandler()
            
        # More detailed context for debugging
        error_context = {
            "function": "run_action",
            "action": action,
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
            "timestamp": time.time()
        }
        
        # Force debug output to trace error handling
        logger.info(f"Calling handle_error_flow with context: {error_context}")
        
        # Try error handling flow with more context
        recovery_success, solution = self.handle_error_flow(error_context)
        
        # Log recovery result
        logger.info(f"Recovery success: {recovery_success}")
        logger.info(f"Solution provided: {solution is not None}")
        
        # Rest of method remains the same...
        """
        
        logger.info(action_patch)
        
        logger.info("\nApplying these fixes should ensure errors properly trigger the recovery flow.")
            
def main():
    """Run the test script"""
    tester = ErrorRecoveryTester()
    
    print("\n" + "="*80)
    print("INFRAMATE ERROR RECOVERY FLOW TEST")
    print("="*80 + "\n")
    
    # Test agentic workflow error recovery
    tester.test_agentic_workflow_error_recovery()
    
    print("\n" + "="*80)
    
    # Test direct error flow
    tester.test_direct_error_flow()
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80 + "\n")
    
if __name__ == "__main__":
    main() 