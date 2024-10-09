from pinecone.grpc import PineconeGRPC as Pinecone

import boto3
import json
import logging
import requests


class ExternalInteractions:

    @staticmethod
    def bedrock_interaction(model, prompt):
            '''Interacts with AWS bedrock using the converse method in boto3
                Params: model (str) - Model ID for model in AWS Bedrock
                        prompt (str) - Prompt to send the model'''
            
            bedrock = boto3.client('bedrock-runtime')
            
            try:
                response = bedrock.converse(modelId= model,
                                            messages= [{
                                                    'role': 'user',
                                                    'content': [
                                                        {
                                                            'text': prompt
                                                            }
                                                            ]
                                                        }])
                
                bedrock_response = response['output']['message']['content'][0]['text']

                return bedrock_response

            except:
                logging.error('Unable to get response from bedrock')
                raise


    @staticmethod
    def huggingface_query(payload, hf_api_url, hf_token):
        '''Passes a string to the given hugging face API and returns response as JSON
        Params: payload (str)- Query to pass to hugging face model
                hf_api_url (str)- API endpoint for hugging face model
                hf_token (str)- API key for hugging face access'''
        
        headers = {"Authorization": "Bearer {}".format(hf_token)}
        response = requests.post(hf_api_url, headers=headers, json=payload)
        return response.json()


    @staticmethod
    def pinecone_query(query_vector, query_filter, pinecone_api, pinecone_index):
                    
        pc = Pinecone(api_key=pinecone_api)
        index = pc.Index(pinecone_index)

        query_response = index.query(
            vector=query_vector,
            filter=query_filter,
            top_k=30,
            include_metadata=True # Include metadata in the response.
        )

        return query_response



# Subquery Generation
class SubqueryGeneration:

    def __init__(self, model, user_query):
        self.model = model
        self.user_query = user_query
        self.decomposition_json = None


    def generate_subqueries(self):
        '''Uses a LLM to break down the user query into subqueries more suitable for vector retrieval'''

        subquery_prompt = """You are an expert at converting user questions into sub-queries for retrieving relevant information from a vector database, taking context from your training data. Perform query decomposition. Given a user question, break it down into distinct sub questions that you need to answer in order to answer the original question. If there are acronyms or words you are not familiar with, do not try to rephrase them.
        {}""".format(self.user_query)

        output_format_instructions = """
        Output only the requested results in the following format:
        {"1" : "question", "2" : "question", "3" : "question"}"""

        decomposition_prompt = subquery_prompt + output_format_instructions

        try:
            decomposition = ExternalInteractions.bedrock_interaction(model=self.model, prompt=decomposition_prompt)
            self.decomposition_json = json.loads(decomposition)
        
        except:
            try:
                decomposition = ExternalInteractions.bedrock_interaction(model=self.model, prompt=decomposition_prompt)
                self.decomposition_json = json.loads(decomposition)
        
            except:
                logging.error("Unable to generate subqueries JSON")
                raise


# Metadata Filtering
class MetadataFiltering:

    def __init__(self, user_query):
        self.user_query = user_query
        self.years = None
        self.clubs = None


    def years_extraction(self, model):
        '''Extracts any year specified in the user query'''

        try:
            year_prompt = """Extract the year from this question:

            {}

            Output should only be years as a comma separated list. If no year found, output None""".format(self.user_query)

            self.years = ExternalInteractions.bedrock_interaction(model=model, prompt=year_prompt)
        
        except:
            logging.warning("Unable to extract years from question")
            self.years = None


    def club_extraction(self, model):
        '''Extracts any club specified in the user query'''

        club_prompt =  """Extract the club from this question:

        {}

        Output should only be clubs as a comma separated list. If no club found, output None""".format(self.user_query)

        try:
            self.clubs = ExternalInteractions.bedrock_interaction(model=model, prompt=club_prompt)

        except:
            logging.warning("Unable to extract clubs from question")
            self.clubs = None




# Entity Extraction
class EntityExtraction:

    def __init__(self, entity_list_bucket, entity_list_key):
        self.entity_list_bucket = entity_list_bucket
        self.entity_list_key = entity_list_key
        self.entity_list = None
        self.query_entities = None


    def retrieve_lookup_list(self):
        '''Retrieves list of entities generated on upsert of data into vector database held in s3'''

        try:
            s3 = boto3.client('s3')

            s3.download_file(self.entity_list_bucket, self.entity_list_key, '../tmp/{}'.format(self.entity_list_key))

            with open('../tmp/{}'.format(self.entity_list_key)) as f:
                self.entity_list = json.load(f)

        except:
            logging.error("Unable to retrieve entity list from {}/{}".format(self.entity_list_bucket, self.entity_list_key))
            raise
    
    
    def entity_extraction(self, model):
        '''Extracts any entities in user queries that match the retrieved list'''

        entity_prompt = """Match any entities from this question that appear in the list below:

        Question - {}


        List - {}


        Output should only be entities as a comma separated list and no other preamble. If no entities found, output None""".format(self.user_query, self.entity_list)

        try:
            self.query_entities = ExternalInteractions.bedrock_interaction(model=model, prompt=entity_prompt)

        except:
            logging.warning("Unable to extract any entities from user query")
            self.query_entities = None


