provider "aws" {
  region = var.aws_region
}

# S3 Raw Data Bucket Creation
resource "aws_s3_bucket" "rag_training_raw" {
  bucket = "rag-training-raw-documents"


  # Enable default server-side encryption
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  # Define bucket ACL (private by default)
  acl = "private"
}

# Add a bucket policy to restrict public access
resource "aws_s3_bucket_policy" "rag_training_raw_policy" {
  bucket = "rag-training-raw-documents"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "s3:*"
        Effect    = "Deny"
        Principal = "*"
        Resource  = [
          "arn:aws:s3:::rag-training-raw-documents",
          "arn:aws:s3:::rag-training-raw-documents/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}


# S3 Lookup Bucket Creation
resource "aws_s3_bucket" "rag_training_lookup" {
  bucket = "rag-training-lookup"


  # Enable default server-side encryption
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  # Define bucket ACL (private by default)
  acl = "private"
}

# Add a bucket policy to restrict public access
resource "aws_s3_bucket_policy" "rag_training_lookup_policy" {
  bucket = "rag-training-lookup"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "s3:*"
        Effect    = "Deny"
        Principal = "*"
        Resource  = [
          "arn:aws:s3:::rag-training-lookup",
          "arn:aws:s3:::rag-training-lookup/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}
