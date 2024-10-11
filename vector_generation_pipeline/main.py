import data_load.data_load as dl
import data_vectorisation.vectorise as vec

def main():

  # Load data from S3 bucket to temp file

  s3_data_load = dl.S3DataLoad()
  s3_data_load.list_files(s3_bucket='')
  s3_data_load.create_tmp_directories()
  s3_data_load.load_data(s3_bucket='')


  # Convert PDF data to vectors and upsert to Pinecone database

  pdf = vec.PDFLoader()
  pdf.retrieve_file_paths()
  pdf.load_and_split_pdfs()

  entities = vec.EntityExtraction()
  entities.entity_extraction(all_chunks=pdf.all_chunks, model ='anthropic.claude-3-haiku-20240307-v1:0')

  metadata = vec.MetadataExtraction(chunks_list = entities.chunks_list)
  metadata.metadata_extraction()
  metadata.chunks_dataframe_creation()

  vectors = vec.VectorGeneration(chunks_df = metadata.chunks_df)
  vectors.vector_generation(encoding_model = 'bge-small-en-v1.5') # Must match the model used to encode queries

  upsert = vec.PineconeUpsert(chunks_df = vectors.chunks_df)
  upsert.pinecone_upsert(pinecone_secret_name='', index_name = '')


if __name__ == "__main__":
        main()
  
  
