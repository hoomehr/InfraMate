#!/usr/bin/env python3
"""
Inframate CLI - Command line interface for Inframate
"""
import os
import sys
import click
import json
from pathlib import Path
from dotenv import load_dotenv

from inframate.analyzers.repository import analyze_repository
from inframate.providers.aws import deploy_to_aws

load_dotenv()

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Inframate: AI-powered infrastructure deployment assistant."""
    pass

@cli.command("analyze")
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("-v", "--verbose", is_flag=True, help="Show detailed output")
@click.option("-o", "--output", help="Output file for Terraform template")
def analyze(repo_path, verbose, output):
    """Analyze a repository for deployment."""
    try:
        full_path = os.path.abspath(repo_path)
        click.echo(f"Analyzing repository at {full_path}...")
        
        analysis = analyze_repository(full_path, verbose)
        
        click.echo("\n📊 Analysis Results:")
        
        # Print languages
        click.echo("\nDetected Languages:")
        for lang in analysis.get("detected_languages", []):
            click.echo(f"- {lang}")
        
        # Print services
        click.echo("\nRecommended AWS Services:")
        for service in analysis.get("detected_services", []):
            click.echo(f"- {service}")
        
        # Print recommendations
        click.echo("\n🚀 Deployment Recommendations:")
        for recommendation in analysis.get("recommendations", []):
            click.echo(f"- {recommendation}")
        
        # Handle Terraform template
        if "terraform_template" in analysis and analysis["terraform_template"]:
            click.echo("\n🏗️ Terraform Template Generated:")
            
            if output:
                # Save to file
                with open(output, 'w') as f:
                    f.write(analysis["terraform_template"])
                click.echo(f"Terraform template saved to {output}")
            else:
                # Print to console
                click.echo("\n```terraform")
                click.echo(analysis["terraform_template"])
                click.echo("```")
        
        # Print cost estimate
        if "estimatedCost" in analysis:
            click.echo(f"\n💰 Estimated Monthly Cost: {analysis['estimatedCost']}")
        
        # Print warnings
        if analysis.get("warnings"):
            click.echo("\n⚠️ Warnings:")
            for warning in analysis["warnings"]:
                click.echo(f"- {warning}")
            
    except Exception as e:
        click.echo(f"Error during analysis: {str(e)}", err=True)
        sys.exit(1)

@cli.command("deploy")
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("-p", "--profile", help="AWS profile to use")
@click.option("-r", "--region", help="AWS region to deploy to")
@click.option("-v", "--verbose", is_flag=True, help="Show detailed output")
@click.option("--terraform", is_flag=True, help="Generate Terraform template instead of deploying directly")
@click.option("-o", "--output", help="Output file for Terraform template when using --terraform")
def deploy(repo_path, profile, region, verbose, terraform, output):
    """Deploy a repository to AWS."""
    try:
        full_path = os.path.abspath(repo_path)
        click.echo(f"Analyzing repository at {full_path}...")
        
        analysis = analyze_repository(full_path, verbose)
        
        if terraform:
            click.echo("\n🏗️ Generating Terraform Template:")
            
            if "terraform_template" in analysis and analysis["terraform_template"]:
                if output:
                    # Save to file
                    with open(output, 'w') as f:
                        f.write(analysis["terraform_template"])
                    click.echo(f"Terraform template saved to {output}")
                else:
                    # Print to console
                    click.echo("\n```terraform")
                    click.echo(analysis["terraform_template"])
                    click.echo("```")
                
                click.echo("\nTo deploy this template:")
                click.echo("1. Initialize Terraform: terraform init")
                click.echo("2. Review the plan: terraform plan")
                click.echo("3. Apply the changes: terraform apply")
            else:
                click.echo("No Terraform template was generated during analysis.")
        else:
            click.echo("\n🚀 Deploying to AWS...")
            result = deploy_to_aws(
                full_path, 
                analysis, 
                profile=profile,
                region=region,
                verbose=verbose
            )
            
            click.echo("\n✅ Deployment successful!")
            click.echo(json.dumps(result, indent=2))
            
    except Exception as e:
        click.echo(f"Error during deployment: {str(e)}", err=True)
        sys.exit(1)

def main():
    """Main entry point for the CLI."""
    cli()

if __name__ == "__main__":
    main() 