"""
Market Data Ingestion Script
Loads market data from CSV/JSON files into the database
"""

import os
import sys
import logging
import argparse
import json
import csv
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.connectors import PostgreSQLConnector
from backend.services.data_ingestion_service import DataIngestionService
from backend.services.data_validator import DataValidator
from backend.connectors import Neo4jConnector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_csv(file_path: str):
    """Load data from CSV file"""
    data = []
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def load_json(file_path: str):
    """Load data from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description='Ingest market data')
    parser.add_argument('file', help='Path to data file (CSV or JSON)')
    parser.add_argument('--validate', action='store_true', help='Validate data before ingestion')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for ingestion')
    args = parser.parse_args()
    
    # Load data
    logger.info(f"Loading data from {args.file}")
    if args.file.endswith('.csv'):
        data = load_csv(args.file)
    elif args.file.endswith('.json'):
        data = load_json(args.file)
    else:
        logger.error("Unsupported file format. Use CSV or JSON")
        return 1
    
    logger.info(f"Loaded {len(data)} records")
    
    # Validate if requested
    if args.validate:
        logger.info("Validating data...")
        validator = DataValidator()
        valid_data = []
        for record in data:
            if validator.validate_market_data(record):
                valid_data.append(record)
        
        logger.info(f"Validation complete: {len(valid_data)}/{len(data)} records valid")
        data = valid_data
    
    # Initialize connectors
    pg_connector = PostgreSQLConnector()
    neo4j_connector = Neo4jConnector()
    
    # Initialize ingestion service
    service = DataIngestionService(
        pg_connector=pg_connector,
        neo4j_connector=neo4j_connector,
        batch_size=args.batch_size
    )
    
    try:
        # Ingest data
        logger.info("Ingesting market data...")
        result = service.ingest_market_data(data)
        
        logger.info(f"Ingestion complete:")
        logger.info(f"  Total: {result['total_records']}")
        logger.info(f"  Successful: {result['successful']}")
        logger.info(f"  Failed: {result['failed']}")
        
        return 0 if result['failed'] == 0 else 1
        
    finally:
        service.close()
        pg_connector.close()
        neo4j_connector.close()


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
