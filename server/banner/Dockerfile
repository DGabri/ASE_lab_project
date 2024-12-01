FROM python:3.12-slim

WORKDIR /app

COPY app.py .
COPY config.json .
COPY requirements.txt .
COPY classes ./classes
COPY DAOs ./DAOs
COPY db ./db
COPY schemes ./schemes
COPY cert.pem /run/secrets/banner_cert_secret
COPY key.pem /run/secrets/banner_key_secret

RUN pip install -r requirements.txt
RUN pip-audit --fix 
RUN bandit -r .

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--reload", "--cert=/run/secrets/banner_cert_secret", "--key=/run/secrets/banner_key_secret"]