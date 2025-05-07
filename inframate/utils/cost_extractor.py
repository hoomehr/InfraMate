"""
Utility to extract cost information from README.md files.
"""
import re
import os
from typing import Optional

def extract_cost_info(readme_path: str) -> Optional[str]:
    """
    Extract cost information from a README.md file.
    
    Args:
        readme_path: Path to the README.md file
        
    Returns:
        str: Extracted cost information, or None if not found
    """
    if not os.path.exists(readme_path):
        print(f"README file not found at: {readme_path}")
        return None
    
    try:
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # First, try to find the cost section with standard markdown heading
        cost_section_match = re.search(r'## Estimated (?:Monthly )?Costs\s+(.*?)(?:\n##|\Z)', 
                                      content, re.DOTALL)
        
        if cost_section_match:
            return cost_section_match.group(1).strip()
        
        # If not found, try broader pattern
        cost_section_match = re.search(r'(?:Cost|Price) Estimation:?(.*?)(?:\n##|\Z)', 
                                      content, re.DOTALL | re.IGNORECASE)
        
        if cost_section_match:
            return cost_section_match.group(1).strip()
        
        return None
    except Exception as e:
        print(f"Error extracting cost information: {str(e)}")
        return None

def get_formatted_cost_info(readme_path: str) -> str:
    """
    Get formatted cost information suitable for GitHub PR description.
    
    Args:
        readme_path: Path to the README.md file
        
    Returns:
        str: Formatted cost information for PR description
    """
    cost_info = extract_cost_info(readme_path)
    
    if not cost_info:
        return "Cost estimation not available"
    
    return f"""## Estimated Monthly Costs

{cost_info}

*Note: These cost estimates are approximate and may vary based on usage patterns, region, and AWS pricing changes.*""" 