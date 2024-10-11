provider "aws" {
  region = var.aws_region
}

# IAM Policy for API Gateway to invoke the Lambda function
resource "aws_lambda_permission" "api_gateway_invoke_lambda" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = data.aws_lambda_function.query_generation_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api_gw.execution_arn}/*/*"
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "api_gw" {
  name        = var.api_name
  description = "API Gateway to trigger ${var.lambda_function_name} via GET request"
}

# Resource for the root path ("/")
resource "aws_api_gateway_resource" "api_resource" {
  rest_api_id = aws_api_gateway_rest_api.api_gw.id
  parent_id   = aws_api_gateway_rest_api.api_gw.root_resource_id
  path_part   = var.api_path
}

# Method for GET requests
resource "aws_api_gateway_method" "api_method" {
  rest_api_id   = aws_api_gateway_rest_api.api_gw.id
  resource_id   = aws_api_gateway_resource.api_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

# Integration between API Gateway and Lambda
resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.api_gw.id
  resource_id             = aws_api_gateway_resource.api_resource.id
  http_method             = aws_api_gateway_method.api_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${data.aws_lambda_function.query_generation_function.arn}/invocations"
}

# Deployment of the API Gateway
resource "aws_api_gateway_deployment" "api_deployment" {
  depends_on = [
    aws_api_gateway_integration.lambda_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.api_gw.id
  stage_name  = var.stage_name
}

# Output the API Gateway invoke URL
output "api_invoke_url" {
  description = "The URL to invoke the API Gateway"
  value       = "${aws_api_gateway_rest_api.api_gw.execution_arn}/${var.stage_name}/${var.api_path}"
}

# Reference the existing Lambda function (Data Source)
data "aws_lambda_function" "query_generation_function" {
  function_name = var.lambda_function_name
}
