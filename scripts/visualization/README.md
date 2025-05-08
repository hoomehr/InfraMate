# Terraform Infrastructure Visualization

This directory contains scripts for visualizing AWS infrastructure defined in Terraform files.

## How It Works

The visualization process uses the following approach:

1. **Terraform Graph**: Leverages `terraform graph` command to generate a DOT representation of the infrastructure
2. **Graph Enhancement**: Customizes the graph with better styling, layout, and resource-specific icons/colors
3. **Resource Extraction**: Parses Terraform files to extract and count AWS resource types
4. **Visualization Generation**: Creates both infrastructure diagrams and resource summary charts

## Key Components

- **tf_visualizer.py**: Main script that handles the entire visualization process
  - **run_terraform_graph()**: Executes Terraform commands to get DOT graph
  - **enhance_graph()**: Improves the appearance of the infrastructure diagram
  - **extract_resources()**: Parses Terraform files to identify AWS resources
  - **create_resource_summary()**: Generates charts and tables of resources

## Prerequisites

- Python 3.6+
- Terraform CLI
- GraphViz
- Python packages: pydot, networkx, matplotlib

## Usage

```bash
python tf_visualizer.py <terraform_directory> <output_directory>
```

## Output

- `terraform-graph.dot`: Raw DOT representation of the infrastructure
- `infrastructure-diagram.png`: Visual diagram of infrastructure components
- `infrastructure-diagram.svg`: SVG version of the diagram
- `resource-summary.png`: Bar chart of AWS resource counts
- `resource-summary.md`: Markdown table listing all resources by count 