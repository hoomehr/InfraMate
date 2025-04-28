// Main JavaScript for Inframate Sample App
document.addEventListener('DOMContentLoaded', function() {
    const analyzeForm = document.getElementById('analyzeForm');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultSection = document.getElementById('resultSection');
    const errorSection = document.getElementById('errorSection');
    const terraformResult = document.getElementById('terraformResult');
    const fullOutput = document.getElementById('fullOutput');
    const errorMessage = document.getElementById('errorMessage');

    analyzeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get the repository path
        const repoPath = document.getElementById('repoPath').value;
        
        if (!repoPath) {
            showError('Please enter a repository path.');
            return;
        }
        
        // Show loading indicator and hide previous results
        loadingIndicator.classList.remove('d-none');
        resultSection.classList.add('d-none');
        errorSection.classList.add('d-none');
        
        // Simulate API call with setTimeout (replace with actual fetch in production)
        setTimeout(() => {
            // For demo purposes, we'll simulate a successful response
            const mockResponse = {
                success: true,
                terraform_template: `provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  
  tags = {
    Name = "WebServer"
    Environment = "Production"
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "my-tf-test-bucket"
  acl    = "private"
  
  tags = {
    Name        = "Data Bucket"
    Environment = "Production"
  }
}`,
                full_output: `Analyzing repository: ${repoPath}
Scanning infrastructure files...
Found 3 Terraform files
Found 2 CloudFormation templates
Found 1 Kubernetes configuration

RESOURCE SUMMARY:
- 5 EC2 instances
- 2 S3 buckets
- 1 RDS database
- 3 Lambda functions
- 1 API Gateway

SECURITY FINDINGS:
- 2 instances with public IP addresses
- 1 S3 bucket with public access
- 3 IAM roles with overly permissive policies

OPTIMIZATION OPPORTUNITIES:
- Consider using Auto Scaling for EC2 instances
- Right-size RDS instance (currently over-provisioned)
- Implement lifecycle policies for S3 buckets

Generated Terraform template based on best practices.`
            };
            
            // Hide loading indicator
            loadingIndicator.classList.add('d-none');
            
            if (mockResponse.success) {
                // Show results
                terraformResult.textContent = mockResponse.terraform_template;
                fullOutput.textContent = mockResponse.full_output;
                resultSection.classList.remove('d-none');
                
                // Initialize syntax highlighting if using a library like Prism or highlight.js
                // For example: Prism.highlightAll();
            } else {
                showError('Failed to analyze the repository. Please try again.');
            }
        }, 2000); // Simulate 2-second API call
    });
    
    function showError(message) {
        errorMessage.textContent = message;
        errorSection.classList.remove('d-none');
        loadingIndicator.classList.add('d-none');
    }
}); 