from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone.grpc import PineconeGRPC
from sentence_transformers import SentenceTransformer

import boto3
import logging
import os
import pandas as pd


class PDFLoader:

    def __init__(self):
        self.file_paths = []
        self.all_chunks = []
        self.text_splitter = RecursiveCharacterTextSplitter(
                                                            chunk_size=500,
                                                            chunk_overlap=20,
                                                            length_function=len,
                                                            is_separator_regex=False,
                                                        )

    
    def retrieve_file_paths(self):
        '''Retrieve list of PDF filepaths'''

        try:
            for i in os.listdir('/tmp'):
                if i != 'readme.md':
                    self.file_paths.append([i, os.listdir('/tmp/{}'.format(i))])
        except:
            logging.error('Unable to retrieve file paths')
            raise
        
    
    def load_and_split_pdfs(self):
        '''Load pdfs into list object'''

        try:
            for i in self.file_paths:
                for j in i[1]:
                    loader = PyPDFLoader('/tmp/{}/{}'.format(i[0], j))
                    chunks = loader.load_and_split(text_splitter=self.text_splitter)
                    self.all_chunks.append(chunks)
        except:
            logging.error('Unable to load PDFs')




class EntityExtraction:
    
    def __init__(self):
        self.chunks_list = []
        self.bedrock = boto3.client('bedrock-runtime')

    
    def bedrock_interaction(self, model, prompt):
        '''Interacts with AWS bedrock using the converse method in boto3
            Params: model (str) - Model ID for model in AWS Bedrock
                    prompt (str) - Prompt to send the model'''
        
        try:
            response = self.bedrock.converse(modelId= model,
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
        
    
    def entity_extraction(self, all_chunks, model):
        '''Extract entities from chunks of text using AWS Bedrock
            Params: all_chunks (list) - List of text chunks in document format from langchain loader'''
        
        for i in all_chunks:
            for j in i:

                try:
                    chunk = j.page_content
                    source = j.metadata['source']


                    prompt = '''Provide a comma separated list of unique entities (organisation, person, league, place etc.) found in this text:

                                {}

                                Output the requested results in the following format - entity 1, entity 2, entity 3, entity n'''.format(chunk)
                    

                    bedrock_response = self.bedrock_interaction(model = model, prompt= prompt)

                    entities = bedrock_response.split(', ')

                    self.chunks_list.append([chunk, source, entities])
                
                except:
                    logging.error('Unable to extract entities')




class MetadataExtraction:

    def __init__(self, chunks_list):

        self.chunks_list = chunks_list
        self.metadata_list = []
        self.chunks_df = None


    def club_select(self, source):
        '''Method for matching clubs from source string
            Params: source (str) - source filepath'''
        
        try:
            for element in source.split('_'):
                match element:
                    case "Arsenal":
                        return 'Arsenal'
                    case "Chelsea":
                        return 'Chelsea'
                    case "Liverpool":
                        return 'Liverpool'
                    case "Manchester":
                        return "Manchester_United"
        
        except:
            logging.error("Unable to select club from source")
            raise
    

    def metadata_extraction(self):
        '''Extracts metadata from filepath'''

        for i in self.chunks_list:
            try:
                chunk_year = os.path.dirname(i.source)[-4:]
                club = self.club_select(i.source)

                self.metadata_list.append([chunk_year, club])
            
            except:
                logging.error("Unable to extract metadata for {}".format(i))

    
    def chunks_dataframe_creation(self):
        '''Concatenates the chunks and metadata lists into a pandas dataframe and generates a unique id for each chunk'''

        try:
            self.chunks_df = pd.DataFrame(self.chunks_list)
            metadata_df = pd.DataFrame(self.metadata_list)

            self.chunks_df = pd.concat([self.chunks_df, metadata_df], ignore_index= True)

            self.chunks_df['rn'] = self.chunks_df.groupby(['year', 'club']).cumcount()+1
            self.chunks_df['id'] = self.chunks_df['year'].astype(str) + '-' + self.chunks_df['club'] + '-' + self.chunks_df['rn'].astype(str)

            logging.info("Chunks dataframe created")

        except:
            logging.error("Unable to create chunks dataframe")   




class VectorGeneration:

    def __init__(self, chunks_df):
        self.chunks_df = chunks_df

    
    def vector_generation(self, encoding_model):
        '''Generates vectors for chunks in a given dataframe with the provide model
            Params: encoding_model (str): Sentence Transformers model name'''
        
        model = SentenceTransformer(encoding_model)

        try:
            self.chunks_df['vector'] = self.chunks_df['chunk'].apply(lambda x: model.encode(x))
            logging.info("Vectors created")
        
        except:
            logging.error('Unable to create vectors')




class PineconeUpsert:

    def __init__(self, chunks_df):

        self.chunks_df = chunks_df

    def pinecone_upsert(self, pinecone_api, index_name):
        '''Upserts data from chunks_df into given pinecone index
            Params: pinecone_api (str) - api key for pinecone instance
                    index_name (str) - name of pinecone index'''
        

        pc = PineconeGRPC(api_key=pinecone_api)
        index = pc.Index(index_name)


        # Break into 100 entry chunks and batch upsert to Pinecone

        try:
            start = 0
            end = 99

            while end <= len(self.chunks_df):
                print(start, end)

                ids_batch = [ self.chunks_df['id'][i] for i in range(start, end)]
                embeds = [self.chunks_df['vector'][x] for x in range(start, end)]
                meta_batch = [{
                        "year" : self.chunks_df['year'][y],
                        "club" : self.chunks_df['club'][y],
                        "entities" : self.chunks_df['entities'][y],
                        "text" : self.chunks_df['chunk'][y]
                    } for y in range(start, end)]
                to_upsert = list(zip(ids_batch, embeds, meta_batch))
                index.upsert(vectors=to_upsert)

                start = start + 100
                end = end + 100

                if end >= len(self.chunks_df):
                    end = len(self.chunks_df)

                    ids_batch = [ self.chunks_df['id'][i] for i in range(start, end)]
                    embeds = [self.chunks_df['vector'][x] for x in range(start, end)]
                    meta_batch = [{
                            "year" : self.chunks_df['year'][y],
                            "club" : self.chunks_df['club'][y],
                            "entities" : self.chunks_df['entities'][y],
                            "text" : self.chunks_df['chunk'][y]
                        } for y in range(start, end)]
                    to_upsert = list(zip(ids_batch, embeds, meta_batch))
                    index.upsert(vectors=to_upsert)

                    break

            logging.info("Upsert to Pinecone complete")
        
        except:
            logging.error("Unable to upsert to Pinecone")

