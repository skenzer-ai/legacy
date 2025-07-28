# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **production-ready AI-powered ITSM automation platform** built with modern full-stack architecture featuring comprehensive workflow orchestration, visual interfaces, and enterprise-grade capabilities. The platform provides sophisticated multi-agent automation for Infraon ITSM operations with advanced visual workflow design and real-time collaboration.

### Core Platform Capabilities

1. **Intelligent Q&A & Chat**: Advanced conversational AI with context-aware responses using hybrid retrieval and multi-agent reasoning
2. **Visual Workflow Orchestration**: Complete workflow state machine system with visual canvas-based design and real-time execution monitoring  
3. **Advanced API Studio**: Live API testing with workflow integration, real-time collaboration, and comprehensive validation
4. **Service Knowledge Graph**: Interactive exploration of service relationships, dependencies, and API mappings
5. **Enterprise Integration**: Production-ready authentication, role-based access, background processing, and comprehensive monitoring

### System Architecture Status

**✅ COMPLETED - Production Foundation**:
- **Phase 1**: Core infrastructure with FastAPI Users authentication, PostgreSQL/SQLite database, Redis caching, role-based access control
- **Phase 2**: Advanced application architecture with workflow state machines, event-driven pub/sub, WebSocket real-time communication, progress tracking, multi-level caching
- **Frontend Milestones 1-4**: Complete React 18 + TypeScript frontend with service dashboard, intelligent chat interface, live API testing studio, admin panels

**🚧 IN DEVELOPMENT**:
- **Man-O-Man System**: Service registry management with intelligent API tier classification and procedural validation
- **Advanced Visual Interfaces**: Infinity canvas foundation for node-based workflow design

**🔮 UPCOMING - Phase 3 Advanced Features**:
- **Proxie Agent**: Enhanced workflow integration with ML-powered API selection
- **Infinity Canvas**: Full visual workflow designer with drag-and-drop nodes and real-time collaboration
- **Knowledge Graph Explorer**: Interactive visualization of service relationships and API dependencies
- **Advanced API Studio**: Canvas-based testing with workflow context and multi-user collaboration

## Key Commands

### Primary Development Server
```bash
# Main backend server (Enhanced Phase 2 Architecture)
uvicorn app.main:app --reload --port 8001

# Frontend development server  
cd ../frontend && npm run dev

# Interactive CLI testing (comprehensive system validation)
python interactive_test.py
```

### Environment Setup & Management
```bash
# Activate Python environment
pyenv activate augment-env

# Database migrations
alembic upgrade head

# Create admin user
python create_admin.py

# Build and verify retrieval indices
python src/scripts/build_indices.py --output_dir dist
```

### Development Workflows
```bash
# Full stack development
uvicorn app.main:app --reload --port 8001 & cd ../frontend && npm run dev

# Backend testing (all Phase 2 systems)
python test_phase2_systems.py
python test_complete_cache_system.py

# Agent framework testing
python tests/test_augment_agent.py
python tests/test_react_strategy.py
python tests/test_agent_api.py

# Man-O-Man development testing
python tests/test_classification_api.py
python tests/test_definition_agent.py
python tests/test_validation_workflow_integration.py
```

### Production Operations
```bash
# System health and monitoring
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/system/stats

# User management
curl -X POST http://localhost:8001/api/v1/auth/register
curl -X POST http://localhost:8001/api/v1/users/

# Task queue monitoring
curl http://localhost:8001/api/v1/tasks/stats
```

## Architecture Overview

### Full-Stack Production Architecture

**Frontend Foundation** (`frontend/`):
- **React 18 + TypeScript**: Modern component architecture with strict typing
- **Tailwind CSS**: Utility-first styling with custom design system
- **Zustand State Management**: Lightweight, TypeScript-first state management
- **React Router**: Single-page application with protected routes
- **Vite Build System**: Fast development and optimized production builds

**Backend Foundation** (`backend/app/`):
- **FastAPI**: Async web framework with automatic API documentation and validation
- **SQLAlchemy 2.0**: Modern async ORM with hybrid PostgreSQL/SQLite support
- **FastAPI Users**: Production-ready authentication with JWT and role-based access
- **Pydantic v2**: Advanced data validation and serialization
- **Alembic**: Database migrations with environment-specific configurations

### Phase 2 Advanced Architecture (✅ COMPLETED)

