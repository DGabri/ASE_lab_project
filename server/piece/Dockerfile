FROM python:3.12-slim

WORKDIR /app

COPY app.py .
COPY DAOs/ .
COPY models/ .
COPY schemes/ .
COPY requirements.txt .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD python app.py