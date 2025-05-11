#!/usr/bin/env python3
"""
Script to analyze security scan results using Google Gemini AI
"""
import os
import sys
import json
import glob
import argparse
from dotenv import load_dotenv
import google.generativeai as genai

def setup_gemini_api():
    """Setup Gemini API with API key from environment variables"""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")
        return None
    
    # Configure Gemini API
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-pro-exp-03-25")

def get_report_content(tfsec_report_path=None, checkov_report_path=None, tf_directory=None):
    """Read the security reports and Terraform files to create context"""
    content = ""
    
    # Read TFSec report
    if tfsec_report_path and os.path.exists(tfsec_report_path):
        with open(tfsec_report_path, 'r') as f:
            content += "## TFSec Report\n" + f.read() + "\n\n"
    
    # Read Checkov report
    if checkov_report_path and os.path.exists(checkov_report_path):
        with open(checkov_report_path, 'r') as f:
            content += "## Checkov Report\n" + f.read() + "\n\n"
    
    # Read terraform files for context if directory is provided
    if tf_directory and os.path.exists(tf_directory):
        tf_files = []
        for root, dirs, files in os.walk(tf_directory):
            for file in files:
                if file.endswith('.tf'):
                    tf_files.append(os.path.join(root, file))
        
        # Get a sample of up to 5 terraform files
        tf_sample = tf_files[:5]
        for tf_file in tf_sample:
            with open(tf_file, 'r') as f:
                file_content = f.read()
                content += f"## Terraform File: {os.path.basename(tf_file)}\n```hcl\n{file_content}\n```\n\n"
    
    return content

def analyze_security_results(model, content):
    """Use Gemini to analyze security scan results and provide recommendations"""
    if not model:
        return "Error: Gemini API not properly configured."
    
    prompt = f"""
You are a highly skilled AWS security expert and Terraform specialist. Analyze the following security scan results and provide detailed, specific recommendations. Your goal is to help improve the infrastructure security posture.

SECURITY SCAN RESULTS:
{content}

Please provide a comprehensive security analysis with the following sections:

1. **Executive Summary**:
   - A concise overview of the key security findings (1-2 paragraphs)
   - Severity assessment (Critical, High, Medium, Low)
   - Overall risk assessment

2. **Critical Issues** (if any):
   - Detailed explanation of each critical security issue
   - Specific code examples showing both problematic code and corrected code
   - Potential impact if not addressed
   - Step-by-step remediation instructions

3. **High and Medium Priority Issues**:
   - Categorized list of important but non-critical issues
   - Brief explanation of each issue and its security implications
   - Recommended fixes with specific AWS best practices

4. **General Security Recommendations**:
   - AWS infrastructure security best practices relevant to this codebase
   - Architectural improvements to enhance security posture
   - Specific IAM role and permissions recommendations
   - Encryption and network security recommendations

5. **Implementation Plan**:
   - Prioritized roadmap for addressing findings
   - Suggested security monitoring improvements
   - Recommendations for ongoing security assessments

Format your response in markdown with clear sections and headings. Be specific, actionable, and reference exact resources from the provided Terraform code when possible. Ensure your recommendations follow AWS Well-Architected Framework security best practices.
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating AI analysis: {e}"

def main(tfsec_report_path, checkov_report_path, tf_directory, output_file):
    """Main function to run the analysis"""
    # Setup Gemini API
    model = setup_gemini_api()
    if not model:
        sys.exit(1)
    
    # Get report content
    content = get_report_content(tfsec_report_path, checkov_report_path, tf_directory)
    
    # Try to find all_findings.txt which might have more context
    all_findings_path = None
    if tfsec_report_path:
        all_findings_dir = os.path.dirname(tfsec_report_path)
        all_findings_path = os.path.join(all_findings_dir, "all_findings.txt")
    
    # If all_findings.txt exists, use it instead as it has more comprehensive data
    if all_findings_path and os.path.exists(all_findings_path):
        print(f"Found comprehensive findings file: {all_findings_path}")
        with open(all_findings_path, 'r') as f:
            content = f.read()
    
    if not content:
        print("No security reports or Terraform files found. Cannot generate AI analysis.")
        with open(output_file, "w") as f:
            f.write("# AI-Powered Security Analysis\n\n")
            f.write("*Unable to generate analysis: No security reports or Terraform files found.*\n")
        sys.exit(1)
    
    # Analyze security results
    analysis = analyze_security_results(model, content)
    
    # Write analysis to file
    with open(output_file, "w") as f:
        f.write("# AI-Powered Security Analysis\n\n")
        f.write("*Generated by Inframate using Google Gemini AI*\n\n")
        f.write(analysis)
    
    print(f"AI security analysis complete. Results written to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate AI-powered security analysis')
    parser.add_argument('--tfsec-report', help='Path to TFSec markdown report')
    parser.add_argument('--checkov-report', help='Path to Checkov text report')
    parser.add_argument('--tf-directory', help='Directory containing Terraform files')
    parser.add_argument('--output', required=True, help='Path to output markdown file')
    
    args = parser.parse_args()
    
    # Validate that at least one report is provided
    if not args.tfsec_report and not args.checkov_report and not args.tf_directory:
        print("Error: At least one of --tfsec-report, --checkov-report, or --tf-directory must be provided")
        sys.exit(1)
    
    main(args.tfsec_report, args.checkov_report, args.tf_directory, args.output) 