#!/usr/bin/env python3
"""Script to visualize Terraform infrastructure as a diagram"""
import os
import sys
import subprocess
import json
import pydot
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

def run_terraform_graph(tf_dir):
    """Run terraform graph to get the DOT representation of the infrastructure"""
    try:
        # Initialize terraform (no providers will be downloaded)
        subprocess.run(["terraform", "init", "-backend=false", "-input=false"], 
                      cwd=tf_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Generate graph
        result = subprocess.run(["terraform", "graph"], 
                               cwd=tf_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        print(f"Error running terraform graph: {e}")
        print(f"Stderr: {e.stderr.decode('utf-8')}")
        return None

def enhance_graph(dot_data, output_file):
    """Enhance the terraform graph with better styling and layout"""
    graphs = pydot.graph_from_dot_data(dot_data)
    if not graphs:
        print("Error: Could not parse DOT data")
        return False
    
    main_graph = graphs[0]
    
    # Set graph attributes for better appearance
    main_graph.set_bgcolor('"#ffffff00"')  # Transparent background
    main_graph.set_rankdir('"LR"')         # Left to right layout
    main_graph.set_concentrate('true')      # Concentrate edges
    main_graph.set_fontname('"Arial"')
    main_graph.set_splines('ortho')         # Orthogonal connectors
    
    # Customize nodes based on type
    for node in main_graph.get_nodes():
        node_name = node.get_name().strip('"')
        
        # Default attributes
        node.set_fontname('"Arial"')
        node.set_fontsize('11')
        node.set_style('"filled"')
        
        # Customize by resource type
        if node_name.startswith('aws_s3_bucket.'):
            node.set_fillcolor('"#FF9900"')  # AWS orange
            node.set_shape('"cylinder"')
            node.set_label(f'"S3 Bucket\\n{node_name.split(".")[-1]}"')
        elif node_name.startswith('aws_lambda_function.'):
            node.set_fillcolor('"#6B48FF"')  # Lambda purple
            node.set_shape('"component"')
            node.set_label(f'"Lambda\\n{node_name.split(".")[-1]}"')
        elif node_name.startswith('aws_dynamodb_table.'):
            node.set_fillcolor('"#4053D6"')  # DynamoDB blue
            node.set_shape('"cylinder"')
            node.set_label(f'"DynamoDB\\n{node_name.split(".")[-1]}"')
        elif node_name.startswith('aws_ec2_instance.') or node_name.startswith('aws_instance.'):
            node.set_fillcolor('"#FF4F8B"')  # EC2 red
            node.set_shape('"box"')
            node.set_label(f'"EC2\\n{node_name.split(".")[-1]}"')
        elif node_name.startswith('aws_vpc.'):
            node.set_fillcolor('"#1A73E8"')  # VPC blue
            node.set_shape('"cloud"')
            node.set_label(f'"VPC\\n{node_name.split(".")[-1]}"')
        elif node_name.startswith('aws_subnet.'):
            node.set_fillcolor('"#7986CB"')  # Subnet light blue
            node.set_shape('"cloud"')
            node.set_label(f'"Subnet\\n{node_name.split(".")[-1]}"')
        elif node_name.startswith('aws_rds_') or node_name.startswith('aws_db_'):
            node.set_fillcolor('"#2E7D32"')  # RDS green
            node.set_shape('"database"')
            node.set_label(f'"RDS\\n{node_name.split(".")[-1]}"')
        elif node_name.startswith('var.'):
            node.set_fillcolor('"#EEEEEE"')  # Light gray for variables
            node.set_shape('"ellipse"')
            node.set_label(f'"Variable\\n{node_name.split(".")[-1]}"')
        elif 'module.' in node_name:
            node.set_fillcolor('"#FDD835"')  # Yellow for modules
            node.set_shape('"folder"')
            node.set_style('"filled,dashed"')
            module_name = node_name.split(".")[-2] if len(node_name.split(".")) > 2 else node_name.split(".")[-1]
            node.set_label(f'"Module\\n{module_name}"')
        else:
            node.set_fillcolor('"#78909C"')  # Default gray
            node.set_shape('"box"')
    
    # Customize edges
    for edge in main_graph.get_edges():
        edge.set_color('"#666666"')
        edge.set_penwidth('1.5')
    
    # Save the enhanced graph
    main_graph.write_png(output_file)
    main_graph.write_svg(output_file.replace(".png", ".svg"))
    
    return True

def extract_resources(tf_dir):
    """Extract AWS resources from terraform files"""
    resource_types = {}
    
    # Find all .tf files
    for root, _, files in os.walk(tf_dir):
        for file in files:
            if file.endswith('.tf'):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    try:
                        content = f.read()
                        
                        # Simple parsing for resource blocks
                        lines = content.split('\n')
                        in_resource_block = False
                        current_resource_type = None
                        
                        for line in lines:
                            line = line.strip()
                            
                            # Look for resource declarations
                            if line.startswith('resource '):
                                parts = line.split('"')
                                if len(parts) >= 3:
                                    resource_type = parts[1]
                                    if resource_type in resource_types:
                                        resource_types[resource_type] += 1
                                    else:
                                        resource_types[resource_type] = 1
                    except Exception as e:
                        print(f"Error parsing file {path}: {e}")
    
    return resource_types

def create_resource_summary(resources, output_file):
    """Create a simple bar chart of resource counts"""
    if not resources:
        return False
    
    # Sort resources by count
    sorted_resources = sorted(resources.items(), key=lambda x: x[1], reverse=True)
    labels = [r[0] for r in sorted_resources]
    counts = [r[1] for r in sorted_resources]
    
    # Limit to top 15 resources for readability
    if len(labels) > 15:
        labels = labels[:15]
        counts = counts[:15]
    
    # Create color gradient
    cmap = LinearSegmentedColormap.from_list("aws_colors", ["#FF9900", "#232F3E"])
    colors = cmap(plt.Normalize()(range(len(labels))))
    
    # Create the bar chart
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, counts, color=colors)
    plt.xlabel('Resource Type')
    plt.ylabel('Count')
    plt.title('AWS Resources Used')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Add count labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom')
    
    plt.savefig(output_file)
    
    return True

def main(tf_dir, output_dir):
    """Main function to create infrastructure visualization"""
    print(f"Visualizing Terraform infrastructure in {tf_dir}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get terraform graph DOT data
    dot_data = run_terraform_graph(tf_dir)
    if not dot_data:
        print("Failed to generate terraform graph")
        return False
    
    # Save raw DOT file
    dot_file = os.path.join(output_dir, "terraform-graph.dot")
    with open(dot_file, 'w') as f:
        f.write(dot_data)
    print(f"Raw graph saved to {dot_file}")
    
    # Create enhanced visualization
    output_file = os.path.join(output_dir, "infrastructure-diagram.png")
    if enhance_graph(dot_data, output_file):
        print(f"Enhanced visualization saved to {output_file}")
    else:
        print("Failed to create enhanced visualization")
    
    # Extract resources and create summary chart
    resources = extract_resources(tf_dir)
    if resources:
        print(f"Found {sum(resources.values())} resources of {len(resources)} types")
        resource_chart = os.path.join(output_dir, "resource-summary.png")
        if create_resource_summary(resources, resource_chart):
            print(f"Resource summary chart saved to {resource_chart}")
        
        # Create resource summary markdown
        summary_file = os.path.join(output_dir, "resource-summary.md")
        with open(summary_file, 'w') as f:
            f.write("# Infrastructure Resource Summary\n\n")
            f.write("## Resource Counts\n\n")
            f.write("| Resource Type | Count |\n")
            f.write("|--------------|-------|\n")
            
            # Sort resources by count
            sorted_resources = sorted(resources.items(), key=lambda x: x[1], reverse=True)
            for resource_type, count in sorted_resources:
                f.write(f"| {resource_type} | {count} |\n")
        
        print(f"Resource summary markdown saved to {summary_file}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python tf_visualizer.py <terraform_directory> <output_directory>")
        sys.exit(1)
    
    tf_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    if not os.path.isdir(tf_dir):
        print(f"Error: {tf_dir} is not a directory")
        sys.exit(1)
    
    success = main(tf_dir, output_dir)
    sys.exit(0 if success else 1) 