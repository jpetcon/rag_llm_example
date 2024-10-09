import json
import query_generation.query_generation as qg


def main(event, context):
  '''Main function for generating RAG answer'''

  user_query = event['user_query']

  # Generate Subqueries
  subqueries = qg.SubqueryGeneration(model='anthropic.claude-3-haiku-20240307-v1:0', user_query=user_query)
  subqueries.generate_subqueries()
  subqueries.decomposition_json


  #Extract Metadata
  metadata = qg.MetadataFiltering(user_query=user_query)
  metadata.years_extraction(model='anthropic.claude-3-haiku-20240307-v1:0')
  metadata.club_extraction(model='anthropic.claude-3-haiku-20240307-v1:0')
  

  #Extract Entities
  entities = qg.EntityExtraction(entity_list_bucket='rag-training-lookup', entity_list_key='entity-list.json', user_query=user_query)
  entities.retrieve_lookup_list()
  entities.entity_extraction(model='anthropic.claude-3-haiku-20240307-v1:0')
  

  #Encode Query and Subqueries
  encoding = qg.QueryEncoding(decomposition_json=subqueries.decomposition_json, hf_api_url= 'https://api-inference.huggingface.co/models/BAAI/bge-small-en-v1.5', hf_token=, user_query=user_query)
  encoding.original_query_encoding()
  encoding.subquery_encoding()
  

  #Retrieve Matched Vectors from Vector Database
  retrieval = qg.VectorRetrieval(user_query_vector=encoding.user_query_vector, decomposition_vector_list=encoding.decomposition_vector_list, years=metadata.years, clubs=metadata.clubs, entity_list=entities.query_entities, pinecone_api=, pinecone_index=)
  retrieval.build_context_list()
  

  #Generate Final Answer
  generation = qg.GenerateFinalAnswer(user_query=user_query, context_list=retrieval.context_list)
  generation.generate_answer(model='anthropic.claude-3-sonnet-20240229-v1:0')


  return{
    'statusCode': 200,
    'body': json.dumps(generation.answer)
  }
  
