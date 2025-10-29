```
glossary-project/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── README.md
├── docker-compose.yml
├── proto/
│   ├── gateway.proto
│   ├── glossary.proto
│   └── graph.proto
│
├── api-gateway/
│   ├── gateway/
│   │   ├── __init__.py
│   │   └── server.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── glossary_client.py
│   │       └── graph_client.py
│   ├── proto/
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
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
│
└── graph-service/
    ├── graph/
    │   ├── __init__.py
    │   ├── database.py
    │   └── service.py
    ├── proto/
    ├── Dockerfile
    ├── requirements.txt
    └── run.py
```