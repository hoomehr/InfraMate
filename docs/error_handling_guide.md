# Inframate Error Handling Guide

This guide explains how to use Inframate's enhanced error handling system, which provides robust error recovery capabilities powered by AI.

## Overview

Inframate implements a comprehensive error handling system with the following components:

1. **Error Detection** - Monitoring for errors during workflow execution
2. **AI-Powered Error Analysis** - Using Gemini to analyze and solve errors
3. **Recovery Strategies** - Specialized handlers for different error types
4. **Fallback Mechanisms** - Rule-based recovery when AI is unavailable
5. **Reporting System** - Detailed error reports and history

## Supported Error Types

The system handles these error types:

| Error Type | Description | Example |
|------------|-------------|---------|
| `api_error` | API-related errors (rate limits, timeouts) | "Rate limit exceeded" |
| `terraform_error` | Terraform execution errors | "Error acquiring state lock" |
| `resource_conflict` | Resource already exists or conflicts | "Resource already exists" |
| `system_error` | General system or runtime errors | "Critical system failure" |
| `permission_error` | Access or permission issues | "Access denied" |
| `network_error` | Network connectivity issues | "Connection timeout" |
| `validation_error` | Input validation failures | "Invalid format" |
| `gemini_error` | Errors with Gemini API | "Quota exceeded" |
| `unknown_error` | Any unclassified errors | (Mapped to system_error) |

## Using the Error Handler

### Basic Usage

```python
from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity

# Initialize the handler
handler = ErrorLoopHandler()

# Handle an error
success, solution = handler.handle_error(
    "terraform_error",  # Error type
    "Error: Error acquiring the state lock",  # Error message
    ErrorSeverity.MEDIUM,  # Severity level
    {"context": "additional info"}  # Optional context
)

# Check if recovery was successful
if success:
    print("Error was successfully recovered")
    
# Check if an AI solution was provided
if solution:
    print(f"AI solution: {solution}")
```

### Integration with Try/Except

```python
from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity

handler = ErrorLoopHandler()

try:
    # Your code that might raise an exception
    result = some_risky_operation()
except Exception as e:
    # Handle the exception using the error handler
    error_type = "system_error"  # Default, or map the exception type
    
    # You can map exception types to error types
    if isinstance(e, ConnectionError):
        error_type = "network_error"
    elif isinstance(e, PermissionError):
        error_type = "permission_error"
    
    success, solution = handler.handle_error(
        error_type,
        str(e),
        ErrorSeverity.MEDIUM
    )
    
    if not success:
        # If recovery failed, you might want to re-raise or log
        logger.error(f"Failed to recover from {error_type}: {e}")
```

## Error Severity Levels

Error severity helps determine retry behavior and recovery strategies:

- `LOW` - Minor issues that might self-resolve
- `MEDIUM` - Standard errors that need handling but aren't critical
- `HIGH` - Serious errors that might impact functionality
- `CRITICAL` - Major failures that require immediate attention (limited retries)

## AI-Powered Solutions

When Gemini API is available, the system will:

1. Analyze the error context and message
2. Generate a detailed solution with:
   - Root cause analysis
   - Step-by-step recovery instructions
   - Preventive measures

The AI solution is returned along with the recovery status and stored in error history.

## Fallback Mechanisms

When Gemini API is not available, the system uses rule-based recovery strategies:

1. Pattern matching on error messages
2. Exponential backoff for retries
3. Specialized handlers for known error patterns
4. Default strategies based on error type

## Error Reporting

You can generate comprehensive error reports:

```python
handler = ErrorLoopHandler()
# ... handle some errors ...

# Get detailed error report
report = handler.get_error_report()

# Report includes:
# - Total error count
# - Recovered vs unrecovered counts
# - Error type distribution
# - Detailed history of each error with solutions
```

## Command-Line Interface

You can use the test scripts to verify error handling:

```bash
# Test all error types
python scripts/test_error_handling.py --test-all

# Test specific system errors (with Gemini integration)
python scripts/test_system_error.py

# Test recovery of injected errors
python scripts/test_system_error.py
```

## GitHub Actions Integration

The error handling system is integrated with GitHub Actions for CI/CD environments:

1. Automated error detection in workflows
2. Error analysis and recovery
3. Reporting through PR comments and artifacts
4. Optional retry of failed workflows after recovery

To use in GitHub Actions, set up the workflow trigger:

```yaml
on:
  workflow_run:
    workflows: ['*']
    types:
      - completed
```

## Best Practices

1. **Classify errors properly** - Use the most specific error type
2. **Provide detailed error messages** - More context helps AI generate better solutions
3. **Include relevant context data** - Add information that helps with recovery
4. **Set appropriate severity levels** - This affects retry behavior
5. **Check both success and solution** - Even failed recoveries might have useful AI solutions

## Extending the System

You can extend the error handling system by:

1. **Adding new error types** - Register new recovery strategies
2. **Enhancing recovery strategies** - Add specialized handlers for specific patterns
3. **Improving AI prompts** - Refine the prompts for better solutions
4. **Adding custom fallbacks** - Create domain-specific recovery mechanisms

Example for adding a custom error type:

```python
# Create a custom handler
def _handle_custom_error(context):
    if "specific pattern" in context.message.lower():
        # Custom recovery logic
        return "custom_recovery"
    return None

# Register with the handler
handler = ErrorLoopHandler()
handler.supervisor.register_recovery_strategy(
    "custom_error",
    lambda ctx: _handle_custom_error(ctx)
)
``` 