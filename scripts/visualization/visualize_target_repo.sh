#!/bin/bash
# Script to clone and visualize Terraform infrastructure in a target repository

set -e

# Check for required arguments
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <repository_url> [branch_name] [output_directory]"
  echo "Example: $0 https://github.com/example/terraform-project main ./output"
  exit 1
fi

# Set variables
REPO_URL="$1"
BRANCH_NAME="${2:-main}"  # Default to 'main' if not provided
OUTPUT_DIR="${3:-./visualization_output}"  # Default output directory

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Cleanup on exit
cleanup() {
  echo "Cleaning up temporary directory..."
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Clone repository
echo "Cloning repository $REPO_URL branch $BRANCH_NAME..."
git clone --depth 1 --branch "$BRANCH_NAME" "$REPO_URL" "$TEMP_DIR/repo"

# Check if clone was successful
if [ ! -d "$TEMP_DIR/repo" ]; then
  echo "Failed to clone repository."
  exit 1
fi

# Find Terraform files
echo "Looking for Terraform files..."
TF_FILES=$(find "$TEMP_DIR/repo" -name "*.tf" | wc -l)

if [ "$TF_FILES" -eq 0 ]; then
  echo "No Terraform files found in the repository."
  exit 1
fi

echo "Found $TF_FILES Terraform files."

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run visualization
echo "Generating infrastructure visualization..."
"$SCRIPT_DIR/generate_visualization.sh" "$TEMP_DIR/repo" "$OUTPUT_DIR"

echo "Visualization complete. Results are in $OUTPUT_DIR"
echo "Open $OUTPUT_DIR/index.md for a summary of all visualizations." 