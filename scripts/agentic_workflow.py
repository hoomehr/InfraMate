#!/usr/bin/env python3
"""
Agentic Workflow for Inframate

This script serves as the orchestrator for autonomous infrastructure management:
1. Analyzes infrastructure in target repositories
2. Makes intelligent decisions about optimizations
3. Implements changes through Pull Requests
4. Learns from feedback
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import google.generativeai as genai

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InfraAgent:
    """Autonomous agent for infrastructure management"""
    
    def __init__(self, repo_path: str, autonomous: bool = False):
        self.repo_path = Path(repo_path).resolve()
        self.autonomous = autonomous
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self.action_history = []
        
        # Initialize Gemini AI if API key is available
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("Gemini AI initialized successfully")
        else:
            logger.warning("GEMINI_API_KEY not found. Operating in limited mode.")
            self.model = None
    
    def analyze_infrastructure(self) -> Dict[str, Any]:
        """Analyze the current infrastructure in the repository"""
        logger.info(f"Analyzing infrastructure in {self.repo_path}")
        
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
            return {"error": str(e)}
    
    def optimize_infrastructure(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations for infrastructure optimization"""
        logger.info("Generating optimization recommendations")
        
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
            return {"error": str(e)}
    
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
                "issue": "General optimization",
                "impact": "cost",
                "severity": "Low",
                "recommendation": "Consider implementing auto-scaling for dynamic workloads",
                "estimated_benefit": "Potential cost savings during low-traffic periods"
            })
        
        return {"recommendations": recommendations}
    
    def visualize_infrastructure(self) -> Dict[str, Any]:
        """Generate infrastructure visualizations"""
        logger.info("Generating infrastructure visualizations")
        
        # Use the visualization script that was created earlier
        try:
            visualization_script = Path(__file__).parent / "visualization" / "tf_visualizer.py"
            output_dir = self.repo_path / "visualizations"
            os.makedirs(output_dir, exist_ok=True)
            
            # Run the visualization script
            subprocess.run([
                "python3", str(visualization_script), 
                str(self.repo_path), str(output_dir)
            ], check=True)
            
            return {
                "status": "success",
                "visualization_path": str(output_dir)
            }
        except Exception as e:
            logger.error(f"Visualization failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def secure_infrastructure(self) -> Dict[str, Any]:
        """Implement security enhancements"""
        logger.info("Analyzing and implementing security enhancements")
        
        # Run security scan
        try:
            security_results = self._run_security_scan()
            
            # If in autonomous mode, implement security fixes
            if self.autonomous and security_results.get("has_issues", False):
                security_results["fixes"] = self._implement_security_fixes(security_results)
            
            return security_results
            
        except Exception as e:
            logger.error(f"Security analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _run_security_scan(self) -> Dict[str, Any]:
        """Run security scan using tfsec or similar tool"""
        # This is a placeholder - you would implement actual security scanning here
        # For example, you could run tfsec and parse the results
        
        # Simulate security scan results
        return {
            "has_issues": True,
            "issues": [
                {
                    "rule_id": "AWS018",
                    "description": "Resources have default security group attached",
                    "impact": "Default security group allows all inbound and outbound traffic",
                    "resolution": "Create and attach a more restrictive security group"
                }
            ]
        }
    
    def _implement_security_fixes(self, security_results: Dict[str, Any]) -> Dict[str, Any]:
        """Implement fixes for security issues"""
        # This would contain the logic to fix security issues
        # For now, we just return a placeholder
        return {
            "fixes_implemented": 0,
            "fixes_skipped": len(security_results.get("issues", [])),
            "result": "No fixes implemented automatically"
        }
    
    def run_action(self, action: str) -> Dict[str, Any]:
        """Run the specified action"""
        logger.info(f"Running action: {action}")
        
        if action == "analyze":
            return self.analyze_infrastructure()
        
        elif action == "optimize":
            analysis = self.analyze_infrastructure()
            return self.optimize_infrastructure(analysis)
        
        elif action == "visualize":
            return self.visualize_infrastructure()
        
        elif action == "secure":
            return self.secure_infrastructure()
        
        elif action == "auto":
            # Run the full agentic workflow
            analysis = self.analyze_infrastructure()
            optimization = self.optimize_infrastructure(analysis)
            visualization = self.visualize_infrastructure()
            security = self.secure_infrastructure()
            
            return {
                "analysis": analysis,
                "optimization": optimization,
                "visualization": visualization,
                "security": security
            }
        
        else:
            return {"error": f"Unknown action: {action}"}

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description="Agentic Workflow for Inframate")
    parser.add_argument("--repo-path", required=True, help="Path to the repository to analyze")
    parser.add_argument("--action", default="analyze", help="Action to perform (analyze, optimize, visualize, secure, auto)")
    parser.add_argument("--autonomous", default="false", help="Run in autonomous mode (true/false)")
    args = parser.parse_args()
    
    # Convert autonomous string to boolean
    autonomous = args.autonomous.lower() in ("true", "t", "yes", "y", "1")
    
    # Initialize agent
    agent = InfraAgent(repo_path=args.repo_path, autonomous=autonomous)
    
    # Run the specified action
    result = agent.run_action(args.action)
    
    # Print the results as JSON
    print(json.dumps(result, indent=2))
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 