import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';
import { Box, CircularProgress, Chip, Stack } from '@mui/material';

const TimeSeriesChart = ({
  data,
  width = 800,
  height = 400,
  series = [],
  showBrush = true,
  annotations = [],
  onBrushChange,
}) => {
  const svgRef = useRef(null);
  const [selectedSeries, setSelectedSeries] = useState(series.map((s) => s.id));

  useEffect(() => {
    if (!svgRef.current || !data || !data.length) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    // Dimensions and margins
    const margin = { top: 40, right: 120, bottom: showBrush ? 100 : 60, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    const brushHeight = 50;

    // Create SVG
    const svg = d3
      .select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    // Main chart group
    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Parse dates
    const parseTime = d3.timeParse('%Y-%m-%d');
    const dataWithDates = data.map((d) => ({
      ...d,
      date: parseTime(d.date) || new Date(d.date),
    }));

    // Create scales
    const xScale = d3
      .scaleTime()
      .domain(d3.extent(dataWithDates, (d) => d.date))
      .range([0, innerWidth]);

    const yScale = d3
      .scaleLinear()
      .domain([
        0,
        d3.max(dataWithDates, (d) =>
          Math.max(...series.map((s) => d[s.id] || 0))
        ),
      ])
      .nice()
      .range([innerHeight, 0]);

    // Color scale for series
    const colorScale = d3
      .scaleOrdinal()
      .domain(series.map((s) => s.id))
      .range(d3.schemeCategory10);

    // Create line generator
    const line = d3
      .line()
      .x((d) => xScale(d.date))
      .y((d, i, nodes) => {
        const seriesId = d3.select(nodes[i].parentNode).datum();
        return yScale(d[seriesId] || 0);
      })
      .curve(d3.curveMonotoneX);

    // Add grid lines
    g.append('g')
      .attr('class', 'grid')
      .attr('opacity', 0.1)
      .call(
        d3
          .axisLeft(yScale)
          .tickSize(-innerWidth)
          .tickFormat('')
      );

    // Draw lines for each series
    series.forEach((s) => {
      if (!selectedSeries.includes(s.id)) return;

      g.append('path')
        .datum(s.id)
        .attr('fill', 'none')
        .attr('stroke', colorScale(s.id))
        .attr('stroke-width', 2)
        .attr('d', () => {
          return d3
            .line()
            .x((d) => xScale(d.date))
            .y((d) => yScale(d[s.id] || 0))
            .curve(d3.curveMonotoneX)(dataWithDates);
        });

      // Add dots
      g.selectAll(`.dot-${s.id}`)
        .data(dataWithDates)
        .join('circle')
        .attr('class', `dot-${s.id}`)
        .attr('cx', (d) => xScale(d.date))
        .attr('cy', (d) => yScale(d[s.id] || 0))
        .attr('r', 3)
        .attr('fill', colorScale(s.id))
        .style('cursor', 'pointer')
        .on('mouseenter', function (event, d) {
          d3.select(this).attr('r', 5);
          
          // Show tooltip
          const tooltip = g
            .append('g')
            .attr('class', 'tooltip')
            .attr('transform', `translate(${xScale(d.date)},${yScale(d[s.id])})`);

          tooltip
            .append('rect')
            .attr('x', 10)
            .attr('y', -30)
            .attr('width', 120)
            .attr('height', 50)
            .attr('fill', 'rgba(0, 0, 0, 0.8)')
            .attr('rx', 4);

          tooltip
            .append('text')
            .attr('x', 70)
            .attr('y', -15)
            .attr('text-anchor', 'middle')
            .attr('fill', '#fff')
            .attr('font-size', '12px')
            .text(s.name);

          tooltip
            .append('text')
            .attr('x', 70)
            .attr('y', 5)
            .attr('text-anchor', 'middle')
            .attr('fill', '#fff')
            .attr('font-size', '14px')
            .attr('font-weight', 'bold')
            .text((d[s.id] || 0).toFixed(2));
        })
        .on('mouseleave', function () {
          d3.select(this).attr('r', 3);
          g.selectAll('.tooltip').remove();
        });
    });

    // Add annotations
    annotations.forEach((annotation) => {
      const annotationDate = parseTime(annotation.date) || new Date(annotation.date);
      const x = xScale(annotationDate);

      // Vertical line
      g.append('line')
        .attr('x1', x)
        .attr('y1', 0)
        .attr('x2', x)
        .attr('y2', innerHeight)
        .attr('stroke', '#ff9800')
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', '5,5')
        .attr('opacity', 0.6);

      // Label
      g.append('text')
        .attr('x', x)
        .attr('y', -10)
        .attr('text-anchor', 'middle')
        .attr('fill', '#ff9800')
        .attr('font-size', '12px')
        .text(annotation.label);
    });

    // Add X axis
    const xAxis = d3.axisBottom(xScale).ticks(10);
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(xAxis);

    // Add Y axis
    const yAxis = d3.axisLeft(yScale);
    g.append('g').call(yAxis);

    // Add Y axis label
    svg
      .append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', 15)
      .attr('text-anchor', 'middle')
      .attr('fill', '#fff')
      .text('Risk Level');

    // Add title
    svg
      .append('text')
      .attr('x', width / 2)
      .attr('y', 20)
      .attr('text-anchor', 'middle')
      .attr('font-size', '16px')
      .attr('font-weight', 'bold')
      .attr('fill', '#fff')
      .text('Risk Over Time');

    // Add legend
    const legend = svg
      .append('g')
      .attr('transform', `translate(${width - margin.right + 10},${margin.top})`);

    series.forEach((s, i) => {
      const legendRow = legend
        .append('g')
        .attr('transform', `translate(0,${i * 25})`)
        .style('cursor', 'pointer')
        .on('click', () => {
          setSelectedSeries((prev) =>
            prev.includes(s.id) ? prev.filter((id) => id !== s.id) : [...prev, s.id]
          );
        });

      legendRow
        .append('rect')
        .attr('width', 15)
        .attr('height', 15)
        .attr('fill', colorScale(s.id))
        .attr('opacity', selectedSeries.includes(s.id) ? 1 : 0.3);

      legendRow
        .append('text')
        .attr('x', 20)
        .attr('y', 12)
        .attr('fill', '#fff')
        .attr('font-size', '12px')
        .text(s.name);
    });

    // Add brush for zooming
    if (showBrush) {
      const brushG = svg
        .append('g')
        .attr('transform', `translate(${margin.left},${height - brushHeight - 20})`);

      const brushXScale = d3
        .scaleTime()
        .domain(xScale.domain())
        .range([0, innerWidth]);

      const brushYScale = d3
        .scaleLinear()
        .domain(yScale.domain())
        .range([brushHeight, 0]);

      // Draw mini chart
      series.forEach((s) => {
        if (!selectedSeries.includes(s.id)) return;

        brushG
          .append('path')
          .datum(dataWithDates)
          .attr('fill', 'none')
          .attr('stroke', colorScale(s.id))
          .attr('stroke-width', 1)
          .attr('d',
            d3
              .line()
              .x((d) => brushXScale(d.date))
              .y((d) => brushYScale(d[s.id] || 0))
              .curve(d3.curveMonotoneX)
          );
      });

      // Add brush
      const brush = d3
        .brushX()
        .extent([
          [0, 0],
          [innerWidth, brushHeight],
        ])
        .on('brush end', (event) => {
          if (!event.selection) return;
          const [x0, x1] = event.selection.map(brushXScale.invert);
          if (onBrushChange) {
            onBrushChange([x0, x1]);
          }
        });

      brushG.append('g').attr('class', 'brush').call(brush);
    }
  }, [data, width, height, series, selectedSeries, showBrush, annotations, onBrushChange]);

  const handleSeriesToggle = (seriesId) => {
    setSelectedSeries((prev) =>
      prev.includes(seriesId) ? prev.filter((id) => id !== seriesId) : [...prev, seriesId]
    );
  };

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
    <Box sx={{ width, position: 'relative' }}>
      <Box
        sx={{
          backgroundColor: 'background.paper',
          borderRadius: 1,
          overflow: 'hidden',
        }}
      >
        <svg ref={svgRef} style={{ display: 'block' }} />
      </Box>

      {/* Series selector chips */}
      <Stack direction="row" spacing={1} sx={{ mt: 2, flexWrap: 'wrap' }}>
        {series.map((s) => (
          <Chip
            key={s.id}
            label={s.name}
            onClick={() => handleSeriesToggle(s.id)}
            color={selectedSeries.includes(s.id) ? 'primary' : 'default'}
            variant={selectedSeries.includes(s.id) ? 'filled' : 'outlined'}
            size="small"
          />
        ))}
      </Stack>
    </Box>
  );
};

export default TimeSeriesChart;

// Made with Bob