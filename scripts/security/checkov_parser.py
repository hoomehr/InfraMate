#!/usr/bin/env python3
"""
Script to parse Checkov JSON output and generate HTML reports
"""
import json
import sys
import argparse

def parse_checkov_report(json_file, html_file):
    """Parse Checkov JSON report and generate HTML report"""
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Count issues
        failed_checks = data.get('results', {}).get('failed_checks', [])
        issue_count = len(failed_checks)
        
        # Generate HTML report
        with open(html_file, 'w') as f:
            # HTML header
            f.write("""<html>
<head>
    <title>Checkov Security Report</title>
    <style>
        body{font-family:Arial,sans-serif;margin:20px}
        h1{color:#333}
        table{border-collapse:collapse;width:100%}
        th,td{text-align:left;padding:8px;border:1px solid #ddd}
        th{background-color:#f2f2f2}
        tr:nth-child(even){background-color:#f9f9f9}
        .failed{background-color:#ffdddd}
        .passed{background-color:#eaffea}
    </style>
</head>
<body>
    <h1>Checkov Security Scan Results</h1>
""")
            
            # Issue count
            f.write(f"<h2>Found {issue_count} potential security issues</h2>\n")
            
            if issue_count > 0:
                # Table header
                f.write("<table>\n<tr><th>Check ID</th><th>Status</th><th>Description</th><th>Resource</th><th>File</th></tr>\n")
                
                # Table rows
                for result in failed_checks:
                    check_id = result.get('check_id', 'unknown')
                    check_name = result.get('check_name', 'No description')
                    resource = result.get('resource', 'unknown')
                    file_path = result.get('file_path', 'unknown')
                    
                    f.write(f'<tr class="failed"><td>{check_id}</td><td>FAILED</td><td>{check_name}</td><td>{resource}</td><td>{file_path}</td></tr>\n')
                
                f.write("</table>\n")
            else:
                f.write("<p>No security issues found by Checkov! 🎉</p>\n")
            
            # HTML footer
            f.write("</body>\n</html>")
        
        print(f"Checkov scan completed. Found {issue_count} issues.")
        return issue_count
    
    except Exception as e:
        print(f"Error parsing Checkov report: {e}")
        return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse Checkov JSON report and generate HTML')
    parser.add_argument('--json', required=True, help='Path to Checkov JSON report')
    parser.add_argument('--html', required=True, help='Path to output HTML report')
    
    args = parser.parse_args()
    parse_checkov_report(args.json, args.html) 