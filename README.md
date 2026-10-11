# Ortho RAG Platform

A production-ready, decoupled microservices architecture for building a Retrieval-Augmented Generation (RAG) system focused on orthopedic hardware data.

## Architecture
- **Discovery Service**: Fetches YouTube video IDs based on keywords and channels.
- **Ingestion Worker**: Transcribes audio, extracts entities (Implants, KPIs), and generates embeddings.
- **RAG API**: Serves the chat interface with vector search capabilities.

## Getting Started
1. Clone this repository.
2. Run `docker-compose up -d` to start Redis and Vector DB.
3. Follow individual service READMEs for local development.


## Commands

- **Build Index**  
- python services/ingestion-worker/scripts --corpus data/transcripts --size 500 --overlap 50 --out data/transcripts/embeddings/small/



my-enterprise-app/
│
├── Makefile                            # NEW: Central workflow automation (NO extension)
├── .env                                # Local secrets & configs (NEVER commit to Git)
├── .env.example                        # Template for new developer onboarding
│
├── .github/                            # CI/CD & DevOps Automation
│   └── workflows/
│       ├── test-and-lint.yml           # Runs on every pull request
│       ├── deploy-dev.yml              # Triggered on merge to develop branch
│       └── deploy-prod.yml             # Triggered on release tags or main branch
│
├── .local_data/                        # LOCAL ONLY: Ignored by Git
│   ├── qdrant/                         # Local Qdrant persistent storage volume
│   └── postgres/                       # Local relational database volume
│
├── apps/                               # Core Application Codebases (Monorepo approach)
│   ├── api-service/                    # Main backend API (Python FastAPI)
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                 # Application entrypoint
│   │   │   ├── config.py               # Reads system env variables
│   │   │   ├── services/               # Business logic / Qdrant client interactions
│   │   │   └── models/                 # Data schemas (Pydantic / SQLModel)
│   │   ├── tests/                      # Unit and integration tests
│   │   ├── Dockerfile                  # Application containerisation configuration
│   │   └── requirements.txt            # Python dependencies
│   │
│   └── ingestion-worker/               # Optional background vector sync/ETL worker
│       ├── src/
│       └── Dockerfile
│
├── infra/                              # Everything Infrastructure & Deployment
│   ├── local/                          # Local container orchestration
│   │   └── docker-compose.yml          # Spins up local Qdrant, DBs, and app mock
│   │
│   └── terraform/                      # Cloud Provisioning Blueprint
│       ├── main.tf                     # Calls infrastructure modules
│       ├── providers.tf                # Configures AWS/GCP, versions, and cloud links
│       ├── backend.tf                  # Configures S3/GCS remote state locking
│       ├── variables.tf                # Input variable schema validation definitions
│       ├── outputs.tf                  # Infrastructure references printed post-apply
│       │
│       ├── environments/               # Target Cloud Environments Parameters
│       │   ├── dev/
│       │   │   ├── dev.tfvars          # Small instance sizes, single nodes
│       │   │   └── backend-dev.hcl     # Dev remote state configuration
│       │   └── prod/
│       │       ├── prod.tfvars         # High availability, auto-scaling, multi-node
│       │       └── backend-prod.hcl    # Prod remote state configuration
│       │
│       └── modules/                    # Reusable Custom Building Blocks
│           ├── networking/             # VPCs, subnets, security groups, firewalls
│           ├── compute/                # AWS ECS / GCP Cloud Run setup
│           └── database/               # Managed Qdrant / RDS instances setup
│
├── .dockerignore                       # Excludes node_modules, data, local configs from containers
├── .gitignore                          # Standard code exclusions (hides .local_data/ and local .env)
├── README.md                           # Comprehensive onboarding documentation
└── CHANGELOG.md                        # Tracking project release history
