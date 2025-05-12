#!/usr/bin/env python3

import json
import argparse
import os
from datetime import datetime
import sys
from pathlib import Path

def load_json_data(input_file):
    """Load and parse JSON data from the input file."""
    try:
        with open(input_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Input file '{input_file}' contains invalid JSON.")
        sys.exit(1)

def generate_html_report(data, output_file):
    """Generate an HTML report from the Inframate results."""
    # Extract relevant information from the data
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Start building the HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inframate Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .section {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        .resource-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .resource-card {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }}
        .cost-summary {{
            background-color: #e8f4f8;
            padding: 15px;
            border-radius: 6px;
            margin-top: 20px;
        }}
        .error-section {{
            background-color: #fff3f3;
            padding: 15px;
            border-radius: 6px;
            margin-top: 20px;
            border-left: 4px solid #dc3545;
        }}
        .success-section {{
            background-color: #f0fff4;
            padding: 15px;
            border-radius: 6px;
            margin-top: 20px;
            border-left: 4px solid #28a745;
        }}
        pre {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
        }}
        .timestamp {{
            color: #6c757d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Inframate Analysis Report</h1>
            <p class="timestamp">Generated on: {timestamp}</p>
        </div>
"""

    # Add Infrastructure Overview section
    html_content += """
        <div class="section">
            <h2>Infrastructure Overview</h2>
            <div class="resource-grid">
"""
    
    # Add resources if available
    if 'resources' in data:
        for resource in data['resources']:
            html_content += f"""
                <div class="resource-card">
                    <h3>{resource.get('type', 'Unknown Resource')}</h3>
                    <p><strong>Name:</strong> {resource.get('name', 'N/A')}</p>
                    <p><strong>Region:</strong> {resource.get('region', 'N/A')}</p>
                    <p><strong>Status:</strong> {resource.get('status', 'N/A')}</p>
                </div>
"""

    html_content += """
            </div>
        </div>
"""

    # Add Cost Summary section
    if 'costs' in data:
        html_content += """
        <div class="section">
            <h2>Cost Summary</h2>
            <div class="cost-summary">
"""
        for cost_item in data['costs']:
            html_content += f"""
                <p><strong>{cost_item.get('service', 'Unknown Service')}:</strong> ${cost_item.get('amount', '0.00')}/month</p>
"""
        html_content += """
            </div>
        </div>
"""

    # Add Error Summary section if there are errors
    if 'errors' in data and data['errors']:
        html_content += """
        <div class="section">
            <h2>Error Summary</h2>
            <div class="error-section">
"""
        for error in data['errors']:
            html_content += f"""
                <p><strong>Type:</strong> {error.get('type', 'Unknown Error')}</p>
                <p><strong>Message:</strong> {error.get('message', 'No message available')}</p>
                <p><strong>Timestamp:</strong> {error.get('timestamp', 'N/A')}</p>
                <hr>
"""
        html_content += """
            </div>
        </div>
"""

    # Add Recommendations section
    if 'recommendations' in data:
        html_content += """
        <div class="section">
            <h2>Recommendations</h2>
            <div class="success-section">
"""
        for rec in data['recommendations']:
            html_content += f"""
                <p><strong>{rec.get('category', 'General')}:</strong> {rec.get('message', 'No recommendation available')}</p>
"""
        html_content += """
            </div>
        </div>
"""

    # Close the HTML document
    html_content += """
    </div>
</body>
</html>
"""

    # Write the HTML content to the output file
    try:
        with open(output_file, 'w') as f:
            f.write(html_content)
        print(f"Report generated successfully: {output_file}")
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Generate Inframate HTML report from JSON results')
    parser.add_argument('--input', required=True, help='Input JSON file path')
    parser.add_argument('--output', required=True, help='Output HTML file path')
    
    args = parser.parse_args()
    
    # Ensure the output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Load and process the data
    data = load_json_data(args.input)
    
    # Generate the report
    generate_html_report(data, args.output)

if __name__ == '__main__':
    main() 