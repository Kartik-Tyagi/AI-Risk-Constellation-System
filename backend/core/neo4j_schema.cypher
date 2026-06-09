// Neo4j Schema for AI Risk Constellation System
// This schema defines the graph database structure for entities, relationships,
// risk events, and network analysis.

// ============================================================================
// CONSTRAINTS AND INDEXES
// ============================================================================

// Entity constraints
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE;

CREATE CONSTRAINT portfolio_id_unique IF NOT EXISTS
FOR (p:Portfolio) REQUIRE p.portfolio_id IS UNIQUE;

CREATE CONSTRAINT counterparty_id_unique IF NOT EXISTS
FOR (c:Counterparty) REQUIRE c.counterparty_id IS UNIQUE;

CREATE CONSTRAINT asset_id_unique IF NOT EXISTS
FOR (a:Asset) REQUIRE a.asset_id IS UNIQUE;

// Risk event constraints
CREATE CONSTRAINT risk_event_id_unique IF NOT EXISTS
FOR (r:RiskEvent) REQUIRE r.event_id IS UNIQUE;

// Market condition constraints
CREATE CONSTRAINT market_condition_id_unique IF NOT EXISTS
FOR (m:MarketCondition) REQUIRE m.condition_id IS UNIQUE;

// Indexes for performance
CREATE INDEX entity_type_idx IF NOT EXISTS
FOR (e:Entity) ON (e.entity_type);

CREATE INDEX entity_name_idx IF NOT EXISTS
FOR (e:Entity) ON (e.name);

CREATE INDEX risk_event_timestamp_idx IF NOT EXISTS
FOR (r:RiskEvent) ON (r.timestamp);

CREATE INDEX risk_event_severity_idx IF NOT EXISTS
FOR (r:RiskEvent) ON (r.severity);

CREATE INDEX market_condition_timestamp_idx IF NOT EXISTS
FOR (m:MarketCondition) ON (m.timestamp);

CREATE INDEX relationship_weight_idx IF NOT EXISTS
FOR ()-[r:TRANSACTS_WITH]-() ON (r.weight);

CREATE INDEX relationship_timestamp_idx IF NOT EXISTS
FOR ()-[r:EXPOSED_TO]-() ON (r.timestamp);

// ============================================================================
// NODE TYPES
// ============================================================================

// Entity Node (Base type for all entities)
// Properties:
//   - entity_id: Unique identifier
//   - entity_type: Type of entity (portfolio, counterparty, asset, etc.)
//   - name: Display name
//   - risk_score: Current risk score (0-1)
//   - created_at: Creation timestamp
//   - updated_at: Last update timestamp
//   - metadata: Additional properties as JSON

// Portfolio Node (extends Entity)
// Additional Properties:
//   - portfolio_type: Type of portfolio
//   - total_value: Total portfolio value
//   - currency: Base currency
//   - num_positions: Number of positions
//   - inception_date: Portfolio start date

// Counterparty Node (extends Entity)
// Additional Properties:
//   - counterparty_type: Type of counterparty
//   - credit_rating: Credit rating
//   - country: Country code
//   - industry: Industry sector
//   - total_exposure: Total exposure amount

// Asset Node (extends Entity)
// Additional Properties:
//   - asset_type: Type of asset
//   - ticker: Trading symbol
//   - sector: Market sector
//   - current_price: Current market price
//   - volatility: Historical volatility

// RiskEvent Node
// Properties:
//   - event_id: Unique identifier
//   - event_type: Type of risk event
//   - severity: Severity level (0-1)
//   - impact_score: Quantified impact
//   - timestamp: Event timestamp
//   - description: Event description
//   - affected_entities: List of affected entity IDs
//   - metadata: Additional event data

// MarketCondition Node
// Properties:
//   - condition_id: Unique identifier
//   - condition_type: Type of market condition
//   - indicator_name: Name of market indicator
//   - value: Indicator value
//   - timestamp: Observation timestamp
//   - regime: Market regime (bull, bear, volatile, stable)
//   - metadata: Additional condition data

// ============================================================================
// RELATIONSHIP TYPES
// ============================================================================

