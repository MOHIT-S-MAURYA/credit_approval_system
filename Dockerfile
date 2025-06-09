# Dockerfile
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /core

# Install dependencies
COPY requirements.txt /core/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project files
COPY . /core/