class QueryEncoding:

    def __init__(self, decomposition_json, hf_api_url, hf_token):
        self.decomposition_json = decomposition_json
        self.hf_api_url = hf_api_url
        self.hf_token = hf_token
        self.user_query_vector = None
        self.decmposition_vector_list = []

    
    def original_query_encoding(self):
        '''Encodes the original query into an embedding/vector based on the given Hugging Face Model URL'''

        try:
            self.user_query_vector = ExternalInteractions.huggingface_query(payload={"inputs": user_query}, hf_api_url=self.hf_api_url, hf_token=self.hf_token)
        except:
            logging.error("Unable to encode original query")
            raise
    

    def subquery_encoding(self):
        '''Encodes the subqueries into an embedding/vector based on the given Hugging Face Model URL'''

        try:
            for i in self.decomposition_json:
	
                subquery_output = ExternalInteractions.huggingface_query(payload={"inputs": self.decomposition_json[i]}, hf_api_url=self.hf_api_url, hf_token=self.hf_token)
                
                self.decomposition_vector_list.append(subquery_output)
        
        except:
            logging.error("Unable to encode subqueries")
            raise



class VectorRetrieval:

    def __init__(self, user_query_vector, decomposition_vector_list, years, clubs, entity_list):
        self.context_list = []
        self.user_query_vector = user_query_vector
        self.decomposition_vector_list = decomposition_vector_list
        self.years = years
        self.clubs = clubs
        self.entity_list = entity_list


    
    def build_context_list(self):
        '''Creates a context list to power retrieval augmented generation based on the filters and subqueries previously generated'''


        # Original user query

        try:

            original_query_response = ExternalInteractions.pinecone_query(query_vector=self.user_query_vector, query_filter= {})

            for i in original_query_response['matches']:
                self.context_list.append(i['metadata']['text'])
        
        except:
            
            logging.error("Unable to retrieve matched vectors for original query")
            raise

        # Decomposition Queries

        try:
            for j in self.decomposition_vector_list:

                decomposition_response = ExternalInteractions.pinecone_query(query_vector=j, query_filter= {})

                for k in decomposition_response['matches']:
                    self.context_list.append(k['metadata']['text'])
        
        except:
            
            logging.error("Unable to retrieve matched vectors for subqueries")
            raise


        # Original query with years filter

        try:
            if self.years != None:

                years_list = self.years.split(', ')

                original_query_response_years = ExternalInteractions.pinecone_query(query_vector=self.user_query_vector, query_filter= {"year": {"$in":years_list}})

                for l in original_query_response_years['matches']:
                    self.context_list.append(l['metadata']['text'])
        
        except:
            
            logging.error("Unable to retrieve matched vectors for years filter")
            raise

        
        # Original query with clubs filter

        try:

            if self.clubs != None:

                clubs_list = self.clubs.split(', ')

                original_query_response_clubs = ExternalInteractions.pinecone_query(query_vector=self.user_query_vector, query_filter= {"club": {"$in":clubs_list}})

                for m in original_query_response_clubs['matches']:
                    self.context_list.append(m['metadata']['text'])
        
        except:
            
            logging.error("Unable to retrieve matched vectors for clubs filter")
            raise

        
        # Original query with entities filter

        try:

            if self.entities != None:

                query_entities_list = self.entity_list.split(', ')

                original_query_response_entities = ExternalInteractions.pinecone_query(query_vector=self.user_query_vector, query_filter= {"entities": {"$in":query_entities_list}})

                for m in original_query_response_entities['matches']:
                    self.context_list.append(m['metadata']['text'])
        
        except:
            
            logging.error("Unable to retrieve matched vectors for entities filter")
            raise



class GenerateFinalAnswer:

    def __init__(self, user_query, context_list):
        self.user_query = user_query
        self.context_list = context_list
        self.answer = None

    
    def generate_answer(self, model):
        '''Passes original query and context list to LLM to generate a final answer'''

        final_prompt = '''Answer the following question, prioritising information from the context below:
                    
                    Question - {}
                    
                    Context - {}'''.format(self.user_query, self.context_list)

        try:
            self.answer = ExternalInteractions.bedrock_interaction(model=model, prompt=final_prompt)
        
        except:
            try:
                self.answer = ExternalInteractions.bedrock_interaction(model=model, prompt=final_prompt)
            
            except:
                logging.error("Unable to generate final answer")
                raise
