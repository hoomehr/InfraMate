#!/usr/bin/env python3
"""
Error Handling Test Script for Inframate

This script tests the error handling capabilities of Inframate by:
1. Testing different error scenarios
2. Validating error recovery mechanisms
3. Checking Gemini API integration for AI-powered solutions
4. Testing fallback mechanisms when AI is unavailable

Usage:
  python scripts/test_error_handling.py --test-all
  python scripts/test_error_handling.py --test-type [api|terraform|resource|unrecoverable]
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path

# Add parent directory to path for imports
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
        logging.FileHandler("error_test.log")
    ]
)
logger = logging.getLogger(__name__)

def test_api_error(handler):
    """Test API error handling"""
    logger.info("Testing API error handling...")
    success, solution = handler.handle_error(
        "api_error",
        "Rate limit exceeded. Please try again later.",
        ErrorSeverity.MEDIUM
    )
    logger.info(f"API error recovery success: {success}")
    logger.info(f"AI solution: {solution}")
    return success

def test_terraform_error(handler):
    """Test Terraform error handling"""
    logger.info("Testing Terraform error handling...")
    success, solution = handler.handle_error(
        "terraform_error",
        "Error: Error acquiring the state lock. State lock file may be already in use.",
        ErrorSeverity.HIGH
    )
    logger.info(f"Terraform error recovery success: {success}")
    logger.info(f"AI solution: {solution}")
    return success

def test_resource_conflict(handler):
    """Test resource conflict error handling"""
    logger.info("Testing resource conflict error handling...")
    success, solution = handler.handle_error(
        "resource_conflict",
        "Error: Resource already exists. Cannot create duplicate resource.",
        ErrorSeverity.MEDIUM
    )
    logger.info(f"Resource conflict recovery success: {success}")
    logger.info(f"AI solution: {solution}")
    return success

def test_gemini_error(handler):
    """Test Gemini API error handling"""
    logger.info("Testing Gemini API error handling...")
    success, solution = handler.handle_error(
        "gemini_error",
        "Quota exceeded for Gemini API. Please try again later.",
        ErrorSeverity.MEDIUM
    )
    logger.info(f"Gemini API error recovery success: {success}")
    logger.info(f"AI solution: {solution}")
    return success

def test_unrecoverable_error(handler):
    """Test unrecoverable error handling"""
    logger.info("Testing unrecoverable error handling...")
    success, solution = handler.handle_error(
        "unknown_error",
        "Critical system failure. Unable to continue execution.",
        ErrorSeverity.CRITICAL
    )
    logger.info(f"Unrecoverable error handling completed: {success}")
    logger.info(f"AI solution: {solution}")
    return success

def verify_error_history(handler):
    """Verify error history tracking"""
    logger.info("Verifying error history...")
    report = handler.get_error_report() if hasattr(handler, 'get_error_report') else None
    
    if report:
        logger.info(f"Total errors: {report.get('total_error_count', 'N/A')}")
        logger.info(f"Recovered: {report.get('recovered_count', 'N/A')}")
        logger.info(f"Unrecovered: {report.get('unrecovered_count', 'N/A')}")
    else:
        logger.info(f"Error history count: {len(handler.supervisor.error_history)}")
    
    return len(handler.supervisor.error_history) > 0

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Test Inframate error handling')
    parser.add_argument('--test-all', action='store_true', help='Run all tests')
    parser.add_argument('--test-type', choices=['api', 'terraform', 'resource', 'gemini', 'unrecoverable'],
                       help='Specific error type to test')
    parser.add_argument('--set-api-key', action='store_true', help='Set mock API key for testing')
    
    args = parser.parse_args()
    
    # Set a mock API key if requested (for testing AI-powered solutions)
    if args.set_api_key and 'GEMINI_API_KEY' not in os.environ:
        logger.info("Setting mock GEMINI_API_KEY for testing")
        os.environ['GEMINI_API_KEY'] = 'mock_key_for_testing'
    
    # Initialize the error handler
    handler = ErrorLoopHandler()
    
    # Run the specified tests
    results = {}
    
    if args.test_all or args.test_type == 'api':
        results['api'] = test_api_error(handler)
    
    if args.test_all or args.test_type == 'terraform':
        results['terraform'] = test_terraform_error(handler)
    
    if args.test_all or args.test_type == 'resource':
        results['resource'] = test_resource_conflict(handler)
    
    if args.test_all or args.test_type == 'gemini':
        results['gemini'] = test_gemini_error(handler)
    
    if args.test_all or args.test_type == 'unrecoverable':
        results['unrecoverable'] = test_unrecoverable_error(handler)
    
    # Verify error history
    results['history'] = verify_error_history(handler)
    
    # Report results
    logger.info("==== Error Handling Test Results ====")
    for test, result in results.items():
        logger.info(f"{test}: {'PASS' if result else 'FAIL'}")
    
    # Exit with appropriate status code
    success = all(results.values())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 