// TRANSACTS_WITH
// Represents transactional relationships between entities
// Properties:
//   - transaction_count: Number of transactions
//   - total_volume: Total transaction volume
//   - avg_transaction_size: Average transaction size
//   - weight: Relationship strength (0-1)
//   - first_transaction: First transaction date
//   - last_transaction: Last transaction date
//   - risk_contribution: Risk contribution score

// EXPOSED_TO
// Represents risk exposure relationships
// Properties:
//   - exposure_type: Type of exposure (credit, market, operational)
//   - exposure_amount: Quantified exposure
//   - exposure_percentage: Exposure as percentage
//   - timestamp: Exposure calculation timestamp
//   - confidence: Confidence level (0-1)
//   - risk_score: Risk score for this exposure

// CORRELATES_WITH
// Represents correlation between entities
// Properties:
//   - correlation_coefficient: Pearson correlation (-1 to 1)
//   - correlation_type: Type of correlation (price, risk, behavior)
//   - lookback_period: Period used for correlation calculation
//   - timestamp: Correlation calculation timestamp
//   - significance: Statistical significance (p-value)

// PROPAGATES_TO
// Represents risk propagation paths
// Properties:
//   - propagation_probability: Probability of risk propagation (0-1)
//   - propagation_delay: Expected delay in propagation (hours)
//   - amplification_factor: Risk amplification factor
//   - path_strength: Overall path strength (0-1)
//   - timestamp: Path calculation timestamp
//   - historical_events: Count of historical propagation events

// CONTAINS
// Represents containment relationships (portfolio contains assets)
// Properties:
//   - quantity: Quantity held
//   - weight: Position weight in portfolio
//   - cost_basis: Average cost basis
//   - market_value: Current market value
//   - unrealized_pnl: Unrealized profit/loss
//   - timestamp: Position timestamp

// TRIGGERS
// Represents event triggering relationships
// Properties:
//   - trigger_probability: Probability of triggering (0-1)
//   - trigger_conditions: Conditions that cause trigger
//   - historical_triggers: Count of historical triggers
//   - timestamp: Relationship timestamp

// AFFECTS
// Represents how market conditions affect entities
// Properties:
//   - impact_magnitude: Magnitude of impact
//   - impact_direction: Direction of impact (positive/negative)
//   - sensitivity: Entity sensitivity to condition
//   - timestamp: Impact calculation timestamp

// ============================================================================
// SAMPLE DATA CREATION QUERIES
// ============================================================================

// Create sample portfolio
// CREATE (p:Entity:Portfolio {
//   entity_id: 'portfolio_001',
//   entity_type: 'portfolio',
//   name: 'Tech Growth Portfolio',
//   risk_score: 0.65,
//   portfolio_type: 'equity',
//   total_value: 10000000.00,
//   currency: 'USD',
//   num_positions: 25,
//   inception_date: date('2020-01-01'),
//   created_at: datetime(),
//   updated_at: datetime()
// })

// Create sample counterparty
// CREATE (c:Entity:Counterparty {
//   entity_id: 'counterparty_001',
//   entity_type: 'counterparty',
//   name: 'Global Bank Corp',
//   risk_score: 0.35,
//   counterparty_type: 'bank',
//   credit_rating: 'AA',
//   country: 'USA',
//   industry: 'Financial Services',
//   total_exposure: 5000000.00,
//   created_at: datetime(),
//   updated_at: datetime()
// })

// Create sample asset
// CREATE (a:Entity:Asset {
//   entity_id: 'asset_AAPL',
//   entity_type: 'asset',
//   name: 'Apple Inc.',
//   risk_score: 0.45,
//   asset_type: 'equity',
//   ticker: 'AAPL',
//   sector: 'Technology',
//   current_price: 175.50,
//   volatility: 0.25,
//   created_at: datetime(),
//   updated_at: datetime()
// })

// Create sample risk event
// CREATE (r:RiskEvent {
//   event_id: 'event_001',
//   event_type: 'market_shock',
//   severity: 0.85,
//   impact_score: 0.75,
//   timestamp: datetime(),
//   description: 'Sudden market volatility spike',
//   affected_entities: ['portfolio_001', 'asset_AAPL'],
//   metadata: '{}'
// })

