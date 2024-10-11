provider "aws" {
  region = var.aws_region
}

# Create ECS Cluster
resource "aws_ecs_cluster" "fargate_cluster" {
  name = var.ecs_cluster_name
}

# IAM role for ECS Task Execution (pull from ECR, logs)
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.ecs_task_name}_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Attach policies to the ECS Task Execution Role
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Create IAM role for the Fargate task to access S3, Bedrock, and Secrets Manager
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.ecs_task_name}_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Policy allowing access to S3 buckets and Secrets Manager
resource "aws_iam_policy" "ecs_task_policy" {
  name = "${var.ecs_task_name}_policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::rag-training-lookup",
          "arn:aws:s3:::rag-training-lookup/*",
          "arn:aws:s3:::rag-training-raw-documents",
          "arn:aws:s3:::rag-training-raw-documents/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${var.api_secret_name}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach the policy to the task role
resource "aws_iam_role_policy_attachment" "ecs_task_role_policy_attachment" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.ecs_task_policy.arn
}

# Create ECS Task Definition
resource "aws_ecs_task_definition" "fargate_task" {
  family                   = var.ecs_task_name
  cpu                      = var.cpu
  memory                   = var.memory
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = var.container_name
      image     = var.ecr_image_uri
      essential = true
      memory    = var.memory

      environment = [
        {
          name  = "AWS_SECRET_API_KEY"
          value = aws_secretsmanager_secret.api_key.secret_string
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"        = var.log_group
          "awslogs-region"       = var.aws_region
          "awslogs-stream-prefix" = var.container_name
        }
      }
    }
  ])
}

# ECS Service to run the Fargate Task
resource "aws_ecs_service" "fargate_service" {
  name            = var.ecs_service_name
  cluster         = aws_ecs_cluster.fargate_cluster.id
  task_definition = aws_ecs_task_definition.fargate_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.subnets
    security_groups = var.security_groups
    assign_public_ip = true
  }
}

