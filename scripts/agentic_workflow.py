#!/usr/bin/env python3
"""
Agentic Workflow for Inframate

This script serves as the orchestrator for autonomous infrastructure management:
1. Analyzes infrastructure in target repositories
2. Makes intelligent decisions about optimizations
3. Implements changes through Pull Requests
4. Learns from feedback
5. Handles errors with a dedicated error recovery flow
"""

import os
import sys
import json
import argparse
import subprocess
import logging
import traceback
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum, auto

# Add parent directory to path to import Inframate modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import google.generativeai as genai
    from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity
except ImportError:
    print("Error: Required modules not found. Make sure they are installed.")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("inframate_agent.log")
    ]
)
logger = logging.getLogger(__name__)

class WorkflowState(Enum):
    """States for the agentic workflow"""
    INITIALIZING = auto()
    ANALYZING = auto()
    OPTIMIZING = auto()
    SECURING = auto()
    VISUALIZING = auto()
    ERROR_HANDLING = auto()
    RECOVERY = auto()
    COMPLETED = auto()
    FAILED = auto()

class InfraAgent:
    """Autonomous agent for infrastructure management with enhanced error handling"""
    
    def __init__(self, repo_path: str, autonomous: bool = False):
        self.repo_path = Path(repo_path).resolve()
        self.autonomous = autonomous
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self.action_history = []
        self.current_state = WorkflowState.INITIALIZING
        self.error_handler = ErrorLoopHandler()
        self.error_context = {}
        self.recovery_attempts = {}
        self.max_recovery_attempts = 3
        
        # Initialize Gemini AI if API key is available
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("Gemini AI initialized successfully")
        else:
            logger.warning("GEMINI_API_KEY not found. Operating in limited mode.")
            self.model = None
    
    def execute_with_error_handling(self, func, *args, **kwargs) -> Tuple[bool, Any, Dict]:
        """
        Execute a function with error handling
        
        Args:
            func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Tuple of (success, result, error_info)
        """
        # Get the function name for context
        func_name = func.__name__
        
        # Initialize or update recovery counter
        if func_name not in self.recovery_attempts:
            self.recovery_attempts[func_name] = 0
        
        try:
            # Execute the function
            result = func(*args, **kwargs)
            # Reset recovery counter on success
            self.recovery_attempts[func_name] = 0
            return True, result, {}
        except Exception as e:
            # Capture the exception details
            error_type = type(e).__name__
            error_message = str(e)
            stack_trace = traceback.format_exc()
            
            # Log the error
            logger.error(f"Error in {func_name}: {error_type}: {error_message}")
            logger.debug(f"Stack trace: {stack_trace}")
            
            # Increment recovery counter
            self.recovery_attempts[func_name] += 1
            
            # Prepare error context
            error_context = {
                "function": func_name,
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace,
                "args": args,
                "kwargs": kwargs,
                "recovery_attempt": self.recovery_attempts[func_name],
                "timestamp": time.time()
            }
            
            # Return failure with error info
            return False, None, error_context
    
    def handle_error_flow(self, error_info: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Secondary flow for handling errors
        
        Args:
            error_info: Dictionary with error information
            
        Returns:
            Tuple of (recovery_success, recovery_solution)
        """
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
            # Call error handler with appropriate context
            recovery_success, ai_solution = self.error_handler.handle_error(
                error_type=error_info.get('error_type', 'unknown_error'),
                message=error_info.get('error_message', 'Unknown error'),
                severity=severity,
                context_data=error_info
            )
            
            # Log the recovery result
            if recovery_success:
                logger.info(f"Successfully recovered from {error_info.get('error_type')} error")
                # Transition back to previous state
                self.current_state = previous_state
            else:
                # After max attempts, transition to failed state
                if error_info.get('recovery_attempt', 0) >= self.max_recovery_attempts:
                    logger.error(f"Failed to recover after {self.max_recovery_attempts} attempts")
                    self.current_state = WorkflowState.FAILED
                else:
                    # Transition to recovery state for another attempt
                    self.current_state = WorkflowState.RECOVERY
            
            # Return the recovery status and solution
            return recovery_success, ai_solution
            
        except Exception as e:
            # Error in the error handler itself
            logger.critical(f"Error in error handling flow: {type(e).__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            self.current_state = WorkflowState.FAILED
            return False, None
    
    def _determine_error_severity(self, error_info: Dict) -> ErrorSeverity:
        """Determine the severity of an error based on context"""
        error_type = error_info.get('error_type', '')
        error_message = error_info.get('error_message', '')
        recovery_attempt = error_info.get('recovery_attempt', 0)
        
        # Higher severity for repeated recovery attempts
        if recovery_attempt >= self.max_recovery_attempts:
            return ErrorSeverity.CRITICAL
        elif recovery_attempt >= 2:
            return ErrorSeverity.HIGH
        
        # Determine severity based on error type
        if 'Permission' in error_type or 'Access' in error_type:
            return ErrorSeverity.HIGH
        elif 'Timeout' in error_type or 'Connection' in error_type:
            return ErrorSeverity.MEDIUM
        elif 'NotFound' in error_type:
            return ErrorSeverity.MEDIUM
        elif 'Validation' in error_type:
            return ErrorSeverity.LOW
        
        # Check message content for known issues
        if 'rate limit' in error_message.lower():
            return ErrorSeverity.MEDIUM
        elif 'credential' in error_message.lower():
            return ErrorSeverity.HIGH
        elif 'permission' in error_message.lower():
            return ErrorSeverity.HIGH
        
        # Default to medium severity
        return ErrorSeverity.MEDIUM
    
    def analyze_infrastructure(self) -> Dict[str, Any]:
        """Analyze the current infrastructure in the repository"""
        self.current_state = WorkflowState.ANALYZING
        logger.info(f"Analyzing infrastructure in {self.repo_path}")
        
        # Execute analysis with error handling
        success, result, error_info = self.execute_with_error_handling(
            self._analyze_infrastructure_impl
        )
        
        if success:
            self.action_history.append({
                "action": "analyze",
                "success": True,
                "timestamp": time.time()
            })
            return result
        else:
            # Handle error and try to recover
            recovery_success, solution = self.handle_error_flow(error_info)
            
            if recovery_success:
                # Try again if recovery was successful
                logger.info("Retrying infrastructure analysis after error recovery")
                success, result, error_info = self.execute_with_error_handling(
                    self._analyze_infrastructure_impl
                )
                
                if success:
                    return result
            
            # Return error result if recovery failed or second attempt failed
            self.action_history.append({
                "action": "analyze",
                "success": False,
                "error": error_info,
                "solution": solution,
                "timestamp": time.time()
            })
            
            return {
                "status": "error",
                "error": error_info,
                "ai_solution": solution
            }
    
    def _analyze_infrastructure_impl(self) -> Dict[str, Any]:
        """Implementation of infrastructure analysis"""
        # Find Terraform files
        tf_files = list(self.repo_path.glob("**/*.tf"))
        if not tf_files:
            logger.warning("No Terraform files found")
            return {"terraform_files": [], "has_terraform": False}
        
        # Extract basic info about the infrastructure
        infra_info = {
            "terraform_files": [str(f.relative_to(self.repo_path)) for f in tf_files],
            "has_terraform": True,
            "resource_counts": self._count_resources(tf_files),
        }
        
        # Add AI analysis if available
        if self.model:
            infra_info["ai_analysis"] = self._ai_analyze_infrastructure(tf_files)
        
        return infra_info
    
    def _count_resources(self, tf_files: List[Path]) -> Dict[str, int]:
        """Count resources in Terraform files"""
        resource_counts = {}
        
        for file_path in tf_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('resource '):
                        parts = line.split('"')
                        if len(parts) >= 3:
                            resource_type = parts[1]
                            if resource_type in resource_counts:
                                resource_counts[resource_type] += 1
                            else:
                                resource_counts[resource_type] = 1
            except Exception as e:
                logger.error(f"Error parsing {file_path}: {e}")
                raise
        
        return resource_counts
    
    def _ai_analyze_infrastructure(self, tf_files: List[Path]) -> Dict[str, Any]:
        """Use AI to analyze the infrastructure"""
        # Collect sample of terraform code (limited to avoid token limits)
        samples = []
        total_chars = 0
        char_limit = 10000  # Limit sample size
        
        for file_path in tf_files:
            if total_chars >= char_limit:
                break
                
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                if total_chars + len(content) <= char_limit:
                    samples.append(f"# File: {file_path.name}\n{content}")
                    total_chars += len(content)
                else:
                    # Take partial content
                    available_chars = char_limit - total_chars
                    samples.append(f"# File: {file_path.name}\n{content[:available_chars]}")
                    total_chars = char_limit
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                raise
        
        terraform_samples = "\n\n".join(samples)
        
        # Create prompt for analysis
        prompt = f"""
        You are an expert AWS infrastructure architect analyzing Terraform code.
        
        Please analyze the following Terraform code and provide:
        1. A summary of the current architecture
        2. Potential optimization opportunities for cost and performance
        3. Security considerations and improvement suggestions
        
        Terraform code:
        ```
        {terraform_samples}
        ```
        
        Format your response as JSON with the following keys:
        - architecture_summary
        - optimization_opportunities
        - security_considerations
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                json_text = response.text
                if "```json" in json_text:
                    json_text = json_text.split("```json")[1].split("```")[0]
                elif "```" in json_text:
                    json_text = json_text.split("```")[1].split("```")[0]
                
                return json.loads(json_text)
            except (json.JSONDecodeError, IndexError) as e:
                # If JSON parsing fails, return the raw text
                return {"raw_analysis": response.text}
                
        except Exception as e:
            logger.error(f"Error using Gemini API: {e}")
            raise
    
    def optimize_infrastructure(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations for infrastructure optimization"""
        self.current_state = WorkflowState.OPTIMIZING
        logger.info("Generating optimization recommendations")
        
        # Execute optimization with error handling
        success, result, error_info = self.execute_with_error_handling(
            self._optimize_infrastructure_impl, analysis
        )
        
        if success:
            self.action_history.append({
                "action": "optimize",
                "success": True,
                "timestamp": time.time()
            })
            return result
        else:
            # Handle error and try to recover
            recovery_success, solution = self.handle_error_flow(error_info)
            
            if recovery_success:
                # Try again if recovery was successful
                logger.info("Retrying optimization after error recovery")
                success, result, error_info = self.execute_with_error_handling(
                    self._optimize_infrastructure_impl, analysis
                )
                
                if success:
                    return result
            
            # Return error result if recovery failed or second attempt failed
            self.action_history.append({
                "action": "optimize",
                "success": False,
                "error": error_info,
                "solution": solution,
                "timestamp": time.time()
            })
            
            return {
                "status": "error",
                "error": error_info,
                "ai_solution": solution
            }
    
    def _optimize_infrastructure_impl(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of infrastructure optimization"""
        if not analysis.get("has_terraform", False):
            return {"status": "No Terraform files to optimize"}
        
        # If we have AI analysis, use it for optimization
        if "ai_analysis" in analysis and self.model:
            return self._ai_generate_optimizations(analysis)
        
        # Fallback to rule-based optimizations
        return self._rule_based_optimizations(analysis)
    
    def _ai_generate_optimizations(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to generate optimization recommendations"""
        resource_counts = json.dumps(analysis.get("resource_counts", {}))
        ai_analysis = json.dumps(analysis.get("ai_analysis", {}))
        
        prompt = f"""
        You are an AWS infrastructure optimization expert.
        
        Based on the following analysis of a Terraform codebase, generate specific
        optimization recommendations:
        
        Resource counts: {resource_counts}
        
        Analysis: {ai_analysis}
        
        For each recommendation:
        1. Provide the specific problem/issue
        2. Explain the impact (cost, performance, security)
        3. Suggest specific Terraform code changes
        4. Estimate the benefit of implementing the change
        
        Format your response as JSON with an array of recommendation objects, each with:
        - issue: The specific problem identified
        - impact: Impact category (cost, performance, security)
        - severity: High/Medium/Low
        - recommendation: Detailed recommendation
        - terraform_changes: Specific code changes to make
        - estimated_benefit: Quantified benefit where possible
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Try to extract JSON from the response
            try:
                json_text = response.text
                if "```json" in json_text:
                    json_text = json_text.split("```json")[1].split("```")[0]
                elif "```" in json_text:
                    json_text = json_text.split("```")[1].split("```")[0]
                
                return json.loads(json_text)
            except (json.JSONDecodeError, IndexError) as e:
                return {"raw_recommendations": response.text}
                
        except Exception as e:
            logger.error(f"Error using Gemini API: {e}")
            raise
    
    def _rule_based_optimizations(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rule-based optimization recommendations when AI is not available"""
        recommendations = []
        resource_counts = analysis.get("resource_counts", {})
        
        # Check for potentially unnecessary resources
        if resource_counts.get("aws_nat_gateway", 0) > 2:
            recommendations.append({
                "issue": "Excessive NAT Gateways",
                "impact": "cost",
                "severity": "High",
                "recommendation": "Reduce the number of NAT Gateways. In most cases, one NAT Gateway per AZ is sufficient.",
                "estimated_benefit": f"~${resource_counts.get('aws_nat_gateway', 0) * 30} per month savings"
            })
        
        # Check for EC2 instances that might benefit from reserved instances
        if resource_counts.get("aws_instance", 0) > 3:
            recommendations.append({
                "issue": "Multiple EC2 Instances on demand",
                "impact": "cost",
                "severity": "Medium",
                "recommendation": "Consider using Reserved Instances for stable workloads",
                "estimated_benefit": "Up to 40-60% cost reduction for EC2"
            })
        
        # Add default recommendations
        if not recommendations:
            recommendations.append({
                "issue": "General cost optimization",
                "impact": "cost",
                "severity": "Low",
                "recommendation": "Review resource sizing and usage patterns for potential cost savings",
                "estimated_benefit": "Varies based on current infrastructure"
            })
        
        return {
            "status": "completed",
            "recommendations": recommendations
        }
    
    def visualize_infrastructure(self) -> Dict[str, Any]:
        """Create visualizations of the infrastructure"""
        self.current_state = WorkflowState.VISUALIZING
        logger.info("Creating infrastructure visualizations")
        
        # Execute visualization with error handling
        success, result, error_info = self.execute_with_error_handling(
            self._visualize_infrastructure_impl
        )
        
        if success:
            self.action_history.append({
                "action": "visualize",
                "success": True,
                "timestamp": time.time()
            })
            return result
        else:
            # Handle error and try to recover
            recovery_success, solution = self.handle_error_flow(error_info)
            
            if recovery_success:
                # Try again if recovery was successful
                logger.info("Retrying visualization after error recovery")
                success, result, error_info = self.execute_with_error_handling(
                    self._visualize_infrastructure_impl
                )
                
                if success:
                    return result
            
            # Return error result if recovery failed or second attempt failed
            self.action_history.append({
                "action": "visualize",
                "success": False,
                "error": error_info,
                "solution": solution,
                "timestamp": time.time()
            })
            
            return {
                "status": "error",
                "error": error_info,
                "ai_solution": solution
            }
    
    def _visualize_infrastructure_impl(self) -> Dict[str, Any]:
        """Implementation of infrastructure visualization"""
        # Create visualization directory if it doesn't exist
        vis_dir = self.repo_path / "visualizations"
        vis_dir.mkdir(exist_ok=True)
        
        # Check for terraform files
        tf_files = list(self.repo_path.glob("**/*.tf"))
        if not tf_files:
            return {"status": "No Terraform files to visualize"}
        
        # Call visualization script (this part would call an actual visualization tool)
        # This is a placeholder for actual visualization logic
        try:
            # Generate a sample visualization (just a placeholder)
            with open(vis_dir / "infrastructure_diagram.txt", "w") as f:
                f.write("# Infrastructure Diagram\n\n")
                f.write("This is a placeholder for an actual infrastructure diagram.\n")
                f.write("In a real implementation, this would use terraform-visual or similar.\n")
            
            return {
                "status": "completed",
                "visualizations": [
                    str(vis_dir / "infrastructure_diagram.txt")
                ]
            }
        except Exception as e:
            logger.error(f"Error creating visualizations: {e}")
            raise
    
    def secure_infrastructure(self) -> Dict[str, Any]:
        """Analyze and improve infrastructure security"""
        self.current_state = WorkflowState.SECURING
        logger.info("Analyzing infrastructure security")
        
        # Execute security analysis with error handling
        success, result, error_info = self.execute_with_error_handling(
            self._secure_infrastructure_impl
        )
        
        if success:
            self.action_history.append({
                "action": "secure",
                "success": True,
                "timestamp": time.time()
            })
            return result
        else:
            # Handle error and try to recover
            recovery_success, solution = self.handle_error_flow(error_info)
            
            if recovery_success:
                # Try again if recovery was successful
                logger.info("Retrying security analysis after error recovery")
                success, result, error_info = self.execute_with_error_handling(
                    self._secure_infrastructure_impl
                )
                
                if success:
                    return result
            
            # Return error result if recovery failed or second attempt failed
            self.action_history.append({
                "action": "secure",
                "success": False,
                "error": error_info,
                "solution": solution,
                "timestamp": time.time()
            })
            
            return {
                "status": "error",
                "error": error_info,
                "ai_solution": solution
            }
    
    def _secure_infrastructure_impl(self) -> Dict[str, Any]:
        """Implementation of infrastructure security analysis"""
        # Run security scan
        security_results = self._run_security_scan()
        
        # Implement security fixes if in autonomous mode
        if self.autonomous and security_results.get("issues", []):
            fixes = self._implement_security_fixes(security_results)
            security_results["fixes"] = fixes
        
        return security_results
    
    def _run_security_scan(self) -> Dict[str, Any]:
        """Run security scan on Terraform files"""
        # This is a placeholder for actual security scanning logic
        # In a real implementation, this would call tfsec, terrascan, or similar
        
        # Check for terraform files
        tf_files = list(self.repo_path.glob("**/*.tf"))
        if not tf_files:
            return {"status": "No Terraform files to scan"}
        
        # Simulate security scanning
        issues = [
            {
                "severity": "HIGH",
                "rule_id": "AWS001",
                "description": "S3 bucket has public access enabled",
                "file": str(tf_files[0]),
                "line": 10,
                "remediation": "Add 'block_public_acls = true' to aws_s3_bucket_public_access_block"
            }
        ]
        
        return {
            "status": "completed",
            "issues": issues,
            "total_issues": len(issues)
        }
    
    def _implement_security_fixes(self, security_results: Dict[str, Any]) -> Dict[str, Any]:
        """Implement fixes for security issues"""
        # This is a placeholder for actual fix implementation
        # In a real implementation, this would modify Terraform files
        
        return {
            "status": "completed",
            "fixed_issues": 1,
            "total_issues": len(security_results.get("issues", []))
        }
    
    def run_action(self, action: str) -> Dict[str, Any]:
        """Run a specific action with error handling"""
        logger.info(f"Running action: {action}")
        
        # Map actions to methods
        action_map = {
            "analyze": self.analyze_infrastructure,
            "optimize": lambda: self.optimize_infrastructure(self.analyze_infrastructure()),
            "secure": self.secure_infrastructure,
            "visualize": self.visualize_infrastructure,
            "auto": self._run_auto_mode
        }
        
        if action not in action_map:
            error_message = f"Unknown action: {action}"
            logger.error(error_message)
            return {"status": "error", "message": error_message}
        
        try:
            # Run the action
            result = action_map[action]()
            
            # Check if action succeeded
            if isinstance(result, dict) and result.get("status") == "error":
                self.current_state = WorkflowState.FAILED
                return result
            
            # Update workflow state to completed
            self.current_state = WorkflowState.COMPLETED
            
            # Add error report if available
            if hasattr(self, 'error_handler'):
                result["error_report"] = self.error_handler.get_error_report()
            
            return result
        except Exception as e:
            # Handle any unhandled exceptions
            error_type = type(e).__name__
            error_message = str(e)
            stack_trace = traceback.format_exc()
            
            logger.error(f"Unhandled error in run_action: {error_type}: {error_message}")
            logger.debug(f"Stack trace: {stack_trace}")
            
            error_context = {
                "function": "run_action",
                "action": action,
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace,
                "timestamp": time.time()
            }
            
            # Try error handling flow
            recovery_success, solution = self.handle_error_flow(error_context)
            
            if not recovery_success:
                self.current_state = WorkflowState.FAILED
            
            return {
                "status": "error",
                "error": error_context,
                "ai_solution": solution,
                "error_report": self.error_handler.get_error_report() if hasattr(self, 'error_handler') else {}
            }
    
    def _run_auto_mode(self) -> Dict[str, Any]:
        """Run all actions in sequence"""
        results = {
            "status": "completed",
            "actions": []
        }
        
        # Run each action in sequence
        for action in ["analyze", "optimize", "secure", "visualize"]:
            logger.info(f"Auto mode: Running {action}")
            
            # Get the appropriate method for this action
            action_method = getattr(self, f"{action}_infrastructure", None)
            if not action_method:
                continue
                
            # Run the action with error handling
            try:
                if action == "optimize":
                    # Optimization needs analysis results
                    if "analyze" in results:
                        action_result = action_method(results["analyze"])
                    else:
                        analysis = self.analyze_infrastructure()
                        action_result = action_method(analysis)
                else:
                    action_result = action_method()
                
                # Add result to results
                results[action] = action_result
                results["actions"].append({
                    "action": action,
                    "status": action_result.get("status", "unknown"),
                    "timestamp": time.time()
                })
                
                # Stop if action failed and not autonomous
                if action_result.get("status") == "error" and not self.autonomous:
                    logger.warning(f"Auto mode: {action} failed, stopping")
                    results["status"] = "partial"
                    break
                    
            except Exception as e:
                # Handle action error
                error_type = type(e).__name__
                error_message = str(e)
                logger.error(f"Auto mode: Error in {action}: {error_type}: {error_message}")
                
                error_context = {
                    "function": f"{action}_infrastructure",
                    "error_type": error_type,
                    "error_message": error_message,
                    "stack_trace": traceback.format_exc(),
                    "timestamp": time.time()
                }
                
                # Try error handling flow
                recovery_success, solution = self.handle_error_flow(error_context)
                
                if not recovery_success and not self.autonomous:
                    # Stop if recovery failed and not autonomous
                    logger.warning(f"Auto mode: {action} failed and recovery failed, stopping")
                    results["status"] = "partial"
                    results[action] = {
                        "status": "error",
                        "error": error_context,
                        "ai_solution": solution
                    }
                    results["actions"].append({
                        "action": action,
                        "status": "error",
                        "timestamp": time.time()
                    })
                    break
        
        # Add error report
        results["error_report"] = self.error_handler.get_error_report()
        
        return results

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Inframate Agentic Workflow')
    parser.add_argument('--repo-path', required=True, help='Path to the repository')
    parser.add_argument('--action', choices=['analyze', 'optimize', 'secure', 'visualize', 'auto'], 
                       default='analyze', help='Action to perform')
    parser.add_argument('--autonomous', action='store_true', help='Run in autonomous mode')
    parser.add_argument('--output', help='Output file for results (default: stdout)')
    args = parser.parse_args()
    
    # Initialize agent
    agent = InfraAgent(repo_path=args.repo_path, autonomous=args.autonomous)
    
    # Run the specified action
    results = agent.run_action(args.action)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
    else:
        print(json.dumps(results, indent=2))
    
    # Return appropriate exit code
    if results.get("status") == "error":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main() 