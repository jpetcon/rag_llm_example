# AWS region
variable "aws_region" {
  description = "The AWS region"
  type        = string
  default     = "us-east-1"
}

# AWS account ID
variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

# ECS Cluster Name
variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
  default     = "fargate-cluster"
}

# ECS Task Definition Name
variable "ecs_task_name" {
  description = "Name of the ECS task"
  type        = string
  default     = "fargate-task"
}

# ECS Service Name
variable "ecs_service_name" {
  description = "Name of the ECS service"
  type        = string
  default     = "fargate-service"
}

# Container Name
variable "container_name" {
  description = "Name of the container"
  type        = string
  default     = "fargate-container"
}

# ECR Image URI
variable "ecr_image_uri" {
  description = "The URI of the Docker image in ECR"
  type        = string
}

# Memory size for Fargate Task
variable "memory" {
  description = "The amount of memory in MiB"
  type        = number
  default     = 512
}

# CPU size for Fargate Task
variable "cpu" {
  description = "The amount of CPU in vCPU units"
  type        = number
  default     = 256
}

# Log Group
variable "log_group" {
  description = "Log group for ECS logs"
  type        = string
  default     = "/ecs/fargate"
}

# Subnet IDs
variable "subnets" {
  description = "List of subnet IDs for ECS tasks"
  type        = list(string)
}

# Security Group IDs
variable "security_groups" {
  description = "List of security group IDs for the ECS task"
  type        = list(string)
}

# API Secret Name in Secrets Manager for Pinecone
variable "api_secret_name_pinecone" {
  description = "Name of the pinecone API key in Secrets Manager"
  type        = string
}
