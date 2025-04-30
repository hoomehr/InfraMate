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

4. **Terraform Generation**: Inframate creates a complete set of Terraform files:
   - `main.tf`: Primary infrastructure definition
   - `variables.tf`: Variable definitions
   - `outputs.tf`: Output declarations
   - `terraform.tfvars`: Default variable values
   - `README.md`: Documentation including cost estimates and deployment instructions

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
   ```

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

## Templates

Inframate includes a set of pre-built Terraform templates for common application patterns:

- **Node.js Lambda**: Serverless applications using Lambda and API Gateway
- **Web Applications**: Frontend (S3+CloudFront) and backend (EC2/ECS)
- **Database Resources**: RDS, DynamoDB, and ElastiCache
- **Microservices**: ECS/EKS deployments for containerized applications

These templates are used as a starting point and enhanced with AI recommendations.

## Example

For a Node.js Express API with MongoDB, Inframate will generate:
- Lambda function for the Express.js API
- API Gateway configuration
- Auto-scaling policies
- IAM roles and permissions
- CloudWatch logging
- MongoDB Atlas connection (or DocumentDB)
- Estimated monthly cost breakdown for all services

## Requirements

- Python 3.8+
- [Google Gemini API key](https://ai.google.dev/)
- Terraform (for deployment)

## Next Steps

- Add support for more cloud providers (Azure, GCP)
- Enhance repository analysis with language-specific parsers
- Add deployment automation
- Create a web interface for easier use

## Inframate Components

- `inframate_flow.py`: Main script that orchestrates the analysis and generation
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

## Requirements

See `requirements.txt` for dependencies:
- flask
- requests

## Next Steps

- Add support for more cloud providers (Azure, GCP)
- Enhance repository analysis with language-specific parsers
- Add deployment automation
- Create a web interface for easier use 