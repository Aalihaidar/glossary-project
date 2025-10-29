I have a python project that I want to apply professionally the task in image.
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
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── service.py
│   ├── proto/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
│
└── scripts/
    └── generate_proto.sh
```