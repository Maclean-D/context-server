FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV UVICORN_RELOAD false # Default to false for Docker environments

WORKDIR /app

# Create a virtual environment
RUN python -m venv /app/venv
# Add venv to PATH
ENV PATH="/app/venv/bin:$PATH"

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
# Activate virtual environment and install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# Copy only necessary files for the application to run
COPY ./src ./src
COPY main.py .

# Make port 5712 available (aligns with config.json and main.py)
EXPOSE 5712

# Run main.py when the container launches
CMD ["python", "main.py"]