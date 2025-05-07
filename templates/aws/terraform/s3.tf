# S3 Bucket for Storage
resource "aws_s3_bucket" "storage" {
  bucket = var.s3_bucket_name != "" ? var.s3_bucket_name : "${var.app_name}-${var.environment}-storage-${random_string.bucket_suffix.result}"
  
  tags = {
    Name        = "${var.app_name}-storage"
    Environment = var.environment
  }
}

# S3 Bucket for Static Website Hosting
resource "aws_s3_bucket" "frontend" {
  count  = var.enable_website_hosting ? 1 : 0
  bucket = var.s3_website_bucket_name != "" ? var.s3_website_bucket_name : "${var.app_name}-${var.environment}-website-${random_string.bucket_suffix.result}"
  
  tags = {
    Name        = "${var.app_name}-website"
    Environment = var.environment
  }
}

# Random string for unique bucket names
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Website Configuration
resource "aws_s3_bucket_website_configuration" "frontend" {
  count  = var.enable_website_hosting ? 1 : 0
  bucket = aws_s3_bucket.frontend[0].id
  
  index_document {
    suffix = var.s3_website_index_document
  }
  
  error_document {
    key = var.s3_website_error_document
  }
  
  # Redirect rules (optional)
  dynamic "routing_rule" {
    for_each = var.s3_website_routing_rules
    content {
      condition {
        key_prefix_equals = routing_rule.value.condition_key_prefix_equals
      }
      
      redirect {
        replace_key_prefix_with = routing_rule.value.redirect_replace_key_prefix_with
        protocol                = routing_rule.value.redirect_protocol
        host_name               = routing_rule.value.redirect_host_name
        http_redirect_code      = routing_rule.value.redirect_http_code
      }
    }
  }
}

# Bucket ACL
resource "aws_s3_bucket_ownership_controls" "storage" {
  bucket = aws_s3_bucket.storage.id
  
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "storage" {
  depends_on = [aws_s3_bucket_ownership_controls.storage]
  
  bucket = aws_s3_bucket.storage.id
  acl    = "private"
}

resource "aws_s3_bucket_ownership_controls" "frontend" {
  count  = var.enable_website_hosting ? 1 : 0
  bucket = aws_s3_bucket.frontend[0].id
  
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "frontend" {
  count     = var.enable_website_hosting ? 1 : 0
  depends_on = [aws_s3_bucket_ownership_controls.frontend]
  
  bucket = aws_s3_bucket.frontend[0].id
  acl    = "public-read"
}

# Bucket Policy for Website
resource "aws_s3_bucket_policy" "frontend" {
  count  = var.enable_website_hosting ? 1 : 0
  bucket = aws_s3_bucket.frontend[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend[0].arn}/*"
      }
    ]
  })
}

# CORS Configuration
resource "aws_s3_bucket_cors_configuration" "frontend" {
  count  = var.enable_website_hosting ? 1 : 0
  bucket = aws_s3_bucket.frontend[0].id
  
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = var.s3_cors_allowed_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Versioning
resource "aws_s3_bucket_versioning" "storage" {
  bucket = aws_s3_bucket.storage.id
  
  versioning_configuration {
    status = var.s3_enable_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_versioning" "frontend" {
  count  = var.enable_website_hosting ? 1 : 0
  bucket = aws_s3_bucket.frontend[0].id
  
  versioning_configuration {
    status = var.s3_enable_versioning ? "Enabled" : "Suspended"
  }
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "storage" {
  bucket = aws_s3_bucket.storage.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  count  = var.enable_website_hosting ? 1 : 0
  bucket = aws_s3_bucket.frontend[0].id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle Rules
resource "aws_s3_bucket_lifecycle_configuration" "storage" {
  count  = length(var.s3_lifecycle_rules) > 0 ? 1 : 0
  bucket = aws_s3_bucket.storage.id
  
  dynamic "rule" {
    for_each = var.s3_lifecycle_rules
    
    content {
      id     = rule.value.id
      status = rule.value.status
      
      dynamic "transition" {
        for_each = rule.value.transitions != null ? rule.value.transitions : []
        
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }
      
      dynamic "expiration" {
        for_each = rule.value.expiration_days != null ? [1] : []
        
        content {
          days = rule.value.expiration_days
        }
      }
      
      dynamic "noncurrent_version_transition" {
        for_each = rule.value.noncurrent_version_transitions != null ? rule.value.noncurrent_version_transitions : []
        
        content {
          noncurrent_days = noncurrent_version_transition.value.days
          storage_class   = noncurrent_version_transition.value.storage_class
        }
      }
      
      dynamic "noncurrent_version_expiration" {
        for_each = rule.value.noncurrent_version_expiration_days != null ? [1] : []
        
        content {
          noncurrent_days = rule.value.noncurrent_version_expiration_days
        }
      }
    }
  }
}

# Block Public Access
resource "aws_s3_bucket_public_access_block" "storage" {
  bucket = aws_s3_bucket.storage.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM Policy for S3 Access
resource "aws_iam_policy" "s3_access" {
  name        = "${var.app_name}-${var.environment}-s3-access-policy"
  description = "Policy for accessing S3 buckets"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.storage.arn,
          "${aws_s3_bucket.storage.arn}/*"
        ]
      }
    ]
  })
}

# CloudWatch Metrics for S3
resource "aws_cloudwatch_metric_alarm" "s3_4xx_errors" {
  alarm_name          = "${var.app_name}-${var.environment}-s3-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4xxErrors"
  namespace           = "AWS/S3"
  period              = "300"
  statistic           = "Sum"
  threshold           = "100"
  alarm_description   = "This metric monitors S3 4xx errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    BucketName = aws_s3_bucket.storage.id
    FilterId   = "EntireBucket"
  }
}

# Outputs
output "storage_bucket_name" {
  description = "The name of the storage S3 bucket"
  value       = aws_s3_bucket.storage.id
}

output "storage_bucket_arn" {
  description = "The ARN of the storage S3 bucket"
  value       = aws_s3_bucket.storage.arn
}

output "storage_bucket_domain_name" {
  description = "The domain name of the storage S3 bucket"
  value       = aws_s3_bucket.storage.bucket_domain_name
}

output "frontend_bucket_name" {
  description = "The name of the frontend S3 bucket"
  value       = var.enable_website_hosting ? aws_s3_bucket.frontend[0].id : null
}

output "frontend_bucket_arn" {
  description = "The ARN of the frontend S3 bucket"
  value       = var.enable_website_hosting ? aws_s3_bucket.frontend[0].arn : null
}

output "frontend_website_endpoint" {
  description = "The website endpoint of the frontend S3 bucket"
  value       = var.enable_website_hosting ? aws_s3_bucket_website_configuration.frontend[0].website_endpoint : null
}

output "frontend_website_domain" {
  description = "The website domain of the frontend S3 bucket"
  value       = var.enable_website_hosting ? aws_s3_bucket_website_configuration.frontend[0].website_domain : null
} 