# Stage 1: Builder Stage
# Use a slim Python base image to build dependencies. Using a specific version
# like 3.11 ensures consistency.
FROM python:3.11-slim as builder

# Set the working directory for the build process.
WORKDIR /app

# --- KEY CHANGE ---
# Copy the requirements file specifically from the glossary-service directory.
COPY glossary-service/requirements.txt .

# Install dependencies into the builder stage. Using --no-cache-dir reduces
# the size of this layer.
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Final Application Stage
# Start from a fresh slim image to keep the final container lightweight.
FROM python:3.11-slim

# Set the working directory for the application.
WORKDIR /app

# Copy the pre-installed Python packages from the builder stage. This is more
# efficient than reinstalling them.
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# --- KEY CHANGE ---
# Copy the application code from the correct glossary-service directory.
# This includes the run.py, the 'glossary' module, and any other necessary files.
COPY glossary-service/ /app/

# Expose the port that Render will use for health checks. This is good practice
# for documentation and container orchestration.
EXPOSE 10000

# Define the command to run the application. This starts the run.py script
# which in turn starts both the gRPC server and the health check server.
CMD ["python", "run.py"]