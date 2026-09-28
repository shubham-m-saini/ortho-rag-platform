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
