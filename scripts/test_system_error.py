#!/usr/bin/env python3
"""
System Error Test Script for Inframate

This script specifically tests the handling of system errors,
including testing the integration with Gemini API for solution generation.

Usage:
  python scripts/test_system_error.py
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity
except ImportError:
    print("Error: Required modules not found. Please check your installation.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("system_error_test.log")
    ]
)
logger = logging.getLogger(__name__)

def test_injected_system_error(handler):
    """Test handling of an injected system error"""
    logger.info("=== Testing injected system error handling ===")
    
    # This is the error message from your example
    error_message = "TEST ERROR: Injected system_error for testing"
    
    success, solution = handler.handle_error(
        "system_error",
        error_message,
        ErrorSeverity.HIGH
    )
    
    logger.info(f"System error recovery success: {success}")
    
    if solution:
        logger.info(f"AI solution type: {type(solution)}")
        if isinstance(solution, dict):
            if "root_cause" in solution:
                logger.info(f"Root cause identified: {solution['root_cause'][:100]}...")
            if "solution" in solution and solution["solution"]:
                steps_count = len(solution["solution"]) if isinstance(solution["solution"], list) else 1
                logger.info(f"Solution steps provided: {steps_count}")
    
    return success

def test_unknown_error(handler):
    """Test handling of an unknown error type that should map to system_error"""
    logger.info("=== Testing unknown error handling ===")
    
    success, solution = handler.handle_error(
        "unknown_error_xyz",  # This type doesn't exist and should be handled as system_error
        "Some unknown error that should be handled as a system error",
        ErrorSeverity.MEDIUM
    )
    
    logger.info(f"Unknown error recovery success: {success}")
    
    if solution:
        logger.info(f"AI solution provided for unknown error")
    
    return success

def create_mock_gemini_solution():
    """Create a mock Gemini solution to inject for testing"""
    return {
        "root_cause": "This is a mocked root cause for testing",
        "solution": [
            {"step": 1, "description": "First step of the solution"},
            {"step": 2, "description": "Second step of the solution"},
            {"step": 3, "description": "Third step of the solution"}
        ],
        "prevention": "This is a mocked prevention measure"
    }

def test_with_mock_solution(handler):
    """Test handling a system error with a mock AI solution"""
    logger.info("=== Testing system error with mock solution ===")
    
    # Create a custom context with an AI solution already provided
    context_data = {
        "ai_solution_steps": [
            {"step": 1, "description": "First step of the solution"},
            {"step": 2, "description": "Second step of the solution"}
        ]
    }
    
    success, solution = handler.handle_error(
        "system_error",
        "System error with a pre-provided solution in context",
        ErrorSeverity.MEDIUM,
        context_data=context_data
    )
    
    logger.info(f"System error with mock solution recovery success: {success}")
    return success

def main():
    """Main entry point for the script"""
    # Check if an API key is available
    has_api_key = "GEMINI_API_KEY" in os.environ
    
    if not has_api_key:
        logger.warning("No GEMINI_API_KEY found. Some tests will use mock solutions.")
        # We'll still run the tests, as the error handler should now handle missing API keys gracefully
    
    # Initialize the error handler
    handler = ErrorLoopHandler()
    
    # Run the tests
    results = {}
    
    # Test injected system error
    results['injected_system_error'] = test_injected_system_error(handler)
    
    # Test unknown error type
    results['unknown_error'] = test_unknown_error(handler)
    
    # Test with mock solution
    results['mock_solution'] = test_with_mock_solution(handler)
    
    # Print summary
    logger.info("=== Test Results ===")
    for test, success in results.items():
        logger.info(f"{test}: {'SUCCESS' if success else 'FAILED'}")
    
    # Overall success
    success = all(results.values())
    logger.info(f"Overall test result: {'SUCCESS' if success else 'FAILED'}")
    
    # Get error report
    report = handler.get_error_report()
    logger.info(f"Total errors handled: {report.get('total_error_count', 0)}")
    logger.info(f"Errors recovered: {report.get('recovered_count', 0)}")
    logger.info(f"Errors unrecovered: {report.get('unrecovered_count', 0)}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 