# Inframate Test Scenarios

This document provides a collection of test scenarios to demonstrate Inframate's agentic workflow and error handling capabilities. Each scenario includes a description, steps to reproduce, expected outcomes, and sample commands.

## Setup

Before running these scenarios, ensure you have Inframate properly installed and configured:

```bash
# Set up your Gemini API key
export GEMINI_API_KEY=your_api_key_here

# Make sure the wrapper script is executable
chmod +x scripts/run_agentic_workflow.sh
```

## Scenario 1: Basic Repository Analysis

**Objective**: Analyze a repository and generate infrastructure recommendations.

**Steps**:
1. Create a sample repository with a simple web application
2. Add an `inframate.md` file with basic requirements
3. Run the analyze action

**Sample Repository Structure**:
```
sample_app/
├── app.js              # Express.js application
├── package.json        # Node.js dependencies
├── public/             # Static assets
├── views/              # HTML templates
└── inframate.md        # Inframate configuration
```

**Sample inframate.md**:
```markdown
# Inframate Configuration

## Description
A simple Express.js web application that serves HTML content.

## Language
Node.js

## Framework
Express.js

## Database
MongoDB

## Requirements
- High availability
- Auto-scaling
- Secure HTTPS connection
```

**Command**:
```bash
./scripts/run_agentic_workflow.sh --repo-path ./sample_app --action analyze
```

**Expected Outcome**:
1. Repository analysis detects Node.js and Express.js
2. AI-powered recommendation suggests AWS Lambda and API Gateway
3. Infrastructure recommendations include high availability setup
4. Cost estimations are generated
5. No errors should occur

## Scenario 2: Infrastructure Optimization with Forced Error

**Objective**: Demonstrate error handling when a resource conflict occurs.

**Steps**:
1. Create a sample repository with Terraform files
2. Intentionally include a resource that will cause conflicts
3. Run the optimize action

**Sample Terraform File (main.tf)**:
```hcl
provider "aws" {
  region = "us-west-2"
}

# This resource will cause a conflict due to invalid parameter
resource "aws_instance" "web" {
  ami           = "non-existent-ami"
  instance_type = "t3.micro"
  name          = "web-server"  # Incorrect parameter (should be 'tags')
  
  # Missing required parameters
}
```

**Command**:
```bash
./scripts/run_agentic_workflow.sh --repo-path ./sample_terraform --action optimize --output results.json
```

**Expected Outcome**:
1. Analysis detects invalid parameters in Terraform configuration
2. Error handler identifies the issue
3. Gemini API analyzes the error and provides a solution
4. Error report contains the root cause and recommended fixes
5. Results JSON includes AI-powered solution

**Error Handling Verification**:
```bash
# Check the error solution
cat results.json | jq '.error.ai_solution'
```

## Scenario 3: Security Analysis with API Rate Limit Error

**Objective**: Demonstrate error recovery from rate limit errors.

**Steps**:
1. Configure the Gemini API key to a test key with rate limits
2. Create a complex repository with many security issues
3. Run the secure action with several repos in sequence to trigger rate limits

**Command Sequence**:
```bash
# Run security analysis on multiple repositories to trigger rate limits
for repo in sample_repo_1 sample_repo_2 sample_repo_3; do
  ./scripts/run_agentic_workflow.sh --repo-path ./$repo --action secure
done
```

**Expected Outcome**:
1. First analysis runs successfully
2. Second analysis triggers a rate limit error
3. Error handler implements exponential backoff
4. System retries after appropriate delay
5. All analyses eventually complete successfully

**Error Handling Verification**:
```bash
# Check the error history
grep "Rate limit" logs/inframate.log
```

## Scenario 4: Autonomous Mode with Unrecoverable Error

**Objective**: Demonstrate comprehensive error reporting for unrecoverable errors.

**Steps**:
1. Create a sample repository with complex infrastructure
2. Configure tools to generate an unrecoverable error (e.g., intentionally corrupt a file)
3. Run the auto action in autonomous mode

**Command**:
```bash
# Run in autonomous mode with output to error_demo.json
./scripts/run_agentic_workflow.sh --repo-path ./complex_app --action auto --autonomous --output error_demo.json
```

**Expected Outcome**:
1. Workflow begins and executes initial steps
2. Unrecoverable error is encountered
3. Error handler attempts recovery strategies
4. AI-powered error analysis provides detailed solution
5. Error report contains comprehensive information