// Create sample market condition
// CREATE (m:MarketCondition {
//   condition_id: 'condition_001',
//   condition_type: 'volatility',
//   indicator_name: 'VIX',
//   value: 28.5,
//   timestamp: datetime(),
//   regime: 'volatile',
//   metadata: '{}'
// })

// ============================================================================
// RELATIONSHIP CREATION QUERIES
// ============================================================================

// Create TRANSACTS_WITH relationship
// MATCH (p:Portfolio {entity_id: 'portfolio_001'})
// MATCH (c:Counterparty {entity_id: 'counterparty_001'})
// CREATE (p)-[r:TRANSACTS_WITH {
//   transaction_count: 150,
//   total_volume: 25000000.00,
//   avg_transaction_size: 166666.67,
//   weight: 0.75,
//   first_transaction: date('2020-01-15'),
//   last_transaction: date('2024-06-01'),
//   risk_contribution: 0.45
// }]->(c)

// Create EXPOSED_TO relationship
// MATCH (p:Portfolio {entity_id: 'portfolio_001'})
// MATCH (c:Counterparty {entity_id: 'counterparty_001'})
// CREATE (p)-[r:EXPOSED_TO {
//   exposure_type: 'credit',
//   exposure_amount: 5000000.00,
//   exposure_percentage: 0.50,
//   timestamp: datetime(),
//   confidence: 0.90,
//   risk_score: 0.35
// }]->(c)

// Create CONTAINS relationship
// MATCH (p:Portfolio {entity_id: 'portfolio_001'})
// MATCH (a:Asset {entity_id: 'asset_AAPL'})
// CREATE (p)-[r:CONTAINS {
//   quantity: 10000,
//   weight: 0.175,
//   cost_basis: 150.00,
//   market_value: 1755000.00,
//   unrealized_pnl: 255000.00,
//   timestamp: datetime()
// }]->(a)

// Create CORRELATES_WITH relationship
// MATCH (a1:Asset {entity_id: 'asset_AAPL'})
// MATCH (a2:Asset {entity_id: 'asset_MSFT'})
// CREATE (a1)-[r:CORRELATES_WITH {
//   correlation_coefficient: 0.85,
//   correlation_type: 'price',
//   lookback_period: 252,
//   timestamp: datetime(),
//   significance: 0.001
// }]->(a2)

// Create PROPAGATES_TO relationship
// MATCH (e1:Entity {entity_id: 'counterparty_001'})
// MATCH (e2:Entity {entity_id: 'portfolio_001'})
// CREATE (e1)-[r:PROPAGATES_TO {
//   propagation_probability: 0.65,
//   propagation_delay: 24,
//   amplification_factor: 1.25,
//   path_strength: 0.70,
//   timestamp: datetime(),
//   historical_events: 5
// }]->(e2)

// Create TRIGGERS relationship
// MATCH (m:MarketCondition {condition_id: 'condition_001'})
// MATCH (r:RiskEvent {event_id: 'event_001'})
// CREATE (m)-[t:TRIGGERS {
//   trigger_probability: 0.80,
//   trigger_conditions: 'VIX > 25',
//   historical_triggers: 12,
//   timestamp: datetime()
// }]->(r)

// Create AFFECTS relationship
// MATCH (m:MarketCondition {condition_id: 'condition_001'})
// MATCH (p:Portfolio {entity_id: 'portfolio_001'})
// CREATE (m)-[a:AFFECTS {
//   impact_magnitude: 0.75,
//   impact_direction: 'negative',
//   sensitivity: 0.85,
//   timestamp: datetime()
// }]->(p)

// ============================================================================
// USEFUL QUERIES
// ============================================================================

// Find all entities with high risk scores
// MATCH (e:Entity)
// WHERE e.risk_score > 0.7
// RETURN e.entity_id, e.name, e.risk_score
// ORDER BY e.risk_score DESC

