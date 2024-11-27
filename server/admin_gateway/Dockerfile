FROM python:3.12-slim

WORKDIR /app

COPY . .
COPY requirements.txt .

RUN pip install -r requirements.txt
RUN pip-audit --fix
RUN bandit -r .

EXPOSE 80

ENV FLASK_ENV=development
ENV FLASK_DEBUG=1
ENV FLASK_APP=app.py

CMD ["flask", "run", "--host=0.0.0.0", "--port=80", "--reload"]