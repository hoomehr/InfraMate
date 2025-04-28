# Inframate

An AI-powered infrastructure deployment assistant that analyzes repositories and helps deploy them to AWS and other cloud providers.

## Features

- 🔍 Repository analysis to understand infrastructure requirements
- 🚀 Automated AWS resource provisioning
- 🛠️ Infrastructure as Code (IaC) generation
- 🔄 Support for multiple cloud providers (AWS, with more coming soon)
- 🤖 AI-powered deployment recommendations

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/inframate.git
cd inframate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

## Usage

```bash
# Analyze and deploy a repository
inframate deploy ./path/to/repo

# Get deployment recommendations only
inframate analyze ./path/to/repo

# Deploy with specific AWS profile
inframate deploy ./path/to/repo --profile myprofile
```

## Requirements

- Python 3.8+
- AWS CLI configured with appropriate credentials
- For repository analysis: Git

## Configuration

You can create an `.inframate.yaml` file in your repository to provide hints to the deployment process:

```yaml
provider: aws
region: us-west-2
resources:
  - type: lambda
    name: my-function
    runtime: python3.9
  - type: dynamodb
    name: my-table
```

## License

MIT 