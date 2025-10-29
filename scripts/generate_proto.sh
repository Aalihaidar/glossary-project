#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Define the base directory for proto files
PROTO_DIR="./proto"

# --- Install Python gRPC Tools at a specific, compatible version ---
echo "Installing pinned version of Python gRPC tools..."
pip install grpcio==1.60.0 grpcio-tools==1.60.0 protobuf==4.25.3

# --- Generate code for Glossary Service ---
echo "Generating code for Glossary Service..."
python -m grpc_tools.protoc \
    -I${PROTO_DIR} \
    --python_out=./glossary-service \
    --pyi_out=./glossary-service \
    --grpc_python_out=./glossary-service \
    ${PROTO_DIR}/glossary.proto

# --- Generate code for Graph Service ---
echo "Generating code for Graph Service..."
python -m grpc_tools.protoc \
    -I${PROTO_DIR} \
    --python_out=./graph-service \
    --pyi_out=./graph-service \
    --grpc_python_out=./graph-service \
    ${PROTO_DIR}/graph.proto

# --- Generate code for API Gateway ---
echo "Generating code for API Gateway..."
python -m grpc_tools.protoc \
    -I${PROTO_DIR} \
    --python_out=./api-gateway \
    --pyi_out=./api-gateway \
    --grpc_python_out=./api-gateway \
    ${PROTO_DIR}/glossary.proto ${PROTO_DIR}/graph.proto ${PROTO_DIR}/gateway.proto

echo "Protobuf code generation complete."

# --- Move generated files into the proto subdirectories ---
echo "Organizing generated files..."
for service in api-gateway glossary-service graph-service; do
    rm -rf ./${service}/proto/*
done

for service in api-gateway glossary-service graph-service; do
    mkdir -p ./${service}/proto
    if ls ./${service}/*.py 1> /dev/null 2>&1; then
        mv ./${service}/*.py ./${service}/proto/
    fi
    if ls ./${service}/*.pyi 1> /dev/null 2>&1; then
        mv ./${service}/*.pyi ./${service}/proto/
    fi
    touch ./${service}/proto/__init__.py
done

echo "File organization complete."
