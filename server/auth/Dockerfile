#FROM python:3.12-slim

#WORKDIR /app

#COPY . .
#COPY requirements.txt .

#RUN pip install -r requirements.txt

#EXPOSE 5000

#CMD flask run --host=0.0.0.0 --port=5000

FROM python:3.12-slim

WORKDIR /app

COPY . .
COPY requirements.txt .

RUN pip install -r requirements.txt

EXPOSE 5000

ENV FLASK_ENV=development
ENV FLASK_DEBUG=1
ENV FLASK_APP=app.py

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--reload"]