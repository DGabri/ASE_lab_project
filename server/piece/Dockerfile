FROM python:3.12-slim

WORKDIR /app

COPY app.py .
COPY __init__.py .
COPY DAO.py .
COPY model.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD python app.py