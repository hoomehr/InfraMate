# Inframate: AI-Powered Infrastructure Deployment Assistant

Inframate is a tool that analyzes code repositories and creates infrastructure deployment recommendations and Terraform templates using AI.

## Overview

Inframate reads an `inframate.md` file containing details about your application, analyzes the repository structure, and generates Terraform files for deploying the infrastructure. It uses the Google Gemini API to generate tailored infrastructure recommendations and Terraform code.

## How It Works

1. **Repository Analysis**: Inframate reads the `inframate.md` file in your repository to understand:
   - Application language and framework
   - Database requirements
   - Infrastructure requirements
   - Deployment preferences

2. **AI-Powered Recommendations**: Using the Google Gemini API, Inframate generates:
   - Recommended AWS services for your application
   - Infrastructure recommendations based on application requirements
   - Complete Terraform templates for deployment

3. **Terraform Generation**: Inframate creates a complete set of Terraform files:
   - `main.tf`: Primary infrastructure definition
   - `variables.tf`: Variable definitions
   - `outputs.tf`: Output declarations
   - `terraform.tfvars`: Default variable values

## Using Inframate

### Prerequisites

- Python 3.7+
- [Google Gemini API key](https://ai.google.dev/)
- Terraform (for deployment)

### Installation

```bash
pip install -r requirements.txt
```

### Usage

1. Create an `inframate.md` file in your repository with details about your application.

2. Set your Gemini API key:
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

3. Run Inframate:
```bash
python inframate_flow.py /path/to/your/repo
```

4. Deploy using the generated Terraform files:
```bash
cd /path/to/your/repo/terraform
terraform init
terraform plan
terraform apply
```

## Example: JSON API Application

We created a sample JSON API application:
- Node.js with Express.js backend
- MongoDB database
- Serverless AWS architecture using Lambda and API Gateway

The generated Terraform template includes:
- Lambda function for the Express.js API
- API Gateway configuration
- Auto-scaling policies
- IAM roles and permissions
- CloudWatch logging

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