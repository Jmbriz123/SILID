FROM apache/airflow:2.10.5

USER root 

# Install build dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
#set user back to airflow after installing build dependencies to avoid having root permissions in the container
USER airflow 
#copy requirements.txt to the root of the container and install dependencies
COPY requirements.txt /requirements.txt
RUN pip install \
    --no-cache-dir \
    --default-timeout=120 \
    --retries=5 \
    -r /requirements.txt
