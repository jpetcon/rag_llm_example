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
  region = "eu-west-2"
}


module "s3-bucket-generation"{
    source = "../modules/s3"
}

module "lambda-query-generation"{
    source = "../modules/lambda"

    ecr_image_uri = ""
}

module "ecs-vector-generation-pipeline"{
    source = "../modules/ecs"

    aws_account_id = ""
    ecr_image_uri = ""
    subnets = ""
    security_groups = ""
    api_secret_name_pinecone = ""

}

module "query-api-gateway"{
    source = "../modules/api-gateway"
}