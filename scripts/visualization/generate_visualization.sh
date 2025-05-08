#!/bin/bash
# Script to generate infrastructure visualizations from Terraform files

set -e

# Check for required dependencies
check_dependencies() {
  echo "Checking dependencies..."
  
  # Check for terraform
  if ! command -v terraform &> /dev/null; then
    echo "Error: terraform is not installed. Please install it from https://www.terraform.io/downloads.html"
    exit 1
  fi
  
  # Check for graphviz
  if ! command -v dot &> /dev/null; then
    echo "Error: graphviz is not installed. Please install it with your package manager."
    echo "For example: sudo apt-get install graphviz or brew install graphviz"
    exit 1
  fi
  
  # Check for Python dependencies
  python3 -c "import pydot, networkx, matplotlib" 2>/dev/null || {
    echo "Error: Missing Python dependencies. Please install them with:"
    echo "pip install pydot networkx matplotlib"
    exit 1
  }
  
  echo "All dependencies found."
}

# Function to find Terraform directories
find_terraform_dirs() {
  local base_dir="$1"
  find "$base_dir" -name "*.tf" -exec dirname {} \; | sort | uniq
}

# Main function
main() {
  if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <terraform_directory> [output_directory]"
    echo "If output_directory is not specified, it will be created as '<terraform_directory>/visualizations'"
    exit 1
  fi
  
  # Get the absolute path of the terraform directory
  TF_DIR=$(realpath "$1")
  
  # Check if the directory exists
  if [ ! -d "$TF_DIR" ]; then
    echo "Error: Directory $TF_DIR does not exist"
    exit 1
  fi
  
  # Set the output directory
  if [ "$#" -ge 2 ]; then
    OUTPUT_DIR=$(realpath "$2")
  else
    OUTPUT_DIR="$TF_DIR/visualizations"
  fi
  
  # Check dependencies
  check_dependencies
  
  # Get the script directory
  SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
  
  echo "Looking for Terraform files in $TF_DIR..."
  TF_DIRS=$(find_terraform_dirs "$TF_DIR")
  
  if [ -z "$TF_DIRS" ]; then
    echo "No Terraform files found in $TF_DIR"
    exit 1
  fi
  
  echo "Found Terraform directories:"
  echo "$TF_DIRS"
  
  # Create main output directory
  mkdir -p "$OUTPUT_DIR"
  
  # Create index file
  echo "# Infrastructure Visualizations" > "$OUTPUT_DIR/index.md"
  echo "" >> "$OUTPUT_DIR/index.md"
  echo "Generated on $(date)" >> "$OUTPUT_DIR/index.md"
  echo "" >> "$OUTPUT_DIR/index.md"
  echo "## Directories" >> "$OUTPUT_DIR/index.md"
  echo "" >> "$OUTPUT_DIR/index.md"
  
  # Process each directory with Terraform files
  for DIR in $TF_DIRS; do
    DIR_NAME=$(basename "$DIR")
    DIR_OUTPUT="$OUTPUT_DIR/$DIR_NAME"
    
    echo "Processing $DIR..."
    echo "- [$DIR_NAME]($DIR_NAME/)" >> "$OUTPUT_DIR/index.md"
    
    # Run the visualizer
    python3 "$SCRIPT_DIR/tf_visualizer.py" "$DIR" "$DIR_OUTPUT"
  done
  
  echo "Visualization complete. See results in $OUTPUT_DIR"
  echo "Summary available in $OUTPUT_DIR/index.md"
}

# Run the main function
main "$@" 