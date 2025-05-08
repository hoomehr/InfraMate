# Inframate: AI-Powered Infrastructure Deployment Assistant

Inframate is a tool that analyzes code repositories and creates infrastructure deployment recommendations and Terraform templates using AI.

## Overview

Inframate reads an `inframate.md` file containing details about your application, analyzes the repository structure, and generates Terraform files for deploying the infrastructure. It uses the Google Gemini API to generate tailored infrastructure recommendations and Terraform code.

## How It Works

1. **Repository Analysis**: Inframate automatically analyzes your repository to understand:
   - Programming languages used
   - Frameworks and libraries
   - Database requirements
   - Directory structure and dependencies

2. **Inframate Configuration**: You can provide an optional `inframate.md` file in your repository with:
   ```markdown
   # Inframate Configuration

   ## Description
   Your application description

   ## Language
   Detected automatically

   ## Framework
   Detected automatically

   ## Database
   MySQL

   ## Requirements
   - High availability
   - Auto-scaling
   - Cost-effective deployment
   ```

3. **AI-Powered Recommendations**: Using the Google Gemini API, Inframate generates:
   - Recommended AWS services for your application
   - Infrastructure recommendations based on application requirements
   - Complete Terraform templates for deployment
   - Estimated monthly cost breakdown for all resources

4. **Terraform Generation**: Inframate uses a template-based approach to generate Terraform files:
   - Templates are stored in the `templates/aws/terraform/` directory
   - Each template focuses on a specific service type (e.g., `nodejs_lambda.tf`, `vpc.tf`, `ecs.tf`)
   - Templates are combined based on the recommended services
   - The following files are generated:
     - `main.tf`: Primary infrastructure definition
     - `variables.tf`: Variable definitions
     - `outputs.tf`: Output declarations
     - `terraform.tfvars`: Default variable values
     - `README.md`: Documentation including cost estimates and deployment instructions

5. **CI/CD Automation**: Inframate includes a full Terraform CI/CD pipeline:
   - Automated Terraform plan execution
   - Security scanning with tfsec
   - Optional deployment after approval
   - PR comments with results of each step
   - Cost estimation included in the PR

## Using Inframate

### As a GitHub Action

The easiest way to use Inframate is as a GitHub Action:

1. Create a repository that will use Inframate
2. Add an `inframate.md` file (optional)
3. Set up a GitHub Actions workflow to run Inframate:
   ```yaml
   name: Inframate

   on:
     push:
       branches: [ main ]

   jobs:
     analyze:
       runs-on: ubuntu-latest
       steps:
         - name: Checkout repository
           uses: actions/checkout@v4

         - name: Run Inframate
           uses: yourusername/inframate@main
           with:
             gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
             should_deploy: false  # Set to true to deploy the infrastructure
   ```

### Full CI/CD Pipeline

Inframate includes a comprehensive CI/CD pipeline for Terraform:

1. **Analysis**: Generate infrastructure recommendations and Terraform files
2. **Plan**: Runs `terraform plan` and adds the output to the PR
3. **Security Testing**: Scans for security issues with tfsec
4. **Optional Deployment**: Can automatically deploy the infrastructure

To use the CI/CD pipeline, you'll need to set up the following secrets:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `REPO_PAT`: GitHub token with repo permissions
- `TF_API_TOKEN`: Terraform Cloud token (optional)
- `AWS_ACCESS_KEY_ID`: AWS access key (for deployment)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key (for deployment)

When triggered, the workflow:
1. Creates a pull request with the Terraform files
2. Adds cost estimates and infrastructure overview to the PR description
3. Runs Terraform plan and adds the results as a comment
4. Scans for security issues and adds the results as a comment
5. Optionally deploys the infrastructure if `should_deploy` is true

### Local Usage

You can also run Inframate locally:

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your Gemini API key:
   ```bash
   export GEMINI_API_KEY="your_gemini_api_key_here"
   ```
4. Run Inframate:
   ```bash
   python inframate_flow.py /path/to/your/repo
   ```

## Available Templates

Inframate includes a comprehensive set of Terraform templates for AWS services, located in `templates/aws/terraform/`:

