#!/usr/bin/env python3
"""
Terraform Operations

This script helps users run terraform operations after Inframate has generated
the infrastructure code. The operations are run as separate, optional steps.

Usage:
  python terraform_operations.py --terraform-dir <path> --operation <plan|apply|destroy>
"""

import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Terraform Operations')
    parser.add_argument('--terraform-dir', required=True, 
                        help='Path to the terraform directory')
    parser.add_argument('--operation', choices=['plan', 'apply', 'destroy', 'output'], 
                        required=True, help='Terraform operation to perform')
    parser.add_argument('--out-file', default='tfplan',
                        help='Output file for plan operation (default: tfplan)')
    parser.add_argument('--var-file', default='terraform.tfvars',
                        help='Variables file for terraform (default: terraform.tfvars)')
    parser.add_argument('--auto-approve', action='store_true',
                        help='Automatically approve apply or destroy operations')
    return parser.parse_args()

def run_terraform_command(tf_dir: str, operation: str, args) -> bool:
    """
    Run terraform command in the specified directory
    
    Args:
        tf_dir: Path to terraform directory
        operation: Terraform operation (plan, apply, destroy, output)
        args: Command line arguments
        
    Returns:
        True if the command succeeded, False otherwise
    """
    # Validate terraform directory
    tf_dir_path = Path(tf_dir)
    if not tf_dir_path.exists():
        logger.error(f"Terraform directory not found: {tf_dir}")
        return False
    
    if not (tf_dir_path / "main.tf").exists():
        logger.error(f"main.tf not found in {tf_dir}. This may not be a valid terraform directory.")
        return False
    
    # Determine command based on operation
    if operation == "plan":
        cmd = ["terraform", "-chdir=" + tf_dir, "plan"]
        # Add output file if specified
        if args.out_file:
            cmd.extend(["-out=" + args.out_file])
        # Add var file if it exists
        var_file_path = tf_dir_path / args.var_file
        if var_file_path.exists():
            cmd.extend(["-var-file=" + args.var_file])
    
    elif operation == "apply":
        cmd = ["terraform", "-chdir=" + tf_dir, "apply"]
        # Check if plan file exists
        plan_file_path = tf_dir_path / args.out_file
        if plan_file_path.exists():
            cmd.append(args.out_file)
        elif args.auto_approve:
            cmd.append("-auto-approve")
            # Add var file if it exists
            var_file_path = tf_dir_path / args.var_file
            if var_file_path.exists():
                cmd.extend(["-var-file=" + args.var_file])
    
    elif operation == "destroy":
        cmd = ["terraform", "-chdir=" + tf_dir, "destroy"]
        if args.auto_approve:
            cmd.append("-auto-approve")
        # Add var file if it exists
        var_file_path = tf_dir_path / args.var_file
        if var_file_path.exists():
            cmd.extend(["-var-file=" + args.var_file])
    
    elif operation == "output":
        cmd = ["terraform", "-chdir=" + tf_dir, "output"]
    
    else:
        logger.error(f"Unknown operation: {operation}")
        return False
    
    # Run terraform init if .terraform directory doesn't exist
    if not (tf_dir_path / ".terraform").exists():
        logger.info("Terraform not initialized. Running 'terraform init' first...")
        init_cmd = ["terraform", "-chdir=" + tf_dir, "init"]
        try:
            subprocess.run(init_cmd, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Terraform init failed: {e}")
            return False
    
    # Run the terraform command
    try:
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        logger.info(f"Terraform {operation} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Terraform {operation} failed: {e}")
        return False

def main():
    """Main entry point"""
    args = parse_args()
    
    # Run the terraform operation
    success = run_terraform_command(args.terraform_dir, args.operation, args)
    
    # Display next steps based on the operation
    if success:
        if args.operation == "plan":
            print("\n✅ Terraform plan completed. Next steps:")
            print(f"  - Review the plan output")
            print(f"  - Apply the plan: python {sys.argv[0]} --terraform-dir {args.terraform_dir} --operation apply\n")
        
        elif args.operation == "apply":
            print("\n✅ Terraform apply completed. Your infrastructure has been deployed!")
            print(f"  - View outputs: python {sys.argv[0]} --terraform-dir {args.terraform_dir} --operation output")
            print(f"  - To destroy when done: python {sys.argv[0]} --terraform-dir {args.terraform_dir} --operation destroy\n")
        
        elif args.operation == "destroy":
            print("\n✅ Terraform destroy completed. Your infrastructure has been removed.")
        
        elif args.operation == "output":
            print("\n✅ Terraform output displayed.")
    
    # Return appropriate exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 