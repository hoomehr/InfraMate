import os
import re
import sys
import glob
import google.generativeai as genai

# Set up Gemini API
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable not set")
    sys.exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro')

def extract_resources(dir_path):
    """
    Extract resources from Terraform files using regex
    
    Args:
        dir_path: Path to directory containing Terraform files
        
    Returns:
        List of resources in "type.name" format
    """
    resources = []
    files = glob.glob(f"{dir_path}/*.tf")
    
    for file in files:
        with open(file, 'r') as f:
            content = f.read()
            
        # Find resource blocks
        resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{'
        for match in re.finditer(resource_pattern, content):
            resource_type = match.group(1)
            resource_name = match.group(2)
            resources.append(f"{resource_type}.{resource_name}")
    
    return sorted(resources)

def get_terraform_content(dir_path):
    """Read all Terraform files and resource list in the directory and concatenate their content"""
    content = ""
    files = glob.glob(f"{dir_path}/*.tf")
    
    # First, extract and add resources
    resources = extract_resources(dir_path)
    if resources:
        content += "# Terraform Resources Found\n\n"
        for resource in resources:
            content += f"- {resource}\n"
        content += "\n\n"
    
    # Add summary of all filenames
    content += "# Terraform Files:\n"
    for file in files:
        content += f"- {os.path.basename(file)}\n"
    
    content += "\n# File Contents:\n"
    
    # Then add file contents, but limit total size
    total_size = 0
    max_size = 100000  # Limit to ~100KB total
    
    for file in files:
        with open(file, 'r') as f:
            file_content = f.read()
            file_size = len(file_content)
            
            if total_size + file_size > max_size:
                # If adding this file would exceed the limit, add a truncated version
                available_space = max_size - total_size
                if available_space > 500:  # Only add if we can include a meaningful portion
                    file_content = file_content[:available_space] + "\n... (truncated)"
                    content += f"\n\n## {os.path.basename(file)}\n```terraform\n{file_content}\n```"
                content += "\n\n... (some files omitted due to size constraints)"
                break
            
            content += f"\n\n## {os.path.basename(file)}\n```terraform\n{file_content}\n```"
            total_size += file_size
    
    return content

def analyze_terraform(tf_content):
    """Use Gemini to analyze Terraform files and provide detailed recommendations"""
    prompt = f"""Analyze the following Terraform configuration files and provide:

# Infrastructure Analysis

## Infrastructure Overview
Provide a brief summary of the infrastructure described in the Terraform files. List the main resources and how they're connected.

## Resource Inventory
Create a complete inventory of AWS resources found in the configuration.

## Cost Estimation
Provide a detailed, realistic cost estimation table for the infrastructure in this format:
| Resource Type | Count | Monthly Cost (USD) | Notes |
|--------------|-------|-------------------|-------|
| Resource 1   | X     | $XX.XX            | Any special notes |
| Resource 2   | X     | $XX.XX            | Any special notes |
| **Total**    |       | $XX.XX            | |

Provide separate pricing for different environments if applicable (dev/prod).

## Improvement Recommendations
Suggest specific improvements for this infrastructure with code examples.

## Security Recommendations
Identify potential security issues and how to fix them.

## Cost Optimization
Suggest specific ways to optimize costs with exact savings amounts.

## Scalability Recommendations
Suggest how to improve scalability for this infrastructure.

## Terraform Best Practices
Suggest improvements to follow Terraform best practices.

Present your analysis in markdown format with clear headings for each section.
Be specific and actionable in your recommendations.

Here is the Terraform configuration:

{tf_content}"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating analysis: {str(e)}")
        return "Error generating analysis. Please try again later."

def main():
    # Get the directory path from command-line argument or use default
    if len(sys.argv) > 1:
        tf_dir = sys.argv[1]
    else:
        tf_dir = "/tmp/tf_files"
    
    tf_content = get_terraform_content(tf_dir)
    
    if not tf_content:
        print("No Terraform files found or files are empty.")
        sys.exit(1)
    
    analysis = analyze_terraform(tf_content)
    
    # Save the analysis to a file
    output_file = "terraform_improvements.md"
    with open(output_file, "w") as f:
        f.write("# Terraform Infrastructure Analysis\n\n")
        f.write("*Generated by Inframate - AI-powered infrastructure assistant*\n\n")
        f.write(analysis)
    
    print(f"Analysis complete. Results saved to {output_file}")

if __name__ == "__main__":
    main() 