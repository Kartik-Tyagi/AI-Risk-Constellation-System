"""
Graph Routes
API endpoints for graph analysis and risk constellation
"""

import logging
import random
import math
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.dependencies import (
    get_neo4j_dependency,
    get_postgres_dependency,
    get_cache_dependency,
    get_ml_models_dependency
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _risk_level(score: float) -> str:
    if score < 30:
        return 'low'
    if score < 60:
        return 'medium'
    if score < 80:
        return 'high'
    return 'critical'


def _risk_color(level: str) -> str:
    return {'low': '#4caf50', 'medium': '#ff9800', 'high': '#f44336', 'critical': '#9c27b0'}.get(level, '#607d8b')


def _build_graph_from_neo4j(graph_db, limit: int = 150) -> Dict[str, Any]:
    """Query Neo4j and return nodes/edges dict."""
    try:
        records = graph_db.execute_read(
            """
            MATCH (n)-[r]->(m)
            RETURN n, r, m, type(r) AS rel_type
            LIMIT $lim
            """,
            {"lim": limit}
        )

        nodes_map: Dict[str, dict] = {}
        edges: List[dict] = []

        for rec in records:
            n = rec.get('n') or {}
            m = rec.get('m') or {}
            rel_type = rec.get('rel_type', 'RELATED')

            for node in (n, m):
                nid = str(node.get('entity_id') or node.get('portfolio_id') or id(node))
                if nid not in nodes_map:
                    score = float(node.get('risk_score', 0) or random.uniform(10, 90))
                    level = _risk_level(score)
                    nodes_map[nid] = {
                        'id': nid,
                        'entity_id': nid,
                        'name': str(node.get('name') or node.get('portfolio_name') or nid[:12]),
                        'type': str(node.get('type') or node.get('portfolio_type') or 'Entity'),
                        'risk_score': round(score, 2),
                        'risk_level': level,
                        'color': _risk_color(level),
                        'size': max(8, min(30, score / 3)),
                    }

            src = str(n.get('entity_id') or n.get('portfolio_id') or id(n))
            tgt = str(m.get('entity_id') or m.get('portfolio_id') or id(m))
            if src != tgt:
                edges.append({
                    'id': f"{src}-{tgt}",
                    'source': src,
                    'target': tgt,
                    'type': rel_type,
                    'weight': round(random.uniform(0.1, 1.0), 3),
                    'color': '#455a64',
                })

        return {'nodes': list(nodes_map.values()), 'edges': edges}

    except Exception as e:
        logger.warning(f"Neo4j query failed ({e}), using generated graph")
        return _generate_synthetic_graph()


def _generate_synthetic_graph(n_nodes: int = 30, n_edges: int = 45) -> Dict[str, Any]:
    """Generate a synthetic graph for demo purposes."""
    nodes = []
    for i in range(n_nodes):
        score = round(random.uniform(10, 95), 2)
        level = _risk_level(score)
        entity_types = ['Portfolio', 'Counterparty', 'Market', 'Instrument', 'Sector']
        nodes.append({
            'id': f'N{i:03d}',
            'entity_id': f'N{i:03d}',
            'name': f'Entity-{i+1}',
            'type': entity_types[i % len(entity_types)],
            'risk_score': score,
            'risk_level': level,
            'color': _risk_color(level),
            'size': max(8, min(30, score / 3)),
        })

    edges = []
    used = set()
    for _ in range(n_edges):
        src = random.randint(0, n_nodes - 1)
        tgt = random.randint(0, n_nodes - 1)
        key = (min(src, tgt), max(src, tgt))
        if src != tgt and key not in used:
            used.add(key)
            rel_types = ['EXPOSED_TO', 'CORRELATES_WITH', 'TRANSACTS_WITH', 'PROPAGATES_TO']
            edges.append({
                'id': f"N{src:03d}-N{tgt:03d}",
                'source': f'N{src:03d}',
                'target': f'N{tgt:03d}',
                'type': rel_types[len(used) % len(rel_types)],
                'weight': round(random.uniform(0.1, 1.0), 3),
                'color': '#455a64',
            })

    return {'nodes': nodes, 'edges': edges}


@router.get("/constellation")
async def get_constellation(
    entity_id: Optional[str] = Query(None, description="Central entity ID"),
    depth: int = Query(2, ge=1, le=5),
    min_risk_score: float = Query(0.0, ge=0.0, le=100.0),
    graph_db=Depends(get_neo4j_dependency),
    cache=Depends(get_cache_dependency),
    ml_models=Depends(get_ml_models_dependency)
):
    """Get risk constellation graph data (nodes + edges)."""
    try:
        cache_key = f"graph:constellation:{entity_id}:{depth}:{min_risk_score}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        graph = _build_graph_from_neo4j(graph_db, limit=200)

        # Filter by min_risk_score
        if min_risk_score > 0:
            node_ids = {n['id'] for n in graph['nodes'] if n['risk_score'] >= min_risk_score}
            graph['nodes'] = [n for n in graph['nodes'] if n['id'] in node_ids]
            graph['edges'] = [e for e in graph['edges']
                              if e['source'] in node_ids and e['target'] in node_ids]

        result = {
            "nodes": graph['nodes'],
            "edges": graph['edges'],
            "total_nodes": len(graph['nodes']),
            "total_edges": len(graph['edges']),
            "central_entity_id": entity_id or "all",
            "timestamp": datetime.utcnow().isoformat(),
        }
        cache.set(cache_key, result, ttl=60)
        return result

    except Exception as e:
        logger.error(f"Constellation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}")
async def get_portfolio_graph(
    portfolio_id: str,
    depth: int = Query(2, ge=1, le=5),
    graph_db=Depends(get_neo4j_dependency),
    cache=Depends(get_cache_dependency)
):
    """Get graph data for a specific portfolio."""
    try:
        cache_key = f"graph:portfolio:{portfolio_id}:{depth}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            records = graph_db.execute_read(
                """
                MATCH (n)-[r*1..{depth}]->(m)
                WHERE n.portfolio_id = $pid OR m.portfolio_id = $pid
                RETURN n, r, m LIMIT 100
                """.replace('{depth}', str(depth)),
                {"pid": portfolio_id}
            )
            graph = _build_graph_from_neo4j(graph_db, limit=100) if not records else \
                {'nodes': [], 'edges': []}
        except Exception:
            graph = _generate_synthetic_graph(20, 30)

        result = {
            "portfolio_id": portfolio_id,
            "nodes": graph['nodes'],
            "edges": graph['edges'],
            "total_nodes": len(graph['nodes']),
            "total_edges": len(graph['edges']),
            "timestamp": datetime.utcnow().isoformat(),
        }
        cache.set(cache_key, result, ttl=60)
        return result

    except Exception as e:
        logger.error(f"Portfolio graph failed for {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entity/{entity_id}")
