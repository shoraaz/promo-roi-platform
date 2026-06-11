# Base image — official Python 3.12 slim variant
# "slim" means stripped of unnecessary OS packages — smaller image size
FROM python:3.12-slim

# Set working directory inside the container
# All subsequent commands run from here
# Think of it as "cd /app" that persists
WORKDIR /app

# Copy requirements FIRST — before any source code
# Why: Docker caches layers. If requirements.txt hasn't changed,
# pip install is skipped on the next build. This saves minutes.
COPY requirements.txt .

# Install dependencies
# --no-cache-dir: don't store pip's download cache inside the image
# keeps image size smaller
RUN pip install --no-cache-dir -r requirements.txt

# NOW copy source code — after pip install
# This way, changing train.py doesn't invalidate the pip cache
COPY train.py .
COPY label_engineering.py .
COPY feature_utils.py .

# Default command when container starts
# Can be overridden at runtime with: docker run <image> python other_script.py
CMD ["python", "train.py"]