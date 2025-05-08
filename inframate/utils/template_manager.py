"""
Template manager for loading and modifying Terraform templates
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

class TemplateManager:
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent.parent / "templates" / "aws" / "terraform"
        self.templates = {}
        self._load_templates()

    def _load_templates(self):
        """Load all Terraform templates from the templates directory"""
        for template_file in self.template_dir.glob("*.tf"):
            with open(template_file, "r") as f:
                self.templates[template_file.stem] = f.read()

    def get_template(self, template_name: str) -> Optional[str]:
        """Get a specific template by name"""
        return self.templates.get(template_name)

    def extract_outputs(self, template: str) -> Tuple[Set[str], str]:
        """
        Extract output names from a Terraform template
        
        Args:
            template: Terraform template content
            
        Returns:
            Tuple of (set of output names, template with outputs extracted but NOT removed)
        """
        output_names = set()
        
        # Match all output blocks to extract their names
        output_pattern = re.compile(r'output\s+"([^"]+)"\s+{', re.DOTALL)
        matches = output_pattern.finditer(template)
        
        for match in matches:
            output_name = match.group(1)
            output_names.add(output_name)
        
        return output_names, template

    def _convert_asg_tags(self, resource_part, tags_content, closing_part):
        """
        Convert AWS autoscaling group tags from list format to tag blocks
        
        Args:
            resource_part: The part of the resource before the tags
            tags_content: The content of the tags list
            closing_part: The closing part of the resource after the tags
            
        Returns:
            Updated resource definition with tag blocks instead of tag format
        """
        # Regular expressions to extract key-value pairs from different tag formats
        tag_pairs = []
        
        # Look for {key = "name", value = "example", propagate_at_launch = true} format
        map_pattern = re.compile(r'{[^}]*?key\s*=\s*"([^"]+)"[^}]*?value\s*=\s*"([^"]+)"[^}]*?}', re.DOTALL)
        for match in map_pattern.finditer(tags_content):
            key = match.group(1)
            value = match.group(2)
            tag_pairs.append((key, value))
        
        # If no tags were found in map format, look for regular key-value format
        if not tag_pairs:
            key_value_pattern = re.compile(r'(?:{\s*|\s+)([a-zA-Z0-9_-]+)\s*=\s*"([^"]+)"', re.DOTALL)
            for match in key_value_pattern.finditer(tags_content):
                key = match.group(1)
                value = match.group(2)
                tag_pairs.append((key, value))
        
        # Build the new resource with tag blocks
        result = resource_part
        
        # Add tags as tag blocks
        for key, value in tag_pairs:
            result += f"""
  tag {{
    key                 = "{key}"
    value               = "{value}"
    propagate_at_launch = true
  }}"""
        
        result += closing_part
        return result

    def _add_launch_configuration(self, template: str) -> str:
        """
        Add aws_launch_configuration if it's referenced but not defined
        
        Args:
            template: Terraform template content
            
        Returns:
            Template with added launch configuration if needed
        """
        # Check if launch_configuration is referenced
        if "launch_configuration = aws_launch_configuration.launch_config.id" in template:
            # Check if it's already defined
            if not re.search(r'resource\s+"aws_launch_configuration"\s+"launch_config"\s+{', template):
                # Add the resource
                launch_config = """
# Default launch configuration for autoscaling groups
resource "aws_launch_configuration" "launch_config" {
  name_prefix                 = "app-"
  image_id                    = var.ami_id
  instance_type               = var.instance_type
  security_groups             = [aws_security_group.app_sg.id]
  associate_public_ip_address = true
  
  lifecycle {
    create_before_destroy = true
  }
}
"""
                # Check if a security group is defined, if not add one
                if not re.search(r'resource\s+"aws_security_group"\s+"app_sg"\s+{', template):
                    launch_config = """
