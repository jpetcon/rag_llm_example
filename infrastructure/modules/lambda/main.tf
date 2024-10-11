terraform {
  required_version = ">= 1.0.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Lambda Execution Role
resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.lambda_function_name}_execution_role"
  
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
}


# Allow Secrets Manager Access
resource "aws_iam_role_policy" "sm_policy" {
  name = "sm_access_permissions"
  role = aws_iam_role.lambda_execution_role.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue",
        ]
        Effect   = "Allow"
        Resource = ["arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${var.api_secret_name_pinecone}", 
                    "arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${var.api_secret_name_hf}"]
      },
    ]
  })
}

# Allow Access to specified Bedrock Models
resource "aws_iam_role_policy" "bedrock_policy" {
  name = "bedrock_access_permissions"
  role = aws_iam_role.lambda_execution_role.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "bedrock:InvokeModel",
        ]
        Effect   = "Allow"
        Resource = ["arn:aws:bedrock:eu-west-2::foundation-model/anthropic.claude-3-haiku-20240307-v1:0", "arn:aws:bedrock:eu-west-2::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"]
      },
    ]
  })
}


# Allow Access to specified S3 Buckets
resource "aws_iam_role_policy" "s3_policy" {
  name = "s3_access_permissions"
  role = aws_iam_role.lambda_execution_role.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          "arn:aws:s3:::rag-training-lookup",
          "arn:aws:s3:::rag-training-lookup/*"
        ]
      }
    ]
  })
}


resource "aws_iam_role_policy_attachment" "lambda_logging_policy" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}


# Lambda function
resource "aws_lambda_function" "query_generation_function" {
  function_name = var.lambda_function_name
  role          = aws_iam_role.lambda_execution_role.arn
  package_type  = "Image"

  architectures = ["arm64"]
  image_uri     = var.ecr_image_uri
  timeout       = var.timeout
  memory_size   = var.memory_size
  maximum_retry_attempts = 2

}