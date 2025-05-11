# Error Handling and Recovery Flow in Inframate

This document explains how Inframate's error handling system works, particularly the secondary flow that is triggered when errors occur in the main workflow.

## Overview

Inframate implements a comprehensive error handling system with the following components:

1. **Primary Workflow** - The main infrastructure management workflow
2. **Error Detection** - Monitoring for errors during workflow execution
3. **Secondary Error Flow** - A dedicated flow triggered when errors are detected
4. **AI-Powered Error Analysis** - Using Gemini to analyze and solve errors
5. **Recovery Mechanisms** - Strategies to recover from different error types
6. **Reporting System** - Comprehensive error reports and visualizations

## Error Handling Architecture

The error handling system is designed as a state machine with the following states:

```
         ┌───────────┐
         │ INITIAL   │
         └─────┬─────┘
               │ Error detected
               ▼
         ┌───────────┐
         │ DETECTED  │◄───────┐
         └─────┬─────┘        │
               │ Begin analysis│
               ▼              │
         ┌───────────┐        │ New error
         │ ANALYZING │        │ detected
         └─────┬─────┘        │
               │ Begin recovery│
               ▼              │
         ┌───────────┐        │
         │ RECOVERY  │────────┘
         └─────┬─────┘
          ▲    │
          │    │ Max retries
          │    │ exceeded
          │    ▼
┌─────────┴───┐ ┌───────────┐
│ RESOLVED    │ │ FAILED    │
└─────────────┘ └───────────┘
```

## Secondary Error Flow

When an error is detected in the main workflow, the following secondary flow is triggered:

1. **Error Detection**
   - Exception is caught in a try/except block
   - Error context is captured (stack trace, parameters, environment)
   - Error state transitions to DETECTED

2. **Error Classification**
   - Error is classified by type (API, Terraform, Permission, etc.)
   - Severity is determined (LOW, MEDIUM, HIGH, CRITICAL)
   - Classification helps determine recovery strategy

3. **AI-Powered Analysis**
   - Error details are sent to Gemini API
   - AI analyzes root cause and suggests solutions
   - Recovery steps are generated based on error type and context

4. **Recovery Attempt**
   - System implements appropriate recovery strategy
   - Recovery may involve retries, backoff, or specific fixes
   - State transitions to RECOVERY

5. **Outcome Determination**
   - If recovery succeeds, state transitions to RESOLVED
   - If recovery fails and max retries not exceeded, return to RECOVERY
   - If recovery fails and max retries exceeded, state transitions to FAILED

6. **Reporting**
   - Comprehensive error report is generated
   - Report includes AI analysis, recovery attempts, and outcomes
   - If in GitHub Actions, issues are created with detailed reports

## Error Types and Recovery Strategies

The system handles several error types with specific recovery strategies:

| Error Type | Description | Recovery Strategy | Example |
|------------|-------------|-------------------|---------|
| API | Rate limits, auth failures | Exponential backoff, retry | Gemini API rate limit |
| Terraform | Syntax, resource conflicts | Fix syntax, handle conflicts | Invalid resource parameter |
| Permission | Access denied | Request permissions, use alternative | IAM permission denied |
| Network | Connectivity issues | Retry, switch endpoints | API endpoint timeout |
| Resource | Resource conflicts | Handle conflict, alter params | Resource already exists |
| Validation | Invalid input | Correct input data | Invalid parameter value |
| System | OS/environment issues | Fix environment | Missing dependency |

## Error Loop Prevention

To prevent infinite error loops, the system implements:

1. **Maximum Retry Limits**
   - Each error type has a configurable maximum retry count
   - Default is 3 retries for most errors

2. **Exponential Backoff**
   - Wait time increases with each retry attempt
   - Formula: `base_delay * (backoff_factor ^ retry_count)`

3. **Error Pattern Detection**
   - System detects repeating error patterns
   - If same error occurs repeatedly, different strategy is used

4. **Recovery History**
   - All recovery attempts are recorded
   - History is used to prevent repeating failed strategies

## Integration with Agentic Workflow

The error handling system integrates with the agentic workflow in two ways:

### 1. Error-Aware Execution

Each action in the agentic workflow is wrapped with error handling:

```python
def analyze_infrastructure(self) -> Dict[str, Any]:
    self.current_state = WorkflowState.ANALYZING
    
    # Execute with error handling
    success, result, error_info = self.execute_with_error_handling(
        self._analyze_infrastructure_impl
    )
    
    if success:
        return result
    else:
        # Handle error and try to recover
        recovery_success, solution = self.handle_error_flow(error_info)
        
        if recovery_success:
            # Try again if recovery was successful
            success, result, error_info = self.execute_with_error_handling(
                self._analyze_infrastructure_impl
            )
            
            if success:
                return result
        
        # Return error result if recovery failed
        return {
            "status": "error",
            "error": error_info,
            "ai_solution": solution
        }
```

### 2. Autonomous Recovery

In autonomous mode, the system can apply fixes automatically:

```python
if recovery_success and ai_solution and self.autonomous:
    logger.info("Applying recommended solution in autonomous mode")
    self.error_state = ErrorState.RECOVERY
    self._apply_ai_solution(ai_solution, error_type, context_data)
```

## Error Reporting

The error handling system generates detailed reports:

```json
{
  "success": false,
  "action": "analyze",
  "error": {
    "type": "terraform_error",
    "message": "Error applying plan: 1 error occurred...",
    "recovery_attempts": [
      {
        "timestamp": 1683024789.23,
        "error_type": "terraform_error",
        "success": true,
        "ai_solution": {
          "root_cause": "Invalid AMI ID specified",
          "solution": "1. Check the AMI ID format...",
          "prevention": "Always validate AMI IDs..."
        },
        "duration": 3.45
      }
    ],
    "ai_solution": {
      "root_cause": "Invalid AMI ID specified",
      "solution": "1. Check the AMI ID format...",
      "prevention": "Always validate AMI IDs..."
    }
  },
  "error_report": {
    "total_errors": 1,
    "recovered_errors": 1,
    "unrecovered_errors": 0,
    "error_types": {
      "terraform_error": 1
    }
  }
}
```

## Using the Error Handling System

You can use the error handling system in different ways:

### 1. Via the Agentic Workflow Script

```bash
# Run with default error handling
./scripts/run_agentic_workflow.sh --repo-path ./my-app --action analyze

# Run with verbose error reporting
./scripts/run_agentic_workflow.sh --repo-path ./my-app --action analyze --error-mode verbose

# Run with silent error handling (minimal reporting)
./scripts/run_agentic_workflow.sh --repo-path ./my-app --action analyze --error-mode silent
```

### 2. Via GitHub Actions

```yaml
- name: Run Inframate with error handling
  uses: actions/github-script@v6
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  with:
    script: |
      const { execSync } = require('child_process');
      execSync('./scripts/run_agentic_workflow.sh --repo-path . --action analyze');
```

### 3. In Your Own Code

```python
from scripts.agentic_error_workflow import AgenticWorkflow

# Create workflow
workflow = AgenticWorkflow(
    repo_path="/path/to/repo",
    action="analyze",
    autonomous=True
)

# Execute with error handling
results = workflow.execute()

# Check for errors
if not results["success"]:
    error = results.get("error", {})
    print(f"Error: {error.get('message')}")
    
    # Get AI solution
    solution = error.get("ai_solution", {})
    if solution:
        print(f"Solution: {solution.get('solution')}")
```

### 4. Via Independent Error Recovery Workflow

For continuous integration environments, you can trigger error recovery as a standalone workflow using:

```yaml
name: Trigger Error Recovery

on:
  workflow_dispatch:
    inputs:
      error_type:
        description: 'Error type to fix'
        required: true
        default: 'terraform_error'

jobs:
  trigger-recovery:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Recovery Workflow
        uses: actions/github-script@v6
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            await github.rest.actions.createWorkflowDispatch({
              owner: context.repo.owner,
              repo: context.repo.repo,
              workflow_id: 'error_recovery.yml',
              ref: 'main',
              inputs: {
                error_type: '${{ github.event.inputs.error_type }}',
                error_message: 'Manually triggered recovery',
                repo_path: '.',
                autonomous_mode: 'true'
              }
            });
```

The error recovery workflow will:

1. **Automatically trigger** when the Agentic Infrastructure Management workflow fails
2. **Download artifacts** from the failed workflow and extract error information
3. **Analyze the error** using the error handling system 
4. **Attempt recovery** using AI-powered analysis and specific strategies
5. **Generate a detailed report** with recovery results and AI-generated solutions
6. **Create an issue** if recovery fails, or just report success if it works