# Default security group for instances
resource "aws_security_group" "app_sg" {
  name        = "app-sg"
  description = "Security group for application instances"
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP access"
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
}
""" + launch_config
                
                # Add the resources after the provider block
                template = re.sub(
                    r'(provider\s+"aws"\s+{[^}]*})',
                    r'\1\n' + launch_config,
                    template
                )
                
        return template

    def fix_template_issues(self, template: str) -> str:
        """Fix common issues in Terraform templates"""
        # Fix network_interface vs network_interfaces block issue in launch_template
        template = re.sub(
            r'(resource\s+"aws_launch_template"\s+"[^"]+"\s+{\s+[^}]*?)network_interface\s+{',
            r'\1network_interfaces {',
            template,
            flags=re.DOTALL
        )
        
        # Fix name vs db_name in aws_db_instance
        template = re.sub(
            r'(resource\s+"aws_db_instance"\s+"[^"]+"\s+{\s+[^}]*?)(\s+)name(\s+)=(\s+)(["\'][^"\']+["\'])',
            r'\1\2db_name\3=\4\5',
            template,
            flags=re.DOTALL
        )
        
        # Ensure RDS instances have valid engine names
        template = re.sub(
            r'(resource\s+"aws_db_instance"[^{]*{\s+[^}]*?)(\s+)engine(\s+)=(\s+)(["\'])(mysql|postgres|mariadb|oracle|mssql)(\s*server|\s*-\s*[\w]+)?(["\'])',
            lambda m: m.group(1) + m.group(2) + "engine" + m.group(3) + "=" + m.group(4) + m.group(5) + 
                     {"mysql": "mysql", "postgres": "postgres", "postgresql": "postgres", "mariadb": "mariadb", 
                      "oracle": "oracle-ee", "mssql": "sqlserver-ee", "mssql server": "sqlserver-ee", 
                      "sql server": "sqlserver-ee"}.get(m.group(6).lower(), m.group(6)) + m.group(8),
            template,
            flags=re.DOTALL
        )
        
        # Fix missing engine version for RDS instances
        template = re.sub(
            r'(resource\s+"aws_db_instance"[^{]*{\s+[^}]*?)(\s+engine\s+=\s+["\'](\w+)["\'])',
            lambda m: m.group(1) + m.group(2) + "\n  engine_version = " + 
                     {"mysql": "\"8.0\"", "postgres": "\"13.4\"", "mariadb": "\"10.5\"", 
                      "oracle-ee": "\"19.0\"", "sqlserver-ee": "\"15.00\""}.get(m.group(3), "\"latest\""),
            template,
            flags=re.DOTALL
        )
        
        # Fix missing instance class for RDS instances
        template = re.sub(
            r'(resource\s+"aws_db_instance"[^{]*{\s+[^}]*?)(?!.*instance_class\s*=)(.*?)(^\s*})',
            r'\1  instance_class = "db.t3.micro"\n\2\3',
            template,
            flags=re.DOTALL | re.MULTILINE
        )
        
        # Fix missing allocated_storage for RDS instances
        template = re.sub(
            r'(resource\s+"aws_db_instance"[^{]*{\s+[^}]*?)(?!.*allocated_storage\s*=)(.*?)(^\s*})',
            r'\1  allocated_storage = 20\n\2\3',
            template,
            flags=re.DOTALL | re.MULTILINE
        )
        
        # Fix autoscaling group tags format - convert from tags list to tag blocks
        template = re.sub(
            r'(resource\s+"aws_autoscaling_group"\s+"[^"]+"\s+{[^}]*?)\s+tags\s+=\s+\[(.*?)\s*\](.*?})',
            lambda m: self._convert_asg_tags(m.group(1), m.group(2), m.group(3)),
            template,
            flags=re.DOTALL
        )
        
        # Fix missing capacity parameters for ASG
        template = re.sub(
            r'(resource\s+"aws_autoscaling_group"\s+"[^"]+"\s+{[^}]*?)(?!.*min_size\s*=)(.*?)(^\s*})',
            r'\1  min_size = 1\n  max_size = 3\n  desired_capacity = 1\n\2\3',
            template,
            flags=re.DOTALL | re.MULTILINE
        )
        
        # Fix missing launch_configuration/launch_template in ASG
        template = re.sub(
            r'(resource\s+"aws_autoscaling_group"\s+"[^"]+"\s+{[^}]*?)(?!.*launch_configuration\s*=|.*launch_template\s*{)(.*?)(^\s*})',
            r'\1  launch_configuration = aws_launch_configuration.launch_config.id\n\2\3',
            template,
            flags=re.DOTALL | re.MULTILINE
        )
        
        # Add required resources if needed (like launch_configuration)
        template = self._add_launch_configuration(template)
        
        # Ensure all referenced resources in outputs have try() functions
        template = re.sub(
            r'(output\s+"[^"]+"\s+{\s+[^}]*?value\s+=\s+)([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)([^}]*?})',
            r'\1try(\2, "N/A")\3',
            template,
            flags=re.DOTALL
        )
        
        # Ensure we don't have duplicate resource definitions
        seen_resources = {}
        clean_lines = []
        current_resource = None
        skip_block = False
        bracket_count = 0
        
        for line in template.split("\n"):
            # Check for resource definition start
            resource_match = re.match(r'resource\s+"([^"]+)"\s+"([^"]+)"\s+{', line)
            if resource_match and not current_resource:
                resource_type, resource_name = resource_match.groups()
                resource_key = f"{resource_type}.{resource_name}"
                
                if resource_key in seen_resources:
                    # Skip this duplicate resource
                    skip_block = True
                    bracket_count = 1
                else:
                    seen_resources[resource_key] = True
                    current_resource = resource_key
                    skip_block = False
                    bracket_count = 1
            
            # Count brackets to track when we exit the resource block
            if skip_block:
                if "{" in line:
                    bracket_count += line.count("{")
                if "}" in line:
                    bracket_count -= line.count("}")
                    
                if bracket_count == 0:
                    skip_block = False
                    current_resource = None
                    
                # Skip the line since we're in a duplicate resource
                continue
                
            # Normal line processing
            if "{" in line and current_resource:
                bracket_count += line.count("{")
            if "}" in line and current_resource:
                bracket_count -= line.count("}")
                if bracket_count == 0:
                    current_resource = None
            
            clean_lines.append(line)
        
        return "\n".join(clean_lines)

    def combine_templates(self, template_names: List[str]) -> str:
        """Combine multiple templates into a single Terraform configuration"""
        combined = """# Terraform configuration generated by Inframate
