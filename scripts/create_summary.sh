#!/bin/bash
# Script to create a security summary report

# Print input arguments for debugging
echo "Script received arguments: $1 $2 $3"

# Validate input arguments
if [ $# -ne 3 ]; then
  echo "Error: Not enough arguments"
  echo "Usage: $0 <tfsec_issues> <checkov_issues> <output_file>"
  echo "Creating default report anyway..."
  # Set default values
  TFSEC_ISSUES=0
  CHECKOV_ISSUES=0
  OUTPUT_FILE=${3:-"SECURITY_REPORT.md"}
else
  TFSEC_ISSUES=$1
  CHECKOV_ISSUES=$2
  OUTPUT_FILE=$3
fi

# Make sure issues are numeric
if ! [[ "$TFSEC_ISSUES" =~ ^[0-9]+$ ]]; then
  echo "Warning: TFSec issues count is not a number, defaulting to 0"
  TFSEC_ISSUES=0
fi

if ! [[ "$CHECKOV_ISSUES" =~ ^[0-9]+$ ]]; then
  echo "Warning: Checkov issues count is not a number, defaulting to 0"
  CHECKOV_ISSUES=0
fi

TOTAL_ISSUES=$((TFSEC_ISSUES + CHECKOV_ISSUES))

# Create basic report
echo "# Security Scan Report" > $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

# Check if AI analysis exists and include it first
if [ -f "AI_SECURITY_ANALYSIS.md" ]; then
  echo "## AI-Powered Security Analysis" >> $OUTPUT_FILE
  echo "" >> $OUTPUT_FILE
  echo "The following security analysis was generated by Google Gemini AI:" >> $OUTPUT_FILE
  echo "" >> $OUTPUT_FILE
  
  # Extract just the content part (skip the title)
  sed -n '3,$p' AI_SECURITY_ANALYSIS.md >> $OUTPUT_FILE
  echo "" >> $OUTPUT_FILE
  echo "---" >> $OUTPUT_FILE
  echo "" >> $OUTPUT_FILE
else
  echo "## AI-Powered Security Analysis" >> $OUTPUT_FILE
  echo "" >> $OUTPUT_FILE
  echo "⚠️ AI security analysis was not generated. Please check the logs for more information." >> $OUTPUT_FILE
  echo "" >> $OUTPUT_FILE
  echo "---" >> $OUTPUT_FILE
  echo "" >> $OUTPUT_FILE
fi

echo "## Summary" >> $OUTPUT_FILE
echo "- **Total Issues Found**: ${TOTAL_ISSUES}" >> $OUTPUT_FILE
echo "- **TFSec Issues**: ${TFSEC_ISSUES}" >> $OUTPUT_FILE
echo "- **Checkov Issues**: ${CHECKOV_ISSUES}" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "## Detailed Reports" >> $OUTPUT_FILE
echo "- [TFSec Report](tfsec_report.md)" >> $OUTPUT_FILE
echo "- [Checkov Report](checkov_report.txt)" >> $OUTPUT_FILE
echo "- [Complete AI Analysis](AI_SECURITY_ANALYSIS.md)" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "## Recommendations" >> $OUTPUT_FILE

# Add recommendations based on common findings
if [ $TOTAL_ISSUES -gt 0 ]; then
  echo "### General Security Recommendations" >> $OUTPUT_FILE
  echo "- Encrypt sensitive data at rest and in transit" >> $OUTPUT_FILE
  echo "- Use IAM roles with least privilege access" >> $OUTPUT_FILE
  echo "- Enable logging and monitoring for all resources" >> $OUTPUT_FILE
  echo "- Implement network security groups with restrictive rules" >> $OUTPUT_FILE
  echo "- Use secure defaults for all resources" >> $OUTPUT_FILE
  echo "" >> $OUTPUT_FILE
  echo "### Common Issues to Fix" >> $OUTPUT_FILE
  
  # Extract common issues from TFSec
  if [ $TFSEC_ISSUES -gt 0 ] && [ -f "tfsec_report.md" ]; then
    echo "#### TFSec Findings" >> $OUTPUT_FILE
    grep -o '\*\*Description\*\*: .*' tfsec_report.md | sed 's/\*\*Description\*\*: /- /' | sort | uniq | head -10 >> $OUTPUT_FILE 2>/dev/null || echo "- Unable to extract TFSec findings" >> $OUTPUT_FILE
  fi
  
  # Extract common issues from Checkov
  if [ $CHECKOV_ISSUES -gt 0 ] && [ -f "checkov_report.txt" ]; then
    echo "#### Checkov Findings" >> $OUTPUT_FILE
    grep 'Check:' checkov_report.txt | sed 's/Check: /- /' | sort | uniq | head -10 >> $OUTPUT_FILE 2>/dev/null || echo "- Unable to extract Checkov findings" >> $OUTPUT_FILE
  fi
else
  echo "🎉 No security issues found! Keep up the good work!" >> $OUTPUT_FILE
  echo "" >> $OUTPUT_FILE
  echo "### Proactive Security Recommendations" >> $OUTPUT_FILE
  echo "- Regularly update your providers and modules" >> $OUTPUT_FILE
  echo "- Implement infrastructure security scanning in your CI/CD pipeline" >> $OUTPUT_FILE
  echo "- Review IAM permissions regularly and follow least privilege principle" >> $OUTPUT_FILE
  echo "- Enable encryption and logging across all services" >> $OUTPUT_FILE
  echo "- Use Terraform modules from trusted sources" >> $OUTPUT_FILE
fi

echo "Security report generated: $OUTPUT_FILE" 