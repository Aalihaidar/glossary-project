I have a professional python Glossary microservices project, it is in GitHub and deployed in Render.
Please don’t provide full code examples upfront or suggest code that stays unchanged.
Instead, tell me which specific part or snippet of my code you need, and I will share it with you.
Then, you can help me improve or rewrite that part into a complete, professional-quality version.
this is the structure:
```
glossary-project/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .flake8
├── .gitignore
├── docker-compose.yml
├── README.md
├── render.yaml
├── proto/
│   ├── gateway.proto
│   ├── glossary.proto
│   └── graph.proto
│
├── api-gateway/
│   ├── gateway/
│   │   ├── __init__.py
│   │   ├── seeder.py
│   │   └── server.py
│   ├── proto/
│   │   ├── __init__.py
│   │   ├── gateway_pb2_grpc.py
│   │   ├── gateway_pb2.py
│   │   ├── gateway_pb2.pyi
│   │   ├── glossary_pb2_grpc.py
│   │   ├── glossary_pb2.py
│   │   ├── glossary_pb2.pyi
│   │   ├── graph_pb2_grpc.py
│   │   ├── graph_pb2.py
│   │   ├── graph_pb2.pyi
│   │   └── run.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
│
├── glossary-service/
│   ├── glossary/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── service.py
│   ├── proto/
│   │   ├── __init__.py
│   │   ├── glossary_pb2_grpc.py
│   │   ├── glossary_pb2.py
│   │   └── glossary_pb2.pyi
│   │   └── run.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
│
└── graph-service/
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── service.py
│   ├── proto/
│   │   ├── __init__.py
│   │   ├── graph_pb2_grpc.py
│   │   ├── graph_pb2.py
│   │   ├── graph_pb2.pyi
│   │   └── run.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
│
└── scripts/
    └── generate_proto.sh
```

I want to write professional Readme to be comprehensive professional and complete and explain everything in the project from the purpose to the purpose of each service to how to test or use it. 