import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';
import { Box, CircularProgress, ToggleButtonGroup, ToggleButton } from '@mui/material';

const RiskDistribution = ({
  data,
  width = 800,
  height = 400,
  type = 'histogram', // 'histogram', 'boxplot', 'violin'
  onTypeChange,
}) => {
  const svgRef = useRef(null);
  const [chartType, setChartType] = React.useState(type);

  useEffect(() => {
    if (!svgRef.current || !data || !data.length) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    // Dimensions and margins
    const margin = { top: 40, right: 40, bottom: 60, left: 60 };
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

    if (chartType === 'histogram') {
      drawHistogram(g, data, innerWidth, innerHeight);
    } else if (chartType === 'boxplot') {
      drawBoxPlot(g, data, innerWidth, innerHeight);
    } else if (chartType === 'violin') {
      drawViolinPlot(g, data, innerWidth, innerHeight);
    }

    // Add title
    svg
      .append('text')
      .attr('x', width / 2)
      .attr('y', 20)
      .attr('text-anchor', 'middle')
      .attr('font-size', '16px')
      .attr('font-weight', 'bold')
      .attr('fill', '#fff')
      .text(`Risk Distribution - ${chartType.charAt(0).toUpperCase() + chartType.slice(1)}`);

  }, [data, width, height, chartType]);

  const drawHistogram = (g, data, innerWidth, innerHeight) => {
    // Create histogram bins
    const xScale = d3
      .scaleLinear()
      .domain([0, 100])
      .range([0, innerWidth]);

    const histogram = d3
      .histogram()
      .domain(xScale.domain())
      .thresholds(xScale.ticks(20));

    const bins = histogram(data.map((d) => d.value));

    const yScale = d3
      .scaleLinear()
      .domain([0, d3.max(bins, (d) => d.length)])
      .nice()
      .range([innerHeight, 0]);

    // Color scale
    const colorScale = d3
      .scaleSequential()
      .domain([0, 100])
      .interpolator(d3.interpolateRdYlGn)
      .range([1, 0]);

    // Draw bars
    g.selectAll('rect')
      .data(bins)
      .join('rect')
      .attr('x', (d) => xScale(d.x0) + 1)
      .attr('y', (d) => yScale(d.length))
      .attr('width', (d) => Math.max(0, xScale(d.x1) - xScale(d.x0) - 2))
      .attr('height', (d) => innerHeight - yScale(d.length))
      .attr('fill', (d) => colorScale((d.x0 + d.x1) / 2))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1);

    // Add axes
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale));

    g.append('g').call(d3.axisLeft(yScale));

    // Add labels
    g.append('text')
      .attr('x', innerWidth / 2)
      .attr('y', innerHeight + 40)
      .attr('text-anchor', 'middle')
      .attr('fill', '#fff')
      .text('Risk Level');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -innerHeight / 2)
      .attr('y', -40)
      .attr('text-anchor', 'middle')
      .attr('fill', '#fff')
      .text('Frequency');
  };

  const drawBoxPlot = (g, data, innerWidth, innerHeight) => {
    const values = data.map((d) => d.value).sort(d3.ascending);
    
    // Calculate quartiles
    const q1 = d3.quantile(values, 0.25);
    const median = d3.quantile(values, 0.5);
    const q3 = d3.quantile(values, 0.75);
    const iqr = q3 - q1;
    const min = Math.max(d3.min(values), q1 - 1.5 * iqr);
    const max = Math.min(d3.max(values), q3 + 1.5 * iqr);

    const yScale = d3
      .scaleLinear()
      .domain([0, 100])
      .range([innerHeight, 0]);

    const boxWidth = 100;
    const center = innerWidth / 2;

    // Draw box
    g.append('rect')
      .attr('x', center - boxWidth / 2)
      .attr('y', yScale(q3))
      .attr('width', boxWidth)
      .attr('height', yScale(q1) - yScale(q3))
      .attr('fill', '#00bcd4')
      .attr('fill-opacity', 0.3)
      .attr('stroke', '#00bcd4')
      .attr('stroke-width', 2);

    // Draw median line
    g.append('line')
      .attr('x1', center - boxWidth / 2)
      .attr('x2', center + boxWidth / 2)
      .attr('y1', yScale(median))
      .attr('y2', yScale(median))
      .attr('stroke', '#fff')
      .attr('stroke-width', 3);

    // Draw whiskers
    g.append('line')
      .attr('x1', center)
      .attr('x2', center)
      .attr('y1', yScale(q3))
      .attr('y2', yScale(max))
      .attr('stroke', '#00bcd4')
      .attr('stroke-width', 2);

    g.append('line')
      .attr('x1', center)
      .attr('x2', center)
      .attr('y1', yScale(q1))
      .attr('y2', yScale(min))
      .attr('stroke', '#00bcd4')
      .attr('stroke-width', 2);

    // Draw whisker caps
    [min, max].forEach((value) => {
      g.append('line')
        .attr('x1', center - 20)
        .attr('x2', center + 20)
        .attr('y1', yScale(value))
        .attr('y2', yScale(value))
        .attr('stroke', '#00bcd4')
        .attr('stroke-width', 2);
    });

    // Draw outliers
    const outliers = values.filter((v) => v < min || v > max);
    g.selectAll('circle.outlier')
      .data(outliers)
      .join('circle')
      .attr('class', 'outlier')
      .attr('cx', center)
      .attr('cy', (d) => yScale(d))
      .attr('r', 4)
      .attr('fill', '#f44336')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1);

    // Add axis
    g.append('g').attr('transform', `translate(${center + boxWidth / 2 + 10},0)`).call(d3.axisRight(yScale));

    // Add statistics labels
    const stats = [
      { label: 'Max', value: max },
      { label: 'Q3', value: q3 },
      { label: 'Median', value: median },
      { label: 'Q1', value: q1 },
      { label: 'Min', value: min },
    ];

    stats.forEach((stat) => {
      g.append('text')
        .attr('x', center - boxWidth / 2 - 10)
        .attr('y', yScale(stat.value) + 5)
        .attr('text-anchor', 'end')
        .attr('fill', '#fff')
        .attr('font-size', '12px')
        .text(`${stat.label}: ${stat.value.toFixed(1)}`);
    });
  };

  const drawViolinPlot = (g, data, innerWidth, innerHeight) => {
    const values = data.map((d) => d.value);

    const yScale = d3
      .scaleLinear()
      .domain([0, 100])
      .range([innerHeight, 0]);

    // Create kernel density estimation
    const kde = kernelDensityEstimator(kernelEpanechnikov(7), yScale.ticks(50));
    const density = kde(values);

    const xScale = d3
      .scaleLinear()
      .domain([0, d3.max(density, (d) => d[1])])
      .range([0, innerWidth / 2 - 50]);

    const center = innerWidth / 2;

    // Create area generator
    const area = d3
      .area()
      .x0((d) => center - xScale(d[1]))
      .x1((d) => center + xScale(d[1]))
      .y((d) => yScale(d[0]))
      .curve(d3.curveCatmullRom);

    // Draw violin
    g.append('path')
      .datum(density)
      .attr('d', area)
      .attr('fill', '#00bcd4')
      .attr('fill-opacity', 0.5)
      .attr('stroke', '#00bcd4')
      .attr('stroke-width', 2);

    // Add median line
    const median = d3.quantile(values.sort(d3.ascending), 0.5);
    g.append('line')
      .attr('x1', center - 50)
      .attr('x2', center + 50)
      .attr('y1', yScale(median))
      .attr('y2', yScale(median))
      .attr('stroke', '#fff')
      .attr('stroke-width', 3);

    // Add axis
    g.append('g').attr('transform', `translate(${center + innerWidth / 2 - 40},0)`).call(d3.axisRight(yScale));
  };

  // Kernel density estimation functions
  function kernelDensityEstimator(kernel, X) {
    return function (V) {
      return X.map((x) => [x, d3.mean(V, (v) => kernel(x - v))]);
    };
  }

  function kernelEpanechnikov(k) {
    return function (v) {
      return Math.abs((v /= k)) <= 1 ? (0.75 * (1 - v * v)) / k : 0;
    };
  }

  const handleTypeChange = (event, newType) => {
    if (newType !== null) {
      setChartType(newType);
      if (onTypeChange) onTypeChange(newType);
    }
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
    <Box sx={{ width }}>
      {/* Chart type selector */}
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'center' }}>
        <ToggleButtonGroup
          value={chartType}
          exclusive
          onChange={handleTypeChange}
          size="small"
        >
          <ToggleButton value="histogram">Histogram</ToggleButton>
          <ToggleButton value="boxplot">Box Plot</ToggleButton>
          <ToggleButton value="violin">Violin Plot</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Box
        sx={{
          backgroundColor: 'background.paper',
          borderRadius: 1,
          overflow: 'hidden',
        }}
      >
        <svg ref={svgRef} style={{ display: 'block' }} />
      </Box>
    </Box>
  );
};

export default RiskDistribution;

// Made with Bob