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


resource "aws_iam_role_policy_attachment" "lambda_logging_policy" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}


# Lambda function
resource "aws_lambda_function" "query_generation_function" {
  function_name = var.lambda_function_name
  role          = aws_iam_role.lambda_execution_role.arn
  package_type  = "Image"

  image_uri     = var.ecr_image_uri
  timeout       = var.timeout
  memory_size   = var.memory_size

}