### Compute
- **nodejs_lambda.tf**: Serverless applications using Lambda and API Gateway
- **ec2.tf**: Traditional VM deployments with auto-scaling capabilities
- **ecs.tf**: Container orchestration using ECS Fargate
- **eks.tf**: Kubernetes clusters with managed node groups

### Networking
- **vpc.tf**: VPC configuration with public/private subnets and NAT gateways
- **alb.tf**: Application Load Balancer with auto-scaling and monitoring
- **cloudfront.tf**: Content delivery network with S3 origins
- **api_gateway.tf**: RESTful API endpoints with Lambda integration

### Database
- **database.tf**: Relational databases using Amazon RDS
- **dynamodb.tf**: NoSQL database with auto-scaling and streams

### Storage
- **webapp.tf**: Static website hosting with S3 and CloudFront

Each template is designed to work independently or in combination with others, providing a flexible and modular approach to infrastructure definition.

## Example

For a Node.js Express API with MongoDB, Inframate will:
1. Analyze the repository and detect Node.js/Express.js
2. Use the Gemini API to recommend appropriate AWS services
3. Combine the `vpc.tf`, `nodejs_lambda.tf`, `api_gateway.tf`, and `dynamodb.tf` templates
4. Generate a complete Terraform configuration with:
   - VPC with public/private subnets
   - Lambda function for the Express.js API
   - API Gateway with custom domain and monitoring
   - DynamoDB table for NoSQL data storage
   - IAM roles and permissions
   - CloudWatch logging and alarms
   - Estimated monthly cost breakdown for all services

## Template Customization

You can easily customize the templates or add new ones:

1. Create a new `.tf` file in the `templates/aws/terraform/` directory
2. Update the template manager in `inframate/utils/template_manager.py` to include your new template
3. Map the appropriate AWS services to your template in the `service_to_template` dictionary

## Requirements

- Python 3.8+
- [Google Gemini API key](https://ai.google.dev/)
- Terraform (for deployment)

## Installation & Dependencies

Inframate uses a modular dependency structure to minimize installation size and optimize performance:

### Basic Installation
```bash
# Install only core dependencies
pip install -e .
```

### Installing with Optional Components
```bash
# Install with RAG (Retrieval-Augmented Generation) support
pip install -e .[rag]

# Install with web interface support
pip install -e .[web]

# Install with development tools
pip install -e .[dev]

# Install all dependencies
pip install -e .[all]
```

### Dependencies Breakdown

- **Core**: Basic functionality for repository analysis and template generation
  - requests, pathlib, boto3, pyyaml, python-dotenv, google-generativeai, gitpython, click, colorama

- **RAG**: Enhanced AI capabilities with RAG approach
  - tiktoken, langchain, sentence-transformers, faiss-cpu, etc.

- **Web**: Web interface for easier management
  - flask

- **Dev**: Development and testing tools
  - pytest, black, isort, flake8

## Project Structure

- `inframate_flow.py`: Main script that orchestrates the analysis and generation
- `inframate/agents/ai_analyzer.py`: AI-powered analysis using Gemini API
- `inframate/utils/template_manager.py`: Manages and combines Terraform templates
- `templates/aws/terraform/`: Pre-built Terraform templates for different service types
- `test_json_app/`: Sample application used for testing
- `test_json_app/terraform/`: Generated Terraform files

## Gemini API Integration

Inframate uses the Google Gemini API to analyze application requirements and generate infrastructure recommendations. The API call format:

```
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=GEMINI_API_KEY" \
-H 'Content-Type: application/json' \
-X POST \
-d '{
  "contents": [{
    "parts":[{"text": "Your prompt here"}]
    }]
   }'
```

When the Gemini API is unavailable, Inframate falls back to rule-based analysis using predefined templates.

## Dependencies

See `requirements.txt` for dependencies:
- flask
- requests
- google-generativeai
- terraform-local

## Next Steps

- Add support for more cloud providers (Azure, GCP)
- Enhance repository analysis with language-specific parsers
- Add deployment automation
- Create a web interface for easier use 