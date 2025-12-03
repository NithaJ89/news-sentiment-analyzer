FROM python:3.10-slim

# Install basic utilities
RUN apt-get update && apt-get install -y libpq-dev gcc

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8051

CMD ["streamlit", "run", "app.py", "--server.port=8051", "--server.address=0.0.0.0"]