**Error Report Analysis**:
```bash
# Generate a human-readable error report
python -c '
import json
with open("error_demo.json") as f:
    data = json.load(f)
    if "error" in data and "ai_solution" in data["error"]:
        print("Root Cause:", data["error"]["ai_solution"].get("root_cause", "Unknown"))
        print("Solution:", data["error"]["ai_solution"].get("solution", "No solution available"))
        print("Prevention:", data["error"]["ai_solution"].get("prevention", "No prevention available"))
'
```

## Scenario 5: Full End-to-End Workflow

**Objective**: Demonstrate the complete agentic workflow with visualization.

**Steps**:
1. Create a comprehensive repository with a complex application
2. Ensure all dependencies are installed
3. Run the auto action

**Command**:
```bash
# Run complete workflow with all actions
./scripts/run_agentic_workflow.sh --repo-path ./full_application --action auto
```

**Expected Outcome**:
1. Repository analysis completes successfully
2. Optimization recommendations are generated
3. Security analysis identifies vulnerabilities
4. Visualizations are created
5. Comprehensive report is generated
6. Any errors are handled appropriately

**Verification**:
```bash
# Check if visualizations were created
ls -la full_application/visualizations/

# Check the analysis results
cat analysis_results.json | jq '.analysis'
```

## Error Injection for Testing

To systematically test error handling, you can use the error injection utility:

```python
# examples/inject_error.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity

def inject_terraform_error():
    handler = ErrorLoopHandler()
    
    # Simulate a Terraform syntax error
    error_message = """
    Error: Error parsing /path/to/main.tf: Invalid block definition
    
    on main.tf line 15:
      15: resource aws_instance "example" {
    
    A block definition must have block content delimited by "{" and "}", starting on the same line as the block header.
    """
    
    success, solution = handler.handle_error(
        error_type="terraform_error",
        message=error_message,
        severity=ErrorSeverity.HIGH,
        context_data={"file": "main.tf", "line": 15}
    )
    
    print(f"Recovery successful: {success}")
    if solution:
        print("AI Solution:")
        print(f"Root cause: {solution.get('root_cause', 'Unknown')}")
        print(f"Solution: {solution.get('solution', 'Not provided')}")
        print(f"Prevention: {solution.get('prevention', 'Not provided')}")

if __name__ == "__main__":
    inject_terraform_error()
```

Run with:
```bash
python examples/inject_error.py
```

## GitHub Actions Tests

To test the GitHub Actions integration, you can use the following workflow file:

```yaml
name: Inframate Test Workflow

on:
  workflow_dispatch:
    inputs:
      scenario:
        description: 'Test scenario to run (1-5)'
        required: true
        default: '1'

jobs:
  test-inframate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up test environment
        run: |
          # Create test repositories based on scenario
          mkdir -p test_repos/scenario_${{ github.event.inputs.scenario }}
          
          # Create sample files based on scenario
          if [ "${{ github.event.inputs.scenario }}" = "1" ]; then
            echo "Creating basic Node.js app for Scenario 1"
            mkdir -p test_repos/scenario_1/{public,views}
            echo '{"name":"sample-app","dependencies":{"express":"^4.17.1"}}' > test_repos/scenario_1/package.json
            echo 'const express = require("express"); const app = express(); app.listen(3000);' > test_repos/scenario_1/app.js
            echo '# Inframate Configuration...' > test_repos/scenario_1/inframate.md
          fi
          
          # [Additional scenario setups would go here]
      
      - name: Run Inframate test
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          # Run the appropriate test scenario
          ./scripts/run_agentic_workflow.sh --repo-path ./test_repos/scenario_${{ github.event.inputs.scenario }} --action auto --output test_results.json
          
      - name: Upload test results
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test_results.json
```

## Conclusion

These test scenarios demonstrate the capabilities of Inframate's agentic workflow and error handling system. By running through these scenarios, you can verify that:

1. The base analysis flow works as expected
2. Error detection and handling functions correctly
3. AI-powered error analysis provides useful solutions
4. The system can recover from recoverable errors
5. Unrecoverable errors are properly reported and documented

For additional test scenarios or custom error handling demonstration, see the `examples/error_handling_example.md` file. 