# Glossary Project

This project is a gRPC-based microservice system for managing a glossary of terms and their relationships.

## Architecture

The system consists of three services:
- **Glossary Service:** Manages terms and definitions.
- **Graph Service:** Manages the relationships between terms.
- **API Gateway:** A single public entry point that orchestrates the backend services.

## Local Development

1.  **Prerequisites:**
    - Docker
    - Docker Compose
    - Python 3.9+
    - `pip`

2.  **Generate Protobuf Code:**
    Run the generation script from the root directory:
    ```bash
    ./scripts/generate_proto.sh
    ```

3.  **Run Services:**
    Use Docker Compose to build and run all services:
    ```bash
    docker-compose up --build
    ```

## API Endpoints

- **API Gateway:** `localhost:50050`
- **Glossary Service:** `localhost:50051`
- **Graph Service:** `localhost:50052`