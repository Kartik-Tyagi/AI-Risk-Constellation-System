# Bob Instructions - AI Risk Constellation System

## Critical Project Constraints

### Deployment & Environment
- **Local deployment only** - No cloud services, everything runs on local infrastructure
- **No paid services** - Use only free and open-source tools
- **Single developer** - All work done by one person, plan accordingly for complexity

### Development Philosophy
- **Complete feature coverage** - Address 100% of requirements, not just 60%
- **Self-contained context** - Each plan step must include all necessary context for execution
- **Incremental validation** - Test each component before moving to next phase

## Technology Stack Constraints (Free/Open-Source Only)

### Data Science/ML
- PyTorch (free, open-source)
- PyTorch Geometric for Graph Neural Networks
- NumPy, SciPy for quantum-inspired algorithms
- Scikit-learn for traditional ML
- MLflow (open-source) for experiment tracking

### Backend/Infrastructure
- Python FastAPI or Flask (not Go/Rust - simpler for solo dev)
- SQLite or PostgreSQL (free, local)
- NetworkX or Neo4j Community Edition (free) for graph database
- Redis (open-source) for caching
- Local message queue (RabbitMQ or simple Python queue)

### Frontend/Visualization
- React with Vite (free)
- D3.js for 2D visualizations (Three.js 3D optional if time permits)
- Recharts or Plotly for charts
- WebSocket for real-time updates
- Local development server

### Infrastructure
- Docker for containerization (free)
- Docker Compose for orchestration (simpler than Kubernetes for local)
- Local file system for storage
- Git for version control

## Feature Coverage Checklist

### Task 1: Quantum-Inspired Risk Engine & GNN
- [ ] Quantum-inspired optimization (QAOA-style algorithm)
- [ ] Graph Attention Networks for risk propagation
- [ ] Temporal graph neural networks
- [ ] Risk DNA generation algorithm
- [ ] Real-time inference pipeline
- [ ] Model training pipeline

### Task 2: Distributed Risk Processing Platform
- [ ] Event-driven data ingestion
- [ ] Graph database for risk networks
- [ ] Real-time data streaming
- [ ] API layer (REST/GraphQL)
- [ ] Caching layer
- [ ] Monitoring and logging

### Task 3: Interactive Risk Constellation Interface
- [ ] Graph visualization (2D/3D)
- [ ] Interactive exploration features
- [ ] Real-time risk heatmaps
- [ ] Natural language query interface
- [ ] Customizable dashboard
- [ ] Real-time updates via WebSocket

### Task 4: Risk Narrative & Documentation
- [ ] Risk taxonomy and glossary
- [ ] User documentation
- [ ] Training materials
- [ ] Compliance documentation
- [ ] Executive briefing templates
- [ ] ROI analysis framework

## Data Requirements

### Synthetic Data Generation
Since this is local/demo, create synthetic data generators for:
- Market data streams (stock prices, volatility, etc.)
- Transaction data
- Portfolio holdings
- Counterparty networks
- Historical risk events

### Sample Datasets
- Create realistic but synthetic financial data
- Include edge cases and stress scenarios
- Generate time-series data for temporal analysis

## Performance Targets (Local Environment)

- Risk calculations: 1K-10K per second (scaled down from 100K for local)
- Dashboard refresh: < 2 seconds
- Graph visualization: Handle 1K-10K nodes
- API response time: < 500ms for most queries
- Model inference: < 100ms per prediction

## Development Phases Priority

1. **Phase 1**: Core risk engine and basic data structures
2. **Phase 2**: Graph database and API layer
3. **Phase 3**: Basic visualization and dashboard
4. **Phase 4**: Advanced ML models and real-time features
5. **Phase 5**: Polish, documentation, and testing

## Testing Strategy

- Unit tests for core algorithms
- Integration tests for API endpoints
- End-to-end tests for critical workflows
- Performance benchmarks for key operations
- Manual testing for UI/UX

## Documentation Requirements

- Code documentation (docstrings, comments)
- API documentation (OpenAPI/Swagger)
- User guide with screenshots
- Architecture documentation
- Setup and deployment guide
- Troubleshooting guide

## Success Criteria

- All 4 tasks from RoughPlan.md fully implemented
- System runs entirely on local machine
- No paid services or cloud dependencies
- Complete documentation for future maintenance
- Demo-ready with synthetic data
- Achieves stated impact goals (scaled for local environment)