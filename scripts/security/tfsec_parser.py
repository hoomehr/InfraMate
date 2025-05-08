#!/usr/bin/env python3
"""
Script to parse TFSec JSON output and generate HTML reports
"""
import json
import sys
import argparse

def parse_tfsec_report(json_file, html_file):
    """Parse TFSec JSON report and generate HTML report"""
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Count issues
        results = data.get('results', [])
        issue_count = len(results)
        
        # Generate HTML report
        with open(html_file, 'w') as f:
            # HTML header
            f.write("""<html>
<head>
    <title>TFSec Security Report</title>
    <style>
        body{font-family:Arial,sans-serif;margin:20px}
        h1{color:#333}
        table{border-collapse:collapse;width:100%}
        th,td{text-align:left;padding:8px;border:1px solid #ddd}
        th{background-color:#f2f2f2}
        tr:nth-child(even){background-color:#f9f9f9}
        .critical{background-color:#ffdddd}
        .high{background-color:#ffffcc}
        .medium{background-color:#e6f3ff}
        .low{background-color:#eaffea}
    </style>
</head>
<body>
    <h1>TFSec Security Scan Results</h1>
""")
            
            # Issue count
            f.write(f"<h2>Found {issue_count} potential security issues</h2>\n")
            
            if issue_count > 0:
                # Table header
                f.write("<table>\n<tr><th>Rule ID</th><th>Severity</th><th>Description</th><th>Location</th></tr>\n")
                
                # Table rows
                for result in results:
                    severity = result.get('severity', 'unknown').lower()
                    rule_id = result.get('rule_id', 'unknown')
                    description = result.get('description', 'No description')
                    location = f"{result.get('location', {}).get('filename', 'unknown')}:{result.get('location', {}).get('start_line', 0)}"
                    
                    f.write(f'<tr class="{severity}"><td>{rule_id}</td><td>{severity.upper()}</td><td>{description}</td><td>{location}</td></tr>\n')
                
                f.write("</table>\n")
            else:
                f.write("<p>No security issues found by TFSec! 🎉</p>\n")
            
            # HTML footer
            f.write("</body>\n</html>")
        
        print(f"TFSec scan completed. Found {issue_count} issues.")
        return issue_count
    
    except Exception as e:
        print(f"Error parsing TFSec report: {e}")
        return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse TFSec JSON report and generate HTML')
    parser.add_argument('--json', required=True, help='Path to TFSec JSON report')
    parser.add_argument('--html', required=True, help='Path to output HTML report')
    
    args = parser.parse_args()
    parse_tfsec_report(args.json, args.html) 