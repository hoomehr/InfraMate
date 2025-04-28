"""Main Inframate flow logic"""
import os
import sys
from pathlib import Path
from typing import Dict, Any

from inframate.analyzers.repository import analyze_repository
from inframate.agents.ai_analyzer import analyze_with_ai, fallback_analyze
from inframate.utils.rag import RAGManager

def read_inframate_file(repo_path: str) -> Dict[str, Any]:
    """Read and parse the inframate.md file"""
    inframate_path = Path(repo_path) / "inframate.md"
    if not inframate_path.exists():
        raise FileNotFoundError("inframate.md file not found in repository")
    
    with open(inframate_path, "r") as f:
        content = f.read()
    
    # Basic parsing of markdown content
    sections = content.split("##")
    info = {}
    for section in sections[1:]:  # Skip the first empty section
        lines = section.strip().split("\n")
        title = lines[0].strip()
        content = "\n".join(lines[1:]).strip()
        info[title.lower()] = content
    
    return info

def generate_terraform_files(repo_path: str, analysis: Dict[str, Any], md_data: Dict[str, Any]) -> str:
    """Generate Terraform files in the repository"""
    print("Generating Terraform files...")
    
    # Create terraform directory if it doesn't exist
    tf_dir = os.path.join(repo_path, 'terraform')
    os.makedirs(tf_dir, exist_ok=True)
    
    # Generate main.tf
    terraform_template = ""
    if "terraform_template" in analysis and analysis["terraform_template"]:
        terraform_template = analysis["terraform_template"]
    else:
        print("No Terraform template in analysis, generating basic template...")
        # Use local templates based on language/framework
        terraform_template = generate_terraform_template(md_data, analysis.get("services", []))
    
    # Create main.tf
    with open(os.path.join(tf_dir, 'main.tf'), 'w') as f:
        f.write(terraform_template)
    
    # Create variables.tf
    variables_tf = generate_variables_tf(md_data)
    with open(os.path.join(tf_dir, 'variables.tf'), 'w') as f:
        f.write(variables_tf)
    
    # Create outputs.tf
    outputs_tf = generate_outputs_tf(md_data)
    with open(os.path.join(tf_dir, 'outputs.tf'), 'w') as f:
        f.write(outputs_tf)
    
    # Create terraform.tfvars
    tfvars = generate_tfvars(md_data)
    with open(os.path.join(tf_dir, 'terraform.tfvars'), 'w') as f:
        f.write(tfvars)
    
    # Create README.md
    readme = generate_readme(md_data, analysis)
    with open(os.path.join(tf_dir, 'README.md'), 'w') as f:
        f.write(readme)
    
    print(f"Terraform files created in {tf_dir}")
    return tf_dir

def main(argv=None):
    """Main entry point for Inframate"""
    if argv is None:
        argv = sys.argv
    
    if len(argv) != 2:
        print("Usage: python -m inframate.flow <repository_path>")
        sys.exit(1)
    
    repo_path = argv[1]
    
    try:
        # Read repository information
        repo_info = read_inframate_file(repo_path)
        
        # Analyze repository structure
        repo_analysis = analyze_repository(repo_path)
        repo_info.update(repo_analysis)
        
        # Get AI analysis
        try:
            analysis_result = analyze_with_ai(repo_info)
        except Exception as e:
            print(f"AI analysis failed: {str(e)}")
            print("Falling back to basic analysis...")
            analysis_result = fallback_analyze(repo_info)
        
        # Generate Terraform files
        terraform_dir = generate_terraform_files(repo_path, analysis_result, repo_info)
        
        print("Inframate analysis complete!")
        print(f"Terraform files generated in: {terraform_dir}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 