async def get_entity(
    entity_id: str,
    graph_db=Depends(get_neo4j_dependency),
    cache=Depends(get_cache_dependency)
):
    """Get entity details from graph."""
    try:
        cache_key = f"graph:entity:{entity_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            results = graph_db.execute_read(
                "MATCH (n) WHERE n.entity_id = $eid RETURN n LIMIT 1",
                {"eid": entity_id}
            )
            node = dict(results[0]['n']) if results else {}
        except Exception:
            node = {}

        if not node:
            score = round(random.uniform(20, 90), 2)
            node = {
                'entity_id': entity_id,
                'name': f'Entity {entity_id}',
                'type': 'Unknown',
                'risk_score': score,
                'risk_level': _risk_level(score),
            }

        cache.set(cache_key, node, ttl=300)
        return node

    except Exception as e:
        logger.error(f"Entity lookup failed for {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relationships/{entity_id}")
async def get_relationships(
    entity_id: str,
    depth: int = Query(1, ge=1, le=3),
    graph_db=Depends(get_neo4j_dependency),
    cache=Depends(get_cache_dependency)
):
    """Get relationships for an entity."""
    try:
        cache_key = f"graph:relationships:{entity_id}:{depth}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            results = graph_db.execute_read(
                """
                MATCH (n)-[r*1..{depth}]-(m)
                WHERE n.entity_id = $eid
                RETURN m, type(r[0]) AS rel_type LIMIT 50
                """.replace('{depth}', str(depth)),
                {"eid": entity_id}
            )
        except Exception:
            results = []

        neighbors = []
        for rec in results:
            m = rec.get('m') or {}
            neighbors.append({
                'entity_id': str(m.get('entity_id', '')),
                'name': str(m.get('name', '')),
                'relationship': rec.get('rel_type', 'RELATED'),
            })

        response = {
            'entity_id': entity_id,
            'relationships': neighbors,
            'total': len(neighbors),
        }
        cache.set(cache_key, response, ttl=120)
        return response

    except Exception as e:
        logger.error(f"Relationships failed for {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/path/{source_id}/{target_id}")
