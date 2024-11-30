FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt
RUN pip-audit --fix
RUN bandit -r .

COPY cert.pem /run/secrets/user_cert_secret
COPY key.pem /run/secrets/user_key_secret

EXPOSE 5000

ENV FLASK_ENV=development
ENV FLASK_DEBUG=1
ENV FLASK_APP=app.py

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--reload", "--cert=/run/secrets/user_cert_secret", "--key=/run/secrets/user_key_secret"]