FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY gps_simulator.py .

CMD ["python", "gps_simulator.py", "--host", "mosquitto", "--port", "1883", "--interval", "2.0", "--loops", "0"]
