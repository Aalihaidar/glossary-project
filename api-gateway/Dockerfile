# Stage 1: Use Python 3.11, a stable version with pre-compiled wheels.
FROM python:3.11-slim as builder

WORKDIR /app

# Copy only the requirements file
COPY requirements.txt .

# Install dependencies.
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Final stage for the application
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy all the application code from the build context into the container
COPY . /app/

# The port will be set by docker-compose, but it's good practice to document it
EXPOSE 50050

# The command to run when the container starts
CMD ["python", "run.py"]