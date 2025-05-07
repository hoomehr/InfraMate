# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.app_name}-${var.environment}-dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      # CPU Utilization (if using EC2/ECS)
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = var.use_ec2 ? [
            ["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", aws_autoscaling_group.app.name]
          ] : (var.use_ecs ? [
            ["AWS/ECS", "CPUUtilization", "ClusterName", aws_ecs_cluster.main.name, "ServiceName", aws_ecs_service.app.name]
          ] : [])
          
          period = 300
          stat   = "Average"
          region = var.region
          title  = "CPU Utilization"
        }
      },
      
      # Memory Utilization (if using ECS)
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = var.use_ecs ? [
            ["AWS/ECS", "MemoryUtilization", "ClusterName", aws_ecs_cluster.main.name, "ServiceName", aws_ecs_service.app.name]
          ] : []
          
          period = 300
          stat   = "Average"
          region = var.region
          title  = "Memory Utilization"
        }
      },
      
      # API Gateway Requests (if using API Gateway)
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = var.use_api_gateway ? [
            ["AWS/ApiGateway", "Count", "ApiName", aws_api_gateway_rest_api.main.name, "Stage", aws_api_gateway_stage.main.stage_name]
          ] : []
          
          period = 300
          stat   = "Sum"
          region = var.region
          title  = "API Gateway Requests"
        }
      },
      
      # Lambda Invocations (if using Lambda)
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = var.use_lambda ? [
            ["AWS/Lambda", "Invocations", "FunctionName", var.lambda_function_name]
          ] : []
          
          period = 300
          stat   = "Sum"
          region = var.region
          title  = "Lambda Invocations"
        }
      },
      
      # Database Metrics (if using RDS)
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          metrics = var.use_rds ? [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.main.id]
          ] : []
          
          period = 300
          stat   = "Average"
          region = var.region
          title  = "RDS CPU Utilization"
        }
      },
      
      # DynamoDB Metrics (if using DynamoDB)
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6
        properties = {
          metrics = var.use_dynamodb ? [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", aws_dynamodb_table.main.name],
            ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", aws_dynamodb_table.main.name]
          ] : []
          
          period = 300
          stat   = "Sum"
          region = var.region
          title  = "DynamoDB Capacity Consumption"
        }
      }
    ]
  })
}

# CloudWatch Log Group for Application
resource "aws_cloudwatch_log_group" "app" {
  name              = "/aws/${var.app_name}/${var.environment}"
  retention_in_days = var.cloudwatch_log_retention_days
  
  tags = {
    Name        = "${var.app_name}-log-group"
    Environment = var.environment
  }
}

# CloudWatch Alarm for Application
resource "aws_cloudwatch_metric_alarm" "app_errors" {
  alarm_name          = "${var.app_name}-${var.environment}-error-count"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ErrorCount"
  namespace           = "AWS/Logs"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors application error logs"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    LogGroupName = aws_cloudwatch_log_group.app.name
    FilterName   = "ErrorFilter"
  }
}

# CloudWatch Log Metric Filter for Errors
resource "aws_cloudwatch_log_metric_filter" "error_filter" {
  name           = "${var.app_name}-${var.environment}-error-filter"
  pattern        = "ERROR"
  log_group_name = aws_cloudwatch_log_group.app.name
  
  metric_transformation {
    name      = "ErrorCount"
    namespace = "AWS/Logs"
    value     = "1"
  }
}

# CloudWatch Synthetic Canary (for website monitoring)
resource "aws_synthetics_canary" "website" {
  count = var.enable_website_monitoring ? 1 : 0
  
  name                 = "${var.app_name}-${var.environment}-website-canary"
  artifact_s3_location = "s3://${aws_s3_bucket.storage.id}/canary-artifacts/"
  execution_role_arn   = aws_iam_role.canary_role[0].arn
  runtime_version      = "syn-nodejs-puppeteer-3.4"
  
  schedule {
    expression = "rate(5 minutes)"
  }
  
  handler = "canary.handler"
  
  s3_bucket = aws_s3_bucket.storage.id
  s3_key    = "canaries/website-monitor.zip"
  
  start_canary = true
  
  depends_on = [
    aws_iam_role_policy_attachment.canary_cloudwatch_policy[0],
    aws_iam_role_policy_attachment.canary_s3_policy[0]
  ]
}

# IAM Role for Canary
resource "aws_iam_role" "canary_role" {
  count = var.enable_website_monitoring ? 1 : 0
  
  name = "${var.app_name}-${var.environment}-canary-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name        = "${var.app_name}-canary-role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "canary_cloudwatch_policy" {
  count = var.enable_website_monitoring ? 1 : 0
  
  role       = aws_iam_role.canary_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchSyntheticsFullAccess"
}

resource "aws_iam_role_policy_attachment" "canary_s3_policy" {
  count = var.enable_website_monitoring ? 1 : 0
  
  role       = aws_iam_role.canary_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

# CloudWatch Alarm for Canary
resource "aws_cloudwatch_metric_alarm" "canary_alarm" {
  count = var.enable_website_monitoring ? 1 : 0
  
  alarm_name          = "${var.app_name}-${var.environment}-canary-failure"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "SuccessPercent"
  namespace           = "CloudWatchSynthetics"
  period              = "300"
  statistic           = "Average"
  threshold           = "100"
  alarm_description   = "This metric monitors website availability"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    CanaryName = aws_synthetics_canary.website[0].name
  }
}

# CloudWatch Composite Alarm
resource "aws_cloudwatch_composite_alarm" "composite" {
  alarm_name = "${var.app_name}-${var.environment}-composite-alarm"
  
  alarm_rule = var.enable_website_monitoring ? 
    "ALARM(${aws_cloudwatch_metric_alarm.app_errors.alarm_name}) OR ALARM(${aws_cloudwatch_metric_alarm.canary_alarm[0].alarm_name})" :
    "ALARM(${aws_cloudwatch_metric_alarm.app_errors.alarm_name})"
  
  alarm_actions = [aws_sns_topic.alerts.arn]
  
  tags = {
    Name        = "${var.app_name}-composite-alarm"
    Environment = var.environment
  }
}

# CloudWatch Event Rule for Regular Checks
resource "aws_cloudwatch_event_rule" "monitoring_check" {
  name                = "${var.app_name}-${var.environment}-monitoring-check"
  description         = "Trigger periodic system health check"
  schedule_expression = "rate(5 minutes)"
  
  tags = {
    Name        = "${var.app_name}-event-rule"
    Environment = var.environment
  }
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.app_name}-${var.environment}-alerts"
  
  tags = {
    Name        = "${var.app_name}-alerts"
    Environment = var.environment
  }
}

# SNS Topic Subscription (Email)
resource "aws_sns_topic_subscription" "email" {
  count = length(var.alert_email_addresses)
  
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email_addresses[count.index]
}

# SNS Topic Subscription (SMS)
resource "aws_sns_topic_subscription" "sms" {
  count = length(var.alert_phone_numbers)
  
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "sms"
  endpoint  = var.alert_phone_numbers[count.index]
}

# Outputs
output "cloudwatch_dashboard_url" {
  description = "URL to the CloudWatch dashboard"
  value       = "https://${var.region}.console.aws.amazon.com/cloudwatch/home?region=${var.region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "alert_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.app.name
} 