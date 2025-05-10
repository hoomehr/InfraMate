#!/bin/bash

# Run Agentic Workflow with Error Handling
# This script makes it easy to run the Inframate agentic workflow with AI-powered error handling

# Default values
REPO_PATH=""
ACTION="analyze"
AUTONOMOUS=false
OUTPUT=""
GEMINI_API_KEY=${GEMINI_API_KEY:-""}
ERROR_MODE="auto"  # Options: auto, verbose, silent

# Display help message
function show_help {
  echo "Usage: $0 --repo-path PATH [--action ACTION] [--autonomous] [--output FILE] [--gemini-key KEY] [--error-mode MODE]"
  echo ""
  echo "Options:"
  echo "  --repo-path PATH       Path to the repository to analyze (required)"
  echo "  --action ACTION        Action to perform: analyze, optimize, secure, visualize, auto (default: analyze)"
  echo "  --autonomous           Run in autonomous mode (default: false)"
  echo "  --output FILE          Output file for results (default: stdout)"
  echo "  --gemini-key KEY       Gemini API key (default: GEMINI_API_KEY environment variable)"
  echo "  --error-mode MODE      Error handling mode: auto, verbose, silent (default: auto)"
  echo "  --help                 Show this help message"
  echo ""
  echo "Examples:"
  echo "  $0 --repo-path ./my-app --action analyze"
  echo "  $0 --repo-path ./my-app --action auto --autonomous --output results.json"
  echo ""
  exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --help)
      show_help
      ;;
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
    --error-mode)
      ERROR_MODE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      ;;
  esac
done

# Validate required arguments
if [ -z "$REPO_PATH" ]; then
  echo "Error: --repo-path is required"
  show_help
fi

# Validate action
valid_actions=("analyze" "optimize" "secure" "visualize" "auto")
if [[ ! " ${valid_actions[*]} " =~ " ${ACTION} " ]]; then
  echo "Error: Invalid action: $ACTION"
  show_help
fi

# Validate error mode
valid_modes=("auto" "verbose" "silent")
if [[ ! " ${valid_modes[*]} " =~ " ${ERROR_MODE} " ]]; then
  echo "Error: Invalid error mode: $ERROR_MODE"
  show_help
fi

# Set up environment
if [ -n "$GEMINI_API_KEY" ]; then
  export GEMINI_API_KEY="$GEMINI_API_KEY"
fi

# Print execution information
echo "├─ Inframate Agentic Workflow ─┤"
echo "│ Repository:   $(realpath $REPO_PATH)"
echo "│ Action:       $ACTION"
echo "│ Autonomous:   $AUTONOMOUS"
echo "│ Error Mode:   $ERROR_MODE"
echo "│ Output:       ${OUTPUT:-stdout}"
echo "│ Gemini API:   ${GEMINI_API_KEY:+Configured}${GEMINI_API_KEY:-Not Configured}"
echo "└─────────────────────────────┘"

# Prepare command arguments
CMD_ARGS=""
CMD_ARGS="$CMD_ARGS --repo-path \"$(realpath $REPO_PATH)\""
CMD_ARGS="$CMD_ARGS --action $ACTION"

if [ "$AUTONOMOUS" = true ]; then
  CMD_ARGS="$CMD_ARGS --autonomous"
fi

if [ -n "$OUTPUT" ]; then
  CMD_ARGS="$CMD_ARGS --output \"$OUTPUT\""
fi

# Set the Python script based on error mode
if [ "$ERROR_MODE" = "auto" ]; then
  # Use the agentic error workflow with full error handling
  SCRIPT="scripts/agentic_error_workflow.py"
elif [ "$ERROR_MODE" = "verbose" ]; then
  # Use the agentic error workflow with verbose logging
  SCRIPT="scripts/agentic_error_workflow.py"
  export LOG_LEVEL=DEBUG
elif [ "$ERROR_MODE" = "silent" ]; then
  # Use the basic workflow with minimal error handling
  SCRIPT="scripts/agentic_workflow.py"
fi

# Run the workflow
echo "Starting workflow execution..."
eval "python $SCRIPT $CMD_ARGS"
EXIT_CODE=$?

# Process the exit code
if [ $EXIT_CODE -eq 0 ]; then
  echo "Workflow completed successfully."
else
  echo "Workflow execution failed with exit code $EXIT_CODE."
  
  # Show error report if available and output is specified
  if [ -n "$OUTPUT" ] && [ -f "$OUTPUT" ]; then
    if [ "$ERROR_MODE" != "silent" ]; then
      echo ""
      echo "Error Report:"
      cat "$OUTPUT" | grep -A20 "error_report"
      
      # Show AI solution if available
      echo ""
      echo "AI Solution:"
      cat "$OUTPUT" | grep -A10 "ai_solution"
    fi
  fi
fi

# Create visualization if output is specified
if [ -n "$OUTPUT" ] && [ -f "$OUTPUT" ]; then
  if [ "$ACTION" = "visualize" ] || [ "$ACTION" = "auto" ]; then
    REPORT_DIR="$(dirname $OUTPUT)/reports"
    mkdir -p "$REPORT_DIR"
    echo "Creating HTML report in $REPORT_DIR/inframate_report.html"
    python scripts/visualization/generate_report.py --input "$OUTPUT" --output "$REPORT_DIR/inframate_report.html"
  fi
fi

exit $EXIT_CODE 