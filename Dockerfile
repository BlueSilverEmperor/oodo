FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port 5000
EXPOSE 5000

# Start production gunicorn WSGI server
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
