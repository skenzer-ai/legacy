# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a production-ready AI-powered ITSM automation platform built with LangChain 2025 that provides three core capabilities:

1. **Intelligent Q&A**: Answer general questions about the Infraon platform using user guide docs and API documentation
2. **Automated Task Execution**: Perform complex operations by reasoning through and calling relevant intermediary APIs (e.g., calculating mean time to ticket resolution over 6 months by fetching historical data and performing calculations)
3. **Workflow Automation**: Create and execute multi-step workflows for complex administrative tasks (e.g., bulk user creation, role management, configuration changes, reminder setup) where users provide details in any format and the agent fills in and executes the workflow

The system features a hybrid retrieval foundation with dual implementations and is designed to scale to a full multi-agent orchestration platform.

## Key Commands

### Interactive CLI (Recommended)
```bash
# Launch comprehensive interactive testing
python interactive_test.py
```

### Development
```bash
# Build retrieval indices (required before first use)
python src/scripts/build_indices.py

# Main retrieval server
uvicorn src.main:app --reload

# Backend API server (legacy implementation)
cd backend && uvicorn app.main:app --reload

# Run all tests
python -m pytest

# Run specific test suites
python -m pytest tests/test_retrieval_v2.py
python -m pytest tests/test_build_indices.py
```

### Index Management
```bash
# Build indices with custom configuration
python src/scripts/build_indices.py --api_spec_path user_docs/infraon-api.json --synonyms_path src/retrieval/synonyms.json --output_dir dist

# Rebuild test indices
python src/scripts/build_indices.py --output_dir test_dist
```

### API Operations
```bash
# Process documents (backend API)
curl -X POST "http://localhost:8000/api/v1/process/document"

# Process API specifications
curl -X POST "http://localhost:8000/api/v1/process/api"

# Test hybrid retrieval
curl -G "http://localhost:8000/api/v1/retrieve/fuse" --data-urlencode "query=create incident ticket"
```

## Architecture Overview

### Multi-Agent Platform Foundation
The system is architected for expansion into a comprehensive multi-agent platform with three primary agent types planned:

1. **Knowledge Agent**: Answers questions using retrieved documentation and API specs
2. **Execution Agent**: Performs complex operations by chaining API calls and data processing
3. **Workflow Agent**: Manages multi-step administrative workflows with dynamic parameter filling

### Dual Implementation Structure

**Main Implementation** (`/src/`): Production-ready hybrid retrieval system
- `src/retrieval/retriever.py` - KnowledgeRetriever orchestrating multi-modal search
- `src/retrieval/api_retriever.py` - API-specific retrieval with FAISS and roaring bitmaps  
- `src/retrieval/document_retriever.py` - Document retrieval for user guides
- `src/scripts/build_indices.py` - Offline index building pipeline
- `src/main.py` - FastAPI server with `/search` endpoint

**Backend Implementation** (`/backend/`): Structured API with processing pipeline
- `backend/app/main.py` - FastAPI app with versioned API routes
- `backend/app/api/v1/endpoints/` - Separate endpoints for processing and retrieval
- `backend/app/core/state.py` - ProcessingStateManager for tracking index readiness
- `backend/app/core/retrieval/fusion/fuser.py` - Result fusion and ranking

### Hybrid Retrieval Engine
The retrieval foundation implements multi-modal search fusion:
- **FAISS Vector Search**: Semantic similarity using BGE-M3 and CodeBERT embeddings
- **TF-IDF Scoring**: Traditional keyword-based retrieval with ITSM domain synonym expansion
- **Roaring Bitmap Index**: High-performance boolean retrieval for exact token matches
- **Intelligent Fusion**: Combines and deduplicates results across all retrieval methods

### ITSM Domain Integration
The platform is specifically designed for Infraon ITSM automation:
- **Domain Knowledge**: Processes Infraon user guides and API specifications
- **ITSM Workflows**: Supports ticket/request/change/problem/release management
- **Administrative Tasks**: Handles user management, role assignment, configuration changes
- **Synonym Expansion**: ITSM-specific terminology mapping in `src/retrieval/synonyms.json`

## Key Components

### Processing Pipeline
- `src/processing/tokenizers.py` - CanonicalTokenizer with domain-specific preprocessing
- `src/processing/config.py` - Pydantic configuration with environment variable support
- `backend/app/core/processing/` - Dual indexers for documents and API specifications

### State Management
- `backend/app/core/state.py` - ProcessingStateManager tracking index build status
- Singleton pattern with disk persistence for processing state
- Status tracking: UNPROCESSED → PROCESSING → READY → ERROR

### Data Sources
- `user_docs/infraon_user_guide.md` - Comprehensive Infraon platform documentation
- `user_docs/infraon-api.json` - Complete OpenAPI specification for Infraon APIs
- `src/retrieval/synonyms.json` - ITSM domain synonym mappings

## Dependencies and Setup

### Core Framework Stack
- **LangChain 2025**: Multi-agent orchestration with LangGraph, LangSmith integration
- **FastAPI**: Async web framework with automatic API documentation
- **Pydantic**: Data validation and settings management

### AI/ML Dependencies  
- **sentence-transformers**: BGE-M3 and CodeBERT embedding models
- **transformers**: Hugging Face model ecosystem
- **torch**: PyTorch for deep learning computations
- **accelerate**: Optimized model loading and inference

### Search Infrastructure
- **FAISS**: High-performance vector similarity search
- **scikit-learn**: TF-IDF vectorization and traditional ML
- **pyroaring**: Compressed bitmap indexing for fast boolean operations

### Development Tools
- **pytest**: Test framework with async support
- **uvicorn**: ASGI server for development and production

## Testing Strategy

### Index Validation
- `test_build_indices.py` - Validates offline index creation, file integrity, and data loading
- Covers bitmap index, TF-IDF matrix, and full-text cache generation

### End-to-End Retrieval
- `test_retrieval_v2.py` - Complete retrieval pipeline testing with isolated test indices
- Tests fusion of API and document results, validates specific query patterns
- Includes accuracy feedback collection for continuous improvement

### Interactive Testing
- `interactive_test.py` - Manual testing interface with index rebuilding and accuracy feedback
- Supports real-time query testing and result evaluation

All tests use isolated directories and proper PYTHONPATH setup to avoid conflicts with production indices.