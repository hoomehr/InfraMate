#!/usr/bin/env python3
import os
import sys
import json
import traceback
import argparse
from typing import Dict, Any, Optional

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity

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
            
            # Determine error type and severity
            error_type = type(e).__name__
            severity = ErrorSeverity.HIGH
            
            # Handle the error with our AI-powered handler
            recovery_success, ai_solution = self.error_handler.handle_error(
                error_type=error_type,
                message=str(e),
                severity=severity,
                context_data=error_context
            )
            
            # Add error information to results
            self.results["success"] = False
            self.results["error"] = {
                "type": error_type,
                "message": str(e),
                "stack_trace": stack_trace,
                "ai_solution": ai_solution
            }
            
            # Add error report to results
            self.results["error_report"] = self.error_handler.get_error_report()
            
            return self.results
            
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
        # Run all actions in sequence
        self._analyze_repo()
        self._optimize_infra()
        self._secure_infra()
        self._visualize_infra()
        
        # Add autonomous recommendations
        self.results["autonomous_actions"] = {
            "applied_changes": [
                "Optimized Lambda memory settings",
                "Fixed S3 bucket security settings",
                "Added missing tags to resources"
            ]
        }

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