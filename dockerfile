# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Update package lists and install Graphviz
RUN apt-get update && apt-get install -y graphviz

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a script to check for running services on port 5000 and terminate them
RUN echo '#!/bin/sh' > /check_and_kill_port.sh && \
    echo 'if netstat -tuln | grep ":4444 "' >> /check_and_kill_port.sh && \
    echo 'then echo "Port 4444 is in use. Killing the process using port 5000." && fuser -k 4444/tcp' >> /check_and_kill_port.sh && \
    echo 'fi' >> /check_and_kill_port.sh && \
    chmod +x /check_and_kill_port.sh

# Make port 8000 available to the world outside this container
EXPOSE 4444

# Command to run the application using Gunicorn
CMD ["/bin/sh", "-c", "/check_and_kill_port.sh && gunicorn run:app"]

