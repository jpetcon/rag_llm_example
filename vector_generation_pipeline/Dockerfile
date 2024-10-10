FROM python:3.9
COPY data_load/ .
COPY data_vectorisation/ .
COPY tmp/ .
COPY main.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
CMD [ "python", "-u", "main.py" ]
