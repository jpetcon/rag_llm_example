# AWS Region
variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "eu-west-2"
}

# Lambda Function Name
variable "lambda_function_name" {
  description = "The name of the Lambda function to be triggered"
  type        = string
  default     = "query-generation-function"
}

# API Name
variable "api_name" {
  description = "The name of the API Gateway"
  type        = string
  default     = "QueryGenerationAPI"
}

# API Path
variable "api_path" {
  description = "The resource path for the API Gateway"
  type        = string
  default     = "query"
}

# API Stage Name
variable "stage_name" {
  description = "The stage name for the API Gateway deployment"
  type        = string
  default     = "dev"
}
