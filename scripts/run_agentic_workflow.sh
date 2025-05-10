#!/bin/bash

# Run Agentic Workflow with Error Handling
# This script makes it easy to run the Inframate agentic workflow with AI-powered error handling

# Default values
REPO_PATH=""
ACTION="analyze"
AUTONOMOUS=false
OUTPUT=""
GEMINI_API_KEY=${GEMINI_API_KEY:-""}

# Display help message
function show_help {
  echo "Usage: $0 --repo-path PATH [--action ACTION] [--autonomous] [--output FILE] [--gemini-key KEY]"
  echo ""
  echo "Options:"
  echo "  --repo-path PATH       Path to the repository to analyze (required)"
  echo "  --action ACTION        Action to perform: analyze, optimize, secure, visualize, auto (default: analyze)"
  echo "  --autonomous           Run in autonomous mode (default: false)"
  echo "  --output FILE          Output file for results (default: stdout)"
  echo "  --gemini-key KEY       Gemini API key (can also be set via GEMINI_API_KEY env var)"
  echo "  --help                 Display this help message"
  echo ""
  echo "Example:"
  echo "  $0 --repo-path ~/my-project --action analyze --output results.json"
  exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-path)
      REPO_PATH="$2"
      shift 2
      ;;
    --action)
      ACTION="$2"
      shift 2
      ;;
    --autonomous)
      AUTONOMOUS=true
      shift
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    --gemini-key)
      GEMINI_API_KEY="$2"
      shift 2
      ;;
    --help)
      show_help
      ;;
    *)
      echo "Error: Unknown option $1"
      show_help
      ;;
  esac
done

# Check required arguments
if [ -z "$REPO_PATH" ]; then
  echo "Error: --repo-path is required"
  show_help
fi

# Check if action is valid
if [[ ! "$ACTION" =~ ^(analyze|optimize|secure|visualize|auto)$ ]]; then
  echo "Error: Invalid action: $ACTION"
  show_help
fi

# Check for Gemini API key
if [ -z "$GEMINI_API_KEY" ]; then
  echo "Warning: No Gemini API key provided. AI-powered error handling will be limited."
  echo "Set the GEMINI_API_KEY environment variable or use --gemini-key"
fi

# Build the command
CMD="python $(dirname "$0")/agentic_error_workflow.py --repo-path $REPO_PATH --action $ACTION"

# Add autonomous flag if true
if [ "$AUTONOMOUS" = true ]; then
  CMD="$CMD --autonomous"
fi

# Add output file if specified
if [ -n "$OUTPUT" ]; then
  CMD="$CMD --output $OUTPUT"
fi

# Set environment variables and run the command
export GEMINI_API_KEY="$GEMINI_API_KEY"
echo "Running: $CMD"
eval "$CMD"

# Check exit code
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
  echo "Error: Workflow failed with exit code $EXIT_CODE"
  
  # Check if output file exists and has error information
  if [ -n "$OUTPUT" ] && [ -f "$OUTPUT" ]; then
    if grep -q '"success": false' "$OUTPUT"; then
      echo "Error details available in $OUTPUT"
      if grep -q '"ai_solution"' "$OUTPUT"; then
        echo "AI solution available in $OUTPUT"
      fi
    fi
  fi
  
  exit $EXIT_CODE
else
  echo "Workflow completed successfully!"
  exit 0
fi 