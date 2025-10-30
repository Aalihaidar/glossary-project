#!/bin/bash
set -e

echo "Removing old generated files..."
rm -rf ./api-gateway/proto/*
rm -rf ./glossary-service/proto/*
rm -rf ./graph-service/proto/*

touch ./api-gateway/proto/__init__.py
touch ./glossary-service/proto/__init__.py
touch ./graph-service/proto/__init__.py


PROTO_DIR="./proto"

API_GATEWAY_OUT="./api-gateway/proto"
GLOSSARY_SERVICE_OUT="./glossary-service/proto"
GRAPH_SERVICE_OUT="./graph-service/proto"

echo "Generating code for Glossary Service..."
python -m grpc_tools.protoc \
    -I${PROTO_DIR} \
    --python_out=${GLOSSARY_SERVICE_OUT} \
    --pyi_out=${GLOSSARY_SERVICE_OUT} \
    --grpc_python_out=${GLOSSARY_SERVICE_OUT} \
    ${PROTO_DIR}/glossary.proto

echo "Generating code for Graph Service..."
python -m grpc_tools.protoc \
    -I${PROTO_DIR} \
    --python_out=${GRAPH_SERVICE_OUT} \
    --pyi_out=${GRAPH_SERVICE_OUT} \
    --grpc_python_out=${GRAPH_SERVICE_OUT} \
    ${PROTO_DIR}/graph.proto

echo "Generating code for API Gateway..."
python -m grpc_tools.protoc \
    -I${PROTO_DIR} \
    --python_out=${API_GATEWAY_OUT} \
    --pyi_out=${API_GATEWAY_OUT} \
    --grpc_python_out=${API_GATEWAY_OUT} \
    ${PROTO_DIR}/glossary.proto ${PROTO_DIR}/graph.proto ${PROTO_DIR}/gateway.proto

echo "Protobuf code generation complete."