provider "aws" {
  region = var.region
}

"""
        for name in template_names:
            template = self.get_template(name)
            if template:
                combined += f"\n# {name} configuration\n{template}\n"

        # Fix common template issues
        combined = self.fix_template_issues(combined)
        
        return combined

    def get_template_for_services(self, services: List[str]) -> str:
        """Get appropriate templates based on the list of services"""
        template_names = []
        
        # Map services to template names
        service_to_template = {
            # Compute Services
            "Lambda": "nodejs_lambda",
            "API Gateway": "nodejs_lambda",  # Included in nodejs_lambda template
            "EC2": "ec2",
            "ECS": "ecs",
            "EKS": "eks",
            "Elastic Beanstalk": "elastic_beanstalk",
            
            # Storage Services
            "S3": "webapp",
            "CloudFront": "webapp",  # Included in webapp template
            "EFS": "efs",
            
            # Database Services
            "RDS": "database",
            "DocumentDB": "database",
            "ElastiCache": "database",
            "DynamoDB": "dynamodb",
            
            # Networking Services
            "VPC": "vpc",
            "Route53": "route53",
            "CloudFront": "cloudfront",
            "API Gateway": "api_gateway",
            
            # Load Balancing
            "ALB": "alb",
            "NLB": "nlb",
            
            # Security Services
            "WAF": "waf",
            "Shield": "shield",
            "GuardDuty": "guardduty",
            
            # Monitoring Services
            "CloudWatch": "cloudwatch",
            "X-Ray": "xray",
            
            # CI/CD Services
            "CodeBuild": "codebuild",
            "CodePipeline": "codepipeline",
            "CodeDeploy": "codedeploy"
        }

        # Add templates based on services
        for service in services:
            template_name = service_to_template.get(service)
            if template_name and template_name not in template_names:
                template_names.append(template_name)

        # Always include these templates
        required_templates = ["variables", "vpc"]
        for template in required_templates:
            if template not in template_names:
                template_names.append(template)

        return self.combine_templates(template_names)

    def detect_resources(self, template: str) -> Set[str]:
        """
        Detect which resources exist in a Terraform template
        
        Args:
            template: Terraform template content
            
        Returns:
            Set of resource identifiers in format "type.name"
        """
        resources = set()
        
        # Match all resource blocks
        resource_pattern = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"\s+{', re.DOTALL)
        matches = resource_pattern.finditer(template)
        
        for match in matches:
            resource_type = match.group(1)
            resource_name = match.group(2)
            resources.add(f"{resource_type}.{resource_name}")
        
        return resources 