FROM python:3.9-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY app/ ./app/
COPY run.py .
COPY samples/ ./samples/
COPY uploads/ ./uploads/

# Create necessary directories
RUN mkdir -p output_logs

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "run.py"]
