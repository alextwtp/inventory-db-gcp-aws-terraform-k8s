FROM python:3.12-slim
FROM ubuntu:22.04

WORKDIR /app

FROM ubuntu:22.04

WORKDIR /app

# Update Package List And Install python3 & python3-pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list first for better Docker cache usage

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy specific directories and files into container
COPY app ./app
COPY config ./config
COPY core ./core
COPY repository ./repository
COPY index.html ./index.html

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
