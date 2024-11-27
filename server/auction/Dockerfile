FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt
RUN pip-audit --fix 
RUN bandit -r .

EXPOSE 5000

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["./start.sh"]
