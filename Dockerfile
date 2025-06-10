# Use Python base image
FROM python:3.11

# Install netcat for entrypoint.sh
RUN apt-get update && apt-get install -y netcat-openbsd

# Set working directory inside container
WORKDIR /core

# Copy requirements and install
COPY requirements.txt /core/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy all project files
COPY . /core/

# Copy entrypoint script into container
COPY entrypoint.sh /entrypoint.sh

# Make the script executable
RUN chmod +x /entrypoint.sh

# Use entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command if not overridden
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
