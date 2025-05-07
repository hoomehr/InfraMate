# DynamoDB Table
resource "aws_dynamodb_table" "main" {
  name         = "${var.app_name}-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"  # On-demand capacity
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  # Add GSI if specified
  dynamic "global_secondary_index" {
    for_each = var.dynamodb_gsi_attributes != null ? var.dynamodb_gsi_attributes : {}
    content {
      name               = "${global_secondary_index.key}-index"
      hash_key           = global_secondary_index.key
      projection_type    = "ALL"
    }
  }

  # Additional attributes
  dynamic "attribute" {
    for_each = var.dynamodb_gsi_attributes != null ? var.dynamodb_gsi_attributes : {}
    content {
      name = attribute.key
      type = attribute.value
    }
  }

  # Enable point-in-time recovery if needed
  point_in_time_recovery {
    enabled = var.enable_dynamodb_point_in_time_recovery
  }

  # Enable server-side encryption
  server_side_encryption {
    enabled = true
  }

  # TTL specification
  ttl {
    attribute_name = var.dynamodb_ttl_attribute
    enabled        = var.dynamodb_ttl_attribute != "" ? true : false
  }

  # Auto scaling configuration (if not using on-demand)
  # lifecycle {
  #   ignore_changes = [
  #     read_capacity,
  #     write_capacity,
  #   ]
  # }

  tags = {
    Name        = "${var.app_name}-table"
    Environment = var.environment
  }
}

# DynamoDB Auto Scaling (for provisioned tables)
# resource "aws_appautoscaling_target" "dynamodb_table_read_target" {
#   count = var.dynamodb_billing_mode == "PROVISIONED" ? 1 : 0
#   
#   max_capacity       = var.dynamodb_max_read_capacity
#   min_capacity       = var.dynamodb_min_read_capacity
#   resource_id        = "table/${aws_dynamodb_table.main.name}"
#   scalable_dimension = "dynamodb:table:ReadCapacityUnits"
#   service_namespace  = "dynamodb"
# }

# resource "aws_appautoscaling_target" "dynamodb_table_write_target" {
#   count = var.dynamodb_billing_mode == "PROVISIONED" ? 1 : 0
#   
#   max_capacity       = var.dynamodb_max_write_capacity
#   min_capacity       = var.dynamodb_min_write_capacity
#   resource_id        = "table/${aws_dynamodb_table.main.name}"
#   scalable_dimension = "dynamodb:table:WriteCapacityUnits"
#   service_namespace  = "dynamodb"
# }

# resource "aws_appautoscaling_policy" "dynamodb_table_read_policy" {
#   count = var.dynamodb_billing_mode == "PROVISIONED" ? 1 : 0
#   
#   name               = "${var.app_name}-dynamodb-read-capacity"
#   policy_type        = "TargetTrackingScaling"
#   resource_id        = aws_appautoscaling_target.dynamodb_table_read_target[0].resource_id
#   scalable_dimension = aws_appautoscaling_target.dynamodb_table_read_target[0].scalable_dimension
#   service_namespace  = aws_appautoscaling_target.dynamodb_table_read_target[0].service_namespace
# 
#   target_tracking_scaling_policy_configuration {
#     predefined_metric_specification {
#       predefined_metric_type = "DynamoDBReadCapacityUtilization"
#     }
#     target_value = 70.0
#   }
# }

# resource "aws_appautoscaling_policy" "dynamodb_table_write_policy" {
#   count = var.dynamodb_billing_mode == "PROVISIONED" ? 1 : 0
#   
#   name               = "${var.app_name}-dynamodb-write-capacity"
#   policy_type        = "TargetTrackingScaling"
#   resource_id        = aws_appautoscaling_target.dynamodb_table_write_target[0].resource_id
#   scalable_dimension = aws_appautoscaling_target.dynamodb_table_write_target[0].scalable_dimension
#   service_namespace  = aws_appautoscaling_target.dynamodb_table_write_target[0].service_namespace
# 
#   target_tracking_scaling_policy_configuration {
#     predefined_metric_specification {
#       predefined_metric_type = "DynamoDBWriteCapacityUtilization"
#     }
#     target_value = 70.0
#   }
# }

# IAM Policy for DynamoDB access
resource "aws_iam_policy" "dynamodb_access" {
  name        = "${var.app_name}-dynamodb-access"
  description = "Policy for ${var.app_name} to access DynamoDB table"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Effect   = "Allow"
        Resource = aws_dynamodb_table.main.arn
      }
    ]
  })
}

# Create a DynamoDB Stream (if enabled)
resource "aws_lambda_event_source_mapping" "dynamodb_stream" {
  count            = var.enable_dynamodb_stream && var.dynamodb_stream_lambda_arn != "" ? 1 : 0
  event_source_arn = aws_dynamodb_table.main.stream_arn
  function_name    = var.dynamodb_stream_lambda_arn
  starting_position = "LATEST"
  batch_size       = 100
  enabled          = true
}

# CloudWatch Alarms for DynamoDB
resource "aws_cloudwatch_metric_alarm" "dynamodb_throttled_requests" {
  alarm_name          = "${var.app_name}-dynamodb-throttled-requests"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ThrottledRequests"
  namespace           = "AWS/DynamoDB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors DynamoDB throttled requests"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    TableName = aws_dynamodb_table.main.name
  }
}

# Outputs
output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.main.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.main.arn
} 