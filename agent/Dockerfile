FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose SSH port and Web port
EXPOSE 2222 80

CMD ["python", "main.py"]
