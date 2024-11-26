FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt
RUN pip-audit --fix 
RUN bandit -r .

EXPOSE 5000

CMD flask run --host=0.0.0.0 --port=5000