# RDS Database Instance
resource "aws_db_instance" "main" {
  identifier           = "${var.app_name}-${var.environment}"
  allocated_storage    = var.db_allocated_storage
  storage_type         = "gp3"
  engine               = var.db_engine
  engine_version       = var.db_engine_version
  instance_class       = var.db_instance_class
  username             = var.db_username
  password             = var.db_password
  parameter_group_name = aws_db_parameter_group.main.name
  db_subnet_group_name = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  # Database name - optional for some engines like Oracle or SQL Server
  db_name              = var.db_name != "" ? var.db_name : null
  
  # Backup configuration
  backup_retention_period = var.db_backup_retention_period
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"
  
  # Multi-AZ deployment for high availability
  multi_az = var.db_multi_az
  
  # Performance Insights
  performance_insights_enabled = var.db_performance_insights_enabled
  performance_insights_retention_period = var.db_performance_insights_enabled ? 7 : 0
  
  # Enhanced monitoring
  monitoring_interval = var.db_monitoring_interval
  monitoring_role_arn = var.db_monitoring_interval > 0 ? aws_iam_role.rds_enhanced_monitoring[0].arn : null
  
  # Auto minor version upgrade
  auto_minor_version_upgrade = true
  
  # Storage encryption
  storage_encrypted = true
  
  # Deletion protection
  deletion_protection = var.environment == "prod" ? true : false
  
  # Skip final snapshot in non-production environments
  skip_final_snapshot = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "${var.app_name}-${var.environment}-final" : null
  
  # Automatic deletion of automated backups
  delete_automated_backups = var.environment != "prod"
  
  # Publicly accessible
  publicly_accessible = false
  
  # Apply immediately in non-production environments
  apply_immediately = var.environment != "prod"
  
  tags = {
    Name        = "${var.app_name}-database"
    Environment = var.environment
  }
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-${var.environment}-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  
  tags = {
    Name        = "${var.app_name}-subnet-group"
    Environment = var.environment
  }
}

# DB Parameter Group
resource "aws_db_parameter_group" "main" {
  name   = "${var.app_name}-${var.environment}-parameter-group"
  family = "${var.db_engine}${length(regexall("^[0-9]+", var.db_engine_version)) > 0 ? regexall("^[0-9]+", var.db_engine_version)[0] : var.db_engine_version}"
  
  # Common parameters
  parameter {
    name  = "character_set_server"
    value = "utf8"
  }
  
  parameter {
    name  = "character_set_client"
    value = "utf8"
  }
  
  # MySQL specific parameters
  dynamic "parameter" {
    for_each = var.db_engine == "mysql" ? [1] : []
    content {
      name  = "max_connections"
      value = var.db_max_connections
    }
  }
  
  # PostgreSQL specific parameters
  dynamic "parameter" {
    for_each = var.db_engine == "postgres" ? [1] : []
    content {
      name  = "max_connections"
      value = var.db_max_connections
    }
  }
  
  tags = {
    Name        = "${var.app_name}-parameter-group"
    Environment = var.environment
  }
}

# DB Security Group
resource "aws_security_group" "rds" {
  name        = "${var.app_name}-${var.environment}-rds-sg"
  description = "Security group for RDS database"
  vpc_id      = aws_vpc.main.id
  
  # MySQL port
  dynamic "ingress" {
    for_each = var.db_engine == "mysql" ? [1] : []
    content {
      from_port   = 3306
      to_port     = 3306
      protocol    = "tcp"
      security_groups = var.allowed_security_groups
    }
  }
  
  # PostgreSQL port
  dynamic "ingress" {
    for_each = var.db_engine == "postgres" ? [1] : []
    content {
      from_port   = 5432
      to_port     = 5432
      protocol    = "tcp"
      security_groups = var.allowed_security_groups
    }
  }
  
  # Oracle port
  dynamic "ingress" {
    for_each = var.db_engine == "oracle-ee" || var.db_engine == "oracle-se2" ? [1] : []
    content {
      from_port   = 1521
      to_port     = 1521
      protocol    = "tcp"
      security_groups = var.allowed_security_groups
    }
  }
  
  # SQL Server port
  dynamic "ingress" {
    for_each = var.db_engine == "sqlserver-ex" || var.db_engine == "sqlserver-se" || var.db_engine == "sqlserver-ee" ? [1] : []
    content {
      from_port   = 1433
      to_port     = 1433
      protocol    = "tcp"
      security_groups = var.allowed_security_groups
    }
  }
  
  # MariaDB port
  dynamic "ingress" {
    for_each = var.db_engine == "mariadb" ? [1] : []
    content {
      from_port   = 3306
      to_port     = 3306
      protocol    = "tcp"
      security_groups = var.allowed_security_groups
    }
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name        = "${var.app_name}-rds-sg"
    Environment = var.environment
  }
}

# Enhanced Monitoring Role
resource "aws_iam_role" "rds_enhanced_monitoring" {
  count = var.db_monitoring_interval > 0 ? 1 : 0
  
  name = "${var.app_name}-${var.environment}-rds-monitoring-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name        = "${var.app_name}-rds-monitoring-role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  count = var.db_monitoring_interval > 0 ? 1 : 0
  
  role       = aws_iam_role.rds_enhanced_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# CloudWatch Alarms for RDS
resource "aws_cloudwatch_metric_alarm" "rds_cpu_utilization" {
  alarm_name          = "${var.app_name}-${var.environment}-rds-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
  
  tags = {
    Name        = "${var.app_name}-rds-cpu-alarm"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_free_storage_space" {
  alarm_name          = "${var.app_name}-${var.environment}-rds-free-storage-space"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.db_allocated_storage * 1024 * 1024 * 1024 * 0.2  # 20% of allocated storage in bytes
  alarm_description   = "This metric monitors RDS free storage space"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
  
  tags = {
    Name        = "${var.app_name}-rds-storage-alarm"
    Environment = var.environment
  }
}

# Outputs
output "db_instance_endpoint" {
  description = "The connection endpoint for the RDS instance"
  value       = aws_db_instance.main.endpoint
}

output "db_instance_name" {
  description = "The database name"
  value       = aws_db_instance.main.db_name
}

output "db_instance_username" {
  description = "The master username for the database"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "db_instance_port" {
  description = "The database port"
  value       = aws_db_instance.main.port
} 