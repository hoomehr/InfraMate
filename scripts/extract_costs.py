#!/usr/bin/env python3
"""
Extract cost information from Terraform README files
"""
import re
import sys
import argparse

def extract_costs_from_readme(readme_path):
    """
    Extract cost information from a README file
    
    Args:
        readme_path: Path to the README file
        
    Returns:
        String containing the extracted cost information
    """
    try:
        with open(readme_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"
    
    # Look for Cost section using various patterns
    cost_patterns = [
        r'(?:##\s*(?:Estimated|Monthly|Approximate)\s*(?:Monthly\s*)?Costs?).*?(?=##|$)',
        r'(?:##\s*Cost\s*Estimation).*?(?=##|$)',
        r'(?:##\s*Costs?).*?(?=##|$)',
        r'(?:Cost\s*Breakdown).*?(?=##|$)'
    ]
    
    for pattern in cost_patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            cost_section = match.group(0).strip()
            # Clean up the section to remove unnecessary formatting
            cost_section = re.sub(r'```.*?```', '', cost_section, flags=re.DOTALL)
            return cost_section
    
    # If no dedicated cost section found, look for cost information in the content
    cost_lines = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if re.search(r'cost|price|\$|usd|estimate', line, re.IGNORECASE):
            # Include context (line before and after)
            start = max(0, i-1)
            end = min(len(lines), i+2)
            cost_lines.extend(lines[start:end])
            cost_lines.append('')  # Add a blank line for readability
    
    if cost_lines:
        return "\n".join(cost_lines)
    
    return "No cost information found in the file."

def main():
    parser = argparse.ArgumentParser(description='Extract cost information from README.md files')
    parser.add_argument('--readme', required=True, help='Path to the README.md file')
    
    args = parser.parse_args()
    
    cost_info = extract_costs_from_readme(args.readme)
    print(cost_info)

if __name__ == "__main__":
    main() 