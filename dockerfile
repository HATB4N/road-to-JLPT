FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/
COPY data/ data/

EXPOSE 80

CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]
