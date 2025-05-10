# Inframate Agentic Infrastructure Management System

## Overview

Inframate is an AI-powered infrastructure deployment assistant that analyzes repositories and generates Terraform templates using the Google Gemini API. This document focuses on the agentic workflow and error handling aspects of Inframate, explaining how they interoperate to create a robust, intelligent infrastructure management system.

## Core Components

### 1. Flow Architecture

Inframate's architecture is structured around several key flows:

![Inframate Architecture](./docs/images/architecture.png)

#### Base Flow (`inframate_flow.py`)
- Reads `inframate.md` files to understand application requirements
- Calls Gemini API to analyze requirements and generate recommendations
- Produces Terraform files based on recommendations
- Includes fallback mechanisms when AI is unavailable

#### Agentic Flow (`scripts/agentic_workflow.py`)
- More advanced flow with autonomous decision-making capabilities
- Analyzes, optimizes, secures, and visualizes infrastructure
- Designed to run as part of GitHub Actions or manually
- Can make intelligent decisions based on context

#### Error-Handling Flow (`scripts/agentic_error_workflow.py`)
- Enhanced version of agentic workflow with robust error handling
- Integrates with Gemini API for AI-powered error analysis and resolution
- Prevents infinite error loops through agent supervision
- Provides comprehensive error reporting and visualizations

### 2. Agent System

The agent system in Inframate provides intelligence and autonomy:

#### AI Analyzer (`inframate/agents/ai_analyzer.py`)
- Calls Gemini API to analyze repository structure
- Generates infrastructure recommendations
- Creates Terraform templates
- Handles fallback analysis when AI is unavailable

#### Agent Supervisor (`inframate/utils/error_handler.py`)
- Monitors and manages error loops
- Implements exponential backoff for retries
- Maintains error history for analysis
- Coordinates with AI for error analysis

### 3. Error Handling System

The error handling system is designed to be robust and intelligent:

#### Error Loop Handler (`inframate/utils/error_handler.py`)
- Central error management system
- Integrated with Gemini API for error analysis
- Implements recovery strategies for common errors
- Generates comprehensive error reports

#### Error Context
- Tracks error types, messages, and severity levels
- Manages retry counts and strategies
- Stores AI-generated solutions
- Preserves context data for better error analysis

## Workflow Execution

### 1. Agentic Workflow

The agentic workflow can be executed in several ways:

#### GitHub Actions
```yaml
name: Inframate Agentic Workflow
on:
  push:
    paths:
      - 'inframate.md'
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

#### Command Line
```bash
./scripts/run_agentic_workflow.sh --repo-path /path/to/repo --action analyze
```

#### Python API
```python
from scripts.agentic_error_workflow import AgenticWorkflow

workflow = AgenticWorkflow(
    repo_path="/path/to/repo",
    action="analyze",
    autonomous=True
)
results = workflow.execute()
```

### 2. Workflow Actions

The agentic workflow supports several actions:

#### analyze
- Examines repository structure and existing infrastructure
- Identifies programming languages, frameworks, and databases
- Analyzes existing Terraform files if present
- Generates comprehensive infrastructure recommendations

#### optimize
- Identifies optimization opportunities in existing infrastructure
- Generates cost-saving recommendations
- Suggests performance improvements
- Creates a comprehensive optimization report

#### secure
- Performs security analysis using tools like tfsec
- Identifies security vulnerabilities
- Generates remediation recommendations
- Produces a security posture report

#### visualize
- Creates visual representations of infrastructure
- Generates cost breakdowns and charts
- Produces dependency diagrams
- Creates comprehensive visualization reports

#### auto
- Runs all actions in sequence (analyze, optimize, secure, visualize)
- Makes autonomous decisions based on findings
- Implements changes through pull requests
- Provides comprehensive reporting

## Error Handling System

### 1. Error Types and Recovery Strategies

Inframate's error handler manages several types of errors:

#### API Errors
- Rate limiting issues
- Authentication failures
- Service unavailability
- Network connectivity problems

#### Terraform Errors
- State lock conflicts
- Resource conflicts
- Syntax errors
- Provider configuration issues

#### Execution Errors
- Permission issues
- Configuration problems
- Environment inconsistencies
- Dependency conflicts

### 2. AI-Powered Error Analysis

When errors occur, Inframate uses Gemini API to:

1. Analyze the root cause of the error
2. Generate step-by-step solutions
3. Provide preventive measures for the future
4. Create a comprehensive error report

### 3. Error Loop Prevention

To prevent infinite error loops, Inframate implements:

1. **Maximum Retry Limits**: Each error type has a maximum number of retries
2. **Exponential Backoff**: Increasing wait times between retries
3. **Error Context Tracking**: Monitoring error patterns to detect loops
4. **Severity-Based Handling**: Different strategies based on error severity

## Integration with GitHub Actions

Inframate's agentic workflow integrates with GitHub Actions to:

1. **Analyze Infrastructure**: Examine repositories and generate recommendations
2. **Create Pull Requests**: Implement recommended changes
3. **Generate Issues**: For errors with AI-powered solutions
4. **Produce Artifacts**: Including visualizations and reports

## Template System

The template system provides modular infrastructure components:

### Template Manager (`inframate/utils/template_manager.py`)
- Manages and combines Terraform templates
- Resolves dependencies between templates
- Fixes common issues in generated templates
- Maps services to appropriate templates

### Template Categories

Templates are organized by service type:

1. **Base Templates**: vpc.tf, variables.tf
2. **Compute Templates**: nodejs_lambda.tf, ec2.tf, ecs.tf, eks.tf
3. **Networking Templates**: alb.tf, cloudfront.tf, api_gateway.tf
4. **Database Templates**: database.tf, dynamodb.tf
5. **Storage Templates**: webapp.tf (S3 static site)

## Custom Error Handling

You can extend the error handling system with custom strategies:

```python
from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity

