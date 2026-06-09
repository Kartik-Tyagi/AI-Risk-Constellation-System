"""
Unified Data Ingestion Script
Ingests transactions, portfolios, and builds graph from data files
"""

import os
import sys
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.connectors import PostgreSQLConnector, Neo4jConnector
from backend.services.data_ingestion_service import DataIngestionService
from backend.services.graph_builder_service import GraphBuilderService
from backend.services.data_validator import DataValidator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_json_file(file_path: str):
    """Load JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)


def ingest_transactions(service: DataIngestionService, file_path: str, validate: bool = True):
    """Ingest transactions from file"""
    logger.info(f"Loading transactions from {file_path}")
    data = load_json_file(file_path)
    
    if validate:
        validator = DataValidator()
        valid_data = [d for d in data if validator.validate_transaction(d)]
        logger.info(f"Validated {len(valid_data)}/{len(data)} transactions")
        data = valid_data
    
    result = service.ingest_transactions(data)
    logger.info(f"Transactions: {result['successful']}/{result['total_records']} ingested")
    return result


def ingest_portfolios(service: DataIngestionService, file_path: str):
    """Ingest portfolios from file"""
    logger.info(f"Loading portfolios from {file_path}")
    data = load_json_file(file_path)
    
    # Ingest portfolio positions
    total_positions = 0
    for portfolio in data:
        if 'positions' in portfolio:
            result = service.ingest_portfolio_positions(portfolio['positions'])
            successful = result.get('successful', 0)
            if isinstance(successful, int):
                total_positions += successful
    
    logger.info(f"Portfolios: {len(data)} portfolios, {total_positions} positions ingested")
    return {'portfolios': len(data), 'positions': total_positions}


def build_graph(graph_service: GraphBuilderService, file_path: str):
    """Build graph from portfolio data"""
    logger.info(f"Building graph from {file_path}")
    data = load_json_file(file_path)
    
    stats = graph_service.build_graph_from_portfolios(data)
    logger.info(f"Graph built: {stats}")
    return stats


def main():
    parser = argparse.ArgumentParser(description='Ingest all data types')
    parser.add_argument('--transactions', help='Path to transactions JSON file')
    parser.add_argument('--portfolios', help='Path to portfolios JSON file')
    parser.add_argument('--build-graph', help='Path to data for graph building')
    parser.add_argument('--validate', action='store_true', help='Validate data')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size')
    args = parser.parse_args()
    
    if not any([args.transactions, args.portfolios, args.build_graph]):
        parser.print_help()
        return 1
    
    # Initialize services
    pg_connector = PostgreSQLConnector()
    neo4j_connector = Neo4jConnector()
    ingestion_service = DataIngestionService(pg_connector, neo4j_connector, batch_size=args.batch_size)
    graph_service = GraphBuilderService(neo4j_connector)
    
    try:
        # Ingest transactions
        if args.transactions:
            ingest_transactions(ingestion_service, args.transactions, args.validate)
        
        # Ingest portfolios
        if args.portfolios:
            ingest_portfolios(ingestion_service, args.portfolios)
        
        # Build graph
        if args.build_graph:
            build_graph(graph_service, args.build_graph)
        
        logger.info("All ingestion tasks completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return 1
    finally:
        ingestion_service.close()
        pg_connector.close()
        neo4j_connector.close()


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
