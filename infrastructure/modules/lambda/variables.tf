# AWS Region
variable "aws_region" {
  description = "The AWS region where resources will be created"
  type        = string
  default     = "eu-west-2"
}

# AWS Account ID
variable "aws_region" {
  description = "The AWS region where resources will be created"
  type        = string
}

# Lambda function name
variable "lambda_function_name" {
  description = "The name of the Lambda function"
  type        = string
  default     = "query-generation-function"
}

# ECR Image URI
variable "ecr_image_uri" {
  description = "The URI of the ECR image to be used by the Lambda function"
  type        = string
}

# Memory Size for Lambda
variable "memory_size" {
  description = "Amount of memory in MB your Lambda Function can use at runtime"
  type        = number
  default     = 512
}

# Timeout for Lambda Function
variable "timeout" {
  description = "The amount of time your Lambda Function has to run in seconds"
  type        = number
  default     = 180
}

# API Secret Name in Secrets Manager for Pinecone
variable "api_secret_name_pinecone" {
  description = "Name of the pinecone API key in Secrets Manager"
  type        = string
}

# API Secret Name in Secrets Manager for Hugging Face
variable "api_secret_name_hf" {
  description = "Name of the Hugging Face API key in Secrets Manager"
  type        = string
}