**Workflow Engine** (`app/core/workflow/`):
- **State Machine System**: Complete workflow orchestration with async execution
- **Event-Driven Progression**: Workflow state transitions triggered by events
- **Parallel & Sequential Processing**: Multi-step workflows with dependency management
- **Persistent State Management**: Database-backed workflow execution tracking
- **Real-time Monitoring**: WebSocket-based progress updates and notifications

**Event-Driven Pub/Sub** (`app/core/events/`):
- **Redis-Backed Publisher**: High-performance event publishing with persistence
- **Flexible Subscriptions**: Pattern-based event filtering and routing  
- **Event History**: Complete audit trail with correlation tracking
- **Real-time Notifications**: WebSocket integration for live event streaming
- **Batch Processing**: Optimized bulk event handling for performance

**WebSocket Real-Time Communication** (`app/core/websocket/`):
- **Connection Management**: Lifecycle management with authentication
- **Room-Based Communication**: User groups and workflow-specific channels
- **Message Routing**: Type-safe message handling with validation
- **Presence Tracking**: User activity and connection health monitoring
- **Integration Hooks**: Deep integration with workflow engine and event system

**Advanced Caching Strategy** (`app/core/cache/`):
- **Multi-Level Hierarchy**: L1 (memory) + L2 (Redis) with intelligent promotion
- **Smart Invalidation**: Tag-based and dependency-aware cache clearing
- **Performance Monitoring**: Cache hit rates and performance analytics
- **Circuit Breaker**: Automatic fallback for cache failures
- **Compression & Encryption**: Optimized storage with security features

**Progress Tracking System** (`app/core/progress/`):
- **Multi-Step Operations**: Granular progress tracking with weighted steps
- **ETA Calculation**: Intelligent time estimation based on historical data
- **Real-time Updates**: WebSocket integration for live progress monitoring
- **Error Handling**: Comprehensive error capture and recovery mechanisms
- **Performance Metrics**: Throughput tracking and optimization insights

### Frontend Component Architecture (✅ COMPLETED)

**Service Dashboard** (`frontend/src/pages/Dashboard.tsx`):
- **Service Grid/List Views**: Flexible service browsing with filtering and search
- **Real-time Status**: Live service health and availability monitoring
- **Quick Actions**: Rapid access to common operations and testing
- **Analytics Integration**: Usage metrics and performance dashboards

**Intelligent Chat Interface** (`frontend/src/components/chat/`):
- **Context-Aware Conversations**: Service-specific AI responses with reasoning chains
- **Memory Management**: Persistent conversation history with token optimization  
- **Multi-Strategy Support**: Direct and ReAct reasoning modes
- **Source Attribution**: Links to documentation and API specifications
- **Real-time Streaming**: Live response generation with thinking transparency

**Live API Testing Studio** (`frontend/src/components/testing/`):
- **Dynamic Form Generation**: Auto-generated forms from OpenAPI specifications
- **Real-time Execution**: Live API calls with comprehensive error handling
- **Syntax Highlighting**: Request/response display with JSON/XML formatting
- **Test History**: Persistent testing sessions with result comparison
- **Workflow Integration**: API tests as workflow building blocks

**Admin Dashboard** (`frontend/src/components/admin/`):
- **User Management**: Complete CRUD operations with role assignment
- **Service Registry**: Visual management of API services and classifications
- **System Monitoring**: Real-time metrics and health dashboards
- **Configuration Management**: Dynamic settings with validation

### Integration & Infrastructure

**Authentication & Authorization** (`app/core/auth.py`):
- **FastAPI Users Integration**: Production-ready user management
- **Role-Based Access Control**: Admin, Developer, Viewer roles with granular permissions
- **JWT Token Management**: Secure token generation and validation
- **Session Management**: Redis-backed sessions with automatic cleanup

**Database Architecture** (`app/models/`):
- **User Management**: Complete user profiles with role assignments
- **Service Registry**: Comprehensive API service metadata and classifications
- **Workflow Definitions**: State machine definitions with step configurations
- **Event History**: Complete audit trail with correlation tracking
- **Progress Records**: Multi-step operation tracking with metadata

**Background Task Processing** (`app/core/tasks/`):
- **Redis Queue**: High-performance task queue with worker management
- **Async Execution**: Non-blocking task processing with progress tracking
- **Retry Logic**: Configurable retry policies with exponential backoff
- **Monitoring**: Task statistics and worker health monitoring