handler = ErrorLoopHandler()

# Define a custom strategy
def handle_custom_error(context):
    if "specific_condition" in context.message:
        # Custom recovery logic
        return "retry"
    return None

# Register the strategy
handler.supervisor.register_recovery_strategy(
    "custom_error_type", 
    handle_custom_error
)
```

## Usage Examples

### 1. Basic Repository Analysis

```bash
# Set Gemini API key
export GEMINI_API_KEY=your_api_key_here

# Run analysis on a repository
./scripts/run_agentic_workflow.sh --repo-path /path/to/repo --action analyze
```

### 2. Full Autonomous Mode

```bash
# Run in fully autonomous mode
./scripts/run_agentic_workflow.sh --repo-path /path/to/repo --action auto --autonomous
```

### 3. Error Handling Demonstration

```bash
# Run the error handling demonstration
python tests/demo_error_handling.py
```

## Error Report Format

Error reports are structured as follows:

```json
{
  "errors": [
    {
      "type": "terraform_error",
      "message": "Error creating resource",
      "severity": "high",
      "retry_count": 2,
      "ai_solution": {
        "root_cause": "Resource already exists",
        "solution": "Step-by-step solution...",
        "prevention": "Prevention tips..."
      }
    }
  ],
  "total_error_count": 1,
  "recovered_count": 1,
  "unrecovered_count": 0
}
```

## Project Structure

```
inframate/
├── inframate/                  # Core module
│   ├── agents/                 # AI agents
│   │   └── ai_analyzer.py      # Gemini API integration
│   ├── analyzers/              # Repository analyzers
│   │   ├── repository.py       # Repo structure analysis
│   │   ├── infrastructure.py   # Infrastructure analysis
│   │   └── framework.py        # Framework detection
│   ├── providers/              # Cloud providers
│   │   └── aws.py              # AWS provider
│   └── utils/                  # Utilities
│       ├── error_handler.py    # Error handling system
│       ├── template_manager.py # Template management
│       └── rag.py              # RAG capabilities
├── scripts/                    # Scripts
│   ├── agentic_workflow.py     # Main agentic workflow
│   ├── agentic_error_workflow.py # Error-handling workflow
│   ├── run_agentic_workflow.sh # Convenience wrapper
│   ├── security/               # Security tools
│   └── visualization/          # Visualization tools
├── templates/                  # Terraform templates
│   └── aws/terraform/          # AWS-specific templates
└── tests/                      # Tests
    ├── demo_error_handling.py  # Error handling demo
    └── test_error_handler.py   # Error handler tests
```

## Workflow Diagrams

### Basic Workflow

```
┌─────────────┐    ┌────────────────┐    ┌────────────────┐    ┌───────────────┐
│ Parse Repo  │───►│ AI Analysis    │───►│ Generate       │───►│ Output        │
│ Structure   │    │ (Gemini API)   │    │ Terraform      │    │ Results       │
└─────────────┘    └────────────────┘    └────────────────┘    └───────────────┘
```

### Agentic Workflow with Error Handling

```
┌─────────────┐    ┌───────────────┐    ┌───────────────┐    ┌────────────────┐
│ Execute     │───►│ Try Action    │───►│ Success?      │───►│ Return Results │
│ Workflow    │    │ (with context)│    │   │           │    │                │
└─────────────┘    └───────────────┘    └───┼───────────┘    └────────────────┘
                                            │ Error
                                            ▼
                   ┌───────────────┐    ┌───────────────┐    ┌────────────────┐
                   │ Return Error  │◄───│ AI Analysis   │◄───│ Error Handler  │
                   │ Report        │    │ (Gemini API)  │    │ (with retries) │
                   └───────────────┘    └───────────────┘    └────────────────┘
```

## Future Development

1. **Enhanced Agent Intelligence**
   - Adding reinforcement learning for better decision-making
   - Implementing more advanced RAG capabilities
   - Expanding error prediction capabilities

2. **Multi-Cloud Support**
   - Azure integration
   - GCP integration
   - Multi-cloud optimization strategies

3. **Advanced Visualization**
   - Interactive infrastructure diagrams
   - Cost forecasting capabilities
   - Real-time monitoring integration

4. **Expanded Error Handling**
   - More error types and recovery strategies
   - Integration with third-party error monitoring
   - Predictive error detection

## Getting Help

If you encounter issues or need assistance:

1. Check the error reports for AI-generated solutions
2. Review the examples in `examples/error_handling_example.md`
3. Run the demo script `tests/demo_error_handling.py`
4. File an issue on GitHub with the error report 