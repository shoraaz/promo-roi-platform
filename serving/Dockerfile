# Base image — same Python version as training
# Critical: training and serving must use identical Python version
# If training uses 3.12 and serving uses 3.10, pickle files may be incompatible
FROM python:3.12-slim

WORKDIR /app

# Same layer caching pattern as training image
# requirements first, source code second
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy only the files needed for serving
# We don't copy train.py or label_engineering.py — not needed at serving time
COPY app.py .
COPY model_utils.py .
COPY schemas.py .

# Document which port this container listens on
# This is documentation only — doesn't actually open the port
# Port binding happens when you run the container
EXPOSE 8080

# Run FastAPI with uvicorn
# --host 0.0.0.0: listen on all network interfaces inside container
#   without this, the API is only reachable from inside the container itself
# --port 8080: the port FastAPI listens on
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]