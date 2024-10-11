# rag_llm_example
Example code of a RAG service deployable to AWS

This includes both Dockerised functions for generating vectors to upser to a Pinecone Database and for querying that database using advanced RAG techniques.

It also includes infrastructure as code using Terraform.

You will need to set the Terraform variables in main.tf in infrastructure/setup, the variables for the s3 bucket, aws secret manager secret name and Pinecone index name in main.py of vector_generation_pipeline, and the variables for pinecone and huggingface secret names in secrets manager, pinecone index name and hugging face api if using a different embeddings model. You can also change the Bedrock foundation models but will need to update IAM permissions in the Terraform code.