FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt
RUN pip-audit --fix
RUN bandit -r .

COPY cert.pem /run/secrets/banner_cert_secret
COPY key.pem /run/secrets/banner_key_secret

EXPOSE 80

ENV FLASK_ENV=development
ENV FLASK_DEBUG=1
ENV FLASK_APP=app.py

CMD ["flask", "run", "--host=0.0.0.0", "--port=80", "--reload", "--cert=/run/secrets/admin_gateway_cert_secret", "--key=/run/secrets/admin_gateway_key_secret"]