**Configuration Management** (`app/core/config.py`):
- **Environment-Specific**: Development (SQLite) and production (PostgreSQL) configurations
- **Proxy Integration**: CORS bypass for external API integration
- **Settings Validation**: Pydantic-based configuration with type safety
- **Runtime Updates**: Dynamic configuration changes without restart

## Agent Framework (✅ PRODUCTION-READY)

### Base Agent Architecture (`app/core/agents/base/`)
- **Abstract Base Class**: Common functionality with strategy pattern support
- **Memory Management**: Token-aware conversation history with automatic trimming
- **LLM Integration**: Multi-provider support with OpenRouter integration
- **Configuration Management**: Runtime configuration updates with validation
- **Response Models**: Structured responses with reasoning chain tracking

### Augment Agent Implementation (`app/core/agents/augment/`)
- **Production Deployment**: Fully operational Q&A agent for Infraon platform
- **Strategy Switching**: Direct (single-pass) and ReAct (iterative reasoning) modes
- **Hybrid Retrieval Integration**: BGE-M3 + CodeBERT embeddings with TF-IDF fusion
- **Template System**: Customizable prompt templates (default, technical)
- **Session Management**: Persistent user context and preferences
- **Source Attribution**: Complete traceability to source documents and APIs

### Agent API Endpoints (`app/api/v1/endpoints/agents.py`)
- `POST /api/v1/agents/augment` - Main query endpoint with structured responses
- `GET /api/v1/agents/augment/info` - Agent configuration and status
- `POST /api/v1/agents/augment/config` - Dynamic configuration updates
- `POST /api/v1/agents/augment/memory/clear` - Conversation history management
- `GET /api/v1/agents/augment/templates` - Available prompt templates

## Man-O-Man Service Registry System (🚧 IN DEVELOPMENT)

### System Overview (`app/core/manoman/`)
The **Man-O-Man** system provides intelligent API service classification, validation, and registry management for the unified platform. It processes complex API specifications and creates enhanced metadata for optimal agent operation.

**Development Reference**: All development follows specifications in `MAN-O-MAN_DEVELOPMENT_PLAN.md`

### Core Components

**Classification Engine** (`engines/`):
- **JSON Parser**: Advanced OpenAPI specification parsing with schema extraction
- **Service Classifier**: Intelligent grouping of APIs into logical services  
- **Tier Classification**: Automatic CRUD vs specialized operation classification
- **Conflict Detection**: Keyword overlap detection and resolution

**Interactive Agents** (`agents/`):
- **Definition Agent**: Conversational service metadata enhancement
- **Testing Agent**: Procedural API validation with Create-Read-Delete cycles
- **Session Management**: Progress tracking for complex definition workflows

**Validation Framework** (`api/validation.py`):
- **Procedural Testing**: Real API lifecycle validation
- **Schema Discovery**: Live API behavior vs documentation comparison
- **Cleanup Automation**: Intelligent test data cleanup with manual fallback
- **Registry Enhancement**: Validated metadata integration

## Advanced Roadmap - Phase 3 Features (🔮 UPCOMING)

### Infinity Canvas Architecture
**Visual Workflow Designer**:
- **Node-Based Interface**: Drag-and-drop workflow creation with rich node libraries
- **Real-time Collaboration**: Multi-user editing with conflict resolution
- **Template System**: Pre-built workflow patterns for common operations
- **State Visualization**: Live workflow execution monitoring on canvas

**Knowledge Graph Explorer**:
- **Interactive Visualization**: Service relationship mapping with zoom/pan/search
- **Dependency Analysis**: API interdependency tracking and impact analysis
- **Visual Navigation**: Click-to-explore from services to APIs to documentation
- **Context Integration**: Seamless transition between graph and workflow design

### Enhanced Agent Integration
**Proxie Agent**:
- **Workflow Context**: Enhanced API selection with workflow state awareness
- **ML-Powered Classification**: Advanced service selection using trained models  
- **Performance Optimization**: Sub-300ms API selection with >90% accuracy
- **Visual Integration**: Canvas-based agent interaction and feedback