// Find risk propagation paths
// MATCH path = (source:Entity)-[:PROPAGATES_TO*1..3]->(target:Entity)
// WHERE source.entity_id = 'counterparty_001'
// RETURN path, length(path) as path_length
// ORDER BY path_length

// Find highly correlated assets
// MATCH (a1:Asset)-[r:CORRELATES_WITH]->(a2:Asset)
// WHERE abs(r.correlation_coefficient) > 0.8
// RETURN a1.name, a2.name, r.correlation_coefficient
// ORDER BY abs(r.correlation_coefficient) DESC

// Find portfolio exposures
// MATCH (p:Portfolio)-[e:EXPOSED_TO]->(c:Counterparty)
// WHERE p.entity_id = 'portfolio_001'
// RETURN c.name, e.exposure_amount, e.exposure_percentage, e.risk_score
// ORDER BY e.exposure_amount DESC

// Find entities affected by market conditions
// MATCH (m:MarketCondition)-[a:AFFECTS]->(e:Entity)
// WHERE m.regime = 'volatile'
// RETURN e.name, e.entity_type, a.impact_magnitude, a.impact_direction
// ORDER BY a.impact_magnitude DESC

// Calculate network centrality (find most connected entities)
// MATCH (e:Entity)
// RETURN e.entity_id, e.name, 
//        size((e)-[:TRANSACTS_WITH]-()) as transaction_degree,
//        size((e)-[:EXPOSED_TO]-()) as exposure_degree,
//        size((e)-[:CORRELATES_WITH]-()) as correlation_degree
// ORDER BY transaction_degree + exposure_degree + correlation_degree DESC
// LIMIT 20

// Find risk cascade paths with high probability
// MATCH path = (source:Entity)-[r:PROPAGATES_TO*1..4]->(target:Entity)
// WHERE source.risk_score > 0.7
// WITH path, reduce(prob = 1.0, rel in relationships(path) | prob * rel.propagation_probability) as total_probability
// WHERE total_probability > 0.3
// RETURN path, total_probability
// ORDER BY total_probability DESC
// LIMIT 10

// Find systemic risk clusters
// MATCH (e:Entity)
// WHERE e.risk_score > 0.6
// MATCH (e)-[r:TRANSACTS_WITH|EXPOSED_TO|CORRELATES_WITH]-(connected:Entity)
// WHERE connected.risk_score > 0.6
// RETURN e.entity_id, e.name, e.risk_score, 
//        collect(distinct connected.name) as connected_high_risk_entities,
//        count(distinct connected) as cluster_size
// ORDER BY cluster_size DESC, e.risk_score DESC

// ============================================================================
// GRAPH ALGORITHMS (using GDS library)
// ============================================================================

// PageRank for entity importance
// CALL gds.pageRank.stream('entity-graph')
// YIELD nodeId, score
// RETURN gds.util.asNode(nodeId).name AS name, score
// ORDER BY score DESC
// LIMIT 20

// Community detection for risk clusters
// CALL gds.louvain.stream('entity-graph')
// YIELD nodeId, communityId
// RETURN gds.util.asNode(nodeId).name AS name, communityId
// ORDER BY communityId

// Shortest path for risk propagation
// MATCH (source:Entity {entity_id: 'counterparty_001'}),
//       (target:Entity {entity_id: 'portfolio_001'})
// CALL gds.shortestPath.dijkstra.stream('entity-graph', {
//   sourceNode: source,
//   targetNode: target,
//   relationshipWeightProperty: 'weight'
// })
// YIELD path
// RETURN path

// ============================================================================
// MAINTENANCE QUERIES
// ============================================================================

// Update entity risk scores
// MATCH (e:Entity {entity_id: $entity_id})
// SET e.risk_score = $new_risk_score,
//     e.updated_at = datetime()

// Delete old risk events (older than 1 year)
// MATCH (r:RiskEvent)
// WHERE r.timestamp < datetime() - duration({days: 365})
// DETACH DELETE r

// Archive old market conditions
// MATCH (m:MarketCondition)
// WHERE m.timestamp < datetime() - duration({days: 90})
// SET m:Archived
// REMOVE m:MarketCondition