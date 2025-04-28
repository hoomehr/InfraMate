# S3 Static Website Template
# This template creates an S3 bucket configured for static website hosting with CloudFront

provider "aws" {
  region = var.region
}

# S3 bucket for hosting the static website
resource "aws_s3_bucket" "website_bucket" {
  bucket = var.bucket_name
  
  tags = {
    Name        = var.bucket_name
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_s3_bucket_ownership_controls" "website_bucket_ownership" {
  bucket = aws_s3_bucket.website_bucket.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "website_bucket_public_access" {
  bucket = aws_s3_bucket.website_bucket.id

  block_public_acls       = var.block_public_access
  block_public_policy     = var.block_public_access
  ignore_public_acls      = var.block_public_access
  restrict_public_buckets = var.block_public_access
}

resource "aws_s3_bucket_acl" "website_bucket_acl" {
  depends_on = [
    aws_s3_bucket_ownership_controls.website_bucket_ownership,
    aws_s3_bucket_public_access_block.website_bucket_public_access,
  ]

  bucket = aws_s3_bucket.website_bucket.id
  acl    = var.block_public_access ? "private" : "public-read"
}

resource "aws_s3_bucket_website_configuration" "website_config" {
  bucket = aws_s3_bucket.website_bucket.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

# If not using CloudFront, we need a bucket policy for public access
resource "aws_s3_bucket_policy" "website_bucket_policy" {
  count = var.create_cloudfront ? 0 : 1
  
  bucket = aws_s3_bucket.website_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.website_bucket.arn}/*"
      }
    ]
  })
}

# CloudFront distribution
resource "aws_cloudfront_distribution" "website_distribution" {
  count = var.create_cloudfront ? 1 : 0
  
  origin {
    domain_name = aws_s3_bucket.website_bucket.bucket_regional_domain_name
    origin_id   = aws_s3_bucket.website_bucket.id
    
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.oai[0].cloudfront_access_identity_path
    }
  }
  
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = var.cloudfront_price_class
  
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = aws_s3_bucket.website_bucket.id
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    cloudfront_default_certificate = true
  }
  
  tags = {
    Name        = "${var.bucket_name}-distribution"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_cloudfront_origin_access_identity" "oai" {
  count = var.create_cloudfront ? 1 : 0
  
  comment = "OAI for ${var.bucket_name}"
}

# S3 bucket policy for CloudFront
resource "aws_s3_bucket_policy" "cloudfront_bucket_policy" {
  count = var.create_cloudfront ? 1 : 0
  
  bucket = aws_s3_bucket.website_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontAccess"
        Effect    = "Allow"
        Principal = {
          AWS = "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity ${aws_cloudfront_origin_access_identity.oai[0].id}"
        }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.website_bucket.arn}/*"
      }
    ]
  })
}

# Variables
variable "region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "block_public_access" {
  description = "Whether to block public access to the S3 bucket"
  type        = bool
  default     = false
}

variable "create_cloudfront" {
  description = "Whether to create a CloudFront distribution"
  type        = bool
  default     = true
}

variable "cloudfront_price_class" {
  description = "Price class for the CloudFront distribution"
  type        = string
  default     = "PriceClass_100" # Use only North America and Europe
}

variable "environment" {
  description = "Environment (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "inframate-project"
}

# Outputs
output "bucket_name" {
  value = aws_s3_bucket.website_bucket.id
}

output "bucket_website_endpoint" {
  value = aws_s3_bucket_website_configuration.website_config.website_endpoint
}

output "cloudfront_domain_name" {
  value = var.create_cloudfront ? aws_cloudfront_distribution.website_distribution[0].domain_name : null
} 