FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt
RUN pip-audit --fix 
RUN bandit -r .

COPY cert.pem /run/secrets/banner_cert_secret
COPY key.pem /run/secrets/banner_key_secret

EXPOSE 5000

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["./start.sh"]
