# Error Handling with Agent Supervision in Inframate

This document explains how to use Inframate's AI-powered error handling system with agent supervision.

## Overview

Inframate's error handling system combines:

1. **Automatic Error Recovery** - Built-in strategies to recover from common errors
2. **AI-powered Analysis** - Uses Google Gemini to analyze error causes and provide solutions
3. **Agent Supervision** - Monitors and manages error loops to prevent infinite retry cycles

## Setting Up

To use the error handling system, you need a Gemini API key:

```bash
export GEMINI_API_KEY=your_api_key_here
```

## Using the Error Handler

The error handler can be used in three ways:

### 1. Via the Agentic Workflow Script

```bash
# Basic usage
./scripts/run_agentic_workflow.sh --repo-path /path/to/repo --action analyze

# With output file
./scripts/run_agentic_workflow.sh --repo-path /path/to/repo --action analyze --output results.json

# With autonomous mode
./scripts/run_agentic_workflow.sh --repo-path /path/to/repo --action auto --autonomous
```

### 2. Directly in Python

```python
from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity

# Initialize the handler
handler = ErrorLoopHandler()

try:
    # Your code that might throw errors
    something_risky()
except Exception as e:
    # Handle the error with AI assistance
    success, solution = handler.handle_error(
        error_type="your_error_type",
        message=str(e),
        severity=ErrorSeverity.HIGH,
        context_data={"additional": "context", "for": "AI"}
    )
    
    if solution:
        print(f"AI solution: {solution}")
```

### 3. Via GitHub Actions

Simply trigger the workflow from GitHub Actions, and it will handle errors automatically:

```yaml
name: Analyze Infrastructure
on: [push]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Inframate Analysis
        uses: yourusername/inframate-action@v1
        with:
          gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
          action: analyze
```

## Example Error Scenarios

### Terraform Errors

```
Error: Error creating DB Instance: DBInstanceAlreadyExists: DB instance already exists
Status code: 400, request id: 5da782a5-c397-45a3-9b6d-1234567890abc

on main.tf line 25, in resource "aws_db_instance" "database":
  25: resource "aws_db_instance" "database" {
```

**AI-powered Solution:**
```json
{
  "root_cause": "You're trying to create an RDS database instance with a name that already exists in your AWS account.",
  "solution": "1. Use the AWS console or CLI to confirm if the database already exists\n2. Add 'lifecycle { create_before_destroy = true }' to the resource\n3. Use a unique name for the database by adding a prefix or suffix\n4. Import the existing database into your Terraform state",
  "prevention": "Always use unique names for resources, preferably with environment-specific prefixes or suffixes. Consider using random_id or random_pet resources to generate unique names."
}
```

### API Rate Limit Errors

```
Rate limit exceeded: API calls quota exceeded, retry after 60 seconds
```

**AI-powered Solution:**
```json
{
  "root_cause": "You've exceeded the AWS API rate limits for the specific service you're using.",
  "solution": "1. Implement exponential backoff for API requests\n2. Decrease the frequency of API calls\n3. Wait for the specified time (60 seconds) before retrying\n4. Consider requesting a rate limit increase from AWS if this happens regularly",
  "prevention": "Implement rate limiting in your application, batch API requests when possible, and use AWS SDK features like automatic retries with exponential backoff."
}
```

## Running the Demo

To see the error handler in action, run:

```bash
GEMINI_API_KEY=your_api_key python tests/demo_error_handling.py
```

This will simulate different error scenarios and show how the AI analyzes and provides solutions.

## The Error Loop Prevention Mechanism

The system prevents infinite error loops through:

1. **Maximum Retry Limits** - Each error type has a maximum number of retry attempts
2. **Exponential Backoff** - Increasing wait times between retries
3. **Error Context Tracking** - Monitoring error patterns to detect loops
4. **Severity-Based Handling** - Different strategies based on error severity

## Custom Error Strategies

You can register custom error recovery strategies:

```python
from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity

handler = ErrorLoopHandler()

# Define a custom recovery strategy
def handle_custom_error(context):
    # Custom recovery logic
    if "specific_condition" in context.message:
        # Do something
        return "retry"
    return None

# Register the strategy
handler.supervisor.register_recovery_strategy(
    "custom_error_type",
    handle_custom_error
)
```

## Error Report Format

The error handler generates structured reports:

```json
{
  "errors": [
    {
      "type": "terraform_error",
      "message": "Error creating resource",
      "severity": "high",
      "retry_count": 2,
      "ai_solution": {
        "root_cause": "...",
        "solution": "...",
        "prevention": "..."
      }
    }
  ],
  "total_error_count": 1,
  "recovered_count": 1,
  "unrecovered_count": 0
}
``` 