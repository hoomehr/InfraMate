"""
Cost estimation utilities for Inframate.
"""
from typing import Dict, Any, List

# Standard AWS service costs for reference (monthly estimates)
AWS_SERVICE_COSTS = {
    "Lambda": {
        "base": 20,
        "range": 40,
        "unit": "1M requests"
    },
    "API Gateway": {
        "base": 10,
        "range": 20,
        "unit": "1M requests"
    },
    "EC2": {
        "base": 30,
        "range": 70,
        "unit": "t3.medium"
    },
    "S3": {
        "base": 1,
        "range": 5,
        "unit": "standard storage"
    },
    "CloudFront": {
        "base": 10,
        "range": 30,
        "unit": "50GB data transfer"
    },
    "RDS": {
        "base": 25,
        "range": 50,
        "unit": "db.t3.small"
    },
    "DynamoDB": {
        "base": 20,
        "range": 40,
        "unit": "25 RCUs/WCUs"
    },
    "ElastiCache": {
        "base": 40,
        "range": 80,
        "unit": "cache.t3.small"
    },
    "ECS": {
        "base": 40,
        "range": 70,
        "unit": "2 tasks"
    },
    "EKS": {
        "base": 70,
        "range": 120,
        "unit": "cluster + 2 nodes"
    },
    "DocumentDB": {
        "base": 200,
        "range": 300,
        "unit": "t3.medium"
    },
    "ELB": {
        "base": 20,
        "range": 40,
        "unit": "standard load balancer"
    },
    "Elastic Beanstalk": {
        "base": 30,
        "range": 60,
        "unit": "t3.small"
    },
    "VPC": {
        "base": 0,
        "range": 0,
        "unit": "basic features"
    },
    "CloudWatch": {
        "base": 5,
        "range": 15,
        "unit": "basic monitoring"
    },
    "IAM": {
        "base": 0,
        "range": 0,
        "unit": "base features"
    },
    "Route53": {
        "base": 0.5,
        "range": 2,
        "unit": "hosted zone"
    },
    "SQS": {
        "base": 0.5,
        "range": 3,
        "unit": "1M requests"
    },
    "SNS": {
        "base": 0.5,
        "range": 3,
        "unit": "1M notifications"
    },
    "Cognito": {
        "base": 0,
        "range": 50,
        "unit": "50K MAUs"
    }
}

def estimate_costs(services: List[str], scale: str = "medium") -> Dict[str, Any]:
    """
    Estimate costs for the given list of AWS services
    
    Args:
        services: List of AWS service names
        scale: Scale of deployment (small, medium, large)
        
    Returns:
        Dictionary with cost estimation data
    """
    scale_multiplier = {
        "small": 0.6,
        "medium": 1.0,
        "large": 1.8,
        "enterprise": 3.0
    }.get(scale.lower(), 1.0)
    
    cost_items = []
    total_min = 0
    total_max = 0
    
    # Remove duplicates while preserving order
    unique_services = []
    for service in services:
        if service not in unique_services:
            unique_services.append(service)
    
    for service in unique_services:
        # Match service to standard AWS services (partial match)
        matched_service = None
        for aws_service in AWS_SERVICE_COSTS:
            if aws_service.lower() in service.lower():
                matched_service = aws_service
                break
        
        if not matched_service:
            continue
        
        cost_data = AWS_SERVICE_COSTS[matched_service]
        min_cost = cost_data["base"] * scale_multiplier
        max_cost = (cost_data["base"] + cost_data["range"]) * scale_multiplier
        
        total_min += min_cost
        total_max += max_cost
        
        cost_items.append(f"{matched_service}: ${min_cost:.0f}-{max_cost:.0f}/month ({cost_data['unit']})")
    
    # Format the cost estimation string
    cost_estimation = f"Estimated total monthly cost: ${total_min:.0f}-{total_max:.0f}/month\n\nBreakdown:\n"
    cost_estimation += "\n".join(cost_items)
    
    return {
        "cost_items": cost_items,
        "total_min": int(total_min),
        "total_max": int(total_max),
        "cost_estimation": cost_estimation
    }

def estimate_costs_by_application_type(app_type: str, database_type: str = None) -> Dict[str, Any]:
    """
    Estimate costs based on application type and database
    
    Args:
        app_type: Type of application (node, python, web, microservice)
        database_type: Type of database (mysql, postgres, mongodb, redis)
        
    Returns:
        Dictionary with cost estimation data
    """
    services = []
    
    # Base services by application type
    if app_type.lower() == "node":
        services = ["Lambda", "API Gateway", "CloudWatch", "S3"]
    elif app_type.lower() == "python":
        services = ["Lambda", "API Gateway", "CloudWatch", "S3"]
    elif app_type.lower() == "web":
        services = ["EC2", "ELB", "S3", "CloudFront", "CloudWatch"]
    elif app_type.lower() == "microservice":
        services = ["ECS", "ELB", "CloudWatch", "ECR"]
    else:
        services = ["EC2", "S3", "CloudWatch"]
    
    # Add database services
    if database_type:
        if database_type.lower() == "mysql" or database_type.lower() == "postgres":
            services.append("RDS")
        elif database_type.lower() == "mongodb":
            services.append("DocumentDB")
        elif database_type.lower() == "redis":
            services.append("ElastiCache")
        elif database_type.lower() == "dynamodb":
            services.append("DynamoDB")
    
    return estimate_costs(services) 