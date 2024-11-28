FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt
RUN pip-audit --fix
RUN bandit -r .

COPY cert.pem /run/secrets/auction_cert_secret
COPY key.pem /run/secrets/auction_key_secret

EXPOSE 5000

ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--cert=/run/secrets/auction_cert_secret", "--key=/run/secrets/auction_key_secret"]