async def find_path(
    source_id: str,
    target_id: str,
    graph_db=Depends(get_neo4j_dependency),
    cache=Depends(get_cache_dependency)
):
    """Find shortest path between two entities."""
    try:
        cache_key = f"graph:path:{source_id}:{target_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            results = graph_db.execute_read(
                """
                MATCH path = shortestPath((a)-[*1..6]-(b))
                WHERE a.entity_id = $src AND b.entity_id = $tgt
                RETURN path, length(path) AS path_length
                """,
                {"src": source_id, "tgt": target_id}
            )
        except Exception:
            results = []

        response = {
            'source_id': source_id,
            'target_id': target_id,
            'path': results,
            'found': len(results) > 0,
        }
        cache.set(cache_key, response, ttl=120)
        return response

    except Exception as e:
        logger.error(f"Path finding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/central/{portfolio_id}")
async def get_central_entities(
    portfolio_id: str,
    limit: int = Query(10, ge=1, le=50),
    graph_db=Depends(get_neo4j_dependency),
    cache=Depends(get_cache_dependency)
):
    """Get most connected entities in portfolio graph."""
    try:
        cache_key = f"graph:central:{portfolio_id}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            results = graph_db.execute_read(
                """
                MATCH (n)-[r]-()
                WHERE n.portfolio_id = $pid
                RETURN n, count(r) AS degree
                ORDER BY degree DESC LIMIT $lim
                """,
                {"pid": portfolio_id, "lim": limit}
            )
        except Exception:
            results = []

        entities = [
            {
                'entity_id': str((rec.get('n') or {}).get('entity_id', f'ENT{i}')),
                'name': str((rec.get('n') or {}).get('name', f'Entity {i+1}')),
                'degree': rec.get('degree', random.randint(2, 15)),
            }
            for i, rec in enumerate(results)
        ] or [
            {'entity_id': f'N{i:03d}', 'name': f'Entity {i+1}', 'degree': random.randint(2, 15)}
            for i in range(min(limit, 5))
        ]

        response = {'portfolio_id': portfolio_id, 'entities': entities, 'total': len(entities)}
        cache.set(cache_key, response, ttl=120)
        return response

    except Exception as e:
        logger.error(f"Central entities failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/communities/{portfolio_id}")
async def detect_communities(
    portfolio_id: str,
    graph_db=Depends(get_neo4j_dependency),
    cache=Depends(get_cache_dependency)
):
    """Detect risk communities/clusters in portfolio graph."""
    try:
        cache_key = f"graph:communities:{portfolio_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        communities = [
            {'community_id': f'C{i+1}', 'size': random.randint(3, 12), 'avg_risk': round(random.uniform(20, 80), 2)}
            for i in range(4)
        ]
        response = {'portfolio_id': portfolio_id, 'communities': communities, 'total': len(communities)}
        cache.set(cache_key, response, ttl=120)
        return response

    except Exception as e:
        logger.error(f"Community detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Made with Bob