**Advanced API Studio**:
- **Canvas-Based Testing**: API testing integrated with workflow design
- **Collaborative Sessions**: Real-time multi-user API testing and validation
- **Workflow Test Integration**: API tests as reusable workflow components
- **Advanced Visualization**: Request/response flow visualization on canvas

### Enterprise Features
**Advanced Analytics**:
- **Usage Pattern Analysis**: Service utilization and optimization insights
- **Performance Monitoring**: Real-time system health and bottleneck detection
- **Predictive Analytics**: Workflow optimization suggestions based on usage patterns

**Scalability Enhancements**:
- **Microservice Architecture**: Component-based scaling for high-load scenarios
- **Event Sourcing**: Complete system state reconstruction and audit capabilities
- **Advanced Caching**: Distributed caching with intelligent preloading

## Development Environment

### SSH Remote Development
- **Server**: `ssh -p 2222 heramb@ssh.skenzer.com`
- **Environment**: Python 3.13.5 with pyenv (augment-env)
- **Ports**: 8001 (backend), 3000 (frontend), additional ports 3001, 2222 available
- **Database**: SQLite for development, PostgreSQL/Redis available for production

### Technology Stack
**Frontend**:
- React 18, TypeScript, Tailwind CSS, Vite, Zustand, React Router
- Future: Canvas libraries for infinity canvas, real-time collaboration frameworks

**Backend**:
- FastAPI, SQLAlchemy 2.0, FastAPI Users, Pydantic v2, Alembic, Redis
- Phase 2: Advanced workflow engine, event system, WebSocket manager, multi-level caching

**AI/ML**:
- sentence-transformers (BGE-M3, CodeBERT), transformers, torch, FAISS
- LLM Integration: OpenRouter API with multiple model support

**Infrastructure**:
- Database: SQLAlchemy with SQLite/PostgreSQL support
- Caching: Redis with intelligent multi-level strategies
- Task Queue: Redis-based background processing
- Real-time: WebSocket with room management and authentication

### Testing Strategy
**Frontend Testing**:
- Component testing with React Testing Library
- Integration testing for service dashboard and chat interface
- End-to-end testing for complete user workflows

**Backend Testing**:
- Agent framework comprehensive testing (`tests/test_*.py`)
- Phase 2 system validation (`test_phase2_systems.py`)
- Man-O-Man development validation (`tests/test_*_agent.py`)
- API endpoint testing with authentication and role validation

**Integration Testing**:
- Full-stack workflow testing from frontend to backend
- Real-time communication testing (WebSocket + events)
- External API integration testing (Infraon proxy)

## Success Metrics & Performance

### Current System Performance
- **Backend Startup**: <10 seconds with full Phase 2 system initialization
- **Frontend Load**: <2 seconds initial page load with service data
- **API Response**: <200ms average for authenticated endpoints
- **Real-time Updates**: <50ms WebSocket message delivery
- **Cache Performance**: >95% hit rate for frequently accessed data

### Phase 3 Target Metrics
- **API Selection**: <300ms with >90% accuracy (Proxie Agent)
- **Visual Workflow**: <1 second canvas rendering for complex workflows
- **Collaboration**: <100ms conflict resolution for multi-user editing
- **Knowledge Graph**: <500ms for service relationship query and visualization

## Development Guidelines

### Code Standards
- **TypeScript**: Strict typing for all frontend components
- **Python**: Type hints and Pydantic models for all backend code
- **Testing**: Comprehensive test coverage for all new features
- **Documentation**: Inline documentation and architectural decision records

### Workflow Integration Patterns
- **Event-Driven**: All system interactions use event publishing for loose coupling
- **State Management**: Centralized state with clear update patterns
- **Real-time Updates**: WebSocket integration for live system monitoring
- **Error Handling**: Comprehensive error capture with user-friendly messaging

### Future Development
- **Canvas Integration**: All new features consider visual workflow integration
- **Collaboration**: Multi-user support built into new feature design
- **Performance**: Sub-second response targets for all user interactions
- **Scalability**: Component-based architecture for horizontal scaling

When developing new features:
1. **Follow Phase 2 Architecture**: Use event system, caching, and WebSocket patterns
2. **Consider Visual Integration**: How features integrate with upcoming infinity canvas
3. **Test Comprehensively**: Unit, integration, and end-to-end testing
4. **Document Thoroughly**: Update this file and maintain architectural records
5. **Performance First**: Optimize for response time and user experience