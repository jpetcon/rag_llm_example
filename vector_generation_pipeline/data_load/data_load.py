from abc import ABC, abstractmethod

import boto3
import logging
import os


class AbstractDataLoad(ABC):
    
    @abstractmethod
    def list_files(self):
        pass

    @abstractmethod
    def load_data(self):
        pass


class S3DataLoad(AbstractDataLoad):

    def __init__(self):
        self.file_list = None
        self.directory_list = []
        self.s3 = boto3.client('s3')

    def list_files(self, s3_bucket):
        '''Lists files in given S3 bucket
            
            params - s3_bucket (str) : Name of S3 bucket'''
        
        try:
            self.file_list = self.s3.list_objects(Bucket = s3_bucket)
            logging.info('S3 file list loaded')
        
        except:
            logging.error('Unable to obtain S3 file list')
            raise

    
    def create_tmp_directories(self):
        '''Creates directories in tmp directory to download files'''

        for i in self.file_list['Contents']:
            self.directory_list.append(os.path.dirname(i['Key']))

        self.directory_list = list(dict.fromkeys(self.directory_list)) # Deduplicate directory list


        for j in self.directory_list:
            os.mkdir('/tmp/{}'.format(j))
        
    
    def load_data(self, s3_bucket):
        '''Loads data from S3 and stores within a temp directory'''

        for i in self.file_list['Contents']:

            try:
                self.s3.download_file(s3_bucket, i['Key'], '/tmp/{}'.format(i['Key']))
                logging.info("{} downloaded".format(i['Key']))
            
            except:
                logging.error("Unable to download file {}".format(i['Key']))
   
        
