FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 5005

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["./start.sh"]
