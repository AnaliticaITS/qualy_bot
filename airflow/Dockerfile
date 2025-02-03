FROM apache/airflow:2.10.4
USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    python3-dev \
    wget \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    default-jdk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
