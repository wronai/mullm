# Mullm - Multi-Agent Learning and Labor Management

A distributed system for orchestrating multiple AI agents with event-driven architecture, CQRS patterns, and real-time projections.

## Architecture Overview

Mullm is built using Domain-Driven Design (DDD) principles with:
- **Event Sourcing** for state management
- **CQRS** for command/query separation
- **Saga Pattern** for distributed transactions
- **Event-Driven Architecture** with NATS messaging
- **Read Model Projections** for real-time dashboards

## Services

### Core Services
- **Orchestrator**: Command handling, domain logic, and event publishing
- **Projector**: Read model projections and query handling
- **Web**: React-based frontend for monitoring and control

### Agents
- **Shell Agent**: Command execution and system operations
- **Browser Host Agent**: Web automation and browser control

## Quick Start

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Development

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- NATS Server

### Local Development

```bash
# Setup environment
cp .env.example .env

# Start infrastructure
docker-compose up postgres nats redis -d

# Install dependencies
pip install -r services/orchestrator/requirements.txt
pip install -r services/projector/requirements.txt
npm install --prefix services/web

# Run services locally
python services/orchestrator/app/main.py
python services/projector/app/main.py
npm start --prefix services/web
```

## API Documentation

### Orchestrator API (Port 8001)
- `POST /api/commands` - Submit commands
- `GET /api/queries` - Execute queries
- `GET /health` - Health check

### Projector API (Port 8002)
- `GET /projections/tasks` - Task board view
- `GET /projections/agents` - Agent fleet status
- `GET /projections/workflows` - Workflow versions

## Domain Model

### Aggregates
- **Task**: Represents work units with state transitions
- **Agent**: AI agents with capabilities and status
- **Workflow**: Multi-step processes with orchestration logic

### Events
- `TaskCreated`, `TaskAssigned`, `TaskCompleted`
- `AgentRegistered`, `AgentStatusChanged`
- `WorkflowStarted`, `WorkflowStepCompleted`

## Monitoring

- **NATS Monitoring**: http://localhost:8222
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Submit a pull request

## License

Licensed under Apache-2.0.
