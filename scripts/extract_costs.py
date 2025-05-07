#!/usr/bin/env python
"""
Extract cost information from the Terraform README.md file.
This script can be used in CI/CD pipelines to include cost 
information in pull request descriptions.
"""
import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from inframate.utils.cost_extractor import get_formatted_cost_info

def main():
    """Extract cost information from README.md file."""
    parser = argparse.ArgumentParser(description="Extract cost information from README.md")
    parser.add_argument("--readme", default="terraform/README.md", 
                        help="Path to the README.md file (default: terraform/README.md)")
    parser.add_argument("--output", default=None,
                        help="Path to output file (default: print to stdout)")
    
    args = parser.parse_args()
    
    # Make path absolute if it's relative
    readme_path = args.readme
    if not os.path.isabs(readme_path):
        readme_path = os.path.join(os.getcwd(), readme_path)
    
    # Get formatted cost information
    cost_info = get_formatted_cost_info(readme_path)
    
    # Write to output file or print to stdout
    if args.output:
        with open(args.output, 'w') as f:
            f.write(cost_info)
        print(f"Cost information written to {args.output}")
    else:
        print(cost_info)

if __name__ == "__main__":
    main() 