You can also manually trigger the workflow from the GitHub Actions tab, specifying:
- Error type (api_error, terraform_error, etc.)
- Error message
- Repository path
- Whether to apply fixes automatically (autonomous mode)

This is especially useful for CI/CD pipelines, where you want infrastructure deployment to self-heal when errors occur.

## Demos and Examples

You can run the error flow demonstration script to see the error handling in action:

```bash
# Demonstrate Terraform error handling
python examples/error_flow_demo.py --error-type terraform

# Demonstrate API rate limit error handling
python examples/error_flow_demo.py --error-type api

# Demonstrate permission error handling
python examples/error_flow_demo.py --error-type permission

# Demonstrate multiple errors in auto mode
python examples/error_flow_demo.py --error-type multi
```

## Best Practices

1. **Always Set Gemini API Key**
   - Full error analysis requires the Gemini API
   - `export GEMINI_API_KEY=your_key_here`

2. **Use Error Reports**
   - Error reports contain valuable insights
   - Check the AI-generated solutions for common issues

3. **Start with Non-Autonomous Mode**
   - Test error handling without autonomous recovery first
   - Switch to autonomous mode once confident

4. **Monitor Recovery Patterns**
   - Watch for recurring errors
   - Adjust retry limits and strategies as needed

5. **Extend for Your Use Case**
   - Add custom error types and recovery strategies
   - Integrate with your monitoring systems

## Troubleshooting and Debugging

If you encounter issues with the error handling system, particularly if errors aren't triggering the recovery flow, you can use the following troubleshooting tools and techniques:

### 1. Using the Debugging Utility

The system includes a debugging utility to help diagnose error handling issues:

```bash
# Test the error handling integration
./scripts/debug_error_flow.py --action test

# Inject a specific error type to test recovery
./scripts/debug_error_flow.py --action inject --error-type terraform_error

# Trace the complete error flow for a specific error type
./scripts/debug_error_flow.py --action trace --error-type api_error
```

### 2. Common Integration Points to Check

If errors aren't triggering the recovery flow, check these integration points:

1. **Error Handler Initialization**
   - Ensure `self.error_handler = ErrorLoopHandler()` is properly initialized in both `InfraAgent` and `AgenticWorkflow` classes
   - Check that the Gemini API key is properly set if you need AI-powered analysis

2. **Error Flow Connection**
   - Verify that `execute_with_error_handling` properly captures errors and passes them to `handle_error_flow`
   - Ensure `handle_error_flow` correctly calls `error_handler.handle_error` with the right parameters

3. **Error Reporting**
   - Make sure error reports are being generated and added to the results
   - Check that recovery attempts are being recorded in the history

### 3. Debugging with Verbose Logging

You can enable verbose logging to trace the error handling flow:

```bash
# Run with verbose error reporting
./scripts/run_agentic_workflow.sh --repo-path ./my-app --action analyze --error-mode verbose

# Set DEBUG logging level
export LOG_LEVEL=DEBUG
```

In the logs, look for:
- "Starting error handling flow" messages
- "Calling error_handler.handle_error" messages
- "Recovery success" or "Recovery failed" messages

### 4. Troubleshooting Recovery Strategies

If a specific error type isn't being recovered properly:

1. Check if a recovery strategy is registered for that error type in `_register_default_strategies`
2. Verify the error classification in `_classify_error` is correctly identifying the error type
3. Ensure the recovery strategy implementation in `_handle_X_error` methods is working correctly

### 5. Using the Test Scripts

The project includes test scripts to validate error handling:

```bash
# Test error flow demo with various error types
python examples/error_flow_demo.py --error-type terraform

# Test error recovery integration
python examples/test_error_recovery.py
```

These tests can help identify if there are disconnections between the error detection and recovery mechanisms.

## Conclusion

Inframate's error handling system with its secondary flow provides robust recovery from common errors, making the infrastructure management process more reliable and resilient. The AI-powered analysis helps identify and fix complex issues that might otherwise require manual intervention.

By using this system, you can build more autonomous and self-healing infrastructure management workflows that handle errors gracefully and intelligently. 