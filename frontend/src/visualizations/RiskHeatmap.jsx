import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';
import { Box, CircularProgress, Tooltip as MuiTooltip } from '@mui/material';

const RiskHeatmap = ({
  data,
  width = 800,
  height = 600,
  onCellClick,
  onCellHover,
}) => {
  const svgRef = useRef(null);
  const [hoveredCell, setHoveredCell] = useState(null);

  useEffect(() => {
    if (!svgRef.current || !data || !data.length) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    // Dimensions and margins
    const margin = { top: 60, right: 100, bottom: 60, left: 100 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create SVG
    const svg = d3
      .select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Extract unique x and y values
    const xValues = [...new Set(data.map((d) => d.x))].sort();
    const yValues = [...new Set(data.map((d) => d.y))].sort();

    // Create scales
    const xScale = d3
      .scaleBand()
      .domain(xValues)
      .range([0, innerWidth])
      .padding(0.05);

    const yScale = d3
      .scaleBand()
      .domain(yValues)
      .range([0, innerHeight])
      .padding(0.05);

    // Color scale for risk levels
    const colorScale = d3
      .scaleSequential()
      .domain([0, 100])
      .interpolator(d3.interpolateRdYlGn)
      .range([1, 0]); // Reverse so red is high risk

    // Add zoom behavior
    const zoom = d3
      .zoom()
      .scaleExtent([0.5, 5])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create cells
    const cells = g
      .selectAll('rect')
      .data(data)
      .join('rect')
      .attr('x', (d) => xScale(d.x))
      .attr('y', (d) => yScale(d.y))
      .attr('width', xScale.bandwidth())
      .attr('height', yScale.bandwidth())
      .attr('fill', (d) => colorScale(d.value))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation();
        if (onCellClick) onCellClick(d);
      })
      .on('mouseenter', (event, d) => {
        setHoveredCell(d);
        if (onCellHover) onCellHover(d);
        
        // Highlight cell
        d3.select(event.currentTarget)
          .attr('stroke', '#000')
          .attr('stroke-width', 3);
      })
      .on('mouseleave', (event) => {
        setHoveredCell(null);
        if (onCellHover) onCellHover(null);
        
        // Reset cell
        d3.select(event.currentTarget)
          .attr('stroke', '#fff')
          .attr('stroke-width', 1);
      });

    // Add cell values (if cells are large enough)
    if (xScale.bandwidth() > 40 && yScale.bandwidth() > 40) {
      g.selectAll('text.cell-value')
        .data(data)
        .join('text')
        .attr('class', 'cell-value')
        .attr('x', (d) => xScale(d.x) + xScale.bandwidth() / 2)
        .attr('y', (d) => yScale(d.y) + yScale.bandwidth() / 2)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', (d) => (d.value > 50 ? '#fff' : '#000'))
        .attr('font-size', '12px')
        .attr('font-weight', 'bold')
        .style('pointer-events', 'none')
        .text((d) => d.value.toFixed(0));
    }

    // Add X axis
    const xAxis = d3.axisBottom(xScale);
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(xAxis)
      .selectAll('text')
      .attr('transform', 'rotate(-45)')
      .style('text-anchor', 'end')
      .attr('dx', '-.8em')
      .attr('dy', '.15em');

    // Add Y axis
    const yAxis = d3.axisLeft(yScale);
    g.append('g').call(yAxis);

    // Add X axis label
    svg
      .append('text')
      .attr('x', width / 2)
      .attr('y', height - 10)
      .attr('text-anchor', 'middle')
      .attr('fill', '#fff')
      .text('Entities');

    // Add Y axis label
    svg
      .append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', 15)
      .attr('text-anchor', 'middle')
      .attr('fill', '#fff')
      .text('Time Periods');

    // Add title
    svg
      .append('text')
      .attr('x', width / 2)
      .attr('y', 25)
      .attr('text-anchor', 'middle')
      .attr('font-size', '18px')
      .attr('font-weight', 'bold')
      .attr('fill', '#fff')
      .text('Risk Heatmap');

    // Add color legend
    const legendWidth = 20;
    const legendHeight = innerHeight;
    const legendScale = d3
      .scaleLinear()
      .domain([0, 100])
      .range([legendHeight, 0]);

    const legendAxis = d3.axisRight(legendScale).ticks(5);

    const legend = svg
      .append('g')
      .attr('transform', `translate(${width - margin.right + 20},${margin.top})`);

    // Create gradient
    const defs = svg.append('defs');
    const gradient = defs
      .append('linearGradient')
      .attr('id', 'risk-gradient')
      .attr('x1', '0%')
      .attr('y1', '100%')
      .attr('x2', '0%')
      .attr('y2', '0%');

    gradient
      .selectAll('stop')
      .data(d3.range(0, 1.01, 0.1))
      .join('stop')
      .attr('offset', (d) => `${d * 100}%`)
      .attr('stop-color', (d) => colorScale(d * 100));

    legend
      .append('rect')
      .attr('width', legendWidth)
      .attr('height', legendHeight)
      .style('fill', 'url(#risk-gradient)');

    legend.append('g').attr('transform', `translate(${legendWidth},0)`).call(legendAxis);

    legend
      .append('text')
      .attr('x', legendWidth / 2)
      .attr('y', -10)
      .attr('text-anchor', 'middle')
      .attr('fill', '#fff')
      .attr('font-size', '12px')
      .text('Risk Level');

  }, [data, width, height, onCellClick, onCellHover]);

  if (!data || !data.length) {
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
      
      {/* Hovered cell tooltip */}
      {hoveredCell && (
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
          <Box sx={{ fontWeight: 600 }}>{hoveredCell.label || `${hoveredCell.x}, ${hoveredCell.y}`}</Box>
          <Box sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>
            Risk: {hoveredCell.value.toFixed(1)}%
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default RiskHeatmap;

// Made with Bob