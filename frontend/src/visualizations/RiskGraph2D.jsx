import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { Box, CircularProgress } from '@mui/material';
import {
  transformGraphData,
  calculateNodeSize,
  getNodeColor,
  getNodeColorByType,
  getEdgeColor,
  getEdgeWidth,
} from '../utils/graphUtils';

const RiskGraph2D = ({
  data,
  width = 800,
  height = 600,
  onNodeClick,
  onNodeDoubleClick,
  onNodeHover,
  colorScheme = 'risk',
  sizeBy = 'riskScore',
  showLabels = true,
  animateTransitions = true,
}) => {
  const svgRef = useRef(null);
  const simulationRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);

  // Transform and prepare graph data
  const graphData = transformGraphData(data);

  // Initialize D3 force simulation
  const initializeSimulation = useCallback(() => {
    if (!graphData.nodes.length) return null;

    const simulation = d3
      .forceSimulation(graphData.nodes)
      .force(
        'link',
        d3
          .forceLink(graphData.links)
          .id((d) => d.id)
          .distance((d) => 100 - d.weight * 50) // Closer for stronger connections
          .strength((d) => d.weight * 0.5)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius((d) => calculateNodeSize(d, { sizeBy }) + 5))
      .alphaDecay(0.02)
      .velocityDecay(0.3);

    return simulation;
  }, [graphData, width, height, sizeBy]);

  // Render graph
  useEffect(() => {
    if (!svgRef.current || !graphData.nodes.length) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    // Create SVG
    const svg = d3
      .select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);

    // Add zoom behavior
    const g = svg.append('g');
    
    const zoom = d3
      .zoom()
      .scaleExtent([0.1, 10])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create arrow markers for directed edges
    svg
      .append('defs')
      .selectAll('marker')
      .data(['end'])
      .join('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#999');

    // Create links
    const link = g
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(graphData.links)
      .join('line')
      .attr('stroke', (d) => getEdgeColor(d.riskContribution))
      .attr('stroke-width', (d) => getEdgeWidth(d.weight))
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', 'url(#arrowhead)');

    // Create nodes
    const node = g
      .append('g')
      .attr('class', 'nodes')
      .selectAll('circle')
      .data(graphData.nodes)
      .join('circle')
      .attr('r', (d) => calculateNodeSize(d, { sizeBy }))
      .attr('fill', (d) =>
        colorScheme === 'risk' ? getNodeColor(d.riskLevel) : getNodeColorByType(d.type)
      )
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .call(drag(simulationRef.current));

    // Add labels
    let label = null;
    if (showLabels) {
      label = g
        .append('g')
        .attr('class', 'labels')
        .selectAll('text')
        .data(graphData.nodes)
        .join('text')
        .text((d) => d.name)
        .attr('font-size', 10)
        .attr('dx', 12)
        .attr('dy', 4)
        .attr('fill', '#fff')
        .style('pointer-events', 'none')
        .style('user-select', 'none');
    }

    // Node interactions
    node
      .on('click', (event, d) => {
        event.stopPropagation();
        setSelectedNode(d);
        if (onNodeClick) onNodeClick(d);
      })
      .on('dblclick', (event, d) => {
        event.stopPropagation();
        if (onNodeDoubleClick) onNodeDoubleClick(d);
      })
      .on('mouseenter', (event, d) => {
        setHoveredNode(d);
        if (onNodeHover) onNodeHover(d);
        
        // Highlight connected nodes and links
        node.style('opacity', (n) => (isConnected(d, n) ? 1 : 0.3));
        link.style('opacity', (l) =>
          l.source.id === d.id || l.target.id === d.id ? 1 : 0.1
        );
      })
      .on('mouseleave', () => {
        setHoveredNode(null);
        if (onNodeHover) onNodeHover(null);
        
        // Reset opacity
        node.style('opacity', 1);
        link.style('opacity', 0.6);
      });

    // Helper function to check if nodes are connected
    function isConnected(a, b) {
      if (a.id === b.id) return true;
      return graphData.links.some(
        (l) =>
          (l.source.id === a.id && l.target.id === b.id) ||
          (l.source.id === b.id && l.target.id === a.id)
      );
    }

    // Initialize simulation
    const simulation = initializeSimulation();
    simulationRef.current = simulation;

    if (simulation) {
      simulation.on('tick', () => {
        link
          .attr('x1', (d) => d.source.x)
          .attr('y1', (d) => d.source.y)
          .attr('x2', (d) => d.target.x)
          .attr('y2', (d) => d.target.y);

        node.attr('cx', (d) => d.x).attr('cy', (d) => d.y);

        if (label) {
          label.attr('x', (d) => d.x).attr('y', (d) => d.y);
        }
      });
    }

    // Cleanup
    return () => {
      if (simulationRef.current) {
        simulationRef.current.stop();
      }
    };
  }, [
    graphData,
    width,
    height,
    colorScheme,
    sizeBy,
    showLabels,
    onNodeClick,
    onNodeDoubleClick,
    onNodeHover,
    initializeSimulation,
  ]);

  // Drag behavior
  const drag = (simulation) => {
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return d3.drag().on('start', dragstarted).on('drag', dragged).on('end', dragended);
  };

  // Restart simulation when data changes
  useEffect(() => {
    if (simulationRef.current && animateTransitions) {
      simulationRef.current.alpha(1).restart();
    }
  }, [graphData, animateTransitions]);

  if (!data || !graphData.nodes.length) {
    return (
      <Box
        sx={{
          width,
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'background.paper',
          borderRadius: 1,
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        width,
        height,
        backgroundColor: 'background.paper',
        borderRadius: 1,
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      <svg ref={svgRef} style={{ display: 'block' }} />
      
      {/* Selected node indicator */}
      {selectedNode && (
        <Box
          sx={{
            position: 'absolute',
            bottom: 16,
            left: 16,
            backgroundColor: 'background.default',
            padding: 2,
            borderRadius: 1,
            border: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Box sx={{ fontWeight: 600 }}>{selectedNode.name}</Box>
          <Box sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>
            Risk: {selectedNode.riskLevel.toFixed(1)}%
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default RiskGraph2D;

// Made with Bob