FROM public.ecr.aws/lambda/python:3.8
COPY main.py .
COPY query_generation/ .
COPY tmp/ tmp/
COPY requirments.txt requirements.txt
RUN pip install -r requirements.txt
CMD [ "main.main" ]
