# Usa una immagine base di Python
FROM python:3.12-slim

# Imposta la directory di lavoro all'interno del container
WORKDIR /app

# Copia i file del progetto all'interno del container
COPY . /app

# Installa le dipendenze
RUN pip install -r requirements.txt

# Esponi la porta su cui Flask esegue il server
EXPOSE 5005

# Comando per avviare il server Flask
CMD ["python", "app.py"]
